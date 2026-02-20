import React, { useState, useEffect, useRef } from 'react';
import { useUserAuth } from './UserAuthContext';
import styles from './RSAgentChat.module.css';

// 内部实际的聊天组件
function RSAgentChatInner({
  apiBaseUrl = 'http://localhost:8000',
  showBilling = false,
  onSessionUpdate = null
}) {
  // 添加版本标识，用于确认代码更新
  const VERSION = '1.4.0-session-management';
  console.log('RSAgentChat 版本:', VERSION);
  const { username } = useUserAuth();
  const [messages, setMessages] = useState([]);
  const [inputMessage, setInputMessage] = useState('');
  const [loading, setLoading] = useState(false);
  const [sessionId, setSessionId] = useState(null);
  const [progressMessage, setProgressMessage] = useState('');
  const [selectedFile, setSelectedFile] = useState(null);
  const [websocket, setWebsocket] = useState(null);
  const [markedLoaded, setMarkedLoaded] = useState(false);
  const [hlJsLoaded, setHlJsLoaded] = useState(false);
  const chatHistoryRef = useRef(null);
  const fileInputRef = useRef(null);

  // 会话管理相关状态
  const [currentChatId, setCurrentChatId] = useState(null);
  const [currentChatTitle, setCurrentChatTitle] = useState('');

  // 动态加载marked和highlight.js库
  useEffect(() => {
    const loadMarked = () => {
      if (window.marked) {
        setMarkedLoaded(true);
        initMarkdownRenderer();
        return;
      }
      
      const script = document.createElement('script');
      script.src = 'https://cdn.jsdelivr.net/npm/marked@9.1.6/marked.min.js';
      script.onload = () => {
        setMarkedLoaded(true);
        if (window.hljs) {
          initMarkdownRenderer();
        }
      };
      document.head.appendChild(script);
    };

    const loadHighlightJs = () => {
      if (window.hljs) {
        setHlJsLoaded(true);
        if (window.marked) {
          initMarkdownRenderer();
        }
        return;
      }
      
      const script = document.createElement('script');
      script.src = 'https://cdn.jsdelivr.net/npm/highlight.js@11.9.0/lib/highlight.min.js';
      script.onload = () => {
        setHlJsLoaded(true);
        if (window.marked) {
          initMarkdownRenderer();
        }
      };
      document.head.appendChild(script);
      
      // 加载CSS
      const link = document.createElement('link');
      link.rel = 'stylesheet';
      link.href = 'https://cdn.jsdelivr.net/npm/highlight.js@11.9.0/styles/github-dark.min.css';
      document.head.appendChild(link);
    };

    loadMarked();
    loadHighlightJs();
  }, []);

  // 初始化Markdown渲染器
  const initMarkdownRenderer = () => {
    if (!window.marked || !window.hljs) return;
    
    window.marked.setOptions({
      highlight: function(code, language) {
        if (language && window.hljs.getLanguage(language)) {
          try {
            return window.hljs.highlight(code, { language: language }).value;
          } catch (err) {}
        }
        return window.hljs.highlightAuto(code).value;
      },
      breaks: true,
      gfm: true,
    });
  };

  // 获取用户token - 修改为获取真正的token而不是temptoken
  const getUserToken = () => {
    if (typeof window !== 'undefined' && localStorage) {
      return localStorage.getItem('realToken') || '';
    }
    return '';
  };

  // 添加新的函数：获取真正的token
  const fetchRealToken = async () => {
    const tempToken = localStorage.getItem('tokenTmp');
    if (!tempToken) {
      console.warn('No temp token found');
      return null;
    }

    try {
      const response = await fetch('https://rshub.zju.edu.cn/profile', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          tokenTmp: tempToken
        }),
      });

      if (!response.ok) {
        throw new Error('Failed to fetch profile');
      }

      const profileData = await response.json();
      if (profileData.result && profileData.token) {
        // 将真正的token存储到localStorage
        localStorage.setItem('realToken', profileData.token);
        return profileData.token;
      } else {
        console.error('Failed to get real token:', profileData.error);
        return null;
      }
    } catch (error) {
      console.error('Error fetching real token:', error);
      return null;
    }
  };

  // 初始化时获取真正的token
  useEffect(() => {
    const initRealToken = async () => {
      const existingRealToken = localStorage.getItem('realToken');
      if (!existingRealToken) {
        await fetchRealToken();
      }
    };
    initRealToken();
  }, []);

  // 创建新会话
  const createNewChat = () => {
    setCurrentChatId(null);
    setCurrentChatTitle('');
    setMessages([]);
    setInputMessage('');
    if (selectedFile) {
      clearFile();
    }
    console.log('创建新会话');
  };

  // 切换到指定会话（由外部组件调用）
  const switchToChat = async (chatId, chatTitle) => {
    let token = getUserToken();
    
    // 如果没有realToken，尝试获取
    if (!token) {
      console.log('No real token found, fetching new one...');
      token = await fetchRealToken();
      if (!token) {
        alert('无法获取有效的认证令牌，请重新登录');
        return;
      }
    }

    try {
      setLoading(true);
      
      console.log('Switching to chat:', chatId, 'with token:', token ? 'present' : 'missing');
      
      // 获取会话历史
      const response = await fetch(`${apiBaseUrl}/api/agent/chat/sessions/${chatId}/history`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          token: token
        })
      });

      console.log('Chat history API response status:', response.status);

      if (response.ok) {
        const data = await response.json();
        console.log('Chat history API response data:', data);
        
        if (data.success) {
          setCurrentChatId(chatId);
          setCurrentChatTitle(chatTitle);
          
          // 转换消息格式
          const formattedMessages = data.messages.map((msg, index) => ({
            id: index,
            role: msg.role,
            content: msg.content,
            timestamp: new Date(msg.timestamp),
            sources: msg.sources || []
          }));
          
          setMessages(formattedMessages);
          console.log('切换到会话成功:', chatId, formattedMessages);
          
          // 滚动到底部
          setTimeout(() => scrollToBottom(), 100);
        } else {
          console.error('获取会话历史失败:', data.error);
          alert('获取会话历史失败: ' + data.error);
        }
      } else {
        // 尝试读取错误信息
        try {
          const errorData = await response.json();
          console.error('获取会话历史网络错误:', response.status, errorData);
          alert('获取会话历史失败: ' + (errorData.detail || `HTTP ${response.status}`));
        } catch {
          console.error('获取会话历史网络错误:', response.status);
          alert(`获取会话历史失败: HTTP ${response.status}`);
        }
      }
    } catch (error) {
      console.error('切换会话错误:', error);
      alert('切换会话失败: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  // 初始化会话ID
  useEffect(() => {
    const newSessionId = 'chat_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
    setSessionId(newSessionId);
  }, []);

  // 清理WebSocket连接
  useEffect(() => {
    return () => {
      closeWebSocket();
    };
  }, []);

  // 判断是否可以发送消息
  const canSend = (inputMessage.trim() || selectedFile) && !loading;

  // 发送消息
  const sendMessage = async () => {
    if (!canSend) return;

    // 确保有真正的token
    let realToken = getUserToken();
    if (!realToken) {
      console.log('No real token found, fetching new one...');
      realToken = await fetchRealToken();
      if (!realToken) {
        alert('无法获取有效的RSHub token，请重新登录');
        return;
      }
    }

    const userMessage = inputMessage.trim();
    const hasFile = !!selectedFile;

    // 添加用户消息到对话历史
    const userMsg = {
      id: Date.now(),
      role: 'user',
      content: userMessage,
      hasFile: hasFile,
      timestamp: new Date()
    };
    setMessages(prev => [...prev, userMsg]);

    setLoading(true);
    connectWebSocket();

    try {
      let response;
      
      if (hasFile) {
        response = await sendFileMessage(userMessage);
      } else {
        response = await sendTextMessage(userMessage);
      }

      const data = await response.json();

      if (response.ok) {
        // 调试：打印API返回的数据结构
        console.log('API返回数据:', data);
        console.log('会话ID:', data.chat_id);
        console.log('会话标题:', data.chat_title);
        
        // 尝试多种可能的字段名
        let sources = [];
        if (data.source_files && Array.isArray(data.source_files)) {
          sources = data.source_files;
        } else if (data.sources && Array.isArray(data.sources)) {
          sources = data.sources;
        } else if (data.references && Array.isArray(data.references)) {
          sources = data.references;
        } else if (data.files && Array.isArray(data.files)) {
          sources = data.files;
        }
        
        console.log('最终使用的源文件数据:', sources);
        
        // 添加AI回答到对话历史
        const assistantMsg = {
          id: Date.now() + 1,
          role: 'assistant',
          content: data.response,
          sources: sources,
          images: extractImages(data.response),
          billing: data.billing_info,
          timestamp: new Date()
        };
        
        setMessages(prev => [...prev, assistantMsg]);
        
        // 更新会话信息
        if (data.chat_id) {
          setCurrentChatId(data.chat_id);
          if (data.chat_title) {
            setCurrentChatTitle(data.chat_title);
          }
          
          // 通知父组件会话已更新
          if (onSessionUpdate) {
            onSessionUpdate();
          }
        }
        
        console.log('AI回答已添加到对话历史');

        // 报告计费信息
        if (data.billing_info && showBilling) {
          console.log('计费信息:', data.billing_info);
        }

      } else {
        throw new Error(data.detail || '请求失败');
      }

    } catch (error) {
      console.error('发送消息失败:', error);
      
      // 添加错误消息
      const errorMsg = {
        id: Date.now() + 2,
        role: 'assistant',
        content: '抱歉，处理您的请求时出现了错误，请稍后重试。',
        timestamp: new Date()
      };
      setMessages(prev => [...prev, errorMsg]);

    } finally {
      setLoading(false);
      setInputMessage('');
      clearFile();
      scrollToBottom();
    }
  };

  // 发送纯文本消息
  const sendTextMessage = async (message) => {
    return await fetch(`${apiBaseUrl}/agent/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        message: message,
        session_id: sessionId,
        token: getUserToken(),
        chat_id: currentChatId,  // 添加会话ID
        stream: false
      })
    });
  };

  // 发送带文件的消息
  const sendFileMessage = async (message) => {
    const formData = new FormData();
    formData.append('message', message);
    formData.append('files', selectedFile);
    formData.append('session_id', sessionId);
    formData.append('token', getUserToken());
    formData.append('chat_id', currentChatId || '');  // 添加会话ID

    return await fetch(`${apiBaseUrl}/agent/chat/upload`, {
      method: 'POST',
      body: formData
    });
  };

  // 处理文件选择
  const handleFileSelect = (event) => {
    const file = event.target.files[0];
    if (file) {
      // 检查文件类型
      const allowedTypes = ['.txt', '.md', '.docx', '.csv', '.xlsx'];
      const fileExtension = '.' + file.name.split('.').pop().toLowerCase();
      
      if (allowedTypes.includes(fileExtension)) {
        setSelectedFile(file);
      } else {
        alert('不支持的文件格式。请上传 .txt, .md, .docx, .csv, .xlsx 格式的文件。');
      }
    }
  };

  // 清除选中文件
  const clearFile = () => {
    setSelectedFile(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  // 连接WebSocket获取实时进度
  const connectWebSocket = () => {
    closeWebSocket();

    if (!sessionId) return;

    const wsUrl = `${apiBaseUrl.replace('http', 'ws')}/ws/progress/${sessionId}`;
    const ws = new WebSocket(wsUrl);

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      setProgressMessage(data.message);

      if (data.stage === 'completed' || data.stage === 'error') {
        setTimeout(() => {
          setProgressMessage('');
        }, 2000);
      }
    };

    ws.onerror = () => {
      setProgressMessage('');
    };

    setWebsocket(ws);
  };

  // 关闭WebSocket连接
  const closeWebSocket = () => {
    if (websocket) {
      websocket.close();
      setWebsocket(null);
    }
    setProgressMessage('');
  };

  // 提取回答中的图片URL
  const extractImages = (response) => {
    const imageRegex = /!\[.*?\]\((.*?)\)/g;
    const images = [];
    let match;

    while ((match = imageRegex.exec(response)) !== null) {
      let imageUrl = match[1];
      
      // 处理temp目录的图片路径，确保指向正确的服务器
      if (imageUrl.includes('temp/') && imageUrl.includes('.png')) {
        // 提取文件名
        const filename = imageUrl.split('/').pop();
        
        // 构建标准化的temp路径：/temp/filename.png
        imageUrl = `/temp/${filename}`;
        
        // 构建完整的图片URL，指向RS-agent-mcp服务器
        imageUrl = apiBaseUrl + imageUrl;
        console.log('处理后的图片URL:', imageUrl);
      }
      
      images.push(imageUrl);
    }

    return images;
  };

  // 使用marked库渲染Markdown内容（过滤图片以避免重复显示）
  const renderMarkdown = (text) => {
    if (!text) return '';
    
    try {
      // 移除图片markdown语法，避免与单独的图片显示区域重复
      const textWithoutImages = text.replace(/!\[.*?\]\(.*?\)/g, '');
      
      if (window.marked) {
        return window.marked.parse(textWithoutImages);
      } else {
        // 回退到原有的简单渲染方式
        return renderMarkdownFallback(textWithoutImages);
      }
    } catch (error) {
      console.error('Markdown渲染错误:', error);
      return escapeHtml(text);
    }
  };

  // HTML转义函数
  const escapeHtml = (text) => {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
  };

  // 回退的markdown渲染（原有的简单方式）
  const renderMarkdownFallback = (content) => {
    if (!content) return '';
    
    let result = content;
    
    // 处理代码块（必须在其他处理之前）
    result = result.replace(/```([\s\S]*?)```/g, '<pre><code>$1</code></pre>');
    
    // 处理行内代码（但不在pre标签内）
    result = result.replace(/(?<!<pre><code>)`([^`]+)`(?!<\/code><\/pre>)/g, '<code>$1</code>');
    
    // 处理标题
    result = result.replace(/^### (.*$)/gim, '<h3>$1</h3>');
    result = result.replace(/^## (.*$)/gim, '<h2>$1</h2>');
    result = result.replace(/^# (.*$)/gim, '<h1>$1</h1>');
    
    // 处理粗体和斜体
    result = result.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    result = result.replace(/\*(.*?)\*/g, '<em>$1</em>');
    
    // 处理链接
    result = result.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank" rel="noopener noreferrer">$1</a>');
    
    // 处理图片
    result = result.replace(/!\[([^\]]*)\]\(([^)]+)\)/g, '<img src="$2" alt="$1" style="max-width: 100%; height: auto; border-radius: 8px; margin: 8px 0;" />');
    
    // 处理列表项
    const lines = result.split('\n');
    const processedLines = [];
    let inList = false;
    
    for (let i = 0; i < lines.length; i++) {
      const line = lines[i];
      
      // 检查是否是列表项
      if (/^[\*\-]\s/.test(line) || /^\d+\.\s/.test(line)) {
        if (!inList) {
          processedLines.push('<ul>');
          inList = true;
        }
        processedLines.push(line.replace(/^[\*\-]\s(.*)$/, '<li>$1</li>').replace(/^\d+\.\s(.*)$/, '<li>$1</li>'));
      } else {
        if (inList) {
          processedLines.push('</ul>');
          inList = false;
        }
        processedLines.push(line);
      }
    }
    
    if (inList) {
      processedLines.push('</ul>');
    }
    
    result = processedLines.join('\n');
    
    // 处理引用
    result = result.replace(/^>\s(.*$)/gim, '<blockquote>$1</blockquote>');
    
    // 处理分割线
    result = result.replace(/^---$/gim, '<hr>');
    
    // 处理段落和换行
    result = result.replace(/\n\n/g, '</p><p>');
    result = result.replace(/\n/g, '<br>');
    
    // 包装在段落标签中（但跳过已经是HTML标签的行）
    const finalLines = result.split('</p><p>');
    const wrappedLines = finalLines.map(block => {
      if (block.trim() === '') return block;
      if (/^<[h|p|b|u|o|li|hr|pre]/.test(block.trim())) return block;
      return `<p>${block}</p>`;
    });
    
    result = wrappedLines.join('</p><p>');
    
    // 清理多余的标签
    result = result.replace(/<p><\/p>/g, '');
    result = result.replace(/<p><p>/g, '<p>');
    result = result.replace(/<\/p><\/p>/g, '</p>');
    
    return result;
  };

  // 注释：不再需要自动删除图片功能，改为服务器启动时清空temp目录
  // const setupImageLoadingAndCleanup = () => { ... };
  // const deleteTempImage = async (filename) => { ... };

  // 格式化时间显示
  const formatTime = (date) => {
    return date.toLocaleTimeString('zh-CN', { 
      hour: '2-digit', 
      minute: '2-digit' 
    });
  };

  // 预览图片
  const previewImage = (imageUrl) => {
    window.open(imageUrl, '_blank');
  };

  // 预览源文件
  const previewSource = async (source) => {
    let fileId = source.file_mapping_id || source.id || source.file_id || source.fileId;
    if (fileId) {
        fileId = String(fileId).trim();
        if (fileId === '' || fileId === 'null' || fileId === 'undefined') {
            fileId = null;
        }
    }
    if (!fileId) {
        alert('无法预览：文件ID无效');
        return;
    }
    const encodedFileId = encodeURIComponent(fileId);
    // 只保留知识库预览接口
    const previewUrl = `${apiBaseUrl}/api/v1/knowledge/preview/${encodedFileId}`;
    window.open(previewUrl, '_blank');
  };

  // 滚动到底部
  const scrollToBottom = () => {
    setTimeout(() => {
      if (chatHistoryRef.current) {
        chatHistoryRef.current.scrollTop = chatHistoryRef.current.scrollHeight;
      }
    }, 100);
  };

  // 处理回车发送
  const handleKeyPress = (event) => {
    if (event.key === 'Enter' && event.ctrlKey) {
      sendMessage();
    }
  };

  // 暴露给父组件的方法
  useEffect(() => {
    if (window.RSAgentChat) {
      window.RSAgentChat.switchToChat = switchToChat;
      window.RSAgentChat.createNewChat = createNewChat;
    } else {
      window.RSAgentChat = {
        switchToChat,
        createNewChat
      };
    }
  }, []);

  return (
    <div className={styles.rsAgentChat}>
      {/* 对话历史区域 */}
      <div className={styles.chatHistory} ref={chatHistoryRef}>
        {messages.length === 0 && (
          <div className={styles.welcomeMessage}>
            <h3>欢迎使用RSHub智能助手</h3>
            <p>我是您的微波遥感专业助手，可以帮您解答相关问题、协助环境建模等。请输入您的问题开始对话。</p>
            {currentChatTitle && (
              <div className={styles.currentChatInfo}>
                <span>当前会话: {currentChatTitle}</span>
              </div>
            )}
            <div className={styles.suggestionCards}>
              <div className={styles.suggestionCard} onClick={() => setInputMessage("什么是微波遥感？")}>
                什么是微波遥感？
              </div>
              <div className={styles.suggestionCard} onClick={() => setInputMessage("如何进行植被建模？")}>
                如何进行植被建模？
              </div>
              <div className={styles.suggestionCard} onClick={() => setInputMessage("解释雷达散射原理")}>
                解释雷达散射原理
              </div>
            </div>
          </div>
        )}

        {messages.map((msg) => (
            <div key={msg.id} className={`${styles.message} ${styles[msg.role]}`}>
              <div className={styles.messageContent}>
                {msg.role === 'user' ? (
                  <div className={styles.userMessage}>
                    <div className={styles.messageText}>{msg.content}</div>
                    {msg.hasFile && (
                      <div className={styles.fileIndicator}>
                        包含文件
                      </div>
                    )}
                  </div>
                ) : (
                  <div className={styles.assistantMessage}>
                    {/* AI回答内容 */}
                    <div 
                      className={`${styles.answerContent} markdown-content`} 
                      dangerouslySetInnerHTML={{ __html: renderMarkdown(msg.content) }}
                    />
                    
                    {/* 建模结果图片 */}
                    {msg.images && msg.images.length > 0 && (
                      <div className={styles.resultImages}>
                        <div className={styles.imagesTitle}>建模结果：</div>
                        {msg.images.map((img, idx) => (
                          <img 
                            key={idx}
                            src={img}
                            onClick={() => previewImage(img)}
                            className={styles.resultImage}
                            alt="建模结果"
                          />
                        ))}
                      </div>
                    )}
                    
                    {/* 参考文献 */}
                    {msg.sources && msg.sources.length > 0 && (
                      <div className={styles.sourceFiles}>
                        <div className={styles.sourceTitle}>
                          参考文献 ({msg.sources.length}个文件)
                        </div>
                        <div className={styles.sourceList}>
                          {msg.sources.map((src, index) => {
                            let fileId = src.file_mapping_id || src.id || src.file_id || src.fileId;
                            let fileName = src.display_name || src.filename || src.name || src.title;
                            
                            // 清理和验证fileId
                            if (fileId) {
                              fileId = String(fileId).trim();
                              if (fileId === '' || fileId === 'null' || fileId === 'undefined') {
                                fileId = null;
                              }
                            }
                            
                            // 清理和验证fileName
                            if (fileName) {
                              fileName = String(fileName).trim();
                              if (fileName === '' || fileName === 'null' || fileName === 'undefined') {
                                fileName = null;
                              }
                            }
                            
                            return (
                              <span 
                                key={fileId || index}
                                className={styles.sourceItem}
                                onClick={() => previewSource(src)}
                                title={`点击预览: ${fileName || '未知文件'}`}
                              >
                                {fileName || `文件${index + 1}`}
                                {!fileId && <span style={{color: 'red', fontSize: '10px'}}> (ID缺失)</span>}
                              </span>
                            );
                          })}
                        </div>
                        {/* 调试信息面板已隐藏 */}
                      </div>
                    )}
                    
                    {/* 计费信息 */}
                    {msg.billing && showBilling && (
                      <div className={styles.billingInfo}>
                        💰 LLM: {msg.billing.llm_calls}次 | 建模: {msg.billing.rshub_tasks}个 | 费用: {msg.billing.total_cost}
                      </div>
                    )}
                    
                    {/* Credit信息 (生产模式下显示) */}
                    {msg.billing && (msg.billing.credit_deducted !== undefined) && !msg.billing.local_mode && (
                      <div className={styles.creditInfo}>
                        🪙 消耗Credit：{msg.billing.credit_deducted} | 剩余Credit：{(typeof msg.billing.remaining_credits === 'number' && msg.billing.remaining_credits >= 0) ? msg.billing.remaining_credits : '未知'}
                      </div>
                    )}
                  </div>
                )}
              </div>
              <div className={styles.messageTime}>{formatTime(msg.timestamp)}</div>
            </div>
          ))}
      </div>
      
      {/* 输入区域 */}
      <div className={styles.chatInput}>
        {/* 文件上传按钮 */}
        <div className={styles.inputToolbar}>
          <input
            ref={fileInputRef}
            type="file"
            accept=".txt,.md,.docx,.csv,.xlsx"
            onChange={handleFileSelect}
            style={{ display: 'none' }}
          />
          <button 
            onClick={() => fileInputRef.current?.click()}
            className={styles.fileButton}
            disabled={loading}
          >
            添加文件
          </button>
          
          <button
            onClick={() => createNewChat()}
            className={styles.newChatButton}
            disabled={loading}
          >
            新会话
          </button>
          
          {/* 选中文件显示 */}
          {selectedFile && (
            <div className={styles.selectedFile}>
              <span>{selectedFile.name}</span>
              <button onClick={clearFile} className={styles.clearFileButton}>×</button>
            </div>
          )}
        </div>
        
        {/* 消息输入框 */}
        <div className={styles.inputArea}>
          <textarea
            value={inputMessage}
            onChange={(e) => setInputMessage(e.target.value)}
            placeholder="请输入您关于微波遥感的问题... (Ctrl+Enter发送)"
            onKeyDown={handleKeyPress}
            disabled={loading}
            className={styles.messageInput}
            rows={2}
          />
          <button
            onClick={sendMessage}
            disabled={!canSend}
            className={`${styles.sendButton} ${loading ? styles.loading : ''}`}
          >
            {loading ? '处理中...' : '发送'}
          </button>
        </div>
      </div>
      
      {/* 实时进度提示 */}
      {progressMessage && (
        <div className={styles.progressIndicator}>
          <div className={styles.loadingSpinner}></div>
          {progressMessage}
        </div>
      )}
    </div>
  );
}

// 错误边界组件
class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true };
  }

  componentDidCatch(error, errorInfo) {
    console.error('RSAgentChat Error:', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className={styles.errorMessage}>
          <h3>聊天组件加载失败</h3>
          <p>请刷新页面重试，或联系管理员。</p>
        </div>
      );
    }

    return this.props.children;
  }
}

// 主要导出组件 - 带错误边界保护
export default function RSAgentChat(props) {
  const [isClient, setIsClient] = useState(false);
  
  useEffect(() => {
    setIsClient(true);
  }, []);
  
  // 只在客户端渲染聊天组件
  if (!isClient) {
    return (
      <div className={styles.loadingMessage}>
        <h3>正在加载智能助手...</h3>
      </div>
    );
  }
  
  return (
    <ErrorBoundary>
      <RSAgentChatInner {...props} />
    </ErrorBoundary>
  );
} 