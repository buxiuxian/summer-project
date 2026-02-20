"""
LangChain版本的Prompt模板定义 - 使用LangChain的PromptTemplate和ChatPromptTemplate
"""

from langchain_core.prompts import ChatPromptTemplate, PromptTemplate
from langchain_core.messages import SystemMessage, HumanMessage
from typing import List, Dict, Any

# 任务分类模板
TASK_CLASSIFICATION_TEMPLATE = ChatPromptTemplate.from_messages([
    ("system", "你是一个任务分类专家，请根据用户的输入判断他们想要执行的任务类型。"),
    ("human", """根据用户的要求 "{user_prompt}"，推断他希望执行的任务，并归类为以下几种任务之一：

1: 询问知识（如：什么是机器学习？如何种植番茄？地球的结构是怎样的？介绍一下量子物理的基本概念？）
2: 提交RSHub建模任务（如：请根据这些土壤参数生成微波遥感数据；帮我建立一个雪地散射模型）
3: 获取RSHub任务结果（如：请获取刚才计算任务的结果并为我可视化；刚才提交的任务完成了吗；请帮我分析之前的建模结果）

请分析用户的意图，并在最后一行单独输出任务对应的编号。
如果不属于任何任务类型，在最后一行单独输出数字"-1"。

用户输入：{user_prompt}
上传文件：{file_info}

请在最后一行单独输出数字。""")
])

# 带会话历史的任务分类模板
TASK_CLASSIFICATION_WITH_HISTORY_TEMPLATE = ChatPromptTemplate.from_messages([
    ("system", "你是一个任务分类专家，请根据用户的输入和之前的对话历史判断他们想要执行的任务类型。"),
    ("human", """根据用户的要求 "{user_prompt}"，推断他希望执行的任务，并归类为以下几种任务之一：

1: 询问知识（如：什么是机器学习？如何种植番茄？地球的结构是怎样的？介绍一下量子物理的基本概念？）
2: 提交RSHub建模任务（如：请根据这些土壤参数生成微波遥感数据；帮我建立一个雪地散射模型）
3: 获取RSHub任务结果（如：请获取刚才计算任务的结果并为我可视化；刚才提交的任务完成了吗；请帮我分析之前的建模结果）

请分析用户的意图，并在最后一行单独输出任务对应的编号。
如果不属于任何任务类型，在最后一行单独输出数字"-1"。

以下是之前的对话历史（用于理解上下文）：
{chat_history}

当前用户输入：{user_prompt}
上传文件：{file_info}

请在最后一行单独输出数字。""")
])

# 关键词提取模板
KEYWORD_EXTRACTION_TEMPLATE = ChatPromptTemplate.from_messages([
    ("system", """你是微波遥感领域的专家，擅长从用户问题中提取相关的技术关键词。
请分析用户希望了解的知识点，并推断每个知识点的重要程度权重（权重总和为1）。
权重小于0.1的关键词请不要输出。

重要要求：无论用户问题是什么语言，提取的关键词必须使用英文。这是因为知识库主要包含英文文献，英文关键词能够更有效地检索到相关内容。"""),
    ("human", """请根据用户的问题 "{user_prompt}"，提取相关的关键词。

重要：提取的关键词必须是英文，即使用户问题是中文。请将相关概念转换为标准的英文技术术语。

请在最后一行输出关键词及其权重，格式为：[(keyword1, weight1), (keyword2, weight2), ...]

用户问题：{user_prompt}
上传文件：{file_info}

请分析并在最后一行输出英文关键词权重列表。""")
])

