# RS Agent MCP 前后端连接诊断工具

## 🎯 目的

这个工具用于诊断RS Agent MCP后端与RSHub前端之间的连接问题，帮助快速定位和解决集成过程中遇到的各种问题。

## 🚀 使用方法

### 1. 安装依赖

确保安装了必要的Python包：

```bash
pip install requests websockets
```

### 2. 运行诊断工具

在RS-agent-mcp项目根目录下运行：

```bash
# 使用默认地址 (http://localhost:8000)
python test/test_frontend_connection.py

# 或指定自定义地址
python test/test_frontend_connection.py http://localhost:8001
```

### 3. 查看结果

工具会执行以下测试：

1. **基本连通性测试** - 验证服务器是否正常运行
2. **CORS配置测试** - 检查跨域访问配置
3. **API端点测试** - 测试聊天接口是否正常工作
4. **WebSocket连接测试** - 验证实时进度功能
5. **前端模拟测试** - 模拟真实前端请求

## 📊 输出说明

### 成功示例
```
🔍 1. 测试服务器基本连通性...
   ✅ 健康检查: 200
   ✅ 根路径: 200

🔍 2. 测试CORS配置...
   ✅ OPTIONS请求: 200
   📋 CORS Headers: {'Access-Control-Allow-Origin': '*', ...}

🔍 3. 测试Agent API端点...
   ✅ 聊天端点: 200
   📝 响应预览: 收到您的消息: 测试连接。这是一个测试响应...

🔍 4. 测试WebSocket连接...
   ✅ WebSocket连接成功
   ✅ 初始消息: WebSocket连接已建立
   ✅ 心跳响应: 心跳响应

🔍 5. 模拟前端请求...
   ✅ 前端模拟请求成功: 200

📈 总体结果: 10/10 项测试通过
✅ 所有测试通过！前后端连接正常。
```

### 失败示例
```
🔍 1. 测试服务器基本连通性...
   ❌ 健康检查失败: Connection refused

📈 总体结果: 0/10 项测试通过
❌ 关键问题: 服务器健康检查失败 - 请确认服务器是否正常运行
```

## 🛠️ 常见问题及解决方案

### 1. 服务器连接失败
**错误**: `Connection refused` 或 `健康检查失败`

**解决方案**:
- 确认RS Agent MCP服务器已在8000端口启动
- 检查防火墙是否阻止了8000端口
- 确认.env配置文件是否正确

### 2. CORS错误
**错误**: `CORS问题: 跨域配置可能有问题`

**解决方案**:
- 检查后端的CORS配置是否允许前端域名
- 在开发环境下，确认CORS配置为允许所有源(`"*"`)

### 3. API端点404错误
**错误**: `聊天端点失败: 404`

**解决方案**:
- 检查路由注册是否正确
- 确认API端点实现是否存在语法错误
- 查看服务器启动日志获取详细信息

### 4. WebSocket连接失败
**错误**: `WebSocket连接失败`

**解决方案**:
- 确认安装了websockets库: `pip install websockets`
- 检查WebSocket端点是否正确实现
- 验证防火墙是否允许WebSocket连接

## 📝 详细结果文件

运行后会生成 `diagnostic_results.json` 文件，包含所有测试的详细结果，可以用于进一步分析。

## 🆘 获取帮助

如果诊断工具显示所有测试通过，但前端仍然无法连接：

1. **检查前端配置**:
   - 确认前端的API URL配置正确
   - 检查前端是否运行在正确的端口
   
2. **检查浏览器**:
   - 打开浏览器开发者工具的Network标签
   - 查看实际发送的请求是否正确
   - 检查Console是否有JavaScript错误

3. **检查网络**:
   - 确认前后端在同一网络环境
   - 检查是否有代理或VPN影响连接

## 🔧 高级用法

### 自定义测试

你可以修改 `test_frontend_connection.py` 中的测试参数：

```python
# 修改测试数据
data = {
    "message": "你的自定义测试消息",
    "session_id": "custom_session_id",
    "token": "your_test_token",
    "stream": False
}
```

### 批量测试

测试多个服务器：

```bash
python test/test_frontend_connection.py http://localhost:8000
python test/test_frontend_connection.py http://localhost:8001
python test/test_frontend_connection.py http://your-server:8000
```

---

**💡 提示**: 运行诊断工具前，请确保RS Agent MCP服务器已经启动并运行正常。 