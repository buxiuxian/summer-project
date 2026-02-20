# RS Agent MCP 项目结构图

## 项目根目录结构

```
RS-agent-mcp/
├── app/                           # 主应用目录
│   ├── agent/                     # AI Agent核心模块
│   │   ├── agent.py               # Agent接口层，提供统一的对外接口和向后兼容性
│   │   ├── agent.py.bak           # Agent接口层备份文件
│   │   ├── langchain_agent.py     # LangChain Agent协调器，轻量级组件调度器
│   │   ├── langchain_agent.py.bak # LangChain Agent备份文件
│   │   ├── langchain_prompts.py   # LangChain提示词模板定义
│   │   ├── rshub_workflow.py      # RSHub工作流协调器，提供向后兼容接口
│   │   ├── rshub_workflow.py.bak  # RSHub工作流备份文件
│   │   ├── config.py              # Agent层配置管理
│   │   ├── core/                  # Agent核心组件
│   │   │   ├── __init__.py        # 核心模块初始化
│   │   │   ├── agent_factory.py   # Agent工厂，负责Agent的创建和配置管理
│   │   │   ├── agent_manager.py   # Agent管理器，负责任务调度和Agent选择
│   │   │   ├── agent_orchestrator.py # Agent编排器，协调各个组件工作
│   │   │   ├── langchain_agent_impl.py # LangChain Agent具体实现
│   │   │   ├── response_generator.py   # 响应生成器，负责各种模式下的响应生成
│   │   │   └── task_classifier.py      # 任务分类器，识别用户意图和任务类型
│   │   ├── chains/                # LangChain执行链
│   │   │   ├── __init__.py        # 链模块初始化
│   │   │   └── knowledge_chain.py # 知识查询的LangChain执行链
│   │   ├── tools/                 # Agent工具集
│   │   │   ├── __init__.py        # 工具模块初始化
│   │   │   └── knowledge_tools.py # 知识库相关工具函数
│   │   └── workflows/             # 工作流管理
│   │       ├── __init__.py        # 工作流模块初始化
│   │       ├── base_workflow.py   # 工作流基类和通用模式
│   │       ├── rshub_components.py # RSHub组件管理器
│   │       ├── rshub_task_extractor.py # 任务提取组件
│   │       ├── rshub_visualizer.py    # 可视化组件
│   │       └── rshub_workflow_impl.py # 主要工作流实现
│   ├── api/                       # API路由模块
│   │   ├── __init__.py            # API模块初始化
│   │   ├── endpoints.py           # API路由聚合器，轻量级路由管理
│   │   ├── endpoints.py.bak       # API路由备份文件
│   │   ├── files.py               # 文件处理相关API
│   │   ├── logs.py                # 日志相关API
│   │   ├── progress.py            # 进度报告API
│   │   └── routers/               # API路由器
│   │       ├── __init__.py        # 路由器模块初始化
│   │       ├── chat_router.py     # 聊天相关路由，项目核心API入口
│   │       ├── health_router.py   # 健康检查和根路径路由
│   │       ├── knowledge_router.py # 知识库API路由
│   │       └── session_router.py  # 会话管理相关路由
│   ├── rag/                       # 知识库和RAG模块
│   │   ├── __init__.py            # RAG模块初始化
│   │   ├── knowledge_base.py      # 知识库统一接口，向后兼容层
│   │   ├── knowledge_base.py.bak  # 知识库备份文件
│   │   ├── core/                  # RAG核心组件
│   │   │   ├── __init__.py        # 核心模块初始化
│   │   │   ├── embedder.py        # 嵌入模型管理器
│   │   │   ├── knowledge_manager.py # 知识库管理器
│   │   │   ├── retriever.py       # 知识检索器
│   │   │   ├── thread_safe_manager.py # 线程安全管理器
│   │   │   └── vector_store.py    # 向量存储管理器
│   │   └── stores/                # 向量存储实现
│   │       ├── __init__.py        # 存储模块初始化
│   │       ├── faiss_store.py     # FAISS向量存储实现
│   │       └── tfidf_store.py     # TF-IDF存储实现
│   ├── services/                  # 业务服务模块
│   │   ├── __init__.py            # 服务模块初始化
│   │   ├── auth/                  # 认证服务
│   │   │   ├── __init__.py        # 认证模块初始化
│   │   │   └── auth_service.py    # RSHub token认证服务
│   │   ├── billing/               # 计费服务
│   │   │   ├── __init__.py        # 计费模块初始化
│   │   │   ├── billing_tracker.py # 计费跟踪服务
│   │   │   └── credit_service.py  # 信用服务
│   │   ├── file/                  # 文件服务
│   │   │   ├── __init__.py        # 文件模块初始化
│   │   │   ├── content_service.py # 文件内容处理服务
│   │   │   ├── processor_service.py # 文件处理服务
│   │   │   └── storage_service.py # 文件存储服务
│   │   ├── session/               # 会话服务
│   │   │   ├── __init__.py        # 会话模块初始化
│   │   │   └── chat_service.py    # 聊天会话管理服务
│   │   ├── file_manager.py        # 文件管理器统一接口
│   │   ├── file_manager.py.bak    # 文件管理器备份文件
│   │   ├── file_storage.py        # 文件存储服务
│   │   └── chat_session_service.py # 聊天会话服务（已迁移）
│   ├── core/                      # 核心配置和客户端
│   │   ├── __init__.py            # 核心模块初始化
│   │   ├── config.py              # 应用配置管理，使用pydantic-settings
│   │   ├── langchain_client.py    # LangChain客户端封装
│   │   └── llm_client.py          # LLM客户端统一接口
│   └── utils/                     # 工具函数
│       ├── __init__.py            # 工具模块初始化
│       └── document_processor.py  # 文档处理工具
├── scripts/                       # 脚本文件
│   ├── __init__.py                # 脚本模块初始化
│   ├── setup/                     # 设置脚本
│   │   ├── __init__.py            # 设置模块初始化
│   │   ├── add_credits.py         # 添加信用脚本
│   │   ├── cleanup_knowledge_base.py # 清理知识库脚本
│   │   ├── download_models.py     # 下载模型脚本
│   │   ├── fix_model_cache.py     # 修复模型缓存脚本
│   │   └── reset_knowledge_base.py # 重置知识库脚本
│   └── testing/                   # 测试脚本
│       ├── __init__.py            # 测试模块初始化
│       ├── test_chat_session_management.py # 会话管理测试
│       ├── test_credit_system.py  # 信用系统测试
│       ├── test_fix.py            # 修复测试
│       ├── test_frontend_connection.py # 前端连接测试
│       ├── test_offline_simple.py # 离线简单测试
│       ├── test_rag_system.py     # RAG系统测试
│       └── test_with_server.py    # 服务器测试
├── tests/                         # 测试框架
│   ├── __init__.py                # 测试框架初始化
│   ├── conftest.py                # pytest配置和fixtures
│   ├── README.md                  # 测试说明文档
│   ├── integration/               # 集成测试目录
│   └── unit/                      # 单元测试
│       ├── test_agent_manager.py  # Agent管理器测试
│       ├── test_api_routers.py    # API路由器测试
│       ├── test_knowledge_tools.py # 知识工具测试
│       ├── test_rag_components.py # RAG组件测试
│       └── test_task_classifier.py # 任务分类器测试
├── guide/                         # 技术指南文档
│   ├── LANGCHAIN_MIGRATION.md     # LangChain迁移说明
│   ├── README_DIAGNOSTIC.md       # 诊断指南
│   ├── RSHub-web图片显示修复说明.md # RSHub图片修复说明
│   ├── RSHub数据建模功能说明.md    # RSHub数据建模说明
│   ├── 会话管理系统说明.md         # 会话管理说明
│   ├── 图片存储和显示功能说明.md   # 图片功能说明
│   ├── 文件源信息显示功能说明.md   # 文件源信息说明
│   ├── 智能进度提示系统说明.md     # 进度提示说明
│   ├── 模型预下载说明.md           # 模型预下载说明
│   ├── 知识库架构统一说明.md       # 知识库架构说明
│   └── 统一LLM接口迁移说明.md      # LLM接口迁移说明
├── workflow_knowledge/            # 工作流知识库
│   ├── RSHub-Technical-documentation.md # RSHub技术文档
│   ├── snow_parameters.md         # 雪地参数文档
│   ├── soil_parameters.md         # 土壤参数文档
│   └── veg_parameters.md          # 植被参数文档
├── file_storage/                   # 文件存储目录
│   ├── converted/                 # 转换后文件
│   ├── originals/                 # 原始文件
│   └── file_mapping.json          # 文件映射表
├── logs/                          # 日志目录
├── static/                        # 静态文件
│   └── index.html                 # Web界面
├── temp/                          # 临时文件目录
├── main.py                        # 主程序入口
├── start.py                       # 启动脚本
├── requirements.txt               # Python依赖
├── env_template.txt              # 环境变量模板
├── pytest.ini                    # pytest配置
├── run_tests.py                   # 测试运行脚本
├── Dockerfile                     # Docker配置
├── LICENSE                        # 开源许可证
├── README.md                      # 项目说明
├── BACKUP_README.md               # 备份说明
├── BUILD_COMPLETE.md              # 构建完成记录
├── debug.md                       # 调试报告
├── 进度.md                        # 项目进度报告
└── 构建完成记录.md                # 构建完成记录
```

## 核心架构特点

### 1. 模块化设计
- **Agent层**: 采用工厂模式和管理器模式，支持多种Agent类型
- **RAG层**: 双存储后端（FAISS + TF-IDF），支持自动降级
- **API层**: 路由器模式，职责分离
- **服务层**: 按业务域组织，支持独立部署

### 2. 向后兼容性
- 所有原始文件都保留为.bak备份
- 主要接口保持向后兼容
- 支持渐进式升级

### 3. 可扩展性
- 支持新的Agent类型注册
- 支持新的工作流模式
- 支持新的存储后端
- 支持新的指令模式

### 4. 代码质量
- 从单体架构重构为模块化架构
- 代码行数大幅减少（LangChain Agent -88%, RSHub工作流 -89%, 知识库 -68%）
- 完善的测试覆盖
- 详细的文档记录