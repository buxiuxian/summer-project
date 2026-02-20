# VPRT模型问题分析与改进计划

## 问题概述

**VPRT模型**：Vegetation Passive Radiative Transfer Model（植被被动辐射传输模型）
- **场景类型**：植被（Vegetation）
- **模型名称**：VPRT 或 RT
- **支持模式**：目前只支持被动模式（passive/tb），不支持主动模式

## 当前问题

1. **任务提交失败**：VPRT模型在提交任务时出现错误
2. **历史数据调用问题**：可能涉及会话历史中的任务信息提取

## VPRT模型参数特点

### 关键参数结构
VPRT模型的参数结构较为复杂，特别是：

1. **scatters参数**（散射体定义）：
   - 类型：嵌套列表 `List[List[float]]`
   - 每个散射体包含9个参数：`[type, VM, L, D, beta1, beta2, disbot, distop, NA]`
   - 示例：
   ```python
   scatters = [
       [1, 0.37, 7.85, 0.15, 0, 10, 0, 8, 0.24],  # 树枝
       [1, 0.444, 0.555, 0.0112, 35, 90, 2, 5, 34.32]  # 次枝
   ]
   ```

2. **必需参数**：
   - `fGHz`: 频率（单个值，不是数组）
   - `veg_height`: 植被高度
   - `scatters`: 散射体列表
   - `sm`: 土壤湿度
   - `Tveg`, `Tgnd`: 植被和地面温度

3. **特殊注意事项**：
   - 植被场景不支持 `inc_ang`（入射角）参数
   - 只支持被动模式（`output_var` 必须是 `'tb'`）
   - `fGHz` 必须是单个值，不能是数组

## Prompt改进计划

### 1. 参数生成Prompt改进

**位置**：`app/agent/langchain_prompts.py` - `RSHUB_PARAMETER_PARSING_TEMPLATE`

**需要添加的内容**：
- 植被场景的特殊说明
- scatters参数的格式要求
- fGHz必须是单个值的强调
- 植被场景不支持inc_ang的说明

### 2. 错误分析Prompt改进

**位置**：`app/agent/langchain_prompts.py` - `RSHUB_ERROR_ANALYSIS_TEMPLATE`

**需要添加的内容**：
- VPRT模型常见错误类型
- scatters参数格式错误的识别和修复
- fGHz数组vs单个值的错误处理

### 3. 历史数据调用改进

**位置**：
- `app/agent/workflows/rshub_task_extractor.py`
- `app/agent/langchain_prompts.py` - `RSHUB_TASK_EXTRACTION_TEMPLATE`

**需要检查**：
- 植被场景的任务匹配逻辑
- VPRT/RT模型名称的识别

## 具体改进步骤

### 步骤1：优化参数生成Prompt（优先级：高）

在 `RSHUB_PARAMETER_PARSING_TEMPLATE` 的 human message 中添加植被场景特殊说明：

```python
植被场景（VPRT模型）特别注意：
- output_var必须使用'tb'（植被场景只支持被动模式）
- fGHz必须是单个值（float），不能是列表，例如：fGHz = 1.41
- 不要包含inc_ang参数（植被场景不支持入射角参数）
- scatters参数必须是嵌套列表格式，每个散射体包含9个参数：
  [type, VM, L, D, beta1, beta2, disbot, distop, NA]
  - type: 1=圆柱(cylinder), 0=圆盘(disc)
  - VM: 体积含水量
  - L: 散射体长度/厚度（米）
  - D: 散射体直径（米）
  - beta1, beta2: 方向角范围（度）
  - disbot, distop: 垂直分布范围（米）
  - NA: 散射体密度（m^-2）
- 如果用户未指定scatters，使用默认配置：
  scatters = [[1, 0.37, 7.85, 0.15, 0, 10, 0, 8, 0.24], [1, 0.444, 0.555, 0.0112, 35, 90, 2, 5, 34.32]]
```

### 步骤2：优化错误分析Prompt（优先级：高）

在 `RSHUB_ERROR_ANALYSIS_TEMPLATE` 的 system message 中添加VPRT特定错误：

```python
VPRT（植被）模型常见错误：
1. fGHz参数格式错误：必须是单个float值，不能是列表
2. scatters参数格式错误：必须是嵌套列表，每个子列表包含9个数值
3. 包含inc_ang参数：植被场景不支持此参数，需要删除
4. output_var错误：植被场景只支持'tb'，不能使用'bs'
5. scatters参数缺失：如果用户未指定，必须提供默认的scatters配置
```

### 步骤3：检查历史数据调用（优先级：中）

检查 `RSHUB_TASK_EXTRACTION_TEMPLATE` 中是否正确识别：
- 植被场景关键词：vegetation, veg, 植被
- VPRT模型关键词：VPRT, RT, rt, vprt

## 测试建议

1. **测试用例1**：基本VPRT任务提交
   - 用户输入："使用VPRT模型计算植被亮温"
   - 检查：是否正确生成scatters参数，fGHz是否为单个值

2. **测试用例2**：指定参数的VPRT任务
   - 用户输入："使用VPRT模型，频率1.5GHz，植被高度10米"
   - 检查：是否正确处理用户指定的参数

3. **测试用例3**：错误恢复
   - 模拟提交失败，检查错误分析和代码修复是否有效

4. **测试用例4**：历史数据调用
   - 提交VPRT任务后，尝试获取结果
   - 检查：是否能正确识别和匹配植被场景的任务

## 实施时间表

- **12月12日前**：完成Prompt优化（步骤1和2）
- **12月15日前**：完成测试和调试
- **12月18日前**：完成历史数据调用检查（步骤3）

## 相关文件

- `app/agent/langchain_prompts.py` - Prompt定义
- `app/agent/workflows/rshub_workflow_impl.py` - 工作流实现
- `app/agent/workflows/rshub_components.py` - 参数管理
- `workflow_knowledge/veg_parameters.md` - VPRT参数文档
- `workflow_knowledge/RSHub-Technical-documentation.md` - 技术文档

