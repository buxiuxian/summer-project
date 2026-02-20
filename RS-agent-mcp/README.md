# RS Agent MCP - 微波遥感智能分析代理

## 项目概述

RS Agent MCP（Remote Sensing Agent with Model-Context Protocol）是一个基于大语言模型的微波遥感数据分析智能代理系统。该系统采用FastAPI框架构建，集成了专业的知识库检索（RAG）、智能任务分类和多模态文档处理能力，为微波遥感领域提供智能化的数据分析和知识问答服务。

## 核心特性

### 当前功能特性（第一阶段）
- **统一 LLM 接口**: 支持任何 OpenAI SDK 兼容的 LLM API，包括 DeepSeek、OpenAI、Claude、Gemini、Llama、腾讯元宝、文心一言、kimi、通义千问、豆包 等
- **智能AI助手**: 基于专业知识库的微波遥感领域问答
- **两阶段任务分类**: 自动识别用户意图并路由到相应处理模块
- **多模态文档上传**: 支持PDF、DOCX、TXT、MD等格式文档
- **向量化知识检索**: 基于FAISS的语义相似度检索
- **实时系统监控**: 完整的日志记录和系统状态监控
- **专业化界面**: 企业级用户界面，支持文件拖拽和批量操作

### 规划功能（后续阶段）
- **参数构建环境**: 根据输入参数生成微波遥感模拟数据
- **环境推断参数**: 从观测数据反推环境参数
- **RSHub集成**: 与遥感数据处理工具深度集成

## 系统架构

### 目录结构
```
rs-agent-mcp/
├── app/                          # 核心应用代码
│   ├── api/                      # API接口层
│   │   ├── __init__.py
│   │   ├── endpoints.py          # 主要API端点
│   │   └── knowledge.py          # 知识库API
│   ├── agent/                    # AI Agent核心逻辑
│   │   ├── __init__.py
│   │   ├── agent.py              # Agent主逻辑
│   │   └── prompts.py            # LLM提示词模板
│   ├── rag/                      # RAG与知识库管理
│   │   ├── __init__.py
│   │   └── knowledge_base.py     # 知识库管理器
│   ├── services/                 # 后端服务
│   │   ├── __init__.py
│   │   └── file_manager.py       # 文件管理服务
│   ├── core/                     # 核心配置
│   │   ├── __init__.py
│   │   └── config.py             # 应用配置
│   ├── utils/                    # 工具模块
│   └── main.py                   # FastAPI应用入口
├── file_storage/                 # 知识库文件存储
│   ├── originals/               # 原始文件
│   ├── converted/               # 转换后的文本文件
│   └── file_mapping.json       # 文件映射关系
├── main.py                       # 应用启动入口
├── requirements.txt              # Python依赖清单
├── reset_knowledge_base.py       # 知识库重建脚本
├── test/                          # 测试文件目录
└── cleanup_knowledge_base.py     # 知识库清理脚本
```

### 技术栈
- **后端框架**: FastAPI + Uvicorn
- **AI模型**: 支持任何 OpenAI SDK 兼容的 LLM
- **向量数据库**: FAISS + SentenceTransformers
- **文档处理**: LLM驱动的文档转换和解析
- **前端**: 原生HTML/CSS/JavaScript
- **数据处理**: NumPy + Python标准库

## 环境要求

### 系统要求
- Python 3.11 或更高版本
- 内存: 最低4GB，推荐8GB以上
- 磁盘空间: 至少2GB可用空间
- 操作系统: Windows 10+, macOS 10.15+, Ubuntu 18.04+

### 必需的API密钥
- 任何 OpenAI SDK 兼容的 LLM API 密钥（如 DeepSeek、OpenAI、Claude 等）
- 稳定的网络连接用于API调用

## 安装指南

### 1. 获取源代码
```bash
git clone https://github.com/Lin5412/RS-agent-mcp.git
cd RS-agent-mcp
```

### 2. 创建虚拟环境（推荐）
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. 配置环境变量（重要！）
在运行项目之前，必须先配置环境变量：

```bash
# 复制环境变量模板文件为.env文件
cp env_template.txt .env
```

然后编辑 `.env` 文件，填入必要的配置信息：

#### 统一的 LLM API 配置（OpenAI SDK 兼容接口）
本系统采用统一的 OpenAI SDK 标准接口，**兼容任何提供 OpenAI 兼容 API 的 LLM 服务商**。您只需配置三个核心参数：

```bash
# LLM 配置 - OpenAI 兼容 API
BASE_URL=your-api-endpoint
API_KEY=your-api-key
MODEL=your-model-name
```

#### 常见 LLM 提供商配置示例：