# 带会话历史的关键词提取模板
KEYWORD_EXTRACTION_WITH_HISTORY_TEMPLATE = ChatPromptTemplate.from_messages([
    ("system", """你是微波遥感领域的专家，擅长从用户问题中提取相关的技术关键词。
请分析用户希望了解的知识点，并推断每个知识点的重要程度权重（权重总和为1）。
权重小于0.1的关键词请不要输出。

重要要求：无论用户问题是什么语言，提取的关键词必须使用英文。这是因为知识库主要包含英文文献，英文关键词能够更有效地检索到相关内容。"""),
    ("human", """请根据用户的问题 "{user_prompt}" 和之前的对话历史，提取相关的关键词。

重要：提取的关键词必须是英文，即使用户问题是中文。请将相关概念转换为标准的英文技术术语。

以下是之前的对话历史（用于理解上下文）：
{chat_history}

当前用户问题：{user_prompt}
上传文件：{file_info}

请在最后一行输出关键词及其权重，格式为：[(keyword1, weight1), (keyword2, weight2), ...]

请分析并在最后一行输出英文关键词权重列表。""")
])

# 知识验证模板
KNOWLEDGE_VALIDATION_TEMPLATE = ChatPromptTemplate.from_messages([
    ("system", """你是微波遥感领域的专家，请判断检索到的知识库内容是否与用户问题相关。
判断标准应该宽松：只要内容涉及用户问题的主要概念，即使是具体应用、案例研究或专业细节，都应该认为是有用的。
如果检索到的内容与用户问题的主题相关，输出"0"。
只有完全无关的内容才输出"-1"。"""),
    ("human", """用户问题：{user_prompt}
从知识库检索到的内容：{retrieved_content}

请使用宽松的标准判断：
- 如果内容涉及用户问题的核心概念（即使是专业应用、技术细节或特定场景），都认为是相关和有用的
- 如果内容可以帮助用户理解相关概念或提供相关信息，都应该通过验证
- 只有完全无关的内容（如完全不同的主题）才判断为不相关

如果检索到的内容与用户问题主题相关，在最后一行单独输出数字"0"。
只有完全无关的内容才输出数字"-1"。

请在最后一行单独输出0或-1。""")
])

# 带会话历史的知识验证模板
KNOWLEDGE_VALIDATION_WITH_HISTORY_TEMPLATE = ChatPromptTemplate.from_messages([
    ("system", """你是微波遥感领域的专家，请判断检索到的知识库内容是否与用户问题相关。
判断标准应该宽松：只要内容涉及用户问题的主要概念，即使是具体应用、案例研究或专业细节，都应该认为是有用的。
如果检索到的内容与用户问题的主题相关，输出"0"。
只有完全无关的内容才输出"-1"。"""),
    ("human", """以下是之前的对话历史（用于理解上下文）：
{chat_history}

当前用户问题：{user_prompt}
从知识库检索到的内容：{retrieved_content}

请使用宽松的标准判断：
- 如果内容涉及用户问题的核心概念（即使是专业应用、技术细节或特定场景），都认为是相关和有用的
- 如果内容可以帮助用户理解相关概念或提供相关信息，都应该通过验证
- 只有完全无关的内容（如完全不同的主题）才判断为不相关

如果检索到的内容与用户问题主题相关，在最后一行单独输出数字"0"。
只有完全无关的内容才输出数字"-1"。

请在最后一行单独输出0或-1。""")
])

# 最终答案模板
FINAL_ANSWER_TEMPLATE = ChatPromptTemplate.from_messages([
    ("system", """你是微波遥感领域的专家，请基于提供的知识库内容为用户提供准确、专业的回答。
回答应该：
1. 直接针对用户问题
2. 基于检索到的专业知识
3. 语言清晰易懂
4. 结构化组织"""),
    ("human", """用户问题：{user_prompt}
上传文件信息：{file_info}
知识库检索内容：{retrieved_content}

请基于检索到的知识库内容，为用户问题提供详细、准确的回答。

请提供完整的回答：""")
])

