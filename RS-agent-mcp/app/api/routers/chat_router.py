"""
聊天相关路由器
处理所有聊天相关的API端点
"""

from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from typing import List, Optional
from pathlib import Path
import json
import asyncio
import logging
import uuid
import os

from ...services import file_manager
from ...services.file_storage import file_storage_manager
from ...agent import agent
from ...api.progress import report_progress
from ...services.billing.billing_tracker import get_billing_tracker
from ...services.auth.auth_service import get_auth_service
from ...services.billing.credit_service import get_credit_service
from ...services.session.chat_service import get_chat_session_service
from ...core.config import get_settings

# 配置日志
logger = logging.getLogger(__name__)

router = APIRouter()

# 请求模型
class ChatRequest(BaseModel):
    message: str
    stream: bool = False
    files: Optional[List[str]] = None  # 为未来文件上传预留
    session_id: Optional[str] = None  # 会话ID，用于进度跟踪
    token: Optional[str] = None  # RSHub token，生产环境从前端传入
    chat_id: Optional[str] = None  # 会话ID，用于会话管理

class ChatResponse(BaseModel):
    response: str
    status: str = "success"
    task_type: Optional[int] = None  # 返回任务类型，用于调试和未来扩展
    session_id: Optional[str] = None  # 返回会话ID给前端
    source_files: Optional[List[dict]] = None  # 源文件信息
    billing_info: Optional[dict] = None  # 计费信息
    credit_info: Optional[dict] = None  # 信用信息
    chat_id: Optional[str] = None  # 返回会话ID给前端
    chat_title: Optional[str] = None  # 返回会话标题给前端

# 新增的知识问答响应模型
class KnowledgeChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None

class KnowledgeChatResponse(BaseModel):
    answer: str
    sources: List[dict] = []
    status: str = "success"
    session_id: Optional[str] = None
    keywords_used: Optional[List[str]] = None