1. **DeepSeek（通过火山引擎）- 推荐**
   ```bash
   BASE_URL=https://ark.cn-beijing.volces.com/api/v3
   API_KEY=your-ark-api-key
   MODEL=deepseek-r1-250528
   ```

2. **OpenAI**
   ```bash
   BASE_URL=https://api.openai.com/v1
   API_KEY=sk-your-openai-api-key
   MODEL=gpt-3.5-turbo
   ```

3. **Ollama（本地部署）**
   ```bash
   BASE_URL=http://localhost:11434/v1
   API_KEY=ollama  # Ollama不需要真实API密钥，但字段必须填写
   MODEL=llama3.2:1b
   ```


#### 可选 LLM 参数：
```bash
LLM_TEMPERATURE=0.7    # 温度参数（0-1）
LLM_TIMEOUT=120        # 超时时间（秒）
LLM_MAX_TOKENS=20000   # 最大令牌数
```

#### 其他配置：
根据需要调整服务器端口、文件大小限制等参数。详见 `env_template.txt` 文件中的完整配置说明。

### 4. 安装Python依赖
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 5. 预下载机器学习模型（推荐）
为避免网络不稳定导致的启动问题，建议提前下载模型：

```bash
# 方法1：运行批处理脚本（Windows用户推荐）

Ctrl+K to generate a command
有的在后端

明白了，API端点在后端。让我修改代码，使用正确的后端API端点。根据错误信息，我需要检查后端API的正确路径。
让我修改 previewSource 函数，使用更合理的API端点：
现在让我也改进一下错误处理，当API返回404时提供更好的用户反馈：
现在让我也添加一个更友好的错误提示，当所有API端点都失败时：
现在让我也添加一个调试功能，在控制台显示所有尝试的API端点，这样可以帮助后端开发者了解前端期望的API结构：
现在让我也改进一下引用文件的显示，添加一个"查看详情"的提示，让用户知道可以点击：
现在让我总结一下修改内容，并提供给后端开发者的建议：
修改总结
我已经改进了AI回答中引用文件的预览功能：
1. 增强了API端点尝试
添加了多个可能的API端点路径
优先尝试 /agent/files/ 路径（因为其他API都在 /agent/ 下）
按优先级顺序尝试不同的端点
2. 改进了错误处理
区分404错误和其他错误
提供详细的错误信息和调试日志
当所有端点都失败时，显示友好的错误提示
3. 增强了调试功能
在控制台打印详细的调试信息
显示文件ID、文件名等关键信息
记录所有尝试的API端点
4. 改进了用户界面
显示文件数量
添加了悬停提示
改进了错误状态的显示
后端API建议
根据前端的实现，后端需要实现以下API端点之一：
推荐端点：GET /agent/files/preview/{file_mapping_id}
备选端点：GET /agent/files/{file_mapping_id}
其他端点：GET /files/preview/{file_mapping_id} 或 GET /api/files/preview/{file_mapping_id}
API响应格式建议：
Apply
现在你可以测试AI助手的引用文件功能，如果仍然无法预览，请检查浏览器控制台的调试信息，这将帮助后端开发者了解问题所在。
问题可能在于前端请求的file_mapping_id不正确。请检查。

你说得对，问题可能在于前端请求的 file_mapping_id 不正确。让我检查一下AI回答中 sources 数据的结构，看看后端返回的数据格式是否正确。
让我先查看一下当前代码中如何处理 sources 数据：
我看到代码中使用了 data.source_files，但可能后端返回的字段名不同。让我改进代码来处理不同的字段名，并添加更详细的调试信息：
现在让我也改进 previewSource 函数，使其能够处理不同的ID字段名：
现在我需要更新所有使用 source.file_mapping_id 的地方，改为使用新的 fileId 变量：
现在我需要更新显示引用文件的部分，使用新的字段名：
现在让我也更新错误提示中的文件名：
现在让我也更新文件内容显示中的文件名：
现在让我总结一下修改内容：
修改总结
我已经改进了代码来处理不同的字段名，现在支持以下字段名：
1. 支持的源文件字段名
source_files (原字段)
sources
references
files
2. 支持的文件ID字段名
file_mapping_id (原字段)
id
file_id
fileId
3. 支持的文件名字段名
display_name (原字段)
filename
name
title
4. 增强的调试功能
在控制台打印所有可能的字段值
显示最终使用的字段值
详细记录每个源文件的数据结构
5. 改进的错误处理
当文件ID不存在时，显示更详细的错误信息
在界面上标记缺失ID的文件
提供更好的用户反馈
现在你可以测试AI助手，当有引用文件时，请查看浏览器控制台的调试信息。这将显示：
后端返回的完整数据结构
所有可能的字段名和值
最终使用的文件ID和文件名
每个API端点的尝试结果
这样我们就能确定后端返回的确切数据格式，并相应地调整前端代码。
还是无法预览文件，请再检查。

# 方法2：直接运行Python脚本
python scripts/setup/download_models.py
```

