---
sidebar_position: 1

---

import Tabs from '@theme/Tabs';
import TabItem from '@theme/TabItem';

# 植被被动辐射传输模型（VPRT）
<Tabs>
  <TabItem value="description" label="模型简介">
    本模型基于辐射传输理论，估算植被覆盖地表的亮温。它同时考虑了植被层内部和植被-土壤散射相互作用中的多重散射效应。该模型支持植被组分的垂直异质分布，可更好地表征复杂植被场景（如不同生长阶段的混合树种）。平台允许用户自定义植被的垂直结构以适应自身科研需求，并为探索其对相关微波辐射的影响提供了可靠工具。

    ![vege model 1](/img/Image2.png)

    **图示。** 四层植被场景示意图。d 为植被总高度（z）。辐射计以入射角 θ 接收信号。

  </TabItem>
  <TabItem value="parameter" label="参数说明">

  以下为默认参数示例：

  ```{"fGHz": 1.41, "core_num": 10, "scatters": [[1, 0.37, 7.85, 0.15, 0, 0, 0, 8, 0.24], [1, 0.444, 0.555, 0.0112, 35, 90, 0, 8, 0.24]], "sm": 0.1, "rmsh": 0.01, "clay": 0.19, "perm_soil_r": 0, "perm_soil_i": 0, "veg_height": 8, "err": 0.1, "Tgnd": 300, "Tveg": 300, "Flag_forced_cal": 0}```

  各参数含义、默认值及单位如下表：
    | 参数                   | 含义                                    | 默认值         | 单位 |
|---------------------------|------------------------------------------|---------------|------|
| **观测设置**              |                                          |               |      |
| fGHz                      | 仿真频率                                 | 1.41          | GHz  |
|                           |                                          |               |      |
| **模型设置**              |                                          |               |      |
| err                       | 收敛误差                                 | 0.1           | K    |
|                           |                                          |               |      |
| **植被设置**              |                                          |               |      |
| T                         | 植被温度                                 | 300           | K    |
| Height_total              | 植被层高度                               | 8             | m    |
| num_scat                  | 散射体类型数                             | 4             |      | 
| **-> 每类散射体的八个属性** |                                         |               |      |
| type                      | 散射体类型；1为圆柱，0为圆盘             | 1, 1, 1, 0    |      |
| VM                        | 散射体体积含水量                         | 0.37, 0.501, 0.444, 0.58 |      |
| L                         | 散射体长度                               | 7.85, 1.41, 0.555, 1e-4 | m    |
| D                         | 散射体直径                               | 15e-2, 2.88e-2, 1.12e-2, 2e-2 | m    |
| betar                     | 散射体取向范围                           | [0,10], [30,90], [35,90], [0,90] | 度   |
| density                   | 散射体密度                               | 0.24, 3.12, 34.32, 7712 | m^-2 |
| distribution              | 散射体垂直分布范围                       | [0,8], [2.3,5], [2,5], [2,8] | m    |
|                           |                                          |               |      |
| **土壤设置**              |                                          |               |      |
| soil_mv                   | 土壤含水量                               | 0.2           |      |
| perm_soil; ```{real,image}```   | 土壤介电常数实部和虚部                 | 0 + i0        | 非必填，默认0 + i0  |
| clay                      | 粘土比例                                 | 0.19          |      |
| rms                       | 均方根高度                               | 1e-2          | m    |
| T2                        | 土壤温度                                 | 300           | K    |
  </TabItem>

  <TabItem value="Demonstration" label="演示">
    本模型演示数据来自 SMAPVEX12 野外观测试验。SMAPVEX12 于2012年6月6日至7月17日开展，旨在研究SMAP产品与土壤和植被水分变化的关系，并开发土壤水分反演算法。

    详情请见 [demo](https://github.com/zjuiEMLab/RShub_demo/blob/main/Vegetation-demo-2.ipynb)
  </TabItem>

  <TabItem value="Reference" label="参考文献">
    K. Chen and S. Tan, “A Multiple-Scattering Microwave Radiative Transfer Model for Land Emission With Vertically Heterogeneous Vegetation Coverage,” IEEE Transactions on Geoscience and Remote Sensing, 2024. 
  </TabItem>

</Tabs>