@router.post("/agent/chat", response_model=ChatResponse)
async def agent_chat(request: ChatRequest):
    """
    Agent聊天端点 - 遵循标准两阶段工作流，支持会话管理
    
    Stage 1: instruction=0 进行任务分类
    Stage 2: 根据分类结果调用相应的instruction执行具体任务
    
    !! 进度回报重要说明 !!
    当添加新功能时，请在关键步骤调用 report_progress() 函数来向前端实时反馈进度：
    - 任务开始: report_progress(session_id, "正在初始化任务...", "init")  
    - 分析阶段: report_progress(session_id, "正在分析用户意图...", "analyzing")
    - 处理阶段: report_progress(session_id, "正在处理数据...", "processing")
    - LLM调用: report_progress(session_id, "正在调用AI模型...", "llm_call")
    - 任务完成: report_progress(session_id, "任务完成", "completed")
    
    Args:
        request: 包含用户消息、是否流式响应、会话ID的请求
    
    Returns:
        Agent的响应，包含任务类型信息、会话ID、会话标题
    """
    session_path = None
    file_paths = request.files or []  # 为未来文件上传预留
    
    # 生成或使用提供的会话ID
    session_id = request.session_id or str(uuid.uuid4())
    
    # 获取计费跟踪器、认证服务、credit服务和会话服务
    billing_tracker = get_billing_tracker()
    auth_service = get_auth_service()
    credit_service = get_credit_service()
    chat_session_service = get_chat_session_service()
    settings = get_settings()
    
    # 会话管理相关变量
    chat_history = []
    chat_id = request.chat_id
    chat_title = None
    is_new_chat = not chat_id
    
    try:
        # === 认证处理 ===
        try:
            rshub_token = auth_service.get_rshub_token(request.token)
        except ValueError as e:
            raise HTTPException(status_code=401, detail=str(e))
        
        # === 会话历史加载 ===
        chat_history = []  # 初始化为空列表
        if chat_id:
            # 如果提供了会话ID，加载会话历史
            session_data = await chat_session_service.load_session(rshub_token, chat_id)
            if session_data:
                all_messages = session_data.get("messages", [])
                # 限制加载的历史消息数量（防止内存爆炸）
                max_load_messages = 30  # 最多加载30条历史消息用于上下文
                if len(all_messages) > max_load_messages:
                    # 保留前2条（初始对话）和最后N-2条
                    chat_history = all_messages[:2] + all_messages[-(max_load_messages-2):]
                    logger.info(f"会话历史较长({len(all_messages)}条)，已截断为{len(chat_history)}条用于上下文")
                else:
                    chat_history = all_messages
                chat_title = session_data.get("title", "对话")
                logger.info(f"加载了会话 {chat_id}，包含 {len(all_messages)} 条历史消息（使用 {len(chat_history)} 条作为上下文）")
            else:
                logger.warning(f"无法加载会话 {chat_id}，将作为新会话处理")
                chat_id = None
                is_new_chat = True
        else:
            # 如果没有提供chat_id，尝试查找最近的会话（用于连续对话）
            logger.info("未提供chat_id，尝试查找最近的会话...")
            latest_session = await chat_session_service.find_latest_session(rshub_token)
            if latest_session:
                chat_id = latest_session.get("session_id")
                all_messages = latest_session.get("messages", [])
                # 限制加载的历史消息数量
                max_load_messages = 30
                if len(all_messages) > max_load_messages:
                    chat_history = all_messages[:2] + all_messages[-(max_load_messages-2):]
                    logger.info(f"会话历史较长({len(all_messages)}条)，已截断为{len(chat_history)}条用于上下文")
                else:
                    chat_history = all_messages
                chat_title = latest_session.get("title", "对话")
                is_new_chat = False
                logger.info(f"找到最近的会话 {chat_id}，包含 {len(all_messages)} 条历史消息（使用 {len(chat_history)} 条作为上下文）")
            else:
                logger.info("未找到最近的会话，将创建新会话")
                is_new_chat = True
        
        # 初始化计费会话
        billing_tracker.init_session(session_id)
        
        # === 进度回报：任务开始 ===
        report_progress(session_id, "正在初始化AI分析任务...", "init")
        
        # === 第一阶段：任务分类 (instruction=0) ===
        logger.info("🔍 Stage 1: 任务分类 - 分析用户意图...")
        report_progress(session_id, "正在分析您的问题类型...", "analyzing")
        
        task_type = await agent.run_analysis_agent(
            instruction_mode=0,  # 模式0：任务分类
            user_prompt=request.message,
            file_paths=file_paths,
            output_path=None,
            session_id=session_id,  # 传递会话ID到Agent
            rshub_token=rshub_token,
            chat_history=chat_history  # 传递会话历史
        )
        
        logger.info(f"📋 任务分类结果: {task_type}")
        report_progress(session_id, f"问题类型识别完成，准备执行任务...", "analyzing")
        
        # 验证任务类型
        if task_type == -100:
            # 用户主动中止请求
            report_progress(session_id, "用户已中止请求", "aborted")
            return ChatResponse(
                response="请求已被用户中止",
                status="user_aborted",
                task_type=task_type,
                session_id=session_id,
                chat_id=chat_id,
                chat_title=chat_title
            )
        
        elif task_type == -101:
            # LLM调用超时
            report_progress(session_id, "AI服务响应超时", "error")
            return ChatResponse(
                response="抱歉，AI服务响应超时，请稍后重试",
                status="llm_timeout",
                task_type=task_type,
                session_id=session_id,
                chat_id=chat_id,
                chat_title=chat_title
            )
        
        elif task_type == -102:
            # 网络连接错误
            report_progress(session_id, "网络连接错误", "error")
            return ChatResponse(
                response="抱歉，网络连接出现问题，请检查网络后重试",
                status="network_error",
                task_type=task_type,
                session_id=session_id,
                chat_id=chat_id,
                chat_title=chat_title
            )
        
        elif task_type == -103:
            # API认证或余额问题
            report_progress(session_id, "AI服务认证失败", "error")
            return ChatResponse(
                response="抱歉，AI服务暂时不可用，可能是认证或余额问题。请稍后重试或联系管理员。",
                status="api_error",
                task_type=task_type,
                session_id=session_id,
                chat_id=chat_id,
                chat_title=chat_title
            )
        
        elif task_type == 3 and not chat_history:
            # RSHub结果获取任务但没有会话历史，提供友好提示
            logger.info("检测到RSHub结果获取任务但没有会话历史，提供友好提示")
            report_progress(session_id, "检测到无历史任务，提供指导信息", "processing")
            
            # 直接返回友好提示，而不是执行RSHub工作流
            friendly_response = """
我理解您想获取之前的建模结果，但这是我们的第一次对话，还没有之前的任务记录。

要使用RSHub建模功能，请按以下步骤：

1. **首先提交建模任务**，例如：
   - "请帮我建立一个土壤湿度反演模型"
   - "根据这些参数生成雪地散射数据"
   - "创建植被参数反演模型"

2. **然后获取结果**，例如：
   - "请获取刚才建模任务的结果"
   - "可视化之前任务的输出数据"

您现在可以直接告诉我您想要进行什么类型的建模，我很乐意帮您！
            """
            
            # 计算计费信息
            billing_info = billing_tracker.calculate_cost(
                session_id,
                settings.LLM_COST_FACTOR,
                settings.RSHUB_TASK_COST_FACTOR
            )
            
            # === Credit扣费 (仅在生产模式下) ===
            credit_info = {}
            if settings.DEPLOYMENT_MODE == "production":
                actual_cost = billing_info["total_cost"]
                logger.info(f"💳 实际任务费用: {actual_cost} credits")
                
                if actual_cost > 0:
                    report_progress(session_id, "正在扣除费用...", "processing")
                    
                    deduct_success, deduct_message, remaining_credits = await credit_service.update_credits(
                        rshub_token, -actual_cost
                    )
                    if not isinstance(remaining_credits, (int, float)) or remaining_credits < 0:
                        remaining_credits = -1
                    if deduct_success:
                        logger.info(f"✅ 费用扣除成功: {actual_cost} credits")
                        credit_info = {
                            "credit_deducted": actual_cost,
                            "remaining_credits": remaining_credits,
                            "deduct_success": True
                        }
                        billing_tracker.clear_session(session_id)
                    else:
                        logger.error(f"❌ 费用扣除失败: {deduct_message}")
                        credit_info = {
                            "credit_deducted": actual_cost,
                            "remaining_credits": remaining_credits,
                            "deduct_success": False,
                            "error_message": deduct_message
                        }
                        billing_tracker.clear_session(session_id)
                else:
                    credit_info = {
                        "credit_deducted": 0,
                        "remaining_credits": None,
                        "deduct_success": True
                    }
            else:
                logger.info("🔧 本地模式，跳过credit扣费")
                credit_info = {
                    "local_mode": True,
                    "credit_deducted": 0,
                    "remaining_credits": None
                }
            
            # 将credit信息添加到billing_info中
            billing_info.update(credit_info)
            
            return ChatResponse(
                response=friendly_response,
                status="guidance_provided",
                task_type=3,
                session_id=session_id,
                source_files=None,
                billing_info=billing_info,
                credit_info=credit_info,
                chat_id=chat_id,
                chat_title=chat_title
            )
        
        elif task_type == -1:
            # 任务分类失败，进入通用回答模式
            logger.info("任务分类失败，进入通用回答模式")
            report_progress(session_id, "无法识别具体任务类型，将直接回答您的问题...", "processing")
            
            # 调用instruction_mode=-1进行通用回答
            result = await agent.run_analysis_agent(
                instruction_mode=-1,  # 通用回答模式
                user_prompt=request.message,
                file_paths=file_paths,
                output_path=session_path,
                session_id=session_id,
                rshub_token=rshub_token,
                chat_history=chat_history  # 传递会话历史
            )
            
            # 计算计费信息
            billing_info = billing_tracker.calculate_cost(
                session_id,
                settings.LLM_COST_FACTOR,
                settings.RSHUB_TASK_COST_FACTOR
            )
            
            # === Credit扣费 (仅在生产模式下) ===
            credit_info = {}
            if settings.DEPLOYMENT_MODE == "production":
                # 计算实际消耗的credit
                actual_cost = billing_info["total_cost"]
                logger.info(f"💳 实际任务费用: {actual_cost} credits")
                
                if actual_cost > 0:
                    report_progress(session_id, "正在扣除费用...", "processing")
                    
                    # 扣除费用
                    deduct_success, deduct_message, remaining_credits = await credit_service.update_credits(
                        rshub_token, -actual_cost
                    )
                    if not isinstance(remaining_credits, (int, float)) or remaining_credits < 0:
                        remaining_credits = -1
                    if deduct_success:
                        logger.info(f"✅ 费用扣除成功: {actual_cost} credits")
                        credit_info = {
                            "credit_deducted": actual_cost,
                            "remaining_credits": remaining_credits,
                            "deduct_success": True
                        }
                        billing_tracker.clear_session(session_id)
                    else:
                        logger.error(f"❌ 费用扣除失败: {deduct_message}")
                        credit_info = {
                            "credit_deducted": actual_cost,
                            "remaining_credits": remaining_credits,
                            "deduct_success": False,
                            "error_message": deduct_message
                        }
                        billing_tracker.clear_session(session_id)
                else:
                    credit_info = {
                        "credit_deducted": 0,
                        "remaining_credits": None,
                        "deduct_success": True
                    }
            else:
                logger.info("🔧 本地模式，跳过credit扣费")
                credit_info = {
                    "local_mode": True,
                    "credit_deducted": 0,
                    "remaining_credits": None
                }
            
            # 将credit信息添加到billing_info中
            billing_info.update(credit_info)
            
            # === 会话管理：创建或更新会话 ===
            if is_new_chat:
                # 创建新会话
                chat_result = await chat_session_service.create_session(
                    rshub_token, request.message, result
                )
                if chat_result.get("success"):
                    chat_id = chat_result.get("session_id")
                    chat_title = chat_result.get("title")
                    logger.info(f"创建新会话成功: {chat_id}")
                else:
                    logger.error(f"创建新会话失败: {chat_result.get('error')}")
            else:
                # 更新现有会话
                update_result = await chat_session_service.update_session(
                    rshub_token, chat_id, request.message, result
                )
                if update_result.get("success"):
                    if update_result.get("rshub_sync"):
                        logger.info(f"更新会话成功: {chat_id}（本地缓存和RSHub同步成功）")
                    else:
                        logger.info(f"更新会话成功: {chat_id}（本地缓存成功，RSHub同步失败但不影响使用）")
                else:
                    logger.warning(f"更新会话失败: {update_result.get('error')}（但对话功能不受影响）")
            
            return ChatResponse(
                response=result,
                status="general_answer",
                task_type=-1,  # 表示通用回答模式
                session_id=session_id,
                source_files=None,
                billing_info=billing_info,
                credit_info=credit_info,
                chat_id=chat_id,
                chat_title=chat_title
            )
        
        # === Credit检查 (仅在生产模式下) ===
        if settings.DEPLOYMENT_MODE == "production":
            logger.info(f"💰 检查用户余额 (任务类型: {task_type})")
            report_progress(session_id, "正在检查账户余额...", "processing")
            
            # 检查用户余额，只要余额>0即可执行任务
            has_sufficient_credits, credit_message, _ = await credit_service.check_credits(
                rshub_token, 1
            )
            
            if not has_sufficient_credits:
                logger.warning(f"用户余额不足: {credit_message}")
                report_progress(session_id, "账户余额不足", "error")
                raise HTTPException(
                    status_code=402,  # Payment Required
                    detail=f"账户余额不足：{credit_message}。请联系管理员充值后再试。"
                )
            
            logger.info(f"✅ 余额检查通过: {credit_message}")
        else:
            logger.info("🔧 本地模式，跳过credit检查")
        
        # === 第二阶段：执行具体任务 ===
        
        # 验证task_type的有效性并保护变量
        if not isinstance(task_type, int):
            logger.error(f"task_type类型错误: {type(task_type)}, 值: {task_type}")
            safe_task_type = 1  # 默认使用知识问答模式
        else:
            safe_task_type = task_type
        
        logger.info(f"🚀 Stage 2: 执行任务 - instruction={safe_task_type}")
        
        # 根据任务类型发送不同的进度消息
        task_descriptions = {
            1: "正在进行知识问答分析...",
            2: "正在构建微波遥感环境模型...",
            3: "正在进行环境参数推断..."
        }
        
        progress_message = task_descriptions.get(safe_task_type, "正在处理您的请求...")
        report_progress(session_id, progress_message, "processing")
        
        # 调用具体的任务处理逻辑
        source_files = None  # 初始化源文件信息
        
        if safe_task_type == 1:
            # 知识查询任务，使用带源文件信息的函数
            knowledge_result = await agent.run_knowledge_query_with_sources(
                user_prompt=request.message,
                file_paths=file_paths,
                session_id=session_id,
                chat_history=chat_history  # 传递会话历史
            )
            result = knowledge_result.get("answer", "未能获取回答")
            source_files = knowledge_result.get("sources", [])
        else:
            # 其他任务使用普通的函数
            result = await agent.run_analysis_agent(
                instruction_mode=safe_task_type,  # 使用安全的分类结果作为指令模式
                user_prompt=request.message,
                file_paths=file_paths,
                output_path=session_path,
                session_id=session_id,
                rshub_token=rshub_token,
                chat_history=chat_history  # 传递会话历史
            )
        
        logger.info(f"✅ 任务执行完成，结果长度: {len(result)}")
        
        # 计算计费信息
        billing_info = billing_tracker.calculate_cost(
            session_id,
            settings.LLM_COST_FACTOR,
            settings.RSHUB_TASK_COST_FACTOR
        )
        
        # === Credit扣费 (仅在生产模式下) ===
        credit_info = {}
        if settings.DEPLOYMENT_MODE == "production":
            # 计算实际消耗的credit
            actual_cost = billing_info["total_cost"]
            logger.info(f"💳 实际任务费用: {actual_cost} credits")
            
            if actual_cost > 0:
                report_progress(session_id, "正在扣除费用...", "processing")
                
                # 扣除费用
                deduct_success, deduct_message, remaining_credits = await credit_service.update_credits(
                    rshub_token, -actual_cost
                )
                if not isinstance(remaining_credits, (int, float)) or remaining_credits < 0:
                    remaining_credits = -1
                if deduct_success:
                    logger.info(f"✅ 费用扣除成功: {actual_cost} credits")
                    credit_info = {
                        "credit_deducted": actual_cost,
                        "remaining_credits": remaining_credits,
                        "deduct_success": True
                    }
                    billing_tracker.clear_session(session_id)
                else:
                    logger.error(f"❌ 费用扣除失败: {deduct_message}")
                    credit_info = {
                        "credit_deducted": actual_cost,
                        "remaining_credits": remaining_credits,
                        "deduct_success": False,
                        "error_message": deduct_message
                    }
                    billing_tracker.clear_session(session_id)
            else:
                credit_info = {
                    "credit_deducted": 0,
                    "remaining_credits": None,
                    "deduct_success": True
                }
        else:
            logger.info("🔧 本地模式，跳过credit扣费")
            credit_info = {
                "local_mode": True,
                "credit_deducted": 0,
                "remaining_credits": None
            }
        
        # 将credit信息添加到billing_info中
        billing_info.update(credit_info)
        
        # === 会话管理：创建或更新会话 ===
        if is_new_chat:
            # 创建新会话
            chat_result = await chat_session_service.create_session(
                rshub_token, request.message, result
            )
            if chat_result.get("success"):
                chat_id = chat_result.get("session_id")
                chat_title = chat_result.get("title")
                logger.info(f"创建新会话成功: {chat_id}")
            else:
                logger.error(f"创建新会话失败: {chat_result.get('error')}")
        else:
            # 更新现有会话
            update_result = await chat_session_service.update_session(
                rshub_token, chat_id, request.message, result
            )
            if update_result.get("success"):
                if update_result.get("rshub_sync"):
                    logger.info(f"更新会话成功: {chat_id}（本地缓存和RSHub同步成功）")
                else:
                    logger.info(f"更新会话成功: {chat_id}（本地缓存成功，RSHub同步失败但不影响使用）")
            else:
                logger.warning(f"更新会话失败: {update_result.get('error')}（但对话功能不受影响）")
        
        # === 进度回报：任务完成 ===
        report_progress(session_id, "任务处理完成", "completed")
        
        return ChatResponse(
            response=result,
            status="success",
            task_type=safe_task_type,
            session_id=session_id,
            source_files=source_files,  # 添加源文件信息
            billing_info=billing_info,
            credit_info=credit_info,
            chat_id=chat_id,
            chat_title=chat_title
        )
        
    except HTTPException:
        # 重新抛出HTTP异常
        raise
    except Exception as e:
        logger.error(f"Agent处理出错: {str(e)}")
        # 确保清理计费会话
        billing_tracker.clear_session(session_id)
        
        # 发送错误进度报告
        report_progress(session_id, f"处理出错: {str(e)}", "error")
        
        return ChatResponse(
            response=f"抱歉，处理您的请求时出现了错误：{str(e)}",
            status="error",
            session_id=session_id,
            chat_id=chat_id,
            chat_title=chat_title
        )
    
    finally:
        # 清理会话目录（如果创建了的话）
        if session_path:
            file_manager.cleanup_session(session_path)