# 带会话历史的最终答案模板
FINAL_ANSWER_WITH_HISTORY_TEMPLATE = ChatPromptTemplate.from_messages([
    ("system", """你是微波遥感领域的专家，请基于提供的知识库内容和之前的对话历史为用户提供准确、专业的回答。
回答应该：
1. 直接针对用户问题
2. 基于检索到的专业知识
3. 考虑之前的对话上下文
4. 语言清晰易懂
5. 结构化组织
6. 如果用户的问题与之前的对话相关，请结合之前的内容提供连贯的回答"""),
    ("human", """以下是之前的对话历史（用于理解上下文）：
{chat_history}

当前用户问题：{user_prompt}
上传文件信息：{file_info}
知识库检索内容：{retrieved_content}

请基于检索到的知识库内容和之前的对话历史，为用户问题提供详细、准确的回答。

请提供完整的回答：""")
])

# 环境构建模板
ENVIRONMENT_CONSTRUCTION_TEMPLATE = ChatPromptTemplate.from_messages([
    ("system", """你是微波遥感建模专家，请根据用户需求编写Python代码来构建遥感环境模型。
你编写的Python脚本应该在回答结尾，用```python和```括起。"""),
    ("human", """请按照用户的要求和上传的文件，按照预设的Python脚本模板和RSHub的技术文档，
编写一段Python脚本代码，使得用户能使用你的代码在RSHub上运行数据分析，
从而根据用户输入的参数构建出微波遥感的环境数据。

用户要求：{user_prompt}
上传文件：{file_info}
技术文档：{technical_docs}

你编写的Python脚本应该在回答结尾，用```python和```括起。""")
])

# 带会话历史的环境构建模板
ENVIRONMENT_CONSTRUCTION_WITH_HISTORY_TEMPLATE = ChatPromptTemplate.from_messages([
    ("system", """你是微波遥感建模专家，请根据用户需求和之前的对话历史编写Python代码来构建遥感环境模型。
你编写的Python脚本应该在回答结尾，用```python和```括起。"""),
    ("human", """请按照用户的要求、上传的文件和之前的对话历史，按照预设的Python脚本模板和RSHub的技术文档，
编写一段Python脚本代码，使得用户能使用你的代码在RSHub上运行数据分析，
从而根据用户输入的参数构建出微波遥感的环境数据。

以下是之前的对话历史（用于理解上下文）：
{chat_history}

当前用户要求：{user_prompt}
上传文件：{file_info}
技术文档：{technical_docs}

你编写的Python脚本应该在回答结尾，用```python和```括起。""")
])



# 文档转换模板
DOCUMENT_CONVERSION_TEMPLATE = ChatPromptTemplate.from_messages([
    ("system", """你是一个专业的文档处理专家。请根据用户上传的文件内容，
总结和概括其中内容，以清晰的结构和准确的语言写成一篇markdown格式的文字。
要求：
1. 保持原文的核心信息和重要细节
2. 使用合适的markdown格式（标题、列表、代码块等）
3. 结构清晰，层次分明
4. 语言准确，表达简洁
5. 如果包含专业术语，请保持原有表述"""),
    ("human", """请将以下文档内容转换为结构化的Markdown格式：

--- 原始文档内容 ---
{extracted_text}
--- 文档内容结束 ---

请以Markdown格式重新组织和呈现这些内容。""")
])

# RSHub场景分类模板
RSHUB_SCENARIO_CLASSIFICATION_TEMPLATE = ChatPromptTemplate.from_messages([
    ("system", """你是RSHub建模专家。请判断用户想要进行哪种场景的建模。
场景类型：
0: 雪地（Snow）- 使用DMRT-QMS或DMRT-BIC模型
1: 土壤（Soil）- 使用AIEM模型
2: 植被（Vegetation）- 使用VPRT模型

如果用户同时提到多种场景、指定不支持的场景或请求不明确，返回-1。
请在最后一行单独输出对应的数字。"""),
    ("human", """用户要求：{user_prompt}
上传文件：{file_info}

请判断用户想要进行哪种场景的建模，在最后一行单独输出对应的数字（0/1/2/-1）。""")
])

