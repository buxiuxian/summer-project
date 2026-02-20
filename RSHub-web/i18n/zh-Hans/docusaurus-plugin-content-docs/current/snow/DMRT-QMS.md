---
sidebar_position: 2

---

import Tabs from '@theme/Tabs';
import TabItem from '@theme/TabItem';

# DMRT-QMS
<Tabs>
  <TabItem value="description" label="模型简介">
    DMRT-QMS 是一种广泛应用于雪层有源和无源微波建模的物理散射模型，基于致密介质辐射传输理论（DMRT）。DMRT 理论可预测致密随机介质中的微波强度散射、吸收和传播。在 DMRT-QCA 中，采用准晶体近似（QCA）方法，通过求解中等粒径、密集粘结球体的多重散射，来表征雪的散射特性。QCA 方法可提供频率、粒径和密度相关的广泛散射特性，并具有中等前向散射模式。雪粒大小、雪的粘结性、雪密度（或等效冰体积分数）以及雪温都会影响这些特性。在 DMRT-QMS 中，采用本征值分析的离散纵标方法求解冰粒子间多重散射下的辐射传输方程。DMRT-QMS 可计算雪层的亮温（Tbs）和后向散射系数。

    ![vege model 1](/img/Image3.png)

    **图示。** DMRT-QMS模型的有源遥感模式

  </TabItem>
  <TabItem value="parameter" label="参数说明">

  以下为模型默认参数：

  ```{"output_var":2,"fGHz": [9.6,17.2], "angle": [40,], "depth": [30,20,7,18],"rho": [0.111,0.224,0.189,0.216],"dia": [0.05,0.1,0.2,0.3],"tau":[0.12,0.15,0.25,0.35],"Tsnow": [260,260,260,260],"Tg": 270,"epsr_ground_r":[3],"epsr_ground_i":[1],"mv": 0.15,"clayfrac": 0.3, "surf_model_setting":[2,0.305,4]} ```

  各参数含义、默认值及单位如下表：
    | 参数                | 含义                                     | 默认值           | 单位         |
|--------------------|---------------------------------------------|--------------------|--------------|
| output_var         | 模式：有源或无源                            | 2                  |              |
| fGHz               | 仿真频率                                   | 9.6, 17.2          | GHz          |
| angle              | 入射角/观测角                              | 40                 | 度           |
| depth              | 层厚                                       | 20                 | cm           |
| rho                | 层密度                                     | 0.3                | g/cm³        |
| dia                | 层粒径                                     | 0.1                | cm           |
| tau                | 层粘结性                                   | 0.1                |              |
| Tsnow              | 雪层温度                                   | 260                | K            |
| Tg                 | 地表温度                                   | 270                | K            |
| epsr_ground_r      | 土壤介电常数实部                           | Null               |              |
| epsr_ground_i      | 土壤介电常数虚部                           | Null               |              |
| mv                 | 土壤含水量                                 | 0.15               |              |
| clayfrac           | 粘土含量质量分数                           | 0.3                |              |
| surf_model_setting | 1. 物理模型用于地表后向散射计算             | 3,1,0              |              |
|                    | 2. 有源：粗糙地表均方根高度（cm）；无源：极化混合因子（无量纲） |       |       |
|                    | 3. 有源：相关长度；无源：粗糙度高度因子（无量纲） |              |              |
  </TabItem>

  <TabItem value="Demonstration" label="演示">
    详情请见 [demo](https://github.com/zjuiEMLab/RShub_demo/blob/main/Snow-demo-1.ipynb)
  </TabItem>

  <TabItem value="Reference" label="参考文献">
    W. Chang, S. Tan, J. Lemmetyinen, L. Tsang, X. Xu and S. H. Yueh, "Dense Media Radiative Transfer Applied to SnowScat and SnowSAR," in IEEE Journal of Selected Topics in Applied Earth Observations and Remote Sensing, vol. 7, no. 9, pp. 3811-3825, Sept. 2014, doi: 10.1109/JSTARS.2014.2343519. 
  </TabItem>

</Tabs>