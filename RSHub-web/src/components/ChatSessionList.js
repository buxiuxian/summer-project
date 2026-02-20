import React, { useState, useEffect } from 'react';
import styles from './ChatSessionList.module.css';
import { useUserAuth } from './UserAuthContext';

const ChatSessionList = ({ 
  apiBaseUrl = 'http://localhost:8000',
  onRefresh = null 
}) => {
  const { username } = useUserAuth();
  const [sessions, setSessions] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // 获取用户token - 使用realToken
  const getUserToken = () => {
    if (typeof window !== 'undefined' && localStorage) {
      return localStorage.getItem('realToken') || '';
    }
    return '';
  };

  // 获取真正的token
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

  // 加载会话列表
  const loadSessions = async () => {
    let token = getUserToken();
    
    // 如果没有realToken，尝试获取
    if (!token) {
      console.log('No real token found, fetching new one...');
      token = await fetchRealToken();
      if (!token) {
        setError('无法获取有效的认证令牌，请重新登录');
        return;
      }
    }

    try {
      setLoading(true);
      setError(null);
      
      console.log('Loading sessions with token:', token ? 'present' : 'missing');
      
      const response = await fetch(`${apiBaseUrl}/api/agent/chat/sessions`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          token: token
        })
      });

      console.log('Sessions API response status:', response.status);

      if (response.ok) {
        const data = await response.json();
        console.log('Sessions API response data:', data);
        
        if (data.success) {
          setSessions(data.sessions || []);
          console.log('会话列表加载成功:', data.sessions);
        } else {
          setError(data.error || '加载失败');
        }
      } else {
        // 尝试读取错误信息
        try {
          const errorData = await response.json();
          setError(errorData.detail || `网络请求失败 (${response.status})`);
        } catch {
          setError(`网络请求失败 (${response.status})`);
        }
      }
    } catch (error) {
      console.error('加载会话列表错误:', error);
      setError('加载失败: ' + error.message);
    } finally {
      setLoading(false);
    }
  };

  // 切换会话
  const switchToSession = async (sessionId, sessionTitle) => {
    if (window.RSAgentChat && window.RSAgentChat.switchToChat) {
      window.RSAgentChat.switchToChat(sessionId, sessionTitle);
    } else {
      console.error('RSAgentChat API未找到');
    }
  };

  // 删除会话
  const deleteSession = async (sessionId) => {
    if (!window.confirm('确定要删除这个会话吗？此操作不可撤销。')) {
      return;
    }

    try {
      console.log('Deleting session:', sessionId);
      
      const response = await fetch(`${apiBaseUrl}/api/agent/chat/sessions/${sessionId}`, {
        method: 'DELETE',
        headers: {
          'Content-Type': 'application/json',
        }
      });

      console.log('Delete API response status:', response.status);

      if (response.ok) {
        const data = await response.json();
        console.log('Delete API response data:', data);
        
        if (data.success) {
          setSessions(prev => prev.filter(session => session.session_id !== sessionId));
          console.log('删除会话成功:', sessionId);
        } else {
          alert('删除会话失败: ' + data.error);
        }
      } else {
        // 尝试读取错误信息
        try {
          const errorData = await response.json();
          alert('删除会话失败: ' + (errorData.detail || `HTTP ${response.status}`));
        } catch {
          alert(`删除会话失败: HTTP ${response.status}`);
        }
      }
    } catch (error) {
      console.error('删除会话错误:', error);
      alert('删除会话失败: ' + error.message);
    }
  };

  // 格式化时间
  const formatTime = (dateString) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffTime = Math.abs(now - date);
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));
    
    if (diffDays === 1) {
      return '今天';
    } else if (diffDays <= 7) {
      return `${diffDays}天前`;
    } else {
      return date.toLocaleDateString('zh-CN');
    }
  };

  // 初始加载
  useEffect(() => {
    loadSessions();
  }, []);

  // 监听外部刷新请求
  useEffect(() => {
    if (onRefresh) {
      loadSessions();
    }
  }, [onRefresh]);

  return (
    <div className={styles.chatSessionList}>
      <div className={styles.header}>
        <h3>会话历史</h3>
        <button 
          className={styles.refreshButton}
          onClick={loadSessions}
          disabled={loading}
        >
          {loading ? '加载中...' : '刷新'}
        </button>
      </div>

      <div className={styles.sessionContainer}>
        {loading && !sessions.length ? (
          <div className={styles.loadingState}>
            <div className={styles.spinner}></div>
            <p>加载会话列表...</p>
          </div>
        ) : error ? (
          <div className={styles.errorState}>
            <p>加载失败: {error}</p>
            <button onClick={loadSessions}>重试</button>
          </div>
        ) : sessions.length === 0 ? (
          <div className={styles.emptyState}>
            <p>暂无会话记录</p>
            <p>开始新的对话来创建会话</p>
          </div>
        ) : (
          <div className={styles.sessionTable}>
            <div className={styles.tableHeader}>
              <div className={styles.headerCell}>名称</div>
              <div className={styles.headerCell}>描述</div>
              <div className={styles.headerCell}>类型</div>
              <div className={styles.headerCell}>更新时间</div>
              <div className={styles.headerCell}>操作</div>
            </div>
            
            <div className={styles.tableBody}>
              {sessions.map(session => (
                <div 
                  key={session.session_id}
                  className={styles.sessionRow}
                  onClick={() => switchToSession(session.session_id, session.title)}
                >
                  <div className={styles.tableCell}>
                    <div className={styles.sessionName}>
                      {session.title || '未命名会话'}
                    </div>
                  </div>
                  <div className={styles.tableCell}>
                    <div className={styles.sessionDescription}>
                      {session.message_count || 0} 条消息的对话
                    </div>
                  </div>
                  <div className={styles.tableCell}>
                    <div className={styles.sessionType}>
                      聊天对话
                    </div>
                  </div>
                  <div className={styles.tableCell}>
                    <div className={styles.sessionTime}>
                      {formatTime(session.updated_at)}
                    </div>
                  </div>
                  <div className={styles.tableCell}>
                    <button
                      className={styles.deleteButton}
                      onClick={(e) => {
                        e.stopPropagation();
                        deleteSession(session.session_id);
                      }}
                      title="删除会话"
                    >
                      ×
                    </button>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default ChatSessionList; 