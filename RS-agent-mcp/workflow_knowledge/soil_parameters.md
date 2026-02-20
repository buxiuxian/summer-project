# Soil Scenario Parameters (土壤场景参数)

## AIEM Model Parameters

### Required Parameters (必需参数)
```python
# Frequency 频率
fGHz = 1.26  # Frequency in GHz

# Observation angles 观测角度
theta_i_deg = [10, 20, 30, 40, 50, 60]  # Incident angles in degrees
theta_s_deg = 3  # Scattering angle in degrees
phi_s_deg = 12.2034  # Scattering azimuth angle in degrees
phi_i_deg = 0  # Incident azimuth angle in degrees

# Surface roughness parameters 表面粗糙度参数
ks = 0.2955  # Normalized surface rms height (k * rms height)
kl = 0.2955  # Normalized surface correlation length (k * correlation length)
rough_type = 2  # Correlation function type
# 1 = Gaussian
# 2 = Exponential (default)
# 3 = Transformed exponential (1.5-power)

# Soil dielectric properties 土壤介电特性
perm_soil_r = 10.0257  # Real part of relative dielectric constant
perm_soil_i = 1.1068  # Imaginary part of relative dielectric constant
```

### Alternative Parameters (替代参数)
```python
# 可以使用土壤湿度和黏土含量代替介电常数
mv = 0.15  # Soil moisture (volumetric)
clayfrac = 0.3  # Clay fraction

# 如果提供了mv和clayfrac，系统会自动计算介电常数
# 如果同时提供了介电常数和土壤参数，介电常数优先
```

### Output Configuration (输出配置)
```python
output_var = 'bs'  # 土壤场景同时计算主动和被动结果
# 使用'bs'标记来获取主动模式结果
# 被动模式结果也会同时计算
```

## Default Values (默认值)
- 频率默认：1.26 GHz
- 入射角默认：[10, 20, 30, 40, 50, 60]度
- 粗糙度类型默认：2 (指数相关函数)
- 如果用户未指定参数，使用上述默认值

## Important Notes (重要说明)
1. AIEM模型可以一次计算多个角度，但load_file目前一次只能加载一个角度的结果
2. 土壤场景的任务名与项目名相同
3. 主动和被动模式结果都会计算，通过output_var选择要获取的结果类型 