# RSHub参数解析模板
RSHUB_PARAMETER_PARSING_TEMPLATE = ChatPromptTemplate.from_messages([
    ("system", """你是RSHub建模专家。请根据用户的输入和技术文档，生成填充参数的Python代码。

重要规则：
1. 只修改用户明确指定的参数，其他参数保持默认值
2. 生成的代码应该可以直接执行
3. 必须生成扁平的data字典结构，不要使用嵌套的params子字典
4. 注意不同场景的参数差异
5. 代码必须包含在```python和```标记之间
6. output_var参数必须使用字符串：'tb'表示被动模式，'bs'表示主动模式
7. 不要在代码中包含token参数，token会自动添加

场景：{scenario_name}
模型：{model_name}
观测模式：{observation_modes}"""),
    ("human", """用户要求：{user_prompt}
上传文件内容：{file_content}
技术文档：{technical_docs}

请生成填充参数的Python代码。

重要格式要求：
- 必须生成扁平的data字典，将所有参数直接放在data字典中
- 不要创建嵌套的子字典（如params、parameters等）
- output_var必须使用字符串：被动模式用'tb'，主动模式用'bs'
- 不要包含token、project_name、task_name等系统参数
- **多参数处理**：如果用户要求分析多个参数值（如"分别分析2米、5米、8米和12米的植被高度"或"分析多个频率"），必须为每个参数值组合生成独立的data字典：
  - 使用data1, data2, data3, data4...等命名（第一个可以用data或data1）
  - 每个data字典包含对应的参数值
  - 其他未变化的参数保持一致
  - 例如：用户要求"分析植被高度2米、5米、8米"，应生成data1（veg_height=2）、data2（veg_height=5）、data3（veg_height=8）

正确的格式示例：
```python
# 参数定义
fGHz = [17.2]
theta_i_deg = [10, 20, 30, 40, 50, 60]  # 土壤场景使用theta_i_deg
# ... 其他参数

# data字典 - 扁平结构，不要嵌套
data = {{
    "output_var": "bs",
    "fGHz": fGHz,
    "theta_i_deg": theta_i_deg,
    # ... 直接包含所有参数，不要创建params子字典
}}
```

土壤场景特别注意：
- 使用'theta_i_deg'参数名（这是土壤场景的标准参数）
- 除非用户明确指定单个角度，否则应该使用多个角度来获取完整的角度响应曲线
- 推荐格式：theta_i_deg = [10, 20, 30, 40, 50, 60]（AIEM模型会在一个任务中计算所有角度）
- 单角度格式：theta_i_deg = 40（仅当用户明确指定时使用）

植被场景（VPRT模型）特别注意：
- output_var必须使用'tb'（植被场景只支持被动模式，不支持主动模式）
- fGHz必须是单个float值，不能是列表，例如：fGHz = 1.41（错误：fGHz = [1.41]）
- **多频率处理**：如果用户要求分析多个频率（如"分别分析1.0 GHz、1.41 GHz和6.9 GHz"或"分析多个频率"），必须为每个频率生成独立的data字典：
  - 使用data1, data2, data3, data4...等命名（第一个可以用data或data1）
  - 每个data字典的fGHz设置为对应的单个频率值
  - 其他参数保持一致（使用相同的默认值或用户指定的值）
  ```python
  # 多频率示例1：用户要求分析1.0 GHz、1.41 GHz和6.9 GHz（3个频率）
  data1 = {{"output_var": "tb", "fGHz": 1.0, "veg_height": 8, "scatters": [...], ...}}
  data2 = {{"output_var": "tb", "fGHz": 1.41, "veg_height": 8, "scatters": [...], ...}}
  data3 = {{"output_var": "tb", "fGHz": 6.9, "veg_height": 8, "scatters": [...], ...}}
  
  # 多频率示例2：用户要求分析4个频率（如1.0, 1.41, 6.9, 10.0 GHz）
  data1 = {{"output_var": "tb", "fGHz": 1.0, "veg_height": 8, "scatters": [...], ...}}
  data2 = {{"output_var": "tb", "fGHz": 1.41, "veg_height": 8, "scatters": [...], ...}}
  data3 = {{"output_var": "tb", "fGHz": 6.9, "veg_height": 8, "scatters": [...], ...}}
  data4 = {{"output_var": "tb", "fGHz": 10.0, "veg_height": 8, "scatters": [...], ...}}
  
  # 关键规则：
  # 1. 用户指定多少个频率，就生成多少个data字典
  # 2. 第一个字典可以用data或data1命名
  # 3. 后续字典必须用data2, data3, data4...依次命名
  # 4. 每个字典的fGHz必须是单个值，不能是列表
  ```
- 不要包含inc_ang参数（植被场景不支持入射角参数，如果代码中有此参数必须删除）
- scatters参数必须是嵌套列表格式，每个散射体包含9个参数：
  [type, VM, L, D, beta1, beta2, disbot, distop, NA]
  - type: 1=圆柱(cylinder), 0=圆盘(disc)
  - VM: 体积含水量（Volumetric moisture）
  - L: 散射体长度/厚度（米）
  - D: 散射体直径（米）
  - beta1, beta2: 方向角范围（度）
  - disbot, distop: 垂直分布范围下限和上限（米）
  - NA: 散射体密度（m^-2）
- 如果用户未指定scatters，必须提供默认配置：
  scatters = [[1, 0.37, 7.85, 0.15, 0, 10, 0, 8, 0.24], [1, 0.444, 0.555, 0.0112, 35, 90, 2, 5, 34.32]]
- 必需参数：fGHz, veg_height, scatters, sm, Tveg, Tgnd
- 可选参数：rmsh, corlength, clay, perm_soil_r, perm_soil_i, rough_type, err, Flag_coupling, Flag_forced_cal, core_num

代码必须用```python和```括起。""")
])

