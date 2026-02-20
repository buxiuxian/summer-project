# Vegetation Scenario Parameters (植被场景参数)

## VPRT (RT) Model Parameters

### Required Parameters (必需参数)
```python
# Frequency 频率
fGHz = 1.41  # Frequency in GHz

# Vegetation height 植被高度
veg_height = 8  # Height of vegetation layer in meters

# Scatterers definition 散射体定义
scatters = []  # List of scatterer properties

# Each scatterer is defined as:
# [type, VM, L, D, beta1, beta2, disbot, distop, NA]
# Where:
# type: 1 = cylinder (圆柱), 0 = disc (圆盘)
# VM: Volumetric moisture (体积含水量)
# L: Length/thickness of scatterer in meters
# D: Diameter of scatterer in meters
# beta1: Lower bound of orientation angle in degrees
# beta2: Upper bound of orientation angle in degrees
# disbot: Lower bound of vertical distribution in meters
# distop: Upper bound of vertical distribution in meters
# NA: Density of scatterer (m^-2)
```

### Example Scatterers (散射体示例)
```python
# Branch 树枝
scatters.append([1, 0.37, 7.85, 0.15, 0, 10, 0, 8, 0.24])

# Primary branch 主枝
scatters.append([1, 0.501, 1.41, 0.0288, 30, 90, 2, 3.5, 3.12])

# Secondary branch 次枝
scatters.append([1, 0.444, 0.555, 0.0112, 35, 90, 2, 5, 34.32])

# Leaf 叶片
scatters.append([0, 0.58, 0.0001, 0.04, 0, 90, 2, 8, 7712.64])
```

### Soil Parameters (土壤参数)
```python
# Soil moisture 土壤湿度
sm = 0.1  # Volumetric soil moisture

# Surface roughness 表面粗糙度
rmsh = 0.01  # RMS height in meters
corlength = 0.1  # Correlation length

# Soil properties 土壤属性
clay = 0.19  # Clay ratio
perm_soil_r = 0  # Real part of soil permittivity (0 = auto-calculate)
perm_soil_i = 0  # Imaginary part of soil permittivity (0 = auto-calculate)

# Roughness model 粗糙度模型
rough_type = 2  # 1 = Gaussian, 2 = Exponential
```

### Temperature Settings (温度设置)
```python
Tveg = 300  # Vegetation temperature in K
Tgnd = 300  # Ground temperature in K
```

### Model Configuration (模型配置)
```python
# Convergence and coupling 收敛和耦合
err = 0.1  # Convergence error in K
Flag_coupling = 1  # 1 = use volume-surface coupling, 0 = volume only

# Computation settings 计算设置
Flag_forced_cal = 0  # 0 = use cached results if available, 1 = force recalculate
core_num = 10  # Number of CPU cores to use
```

## Default Values (默认值)
- 频率默认：1.41 GHz
- 植被高度默认：8米
- 温度默认：300K
- 如果用户未指定散射体，使用上述示例配置

## Important Notes (重要说明)
1. 植被场景目前只支持被动模式（亮温）
2. 可以通过修改散射体的垂直分布范围来模拟分层或均匀植被
3. 散射体必须按照指定的9个参数顺序定义 