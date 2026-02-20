# LangChain Agent迁移指南

## 概述

本项目已成功将Agent实现从原生HTTP客户端迁移到LangChain框架，同时保持原有的业务逻辑不变。您现在可以在原生实现和LangChain实现之间自由切换。

## 主要变更

### 新增文件

1. **`app/core/langchain_client.py`** - LangChain客户端封装
2. **`app/agent/langchain_prompts.py`** - LangChain版本的提示词模板
3. **`app/agent/langchain_agent.py`** - LangChain版本的Agent实现
4. **`app/agent/config.py`** - Agent配置管理
5. **`test_langchain_agent.py`** - 测试脚本

### 修改文件

1. **`app/agent/agent.py`** - 添加了实现切换逻辑

## 使用方法

### 1. 环境变量配置

```bash
# 启用LangChain实现（默认）
export USE_LANGCHAIN=true

# 使用原生实现
export USE_LANGCHAIN=false

# 启用调试模式
export AGENT_DEBUG=true
```

### 2. 代码中动态切换

```python
from app.agent.config import set_use_langchain, print_config

# 切换到LangChain实现
set_use_langchain(True)

# 切换到原生实现
set_use_langchain(False)

# 查看当前配置
print_config()
```

### 3. 使用Agent

使用方式与原来完全相同，系统会根据配置自动选择实现：

```python
from app.agent.agent import run_analysis_agent

# 调用Agent（会根据配置自动选择LangChain或原生实现）
result = await run_analysis_agent(
    instruction_mode=1,
    user_prompt="什么是微波散射？",
    file_paths=None,
    output_path=None
)
```

## LangChain实现的优势

### 1. 标准化的提示词管理
- 使用`ChatPromptTemplate`和`PromptTemplate`进行结构化管理
- 更好的提示词复用和维护
- 类型安全的变量注入

### 2. 统一的LLM接口
- 支持多种LLM提供商（OpenAI、DeepSeek、Ollama）
- 标准化的消息格式
- 更好的错误处理

### 3. 链式调用
- 支持复杂的处理链
- 更容易扩展和组合功能
- 更好的可观察性

### 4. 异步支持
- 完整的异步支持
- 更好的性能
- 非阻塞操作

## 测试

运行测试脚本验证LangChain实现：

```bash
python test_langchain_agent.py
```

测试包括：
- LangChain版本的功能测试
- 原生vs LangChain对比测试
- 各个指令模式的测试

## 配置选项

### Agent配置类

```python
from app.agent.config import AgentConfig, get_agent_config

config = get_agent_config()

# 检查当前实现
print(config.get_current_implementation())  # "LangChain" 或 "原生"

# 检查是否启用LangChain
print(config.is_langchain_enabled())  # True/False

# 检查调试模式
print(config.is_debug_enabled())  # True/False
```

### 便捷函数

```python
from app.agent.config import (
    set_use_langchain, 
    is_langchain_enabled,
    set_debug_mode,
    print_config
)

# 设置使用LangChain
set_use_langchain(True)

# 检查LangChain状态
if is_langchain_enabled():
    print("使用LangChain实现")

# 启用调试模式
set_debug_mode(True)

# 打印配置信息
print_config()
```

## 功能对比

| 功能 | 原生实现 | LangChain实现 | 备注 |
|------|----------|---------------|------|
| 任务分类 | ✅ | ✅ | 完全兼容 |
| 知识问答 | ✅ | ✅ | 完全兼容 |
| 环境构建 | ✅ | ✅ | 完全兼容 |
| 参数推断 | ✅ | ✅ | 完全兼容 |
| 文档转换 | ✅ | ✅ | 完全兼容 |
| 提示词管理 | 基础 | 高级 | LangChain提供更好的模板系统 |
| 错误处理 | 基础 | 增强 | LangChain提供更好的错误处理 |
| 可扩展性 | 一般 | 优秀 | LangChain提供链式调用 |

## 迁移建议

1. **默认使用LangChain**: 新项目推荐直接使用LangChain实现
2. **渐进式迁移**: 现有项目可以逐步从原生切换到LangChain
3. **保留原生实现**: 作为备用方案，确保系统稳定性
4. **监控性能**: 对比两种实现的性能表现
5. **测试验证**: 充分测试确保功能一致性

## 故障排除

### 常见问题

1. **ImportError**: 确保安装了所需的LangChain包
   ```bash
   pip install -r requirements.txt
   ```

2. **配置问题**: 检查环境变量设置
   ```bash
   echo $USE_LANGCHAIN
   ```

3. **API连接问题**: 确保LLM配置正确
   ```python
   from app.core.langchain_client import get_langchain_client
   client = await get_langchain_client()
   is_available = await client.is_available()
   ```

### 调试模式

启用调试模式获取更多信息：

```python
from app.agent.config import set_debug_mode
set_debug_mode(True)
```

## 未来规划

1. **增强链式调用**: 利用LangChain的链式调用能力
2. **添加记忆功能**: 使用LangChain的记忆组件
3. **工具集成**: 集成更多LangChain工具
4. **性能优化**: 优化LangChain调用性能
5. **监控集成**: 添加LangSmith等监控工具

## 总结

LangChain迁移成功保持了原有功能的完整性，同时提供了更好的可维护性和扩展性。通过配置开关，您可以在需要时随时切换回原生实现，确保系统的稳定性和灵活性。 