# RSHub错误分析模板
RSHUB_ERROR_ANALYSIS_TEMPLATE = ChatPromptTemplate.from_messages([
    ("system", """你是RSHub调试专家。请分析任务提交失败的原因并提供修复建议。
常见错误类型：
1. 参数类型错误（如应该是列表但提供了单个值，或应该是单个值但提供了列表）
2. 参数超出有效范围
3. 必需参数缺失
4. 参数格式错误

VPRT（植被）模型特定错误：
1. fGHz参数格式错误：必须是单个float值（如 fGHz = 1.41），不能是列表（错误：fGHz = [1.41]）
2. scatters参数格式错误：
   - 必须是嵌套列表：scatters = [[...], [...]]
   - 每个子列表必须包含9个数值
   - 不能是单个列表或字典格式
3. 包含inc_ang参数：植被场景不支持此参数，必须删除
4. output_var错误：植被场景只支持'tb'（被动模式），不能使用'bs'（主动模式）
5. scatters参数缺失：如果代码中没有scatters参数，必须添加默认配置
6. scatters参数中数值类型错误：所有9个值都必须是数值类型（int或float），不能是字符串"""),
    ("human", """错误信息：{error_message}
原始代码：{original_code}
场景类型：{scenario_type}

请分析错误原因并提供修正后的代码。修正后的代码用```python和```括起。""")
])

# RSHub任务总结模板
RSHUB_TASK_SUMMARY_TEMPLATE = ChatPromptTemplate.from_messages([
    ("system", """你是RSHub建模专家。请总结刚刚完成的建模任务。
总结应包括：
1. 模拟的场景类型
2. 使用的模型
3. 观测模式
4. 修改的参数（只列出非默认值的参数）
5. 任务执行状态
6. 生成的结果说明"""),
    ("human", """任务信息：
场景：{scenario}
模型：{model}
观测模式：{observation_modes}
修改的参数：{modified_params}
任务状态：{task_status}
错误信息（如有）：{error_info}

请生成简洁的任务总结。""")
])

