# Snow Scenario Parameters (雪地场景参数)

## DMRT-QMS Model Parameters

### Required Parameters (必需参数)
```python
# Frequency 频率
fGHz = [17.2]  # List of frequencies in GHz

# Observation angles 观测角度
angle = [30, 40, 50]  # List of incident angles in degrees

# Snow layer properties 雪层属性
depth = [30, 20, 7, 18]  # Layer thickness in cm
rho = [0.111, 0.224, 0.189, 0.216]  # Layer density in g/cm³
dia = [0.05, 0.1, 0.2, 0.3]  # Grain size diameter in cm
tau = [0.12, 0.15, 0.25, 0.35]  # Stickiness parameter
Tsnow = [260, 260, 260, 260]  # Snow temperature in K

# Ground properties 地面属性
Tg = 270  # Ground temperature in K
mv = 0.15  # Soil moisture
clayfrac = 0.3  # Clay fraction
```

### Surface Model Settings (表面模型设置)
```python
# Passive mode 被动模式
surf_model_setting_passive = [1, 0.5, 0.5]  # [model, Q, H]
# model: 1 = Q/H model
# Q: polarization mixing factor (0-1)
# H: roughness height factor (0-1)

# Active mode 主动模式
surf_model_setting_active = [1, 0.25, 7]  # [model, rms, ratio]
# model: 1 = OH, 2 = SPM3D, 3 = NMM3D
# rms: rough ground rms height in cm
# ratio: correlation length / rms height
```

## DMRT-BIC Model Parameters

### Required Parameters (必需参数)
```python
# Frequency 频率
fGHz = [9.6, 13.4, 17.2]  # List of frequencies in GHz

# Observation angles 观测角度
angle = [30, 40, 50]  # List of incident angles in degrees

# Snow layer properties 雪层属性
depth = [6, 2, 8]  # Layer thickness in cm
rho = [0.108, 0.108, 0.208]  # Layer density in g/cm³
zp = [1.2, 1.2, 1.6]  # Control size distribution parameter
kc = [7000, 7500, 5500]  # Inversely proportional to grain size [m^-1]
Tsnow = [260, 262, 265]  # Snow temperature in K

# Ground properties 地面属性
Tg = 270  # Ground temperature in K
mv = 0.2  # Soil moisture
clayfrac = 0.3  # Clay fraction
```

### Surface Model Settings (表面模型设置)
```python
# Passive mode 被动模式
surf_model_setting_passive = [1, 0.5, 0.5]  # [model, Q, H]

# Active mode 主动模式
surf_model_setting_active = [3, 0.25, 7]  # [model, rms, ratio]
# model: 1 = OH, 2 = SPM3D, 3 = NMM3D
```

## Default Values (默认值)
- 如果用户未指定，使用上述示例中的默认值
- 频率默认：QMS使用17.2 GHz，BIC使用[10.2, 16.7] GHz
- 角度默认：0到65度，步长5度
- 模型选择：未指定时默认使用QMS模型 