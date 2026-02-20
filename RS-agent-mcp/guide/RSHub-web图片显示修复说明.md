# RSHub-web图片显示修复说明

## 问题描述

在RSHub-web中嵌入的Agent页面，当AI回答生成图片时存在以下问题：
1. 图片无法正确显示
2. 原本设置的图片在浏览器中正常显示后自动从temp目录中删除该图片的机制失效

## 解决方案

参考 `RS-agent-mcp/static/index.html` 中的图片显示机制，在RSHub-web的RSAgentChat组件中实现了完整的图片显示和自动删除功能。

## 修改内容

### 1. RSAgentChat.js 主要修改

#### 新增功能模块
- **动态库加载**: 动态加载marked和highlight.js库，确保markdown渲染功能可用
- **专业Markdown渲染**: 使用marked库替代原有的简单正则表达式处理
- **图片自动清理**: 实现图片加载完成后自动删除temp文件的机制

#### 具体修改点

1. **添加状态管理**
```javascript
const [markedLoaded, setMarkedLoaded] = useState(false);
const [hlJsLoaded, setHlJsLoaded] = useState(false);
```

2. **动态加载依赖库**
```javascript
// 动态加载marked和highlight.js库
useEffect(() => {
  const loadMarked = () => { /* 加载marked库 */ };
  const loadHighlightJs = () => { /* 加载highlight.js库 */ };
  loadMarked();
  loadHighlightJs();
}, []);
```

3. **初始化Markdown渲染器**
```javascript
const initMarkdownRenderer = () => {
  if (!window.marked || !window.hljs) return;
  
  window.marked.setOptions({
    highlight: function(code, language) {
      // 配置代码高亮
    },
    breaks: true,
    gfm: true,
  });
};
```

4. **专业Markdown渲染**
```javascript
const renderMarkdown = (text) => {
  if (!text) return '';
  
  try {
    if (window.marked) {
      return window.marked.parse(text);
    } else {
      return renderMarkdownFallback(text); // 回退到原有方式
    }
  } catch (error) {
    console.error('Markdown渲染错误:', error);
    return escapeHtml(text);
  }
};
```

5. **图片加载监听和自动删除**
```javascript
const setupImageLoadingAndCleanup = () => {
  setTimeout(() => {
    const images = document.querySelectorAll('.markdown-content img, .answerContent img');
    images.forEach((img) => {
      if (img.src && img.src.includes('/temp/') && img.src.includes('.png')) {
        const filename = new URL(img.src).pathname.split('/').pop();
        
        if (img.complete && img.naturalHeight !== 0) {
          deleteTempImage(filename);
        } else {
          img.onload = () => {
            setTimeout(() => deleteTempImage(filename), 1000);
          };
          img.onerror = () => deleteTempImage(filename);
        }
      }
    });
  }, 100);
};
```

6. **删除临时图片文件**
```javascript
const deleteTempImage = async (filename) => {
  try {
    const response = await fetch(`${apiBaseUrl}/api/v1/files/temp/${filename}`, {
      method: 'DELETE'
    });
    
    if (response.ok) {
      console.log(`成功删除temp图片: ${filename}`);
    }
  } catch (error) {
    console.error(`删除temp图片时出错: ${filename}`, error);
  }
};
```

7. **集成图片清理到消息显示流程**
- 在AI回答添加到消息历史后，立即调用 `setupImageLoadingAndCleanup()`
- 为AI回答内容添加 `markdown-content` CSS类，便于图片选择器定位

### 2. RSAgentChat.module.css 样式修改

#### 新增Markdown内容样式
```css
/* Markdown内容样式 */
.markdown-content {
  word-wrap: break-word;
  overflow-wrap: break-word;
  max-width: 100%;
  overflow-x: hidden;
  box-sizing: border-box;
}

.markdown-content img {
  max-width: 100%;
  height: auto;
  border-radius: 8px;
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
  margin: 15px 0;
  display: block;
  border: 1px solid #e9ecef;
  cursor: pointer;
  transition: all 0.3s ease;
}

.markdown-content img:hover {
  box-shadow: 0 6px 12px rgba(0, 0, 0, 0.15);
  transform: scale(1.02);
  border-color: #B08EAD;
}
```