# RSHub模型判断模板
RSHUB_MODEL_SELECTION_TEMPLATE = ChatPromptTemplate.from_messages([
    ("system", """你是RSHub建模专家。根据用户需求判断应使用的模型。

雪地场景：
- 默认使用QMS模型
- 如果用户明确提到BIC，则使用BIC模型

土壤场景：
- 只有AIEM模型

植被场景：
- 只有VPRT(RT)模型

请在最后一行输出模型名称（QMS/BIC/AIEM/RT）。"""),
    ("human", """场景类型：{scenario_type}
用户要求：{user_prompt}

请判断应使用的模型，在最后一行单独输出模型名称。""")
])

# RSHub观测模式判断模板  
RSHUB_OBSERVATION_MODE_TEMPLATE = ChatPromptTemplate.from_messages([
    ("system", """你是RSHub建模专家。根据场景和用户需求判断需要的观测模式。

观测模式类型：
- active (bs): 主动模式，后向散射
- passive (tb): 被动模式，亮温

不同场景的规则：
- 雪地：支持active和passive，默认只创建passive
- 土壤：同时计算active和passive，只需一个任务
- 植被：目前只支持passive

输出格式：['active', 'passive'] 或 ['passive'] 或 ['active']"""),
    ("human", """场景类型：{scenario_name}
用户要求：{user_prompt}

请判断需要的观测模式，在最后一行输出列表格式，如：['passive'] 或 ['active', 'passive']""")
])

# 通用回答模板（用于处理任务分类失败的情况）
GENERAL_ANSWER_TEMPLATE = ChatPromptTemplate.from_messages([
    ("system", """你是微波遥感领域的专家助手，请根据用户的问题提供专业、准确的回答。
如果问题不在你的专业领域内，请诚实地说明并尽可能提供相关的建议或指导。"""),
    ("human", """用户问题：{user_prompt}
上传文件信息：{file_info}

请为用户问题提供专业的回答。""")
])

# 带会话历史的通用回答模板
GENERAL_ANSWER_WITH_HISTORY_TEMPLATE = ChatPromptTemplate.from_messages([
    ("system", """你是微波遥感领域的专家助手，请根据用户的问题和之前的对话历史提供专业、准确的回答。
如果问题不在你的专业领域内，请诚实地说明并尽可能提供相关的建议或指导。
请确保回答与之前的对话上下文保持一致和连贯。"""),
    ("human", """以下是之前的对话历史（用于理解上下文）：
{chat_history}

当前用户问题：{user_prompt}
上传文件信息：{file_info}

请基于之前的对话历史和当前问题，为用户提供专业、连贯的回答。""")
])

# RSHub任务信息提取模板
RSHUB_TASK_EXTRACTION_TEMPLATE = ChatPromptTemplate.from_messages([
    ("system", """你是RSHub任务管理专家。请根据用户的当前请求和会话历史，精确确定用户想要获取结果的具体任务。

重要匹配规则：
1. 场景类型匹配是最高优先级，必须严格匹配：
   - 雪地/雪/snow 关键词 → 只能匹配项目名称包含"snow"的任务
   - 土壤/soil 关键词 → 只能匹配项目名称包含"soil"的任务  
   - 植被/vegetation/veg 关键词 → 只能匹配项目名称包含"veg"的任务
   - 绝对禁止：雪地请求匹配植被任务，土壤请求匹配雪地任务等交叉匹配

2. 模型匹配作为次要条件：
   - BIC/bic → 项目名称包含"bic"
   - QMS/qms → 项目名称包含"qms"
   - NMM3D/nmm3d → 项目名称包含"nmm3d"
   - VPRT/RT/rt → 项目名称包含"rt"

3. 时间指示词：
   - 最近/最新/刚才/刚刚 → 时间戳最晚的任务
   - 第一个/之前的/早期 → 时间戳最早的任务

4. 严格验证：
   - 在输出项目名称前，必须验证该项目的场景类型是否与用户请求匹配
   - 如果场景类型不匹配，必须输出"NOT_FOUND"

输出格式：输出完整的项目名称（project_name），如果无法确定或场景不匹配则输出"NOT_FOUND"。"""),
    ("human", """用户当前请求：{user_prompt}

会话历史和可选任务：
{chat_history}

请严格按照以下步骤分析：

第一步：提取用户请求中的场景关键词
- 是否包含"雪地"、"雪"、"snow"？
- 是否包含"土壤"、"soil"？  
- 是否包含"植被"、"vegetation"、"veg"？

第二步：提取用户请求中的模型关键词
- 是否包含"BIC"、"bic"？
- 是否包含"QMS"、"qms"？
- 是否包含"NMM3D"、"nmm3d"？
- 是否包含"VPRT"、"RT"、"rt"？

第三步：在可选任务列表中匹配
- 先按场景类型筛选任务
- 再按模型类型进一步筛选
- 最后按时间顺序选择

第四步：验证匹配结果
- 确认选中的任务场景类型与用户请求一致
- 如果不一致，输出"NOT_FOUND"

请在最后一行输出目标任务的项目名称（project_name）。""")
])

