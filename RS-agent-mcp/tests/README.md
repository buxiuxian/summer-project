# 测试说明

本目录包含 RS Agent MCP 项目的单元测试和集成测试。

## 测试结构

```
tests/
├── conftest.py              # 测试配置和fixtures
├── unit/                    # 单元测试
│   ├── test_agent_manager.py
│   ├── test_task_classifier.py
│   ├── test_knowledge_tools.py
│   ├── test_api_routers.py
│   └── test_rag_components.py
└── integration/             # 集成测试（待添加）
```

## 运行测试

### 快速开始
```bash
# 运行所有测试
python run_tests.py

# 只运行单元测试
python run_tests.py unit

# 只运行集成测试
python run_tests.py integration

# 运行覆盖率测试
python run_tests.py coverage
```

### 使用pytest直接运行
```bash
# 运行所有测试
pytest

# 运行特定测试文件
pytest tests/unit/test_agent_manager.py

# 运行特定测试类
pytest tests/unit/test_agent_manager.py::TestAgentManager

# 运行特定测试方法
pytest tests/unit/test_agent_manager.py::TestAgentManager::test_agent_manager_initialization

# 生成覆盖率报告
pytest --cov=app --cov-report=html --cov-report=term-missing
```

## 测试配置

### pytest.ini
- `testpaths`: 测试文件搜索路径
- `python_files`: 测试文件命名模式
- `python_classes`: 测试类命名模式
- `python_functions`: 测试函数命名模式
- `asyncio_mode`: 异步测试模式

### 环境变量
- `PYTHONPATH`: 自动设置为项目根目录

## 测试类型

### 单元测试 (Unit Tests)
- 测试各个模块的独立功能
- 使用mock对象隔离依赖
- 快速执行，适合开发过程中频繁运行

### 集成测试 (Integration Tests)
- 测试模块间的交互
- 验证整体功能
- 执行时间较长，适合发布前验证

## 测试覆盖的组件

### Agent层
- `AgentManager`: Agent管理和调度
- `TaskClassifier`: 任务分类
- `KnowledgeTools`: 知识工具

### API层  
- `ChatRouter`: 聊天路由器
- `SessionRouter`: 会话路由器
- `KnowledgeRouter`: 知识路由器

### RAG层
- `KnowledgeBaseManager`: 知识库管理
- `EmbeddingManager`: 嵌入管理
- `VectorStoreManager`: 向量存储管理

## 编写测试指南

### 1. 测试文件命名
- 文件名以 `test_` 开头
- 类名以 `Test` 开头
- 方法名以 `test_` 开头

### 2. 使用fixtures
```python
@pytest.fixture
def sample_data():
    return {"key": "value"}

def test_example(sample_data):
    assert sample_data["key"] == "value"
```

### 3. 异步测试
```python
@pytest.mark.asyncio
async def test_async_function():
    result = await async_function()
    assert result is not None
```

### 4. Mock对象
```python
from unittest.mock import Mock, patch

def test_with_mock():
    with patch('module.function') as mock_func:
        mock_func.return_value = "mocked"
        result = module.function()
        assert result == "mocked"
```

## 持续集成

测试已配置为在以下情况下自动运行：
- 代码提交时
- 创建Pull Request时
- 合并到主分支时

## 测试报告

### 覆盖率报告
运行 `python run_tests.py coverage` 后，在 `htmlcov/` 目录下生成HTML覆盖率报告。

### 测试结果
测试结果会显示：
- 通过的测试数量
- 失败的测试数量
- 执行时间
- 错误信息（如果有）

## 故障排除

### 常见问题

1. **导入错误**
   - 确保 `PYTHONPATH` 正确设置
   - 检查模块路径是否正确

2. **异步测试失败**
   - 确保使用 `@pytest.mark.asyncio` 装饰器
   - 检查异步函数调用是否正确

3. **Mock对象不工作**
   - 确保mock路径正确
   - 检查patch装饰器的使用

### 调试技巧

1. 使用 `-v` 参数查看详细输出
2. 使用 `-s` 参数禁止捕获输出
3. 使用 `--pdb` 在失败时启动调试器

## 贡献指南

### 添加新测试
1. 在相应的测试目录中创建测试文件
2. 遵循现有的测试命名约定
3. 确保测试覆盖新的功能
4. 运行所有测试确保没有破坏现有功能

### 提高测试覆盖率
1. 识别未覆盖的代码路径
2. 添加相应的测试用例
3. 确保边界条件和错误情况都被测试

## 依赖项

- pytest
- pytest-asyncio
- pytest-cov (可选，用于覆盖率测试)
- fastapi testclient (用于API测试)
    httpx (用于异步HTTP测试)