@router.post("/agent/chat/upload")
async def agent_chat_with_files(
    message: str = Form(...),
    files: List[UploadFile] = File(...),
    stream: bool = Form(False),
    session_id: Optional[str] = Form(None),
    token: Optional[str] = Form(None),  # 添加token参数
    chat_id: Optional[str] = Form(None)  # 添加chat_id参数用于会话管理
):
    """
    支持文件上传的Agent聊天端点 - 单文件上传模式
    
    这个端点支持用户上传单个文件并将文件内容提取后拼接到用户输入：
    1. 限制只能上传1个文件
    2. 支持txt、md、docx、csv、xlsx格式
    3. 将文件内容拼接到用户输入后面
    4. 执行标准的两阶段工作流
    5. 支持会话管理，与普通聊天端点一致
    
    Args:
        message: 用户消息
        files: 上传的文件列表（限制为1个文件）
        stream: 是否使用流式响应
        session_id: 会话ID
        token: RSHub token
        chat_id: 会话ID，用于会话管理
    
    Returns:
        Agent响应，包含任务类型、文件处理信息和会话信息
    """
    session_path = None
    
    # 获取计费跟踪器、认证服务、credit服务、会话服务和设置
    billing_tracker = get_billing_tracker()
    auth_service = get_auth_service()
    credit_service = get_credit_service()
    chat_session_service = get_chat_session_service()
    settings = get_settings()
    
    # 会话管理相关变量
    chat_history = []
    chat_title = None
    is_new_chat = not chat_id
    
    try:
        # 确保有session_id用于进度报告
        if not session_id:
            session_id = str(uuid.uuid4())
        
        # === 认证处理 ===
        try:
            rshub_token = auth_service.get_rshub_token(token)
        except ValueError as e:
            raise HTTPException(status_code=401, detail=str(e))
        
        # === 会话历史加载 ===
        chat_history = []  # 初始化为空列表
        if chat_id:
            # 如果提供了会话ID，加载会话历史
            session_data = await chat_session_service.load_session(rshub_token, chat_id)
            if session_data:
                all_messages = session_data.get("messages", [])
                # 限制加载的历史消息数量（防止内存爆炸）
                max_load_messages = 30  # 最多加载30条历史消息用于上下文
                if len(all_messages) > max_load_messages:
                    # 保留前2条（初始对话）和最后N-2条
                    chat_history = all_messages[:2] + all_messages[-(max_load_messages-2):]
                    logger.info(f"会话历史较长({len(all_messages)}条)，已截断为{len(chat_history)}条用于上下文")
                else:
                    chat_history = all_messages
                chat_title = session_data.get("title", "对话")
                logger.info(f"加载了会话 {chat_id}，包含 {len(all_messages)} 条历史消息（使用 {len(chat_history)} 条作为上下文）")
            else:
                logger.warning(f"无法加载会话 {chat_id}，将作为新会话处理")
                chat_id = None
                is_new_chat = True
        else:
            # 如果没有提供chat_id，尝试查找最近的会话（用于连续对话）
            logger.info("未提供chat_id，尝试查找最近的会话...")
            latest_session = await chat_session_service.find_latest_session(rshub_token)
            if latest_session:
                chat_id = latest_session.get("session_id")
                all_messages = latest_session.get("messages", [])
                # 限制加载的历史消息数量
                max_load_messages = 30
                if len(all_messages) > max_load_messages:
                    chat_history = all_messages[:2] + all_messages[-(max_load_messages-2):]
                    logger.info(f"会话历史较长({len(all_messages)}条)，已截断为{len(chat_history)}条用于上下文")
                else:
                    chat_history = all_messages
                chat_title = latest_session.get("title", "对话")
                is_new_chat = False
                logger.info(f"找到最近的会话 {chat_id}，包含 {len(all_messages)} 条历史消息（使用 {len(chat_history)} 条作为上下文）")
            else:
                logger.info("未找到最近的会话，将创建新会话")
                is_new_chat = True
        
        # 初始化计费会话
        billing_tracker.init_session(session_id)
        
        # === 进度回报：初始化 ===
        report_progress(session_id, "正在初始化文件上传处理...", "init")
        
        # === 文件验证：确保只有1个文件 ===
        if not files or len(files) == 0:
            raise HTTPException(status_code=400, detail="请上传1个文件")
        
        if len(files) > 1:
            raise HTTPException(status_code=400, detail="AI助手页面只支持上传1个文件，请重新选择")
        
        uploaded_file = files[0]
        
        # === 文件格式验证 ===
        supported_extensions = ['.txt', '.md', '.docx', '.csv', '.xlsx']
        file_extension = Path(uploaded_file.filename).suffix.lower() if uploaded_file.filename else ''
        
        if file_extension not in supported_extensions:
            raise HTTPException(
                status_code=400, 
                detail=f"不支持的文件格式：{file_extension}。支持的格式：{', '.join(supported_extensions)}"
            )
        
        logger.info(f"📁 处理单个上传文件: {uploaded_file.filename} ({file_extension})")
        report_progress(session_id, f"正在处理上传文件：{uploaded_file.filename}...", "processing")
        
        # === 文件内容提取阶段 ===
        file_content_text = ""
        
        try:
            # 读取文件内容
            file_content = await uploaded_file.read()
            
            # 保存临时文件用于内容提取
            import tempfile
            with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as temp_file:
                temp_file.write(file_content)
                temp_file_path = temp_file.name
            
            try:
                # 根据文件类型提取内容
                if file_extension in ['.txt', '.md']:
                    # 文本文件直接解码
                    encodings = ['utf-8', 'gbk', 'gb2312', 'big5', 'latin-1']
                    for encoding in encodings:
                        try:
                            file_content_text = file_content.decode(encoding)
                            break
                        except UnicodeDecodeError:
                            continue
                    else:
                        raise HTTPException(status_code=400, detail="无法解析文件编码")
                
                elif file_extension in ['.docx', '.csv', '.xlsx']:
                    # 使用document_processor提取内容
                    from ...utils.document_processor import extract_document_text
                    extracted_text = extract_document_text(temp_file_path)
                    
                    if not extracted_text:
                        raise HTTPException(status_code=400, detail=f"无法提取{file_extension}文件内容")
                    
                    file_content_text = extracted_text
                
                else:
                    raise HTTPException(status_code=400, detail=f"不支持的文件类型：{file_extension}")
                
            finally:
                # 清理临时文件
                try:
                    os.unlink(temp_file_path)
                except:
                    pass
            
            # 验证提取的内容
            if not file_content_text or len(file_content_text.strip()) < 5:
                raise HTTPException(status_code=400, detail="文件内容为空或太短")
            
            logger.info(f"✅ 成功提取文件内容，长度: {len(file_content_text)} 字符")
            
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"文件内容提取失败: {str(e)}")
            raise HTTPException(status_code=500, detail=f"文件处理失败: {str(e)}")
        
        # === 消息拼接阶段 ===
        # 按照要求的格式拼接用户输入和文件内容
        enhanced_message = f"{message}；以下是我上传的文件，文件名为{uploaded_file.filename}，内容为{file_content_text}；请将我的要求和上传文件内容综合起来。"
        
        logger.info(f"🔗 消息拼接完成，总长度: {len(enhanced_message)} 字符")
        report_progress(session_id, "文件内容已提取，正在分析问题类型...", "analyzing")
        
        # === 第一阶段：任务分类 (instruction=0) ===
        logger.info(f"🔍 Stage 1: 任务分类 - 分析用户意图和文件内容...")
        report_progress(session_id, "正在分析您的问题类型...", "analyzing")
        
        task_type = await agent.run_analysis_agent(
            instruction_mode=0,  # 模式0：任务分类
            user_prompt=enhanced_message,  # 使用拼接后的消息
            file_paths=[],  # 不传递文件路径，因为内容已拼接到消息中
            output_path=None,
            session_id=session_id,
            rshub_token=rshub_token,
            chat_history=chat_history  # 传递会话历史
        )
        
        logger.info(f"📋 任务分类结果: {task_type}")
        
        # 验证任务类型
        if task_type == -100:
            # 用户主动中止请求
            report_progress(session_id, "用户已中止请求", "aborted")
            return {
                "response": "请求已被用户中止",
                "status": "user_aborted",
                "task_type": task_type,
                "files_processed": 1,
                "session_id": session_id,
                "chat_id": chat_id,
                "chat_title": chat_title
            }
        
        elif task_type == -101:
            # LLM调用超时
            report_progress(session_id, "AI服务响应超时", "error")
            return {
                "response": "抱歉，AI服务响应超时，请稍后重试",
                "status": "llm_timeout",
                "task_type": task_type,
                "files_processed": 1,
                "session_id": session_id,
                "chat_id": chat_id,
                "chat_title": chat_title
            }
        
        elif task_type == -102:
            # 网络连接错误
            report_progress(session_id, "网络连接错误", "error")
            return {
                "response": "抱歉，网络连接出现问题，请检查网络后重试",
                "status": "network_error",
                "task_type": task_type,
                "files_processed": 1,
                "session_id": session_id,
                "chat_id": chat_id,
                "chat_title": chat_title
            }
        
        elif task_type == -1:
            # 任务分类失败，进入通用回答模式
            logger.info("任务分类失败，进入通用回答模式")
            report_progress(session_id, "无法识别具体任务类型，将直接回答您的问题...", "processing")
            
            # 调用instruction_mode=-1进行通用回答
            result = await agent.run_analysis_agent(
                instruction_mode=-1,  # 通用回答模式
                user_prompt=enhanced_message,
                file_paths=[],
                output_path=session_path,
                session_id=session_id,
                rshub_token=rshub_token,
                chat_history=chat_history  # 传递会话历史
            )
            
            # 计算计费信息
            billing_info = billing_tracker.calculate_cost(
                session_id,
                settings.LLM_COST_FACTOR,
                settings.RSHUB_TASK_COST_FACTOR
            )
            
            # === Credit扣费 (仅在生产模式下) ===
            credit_info = {}
            if settings.DEPLOYMENT_MODE == "production":
                # 计算实际消耗的credit
                actual_cost = billing_info["total_cost"]
                logger.info(f"💳 实际任务费用(上传): {actual_cost} credits")
                
                if actual_cost > 0:
                    report_progress(session_id, "正在扣除费用...", "processing")
                    
                    # 扣除费用
                    deduct_success, deduct_message, remaining_credits = await credit_service.update_credits(
                        rshub_token, -actual_cost
                    )
                    if not isinstance(remaining_credits, (int, float)) or remaining_credits < 0:
                        remaining_credits = -1
                    if deduct_success:
                        logger.info(f"✅ 费用扣除成功(上传): {actual_cost} credits")
                        credit_info = {
                            "credit_deducted": actual_cost,
                            "remaining_credits": remaining_credits,
                            "deduct_success": True
                        }
                        billing_tracker.clear_session(session_id)
                    else:
                        logger.error(f"❌ 费用扣除失败(上传): {deduct_message}")
                        credit_info = {
                            "credit_deducted": actual_cost,
                            "remaining_credits": remaining_credits,
                            "deduct_success": False,
                            "error_message": deduct_message
                        }
                        billing_tracker.clear_session(session_id)
                else:
                    credit_info = {
                        "credit_deducted": 0,
                        "remaining_credits": None,
                        "deduct_success": True
                    }
            else:
                logger.info("🔧 本地模式，跳过credit扣费(上传)")
                credit_info = {
                    "local_mode": True,
                    "credit_deducted": 0,
                    "remaining_credits": None
                }
            
            # === 会话保存 ===
            try:
                if is_new_chat:
                    # 创建新会话
                    session_result = await chat_session_service.create_session(
                        rshub_token, message, result
                    )
                    if session_result.get("success"):
                        chat_id = session_result.get("session_id")
                        chat_title = session_result.get("title")
                        logger.info(f"创建新会话成功: {chat_id}")
                    else:
                        logger.error(f"创建会话失败: {session_result.get('error')}")
                else:
                    # 更新现有会话
                    update_result = await chat_session_service.update_session(
                        rshub_token, chat_id, message, result
                    )
                    if update_result.get("success"):
                        logger.info(f"更新会话成功: {chat_id}")
                    else:
                        logger.error(f"更新会话失败: {update_result.get('error')}")
                
            except Exception as e:
                logger.error(f"会话保存失败: {str(e)}")
                # 不影响主流程，继续执行
            
            return {
                "response": result,
                "status": "general_answer",
                "task_type": task_type,
                "files_processed": 1,
                "session_id": session_id,
                "file_list": [{"name": uploaded_file.filename, "size": len(file_content), "type": file_extension}],
                "source_files": None,
                "billing_info": billing_info,
                "credit_info": credit_info,
                "chat_id": chat_id,  # 返回会话ID给前端
                "chat_title": chat_title  # 返回会话标题给前端
            }
        
        # === 正常任务类型处理 (1, 2, 3) ===
        # === Credit检查 (仅在生产模式下) ===
        if settings.DEPLOYMENT_MODE == "production":
            logger.info(f"💰 检查用户余额(上传) (任务类型: {task_type})")
            report_progress(session_id, "正在检查账户余额...", "processing")
            
            # 检查用户余额，只要余额>0即可执行任务
            has_sufficient_credits, credit_message, _ = await credit_service.check_credits(
                rshub_token, 1
            )
            
            if not has_sufficient_credits:
                logger.warning(f"用户余额不足(上传): {credit_message}")
                report_progress(session_id, "账户余额不足", "error")
                raise HTTPException(
                    status_code=402,  # Payment Required
                    detail=f"账户余额不足：{credit_message}。请联系管理员充值后再试。"
                )
            
            logger.info(f"✅ 余额检查通过(上传): {credit_message}")
        else:
            logger.info("🔧 本地模式，跳过credit检查(上传)")
        
        # === 第二阶段：执行具体任务 ===
        logger.info(f"🚀 Stage 2: 执行任务(上传) - instruction={task_type}")
        
        # 根据任务类型发送不同的进度消息
        task_descriptions = {
            1: "开始知识问答分析(上传文件)...",
            2: "开始环境建模分析(上传文件)...", 
            3: "开始参数反演分析(上传文件)..."
        }
        progress_message = task_descriptions.get(task_type, "开始执行分析任务(上传文件)...")
        report_progress(session_id, progress_message, "processing")
        
        # 执行具体任务
        source_files = None
        
        # 对于知识问答任务，使用增强的函数获取源文件信息
        if task_type == 1:
            # 使用带源信息的知识问答函数
            knowledge_result = await agent.run_knowledge_query_with_sources(
                user_prompt=enhanced_message,
                file_paths=[],  # 文件内容已拼接到消息中
                session_id=session_id,
                chat_history=chat_history,  # 添加会话历史参数
                rshub_token=rshub_token  # 添加token参数
            )
            result = knowledge_result.get("answer", "未能获取回答")
            source_files = knowledge_result.get("sources", [])
        else:
            # 其他任务类型使用原来的函数
            result = await agent.run_analysis_agent(
                instruction_mode=task_type,
                user_prompt=enhanced_message,
                file_paths=[],  # 文件内容已拼接到消息中
                output_path=session_path,
                session_id=session_id,
                rshub_token=rshub_token,
                chat_history=chat_history  # 传递会话历史
            )
        
        # === 进度回报：任务完成 ===
        report_progress(session_id, "AI分析完成，正在整理回答...", "completing")
        
        # 根据任务类型添加额外的响应信息
        if task_type == 1:
            status = "knowledge_answered"
        elif task_type == 2:
            status = "environment_constructed"
        elif task_type == 3:
            status = "parameters_inferred" 
        else:
            status = "task_completed"
        
        # === 进度回报：任务完成 ===
        report_progress(session_id, "回答已生成完成", "completed")
        
        # 计算计费信息
        billing_info = billing_tracker.calculate_cost(
            session_id,
            settings.LLM_COST_FACTOR,
            settings.RSHUB_TASK_COST_FACTOR
        )
        
        # === 会话保存 ===
        try:
            if is_new_chat:
                # 创建新会话
                session_result = await chat_session_service.create_session(
                    rshub_token, message, result
                )
                if session_result.get("success"):
                    chat_id = session_result.get("session_id")
                    chat_title = session_result.get("title")
                    logger.info(f"创建新会话成功: {chat_id}")
                else:
                    logger.error(f"创建会话失败: {session_result.get('error')}")
            else:
                # 更新现有会话
                update_result = await chat_session_service.update_session(
                    rshub_token, chat_id, message, result
                )
                if update_result.get("success"):
                    logger.info(f"更新会话成功: {chat_id}")
                else:
                    logger.error(f"更新会话失败: {update_result.get('error')}")
            
        except Exception as e:
            logger.error(f"会话保存失败: {str(e)}")
            # 不影响主流程，继续执行
        
        # === Credit扣费 (仅在生产模式下) ===
        credit_info = {}
        if settings.DEPLOYMENT_MODE == "production":
            # 计算实际消耗的credit
            actual_cost = billing_info["total_cost"]
            logger.info(f"💳 实际任务费用(上传): {actual_cost} credits")
            
            if actual_cost > 0:
                report_progress(session_id, "正在扣除费用...", "processing")
                
                # 扣除费用
                deduct_success, deduct_message, remaining_credits = await credit_service.update_credits(
                    rshub_token, -actual_cost
                )
                if not isinstance(remaining_credits, (int, float)) or remaining_credits < 0:
                    remaining_credits = -1
                if deduct_success:
                    logger.info(f"✅ 费用扣除成功(上传): {actual_cost} credits")
                    credit_info = {
                        "credit_deducted": actual_cost,
                        "remaining_credits": remaining_credits,
                        "deduct_success": True
                    }
                    billing_tracker.clear_session(session_id)
                else:
                    logger.error(f"❌ 费用扣除失败(上传): {deduct_message}")
                    credit_info = {
                        "credit_deducted": actual_cost,
                        "remaining_credits": remaining_credits,
                        "deduct_success": False,
                        "error_message": deduct_message
                    }
                    billing_tracker.clear_session(session_id)
            else:
                credit_info = {
                    "credit_deducted": 0,
                    "remaining_credits": None,
                    "deduct_success": True
                }
        else:
            logger.info("🔧 本地模式，跳过credit扣费(上传)")
            credit_info = {
                "local_mode": True,
                "credit_deducted": 0,
                "remaining_credits": None
            }
        
        return {
            "response": result,
            "status": status,
            "task_type": task_type,
            "files_processed": 1,
            "session_id": session_id,
            "file_list": [{"name": uploaded_file.filename, "size": len(file_content), "type": file_extension}],
            "source_files": source_files,
            "billing_info": billing_info,
            "credit_info": credit_info,
            "chat_id": chat_id,  # 返回会话ID给前端
            "chat_title": chat_title  # 返回会话标题给前端
        }

    except Exception as e:
        error_msg = f"处理文件上传聊天请求时发生错误: {str(e)}"
        logger.error(f"❌ Upload Chat Error: {error_msg}")
        
        # === 进度回报：错误发生 ===
        try:
            report_progress(session_id, f"处理过程中发生错误: {str(e)}", "error")
        except:
            pass  # 避免进度回报本身出错影响主流程
            
        raise HTTPException(status_code=500, detail=error_msg)
    
    finally:
        # 由于我们将文件内容直接拼接到消息中，不需要保留临时文件
        if session_path:
            logger.info(f"💾 会话处理完成: {session_path}")