# 通用知识回答模板 - 用于知识库查询失败时的回退机制
GENERAL_KNOWLEDGE_ANSWER_TEMPLATE = ChatPromptTemplate.from_messages([
    ("system", """你是一个知识渊博、友好的AI助手，能够回答各个领域的问题。
请根据你的知识为用户提供准确、有帮助的回答。
回答应该：
1. 针对用户问题直接回答
2. 结构清晰，容易理解
3. 如果涉及专业概念，请用通俗易懂的语言解释
4. 如果不确定某些信息，请诚实说明"""),
    ("human", """用户问题：{user_prompt}
上传文件信息：{file_info}

请基于你的知识为用户问题提供详细、准确的回答。

请提供完整的回答：""")
])

# 便捷函数，用于获取已格式化的提示词
def get_task_classification_prompt(user_prompt: str, file_info: str) -> ChatPromptTemplate:
    """获取任务分类提示词"""
    return TASK_CLASSIFICATION_TEMPLATE

def get_keyword_extraction_prompt(user_prompt: str, file_info: str) -> ChatPromptTemplate:
    """获取关键词提取提示词"""
    return KEYWORD_EXTRACTION_TEMPLATE

def get_knowledge_validation_prompt(user_prompt: str, retrieved_content: str) -> ChatPromptTemplate:
    """获取知识验证提示词"""
    return KNOWLEDGE_VALIDATION_TEMPLATE

def get_final_answer_prompt(user_prompt: str, file_info: str, retrieved_content: str) -> ChatPromptTemplate:
    """获取最终答案提示词"""
    return FINAL_ANSWER_TEMPLATE

def get_environment_construction_prompt(user_prompt: str, file_info: str, technical_docs: str) -> ChatPromptTemplate:
    """获取环境构建提示词"""
    return ENVIRONMENT_CONSTRUCTION_TEMPLATE



def get_document_conversion_prompt(extracted_text: str) -> ChatPromptTemplate:
    """获取文档转换提示词"""
    return DOCUMENT_CONVERSION_TEMPLATE

# 便捷函数
def get_rshub_scenario_classification_prompt(user_prompt: str, file_info: str) -> ChatPromptTemplate:
    """获取RSHub场景分类提示词"""
    return RSHUB_SCENARIO_CLASSIFICATION_TEMPLATE

def get_rshub_parameter_parsing_prompt(scenario_name: str, model_name: str, observation_modes: str, 
                                     user_prompt: str, file_content: str, technical_docs: str) -> ChatPromptTemplate:
    """获取RSHub参数解析提示词"""
    return RSHUB_PARAMETER_PARSING_TEMPLATE

def get_rshub_error_analysis_prompt(error_message: str, original_code: str, scenario_type: str) -> ChatPromptTemplate:
    """获取RSHub错误分析提示词"""
    return RSHUB_ERROR_ANALYSIS_TEMPLATE

