---
sidebar_position: 3

---

import Tabs from '@theme/Tabs';
import TabItem from '@theme/TabItem';

# 分层土壤全波模型 - 基于体积积分方程的三维数值Maxwell模型与离散偶极子近似（Layed Soil-NMM3D-VIE-DDA）
<Tabs>
  <TabItem value="description" label="模型简介">
    分层土壤半空间等效微波模型是一种简化方法，用于模拟分层土壤的有源/无源微波观测。该模型通过定义分层土壤的半空间等效表示形式，并依赖AIEM模型处理均匀介质半空间中的土壤粗糙表面，来模拟土壤的微波参数，如后向散射系数、双站散射系数、相干反射系数和微波亮温。模型通过界面粗糙度、各层厚度和介电常数来描述分层土壤。

    ![vege model 1](/img/image1.png)

    **图示。** 分层土壤及平面波入射示意图。

  </TabItem>
  <TabItem value="parameter" label="参数说明">

  以下为模型参数示例：

  ```{"h": 0.01, "cLx": 0.1, "cLy": 0.1, "Lx": 1.6, "Ly": 1.6, "Lz": 0.08, "xr": -0.8, "yr": -0.8, "zr": 0, "d": 0.01, "freq": 1.26e9, "deg0": 40, "epsr_ice_re": 4.024, "epsr_ice_im": 0.3, "epsr_g_re": 5.198, "epsr_g_im": 0.445, "Ts": 300.75, "Tg": 295.15, "nr": 15, "ir_beg": 1, "ir_end": 15, "tol": 0.001, "rest": 10, "maxiter": 30000, "N": 10000, "seed": 100}```

  各参数含义、默认值及单位如下表：
    | 参数         | 含义                                  | 默认值         | 单位       |
    |--------------|---------------------------------------|----------------|------------|
    | h            | 土壤粗糙度的均方根高度                | 0.013          | m          |
    | cLx          | x方向粗糙度相关长度                   | 0.15           | m          |
    | cLy          | y方向粗糙度相关长度                   | 0.15           | m          |
    | Lx           | x方向切割立方体长度                   | 1.8            | m          |
    | Ly           | y方向切割立方体长度                   | 1.8            | m          |
    | Lz           | z方向切割立方体长度                   | 0.05           | m          |
    | xr           | x方向起始边界                         | -0.9           | m          |
    | yr           | y方向起始边界                         | -0.9           | m          |
    | zr           | z方向起始边界                         | 0              |            |
    | d            | 表层土壤深度                          | 0.005          | m          |
    | freq         | 波频率                                 | 1.26e9         | Hz         |
    | deg0         | 入射角（度）                          | 40             | 度         |
    | epsr_ice_re  | 表层介质介电常数实部                  | 5.2            | 1          |
    | epsr_ice_im  | 表层介质介电常数虚部                  | 0.46           | 1          |
    | epsr_g_re    | 基底层介质介电常数实部                | 5.2            | 1          |
    | epsr_g_im    | 基底层介质介电常数虚部                | 0.46           | 1          |
    | Ts           | 表层介质温度                          | 300.75         | K          |
    | Tg           | 基底层温度                            | 295.15         | K          |
    | nr           | 蒙特卡洛实现次数                      | 15             | 1          |
    | ir_beg       | 实现起始编号                          | 1              | 1          |
    | ir_end       | 实现结束编号                          | 15             | 1          | 
    | tol          | GMRES 收敛容差                        | 0.001          | 1          |
    | rest         | GMRES 重启次数                        | 10             | 1          |
    | maxiter      | GMRES 内循环最大迭代次数               | 30000          | 1          |
    | N            | 无需设置                              | 10000          | 1          |
    | seed         | 无需设置                              | 100            | 1          | 
  </TabItem>

  <TabItem value="Reference" label="参考文献">
    [5] Tsang, L., Liao, T. H., Tan, S., Huang, H., Qiao, T., & Ding, K. H. (2017). Rough Surface and Volume Scattering of Soil Surfaces, Ocean Surfaces, Snow, and Vegetation Based on Numerical Maxwell Model of 3-D Simulations. IEEE J. Sel. Topics Appl. Earth Observ. Remote Sens., 10(11), 4703-4720. 
  </TabItem>

</Tabs>