@router.post("/agent/knowledge", response_model=KnowledgeChatResponse)
async def knowledge_chat_with_sources(request: KnowledgeChatRequest):
    """
    增强的知识问答端点 - 返回带有文件源信息的回答
    
    这个端点专门用于知识问答，会返回：
    1. AI生成的答案
    2. 引用的源文件信息（包括文件名、类型、预览链接等）
    3. 使用的关键词
    
    Args:
        request: 包含用户问题和会话ID的请求
    
    Returns:
        包含答案和源文件信息的响应
    """
    try:
        # 生成或使用提供的会话ID
        session_id = request.session_id or str(uuid.uuid4())
        
        logger.info(f"🔍 开始知识问答（带源信息）: {request.message[:50]}...")
        
        # 调用增强的知识问答功能
        result = await agent.run_knowledge_query_with_sources(
            user_prompt=request.message,
            file_paths=None,  # 当前版本不支持上传文件
            session_id=session_id
        )
        
        # 构建响应
        response = KnowledgeChatResponse(
            answer=result.get("answer", ""),
            sources=result.get("sources", []),
            status=result.get("status", "success"),
            session_id=session_id,
            keywords_used=result.get("keywords_used", [])
        )
        
        logger.info(f"✅ 知识问答完成，返回 {len(response.sources)} 个源文件")
        return response
        
    except Exception as e:
        error_msg = f"处理知识问答请求时发生错误: {str(e)}"
        logger.error(f"❌ Knowledge Chat Error: {error_msg}")
        
        return KnowledgeChatResponse(
            answer=f"抱歉，处理您的问题时遇到了错误：{str(e)}",
            sources=[],
            status="error",
            session_id=session_id if 'session_id' in locals() else None
        )