def get_rshub_task_summary_prompt(scenario: str, model: str, observation_modes: str, 
                                modified_params: str, task_status: str, error_info: str) -> ChatPromptTemplate:
    """获取RSHub任务总结提示词"""
    return RSHUB_TASK_SUMMARY_TEMPLATE

def get_rshub_model_selection_prompt(scenario_type: str, user_prompt: str) -> ChatPromptTemplate:
    """获取RSHub模型判断提示词"""
    return RSHUB_MODEL_SELECTION_TEMPLATE

def get_rshub_observation_mode_prompt(scenario_name: str, user_prompt: str) -> ChatPromptTemplate:
    """获取RSHub观测模式判断提示词"""
    return RSHUB_OBSERVATION_MODE_TEMPLATE

def get_general_answer_prompt(user_prompt: str, file_info: str) -> ChatPromptTemplate:
    """获取通用回答提示词"""
    return GENERAL_ANSWER_TEMPLATE

def get_general_knowledge_answer_prompt(user_prompt: str, file_info: str) -> ChatPromptTemplate:
    """获取通用知识回答prompt"""
    return GENERAL_ANSWER_TEMPLATE

def get_rshub_task_extraction_prompt(user_prompt: str, chat_history: str) -> ChatPromptTemplate:
    """获取RSHub任务信息提取prompt"""
    return RSHUB_TASK_EXTRACTION_TEMPLATE

# 辅助函数：格式化会话历史
def format_chat_history(messages: List[Dict[str, Any]]) -> str:
    """
    格式化会话历史为字符串
    
    Args:
        messages: 消息列表，每个消息包含role和content
        
    Returns:
        格式化后的会话历史字符串
    """
    if not messages:
        return "无历史对话记录"
    
    formatted_history = []
    for msg in messages:
        role = msg.get("role", "unknown")
        content = msg.get("content", "")
        timestamp = msg.get("timestamp", "")
        
        if role == "user":
            formatted_history.append(f"用户: {content}")
        elif role == "assistant":
            formatted_history.append(f"AI助手: {content}")
        else:
            formatted_history.append(f"{role}: {content}")
    
    return "\n".join(formatted_history)

# 辅助函数：获取带会话历史的prompt模板
def get_task_classification_prompt_with_history(user_prompt: str, file_info: str, chat_history: str) -> ChatPromptTemplate:
    """获取带会话历史的任务分类prompt"""
    return TASK_CLASSIFICATION_WITH_HISTORY_TEMPLATE

def get_keyword_extraction_prompt_with_history(user_prompt: str, file_info: str, chat_history: str) -> ChatPromptTemplate:
    """获取带会话历史的关键词提取prompt"""
    return KEYWORD_EXTRACTION_WITH_HISTORY_TEMPLATE

def get_knowledge_validation_prompt_with_history(user_prompt: str, retrieved_content: str, chat_history: str) -> ChatPromptTemplate:
    """获取带会话历史的知识验证prompt"""
    return KNOWLEDGE_VALIDATION_WITH_HISTORY_TEMPLATE

def get_final_answer_prompt_with_history(user_prompt: str, file_info: str, retrieved_content: str, chat_history: str) -> ChatPromptTemplate:
    """获取带会话历史的最终答案prompt"""
    return FINAL_ANSWER_WITH_HISTORY_TEMPLATE

def get_environment_construction_prompt_with_history(user_prompt: str, file_info: str, technical_docs: str, chat_history: str) -> ChatPromptTemplate:
    """获取带会话历史的环境构建prompt"""
    return ENVIRONMENT_CONSTRUCTION_WITH_HISTORY_TEMPLATE



def get_general_answer_prompt_with_history(user_prompt: str, file_info: str, chat_history: str) -> ChatPromptTemplate:
    """获取带会话历史的通用回答prompt"""
    return GENERAL_ANSWER_WITH_HISTORY_TEMPLATE 