#### 暗色模式支持
```css
[data-theme='dark'] .markdown-content img {
  border-color: #404040;
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.4);
}

[data-theme='dark'] .markdown-content img:hover {
  box-shadow: 0 6px 12px rgba(0, 0, 0, 0.5);
  border-color: var(--ifm-color-primary-lighter);
}
```

## 核心技术特性

### 1. 渐进式增强
- 优先使用专业的marked库进行markdown渲染
- 如果库加载失败，自动回退到原有的简单渲染方式
- 确保在任何情况下都能正常显示内容

### 2. 图片生命周期管理
- 监听图片的加载完成事件
- 处理图片加载失败的情况
- 延迟删除确保用户能看到图片
- 避免删除非临时图片文件

### 3. 用户体验优化
- 图片悬停效果和点击预览
- 响应式设计支持
- 暗色模式兼容
- 渐进式加载指示

## 使用方法

修改完成后，RSHub-web中的Agent页面会自动应用新的图片显示机制：

1. **自动启用**: 无需额外配置，修改后的组件会自动加载所需依赖
2. **图片显示**: AI生成包含图片的回答时，图片会正确渲染并显示
3. **自动清理**: 图片加载完成后，临时文件会在1秒后自动删除
4. **错误处理**: 如果图片加载失败，仍会尝试删除临时文件

## 兼容性说明

- **向后兼容**: 保留了原有的渲染方式作为回退方案
- **库依赖**: 动态加载CDN资源，不影响打包体积
- **性能优化**: 图片清理机制不会影响用户交互性能
- **错误处理**: 全面的错误处理确保功能稳定性

## 测试建议

1. **基本图片显示**: 向AI询问需要生成图表的问题，验证图片正确显示
2. **自动删除**: 检查temp目录中的图片文件是否在显示后被删除
3. **多图片处理**: 测试AI回答包含多张图片的情况
4. **错误恢复**: 测试网络不佳时的图片加载和处理情况
5. **暗色模式**: 在暗色和亮色主题间切换，验证图片样式正确

## 最新修复

### 2025-01-03 关键问题修复

**问题描述**：
在实际测试中发现，尽管前端组件已经修复，但仍然出现404错误：
- 图片文件正确生成：`temp\snow_tb_snow-qms-20250703125024909.png`
- 但访问 `/temp/xxx.png` 时返回404

**根本原因**：
1. **extractImages函数逻辑缺陷**：原有逻辑只处理以 `/temp/` 开头的路径
2. **静态文件服务缺失**：RS-agent-mcp服务器没有配置 `/temp` 静态文件服务

**完整修复方案**：

1. **优化图片URL处理逻辑**
```javascript
// 修复前（有问题）
if (imageUrl.startsWith('/temp/')) {
  imageUrl = apiBaseUrl + imageUrl;
}

// 修复后（简化且健壮）
if (imageUrl.includes('temp/') && imageUrl.includes('.png')) {
  const filename = imageUrl.split('/').pop();
  imageUrl = `/temp/${filename}`;
  imageUrl = apiBaseUrl + imageUrl;
}
```

2. **添加静态文件服务配置**
在 `RS-agent-mcp/main.py` 中添加：
```python
# 挂载静态文件目录
app.mount("/static", StaticFiles(directory="static"), name="static")
app.mount("/temp", StaticFiles(directory="temp"), name="temp")  # 新增
```

3. **确保temp目录存在**
```python
# 确保temp目录存在
temp_dir = "temp"
if not os.path.exists(temp_dir):
    os.makedirs(temp_dir)
    logger.info(f"📁 创建temp目录: {temp_dir}")
```

**测试验证**：
创建了专门的验证脚本 `test/test_rshub_web_image_fix.py`，包含：
- 图片URL处理逻辑测试
- 静态文件服务验证
- Markdown渲染测试
- 端到端功能验证

## 版本标识

当前修改版本: `1.3.0-image-fix`

通过控制台可以看到版本信息：
```
RSAgentChat 版本: 1.3.0-image-fix
```

## 快速验证

修复完成后，请按以下步骤验证：

1. **重启RS-agent-mcp服务器**：
```bash
cd RS-agent-mcp
python main.py
```

2. **运行验证脚本**：
```bash
cd RS-agent-mcp
python test/test_rshub_web_image_fix.py
```

3. **在RSHub-web中测试**：
- 访问Agent页面
- 询问需要生成图表的问题
- 确认图片正确显示且自动删除 