@router.post("/analyze/")
async def analyze_user_request(
    instruction_text: str,
    files: List[UploadFile] = File(...)
):
    """
    分析用户请求的主要端点
    
    Args:
        instruction_text: 用户输入的提示词
        files: 用户上传的文件列表
    
    Returns:
        分析结果和响应状态
    """
    session_path = None
    try:
        # 1. 使用文件服务保存上传的文件
        session_path, saved_paths = await file_manager.save_uploads(files)

        # 2. (核心步骤) 先调用Agent进行任务分类
        task_type = await agent.run_analysis_agent(
            instruction_mode=0,  # 模式0：任务分类
            user_prompt=instruction_text,
            file_paths=saved_paths
        )

        if task_type == -1:
            # 任务分类失败，进入通用回答模式
            result = await agent.run_analysis_agent(
                instruction_mode=-1,  # 通用回答模式
                user_prompt=instruction_text,
                file_paths=saved_paths,
                output_path=session_path
            )
            return {
                "status": "success", 
                "result": result, 
                "task_type": "general_answer",
                "billing_info": {"note": "此端点不支持计费功能，请使用 /agent/chat 或 /agent/chat/upload 端点获取完整计费信息"},
                "credit_info": {"note": "此端点不支持credit管理"}
            }
        
        elif task_type == -100:
            raise HTTPException(status_code=400, detail="请求已被用户中止")
        
        elif task_type == -101:
            raise HTTPException(status_code=408, detail="AI服务响应超时，请稍后重试")
        
        elif task_type == -102:
            raise HTTPException(status_code=503, detail="网络连接出现问题，请检查网络后重试")
        
        elif task_type < 0:
            raise HTTPException(status_code=500, detail="处理请求时发生未知错误")

        # 3. 根据任务类型，再次调用Agent执行具体任务
        result = await agent.run_analysis_agent(
            instruction_mode=task_type,  # 模式1：知识问答（第一阶段）
            user_prompt=instruction_text,
            file_paths=saved_paths,
            output_path=session_path  # 结果输出到会话目录
        )

        return {
            "status": "success", 
            "result": result, 
            "task_type": task_type,
            "billing_info": {"note": "此端点不支持计费功能，请使用 /agent/chat 或 /agent/chat/upload 端点获取完整计费信息"},
            "credit_info": {"note": "此端点不支持credit管理"}
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"处理请求时发生错误: {str(e)}")
    
    finally:
        # 4. 清理会话目录
        if session_path:
            file_manager.cleanup_session(session_path)