该脚本会预下载以下5个embedding模型到本地缓存：
- **all-MiniLM-L6-v2** (推荐，22MB，速度快)
- **paraphrase-MiniLM-L6-v2** (备选方案)
- **paraphrase-multilingual-MiniLM-L12-v2** (多语言支持)
- **distiluse-base-multilingual-cased** (多语言备选)
- **all-MiniLM-L12-v2** (效果更好的备选方案)

**预下载的优势**：
- 避免首次启动时的网络下载等待
- 支持离线使用
- 提高系统启动速度和稳定性
- 防止网络问题导致的服务启动失败

> **注意**：如果跳过此步骤，系统首次运行时会自动下载模型，但可能因网络问题导致启动失败。

**如果遇到模型缓存问题**：
如果在启动服务器时遇到模型加载问题（如网络超时、长时间尝试下载已缓存的模型），请运行：
```bash
# 修复模型缓存问题
python fix_model_cache.py
```

## 配置指南

### API密钥获取方式

由于系统采用统一的 OpenAI SDK 兼容接口，您可以使用任何提供此类接口的 LLM 服务商。以下是一些常见提供商的配置方法：

#### DeepSeek（推荐）
1. 访问[火山引擎大模型服务控制台](https://console.volcengine.com/ml_maas)
2. 创建DeepSeek R1模型实例
3. 获取ARK API密钥
4. 在`.env`文件中配置：
   ```bash
   BASE_URL=https://ark.cn-beijing.volces.com/api/v3
   API_KEY=your-ark-api-key
   MODEL=deepseek-r1-250528
   ```

#### OpenAI
1. 访问[OpenAI平台](https://platform.openai.com/)
2. 创建API密钥
3. 在`.env`文件中配置：
   ```bash
   BASE_URL=https://api.openai.com/v1
   API_KEY=sk-your-openai-api-key
   MODEL=gpt-3.5-turbo
   ```

#### Ollama（本地部署）
1. 安装[Ollama](https://ollama.ai/)
2. 下载推荐模型：`ollama pull llama3.2:1b` 或 `ollama pull deepseek-r1:14b`
3. 确保Ollama服务正在运行：`ollama serve`
4. 在`.env`文件中配置：
   ```bash
   BASE_URL=http://localhost:11434/v1
   API_KEY=ollama
   MODEL=llama3.2:1b
   ```

#### 其他提供商
只要提供商支持 OpenAI SDK 兼容接口，您都可以通过配置 `BASE_URL`、`API_KEY` 和 `MODEL` 来使用。系统会自动识别并适配不同的服务商。

### 知识库初始化
```bash
# 检查知识库状态
python reset_knowledge_base.py --status

# 重建知识库（如果需要）
python reset_knowledge_base.py --reset
```

## 启动和使用

### 启动前检查清单
在首次启动服务器之前，请确认已完成以下步骤：

- ✅ 已复制 `env_template.txt` 为 `.env` 文件
- ✅ 已在 `.env` 文件中配置 `BASE_URL`、`API_KEY` 和 `MODEL` 三个核心参数
- ✅ 已安装所有Python依赖包 （pip install -r requirements.txt）
- ✅ **已运行模型预下载脚本** (`./download_models.bat` 或 `python download_models.py`)
- ✅ 网络连接正常（用于API调用）

**如果启动时遇到模型加载问题**，请运行：`python fix_model_cache.py`

### 启动或重启服务
```bash
# 使用Python脚本
python start.py

# 使用批处理文件
./quick_restart.bat
```

> **重要提示**：如果是第一次启动，系统会自动下载SentenceTransformers模型，这可能需要几分钟时间，请耐心等待。

### 访问服务
- **Web界面**: http://localhost:8000/static/index.html
- **API文档**: http://localhost:8000/docs


## 功能使用指南

### AI助手功能
1. 访问Web界面的"AI助手"页签
2. 在输入框中输入微波遥感相关问题
3. 可选择上传相关文档文件
4. 点击"发送"获取AI回答
5. AI回答完成后，可以在页面底部浏览或下载引用来源

### 文档上传功能
1. 访问"文档上传"页签
2. 拖拽文件到上传区域或点击选择文件
3. 支持格式：PDF, DOCX, TXT, MD
4. 文档将自动转换并加入知识库

### 系统状态监控
1. 访问"系统状态"页签
2. 查看知识库状态和文件列表
3. 可以删除不需要的文档
4. 右侧实时日志显示系统运行状态

## API文档

### 核心API端点

#### 1. AI助手聊天
```http
POST /api/v1/agent/chat
Content-Type: application/json

{
  "message": "什么是微波散射理论？",
  "stream": false
}
```

#### 2. 文件上传聊天
```http
POST /api/v1/agent/chat/upload
Content-Type: multipart/form-data

message: "分析这个参数文件"
files: [file1.pdf, file2.docx]
stream: false
```

#### 3. 知识库状态
```http
GET /api/v1/knowledge/status
```

#### 4. 文档上传
```http
POST /api/v1/knowledge/upload
Content-Type: multipart/form-data

file: document.pdf
description: "可选描述"
```

## 维护和故障排除

### 知识库维护
```bash
# 查看知识库状态
python reset_knowledge_base.py --status

# 完全重建知识库
python reset_knowledge_base.py --reset

# 清理临时文件
python cleanup_knowledge_base.py
```

### 常见问题排除

#### 1. 环境变量配置错误
- **错误现象**：启动时报错"找不到环境变量"或"API密钥无效"
- **解决方案**：
  ```bash
  # 确认.env文件存在
  ls -la .env
  
  # 如果不存在，复制模板文件
  cp env_template.txt .env
  
  # 编辑.env文件，填入正确的API密钥
  # Windows用户可以使用记事本打开.env文件
  ```

#### 2. 服务启动失败
- 检查Python版本是否满足要求
- 确认所有依赖已正确安装
- 验证端口8000是否被占用
- **确认.env文件已正确配置**

#### 3. API调用失败
- 检查DeepSeek API密钥配置
- 确认网络连接正常
- 查看实时日志获取详细错误信息
- 验证API密钥是否有效且未过期

#### 4. 知识库问题
- 运行知识库状态检查
- 重建FAISS索引
- 确认文档格式正确

#### 5. 文件上传问题
- 检查文件大小限制
- 确认文件格式支持
- 查看服务器磁盘空间

#### 6. 模型缓存问题
- **错误现象**：启动时提示网络连接超时，或长时间尝试下载已缓存的模型
- **解决方案**：
  ```bash
  # 运行模型缓存修复脚本
  python fix_model_cache.py
  
  # 如果问题持续，可以手动清理并重新下载
  python download_models.py
  
  # 测试离线模型加载
  python test/test_offline_simple.py
  ```
- **预防措施**：确保在网络稳定的环境下完成初次模型下载
- **技术细节**：参考 `guide/模型缓存问题修复指南.md` 获取详细解决方案

### 日志文件位置
- 实时日志：Web界面右侧面板
- 系统日志：控制台输出
- 错误日志：标准错误输出

## 开发指南

### 代码贡献流程
1. Fork项目仓库
2. 创建功能分支
3. 实现功能并添加测试
4. 提交Pull Request

### 代码规范
- 遵循PEP 8编码规范
- 使用类型提示
- 添加适当的文档字符串
- 禁止在用户界面使用emoji表情

### 测试
```bash
# 运行API测试
python test/test_with_server.py

# 运行特定功能测试
python -m pytest tests/

# 性能测试
python test/test_rag_system.py
```

### 添加新功能
1. 在相应模块中实现功能
2. 在agent.py中添加处理逻辑
3. 在endpoints.py中添加API端点
4. 更新前端界面（如需要）
5. 添加测试用例

## 部署指南

### 生产环境部署
```bash
# 使用gunicorn部署
pip install gunicorn
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000

# 使用Docker部署
docker build -t rs-agent-mcp .
docker run -d -p 8000:8000 --env-file .env RS-agent-mcp
```

### 性能优化建议
- 使用多进程worker
- 配置合适的内存限制
- 启用文档缓存
- 定期清理临时文件

## 安全注意事项

- 妥善保管API密钥，不要提交到版本控制
- 在生产环境中禁用DEBUG模式
- 配置适当的文件上传限制
- 定期更新依赖包以修复安全漏洞

## 许可证

本项目采用MIT许可证。详见LICENSE文件。


## 下一版本计划
- RSHub集成
- 参数构建环境功能
- 环境推断参数功能
- 增强的API安全性

## 支持和联系

- **问题报告**: 通过GitHub Issues提交
- **功能请求**: 通过GitHub Discussions讨论
- **技术支持**: 查看文档或联系维护团队

## 致谢

感谢所有为本项目做出贡献的开发者和微波遥感领域的专家，以及ZJUI的RSHub技术团队的支持。 