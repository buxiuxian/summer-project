# 统一LLM接口迁移说明

## 概述
本次更新将原有的分散LLM配置（deepseek、openai、ollama）统一为OpenAI标准格式，简化了配置和代码维护。

## 主要改动

### 1. 环境变量变更

#### 旧配置方式
```
# 需要选择提供商
LLM_PROVIDER=deepseek

# DeepSeek配置
ARK_API_KEY=your-ark-api-key
DEEPSEEK_BASE_URL=https://ark.cn-beijing.volces.com/api/v3
DEEPSEEK_MODEL=deepseek-r1-250528
DEEPSEEK_TEMPERATURE=0.1
DEEPSEEK_TIMEOUT=60

# OpenAI配置
OPENAI_API_KEY=sk-your-openai-api-key
OPENAI_MODEL=gpt-3.5-turbo
OPENAI_TEMPERATURE=0.1

# Ollama配置
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2:1b
OLLAMA_TEMPERATURE=0.1
OLLAMA_TIMEOUT=60
```

#### 新配置方式（统一格式）
```
# 统一的LLM配置
BASE_URL=https://ark.cn-beijing.volces.com/api/v3
API_KEY=your-api-key-here
MODEL=deepseek-r1-250528

# 可选的LLM参数
LLM_TEMPERATURE=0.7
LLM_TIMEOUT=120
LLM_MAX_TOKENS=20000
```

### 2. 常见提供商配置示例

#### DeepSeek（通过火山引擎）
```
BASE_URL=https://ark.cn-beijing.volces.com/api/v3
API_KEY=your-ark-api-key
MODEL=deepseek-r1-250528
```

#### OpenAI
```
BASE_URL=https://api.openai.com/v1
API_KEY=sk-your-openai-api-key
MODEL=gpt-3.5-turbo
```

#### Ollama（本地服务）
```
BASE_URL=http://localhost:11434/v1
API_KEY=ollama  # Ollama不需要真实API密钥，但字段必须填写
MODEL=llama3.2:1b
```

#### Azure OpenAI
```
BASE_URL=https://your-resource.openai.azure.com/openai/deployments/your-deployment
API_KEY=your-azure-api-key
MODEL=gpt-35-turbo
```

### 3. 代码改动

- `app/core/config.py`: Settings类现在只包含统一的BASE_URL、API_KEY、MODEL等配置
- `app/core/langchain_client.py`: 自动根据BASE_URL判断是否是Ollama，其他都使用ChatOpenAI
- `app/core/llm_client.py`: 简化了客户端工厂，根据URL自动选择合适的客户端

### 4. 优势

1. **配置简化**: 只需要3个核心配置即可使用任何OpenAI兼容的LLM服务
2. **扩展性强**: 新增LLM提供商无需修改代码，只需填写对应的BASE_URL和API_KEY
3. **维护方便**: 减少了代码中的条件判断和重复逻辑
4. **标准化**: 所有主流LLM提供商都支持OpenAI SDK标准接口

### 5. 注意事项

1. Ollama的BASE_URL需要加上`/v1`后缀（如：`http://localhost:11434/v1`）
2. 某些提供商（如Ollama）不需要真实的API密钥，但API_KEY字段仍需填写
3. 旧的测试文件（如test_deepseek.py）可能需要单独更新

## 迁移步骤

1. 备份当前的`.env`文件
2. 复制新的`env_template.txt`为`.env`
3. 根据您使用的LLM提供商，填写对应的BASE_URL、API_KEY和MODEL
4. 重启服务

迁移完成！ 