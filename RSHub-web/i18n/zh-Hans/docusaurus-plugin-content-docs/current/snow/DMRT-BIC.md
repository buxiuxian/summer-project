---
sidebar_position: 1

---

import Tabs from '@theme/Tabs';
import TabItem from '@theme/TabItem';

# DMRT-BIC
<Tabs>
  <TabItem value="description" label="模型简介">
    DMRT-双连续模型（DMRT-bicontinuous）是近年来分析雪微波遥感特性的先进方法。该模型结合了Maxwell方程的数值解（NMM3D）与计算机生成的真实雪微观结构。

    双连续表示：本模型的核心在于对雪层内部结构的连续性描述。该结构将不同相（如空气和冰）之间的界面表现为不规则且聚集的形态，模拟了Micro-CT扫描下真实雪的观测结果。

    散射特性提取：为捕捉雪层整体的散射行为，模型采用离散偶极子近似（DDA）方法在生成的微观结构上求解体积积分方程（VIE），得到相位矩阵、消光系数、散射系数和介电常数等关键参数。这些参数有效表征了整个雪层的统计散射特性。

    DMRT用于后向散射与亮温计算：最终，将上述散射特性输入DMRT框架，求解DMRT方程后可预测雪层的后向散射系数和亮温，为遥感应用提供有价值的参考。

    ![vege model 1](/img/Image4.png)

    **图示。** DMRT-BIC模型的有源遥感模式

  </TabItem>
  <TabItem value="parameter" label="参数说明">

  以下为模型参数示例：

  ```{"output_var":2,"fGHz": [9.6,13.4,17.2], "angle": [30,40,50], "depth": [20,20,20],"rho": [0.3,0.3,0.3],"zp": [1.2,1.2,1.2],"kc":[10000,10000,10000],"Tsnow": [260,260,260],"Tg": 270,"epsr_ground_r":[],"epsr_ground_i":[],"mv": 0.15,"clayfrac": 0.3, "surf_model_setting":[1,0,0]} ```

  各参数含义、默认值及单位如下表：
| 参数                | 含义                                     | 默认值           | 单位         |
|---------------------|------------------------------------------|------------------|--------------|
| output_var          | 模式：有源或无源                        | 2                |              |
| fGHz                | 仿真频率                                 | 17.2             | GHz          |
| angle               | 入射角/观测角                            | 40               | 度           |
| depth               | 层厚                                     | 20               | cm           |
| rho                 | 层密度                                   | 0.3              | g/cm³        |
| kc                  | 层kc：与晶粒尺寸成反比                   | 0.1              | m^-1         |
| zp                  | 层zp：控制粒径分布                       | 0.1              |              |
| Tsnow               | 雪层温度                                 | 260              | K            |
| Tg                  | 地表温度                                 | 270              | K            |
| epsr_ground_r       | 土壤介电常数实部                         | Null             |              |
| epsr_ground_i       | 土壤介电常数虚部                         | Null             |              |
| mv                  | 土壤含水量                               | 0.15             |              |
| clayfrac            | 粘土含量质量分数                         | 0.3              |              |
| surf_model_setting  | 1. 物理模型用于地表后向散射计算           | 3,1,0            |              |
|                     | 2. 粗糙地表均方根高度                    |                  |              |
|                     | 3. 相关长度                              |                  |              |
  </TabItem>
  
  <TabItem value="Demonstration" label="演示">
    详情请见 [demo](https://github.com/zjuiEMLab/RShub_demo/blob/main/Snow-demo-2.ipynb)
  </TabItem>

  <TabItem value="Reference" label="参考文献">
    W. Chang, S. Tan, J. Lemmetyinen, L. Tsang, X. Xu and S. H. Yueh, "Dense Media Radiative Transfer Applied to SnowScat and SnowSAR," in IEEE Journal of Selected Topics in Applied Earth Observations and Remote Sensing, vol. 7, no. 9, pp. 3811-3825, Sept. 2014, doi: 10.1109/JSTARS.2014.2343519. 
  </TabItem>
  

</Tabs>