import React, { useState, useEffect } from 'react';
import Layout from '@theme/Layout';
import { translate } from '@docusaurus/Translate';
import Heading from '@theme/Heading';
import RSAgentChat from '../components/RSAgentChat';
import ChatSessionList from '../components/ChatSessionList';
import { useUserAuth } from '../components/UserAuthContext';
import styles from './Agent.module.css';

// 内部Agent组件
function AgentInner() {
  const { isLoggedIn, username } = useUserAuth();
  // 添加状态来管理会话列表的刷新
  const [sessionRefreshTrigger, setSessionRefreshTrigger] = useState(0);

  // 会话更新回调
  const handleSessionUpdate = () => {
    // 通过改变state来触发会话列表刷新
    setSessionRefreshTrigger(prev => prev + 1);
  };
  
  return (
    <div className={styles.agentPage}>
      {/* 页面头部 */}
      <div className={styles.heroSection}>
        <div className={styles.heroContent}>
          <Heading as="h1" className={styles.heroTitle}>
            {translate({id: 'agent.heroTitle', message: 'RS Agent 智能助手'})}
          </Heading>
          <p className={styles.heroSubtitle}>
            {translate({id: 'agent.heroSubtitle', message: '基于大语言模型的微波遥感专业助手，助您解答问题、构建模型、分析数据'})}
          </p>
          
          {/* 功能特性卡片 */}
          <div className={styles.featuresGrid}>
            <div className={styles.featureCard}>
              <div className={styles.featureIcon}>🧠</div>
              <h3>智能问答</h3>
              <p>专业的微波遥感知识问答，基于丰富的科学文献和实践经验</p>
            </div>
            <div className={styles.featureCard}>
              <div className={styles.featureIcon}>🔬</div>
              <h3>环境建模</h3>
              <p>智能识别建模需求，自动提交RSHub计算任务，获取精确建模结果</p>
            </div>
            <div className={styles.featureCard}>
              <div className={styles.featureIcon}>📄</div>
              <h3>文档分析</h3>
              <p>上传研究文档，AI将结合文档内容进行深度分析和专业解答</p>
            </div>
            <div className={styles.featureCard}>
              <div className={styles.featureIcon}>⚡</div>
              <h3>实时处理</h3>
              <p>WebSocket实时进度反馈，让您及时了解任务处理状态</p>
            </div>
          </div>
        </div>
      </div>

      {/* 聊天界面区域 */}
      <div className={styles.chatSection}>
        <div className={styles.chatContainer}>
          {isLoggedIn ? (
            <div className={styles.chatWrapper}>
              <div className={styles.chatHeader}>
                <h2>{translate({id: 'agent.chatTitle', message: '开始与AI助手对话'})}</h2>
                <p className={styles.userGreeting}>
                  {translate({id: 'agent.userGreeting', message: '欢迎您'}, {username: username})} {username}！
                </p>
              </div>
              <div className={styles.chatMainArea}>
                <RSAgentChat 
                  apiBaseUrl="http://localhost:8000"
                  showBilling={false}
                  onSessionUpdate={handleSessionUpdate}
                />
              </div>
            </div>
          ) : (
            <div className={styles.loginPrompt}>
              <div className={styles.loginPromptContent}>
                <div className={styles.loginIcon}>🔐</div>
                <h3>{translate({id: 'agent.loginRequired', message: '请先登录'})}</h3>
                <p>{translate({id: 'agent.loginMessage', message: '使用RS Agent智能助手需要登录RSHub账户'})}</p>
                <a href="/Login" className={styles.loginButton}>
                  {translate({id: 'agent.loginButtonText', message: '立即登录'})}
                </a>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* 会话历史区域 */}
      {isLoggedIn && (
        <div className={styles.sessionHistorySection}>
          <div className={styles.sessionHistoryContainer}>
            <Heading as="h2" className={styles.sessionHistoryTitle}>
              {translate({id: 'agent.sessionHistoryTitle', message: '会话历史'})}
            </Heading>
            <ChatSessionList 
              apiBaseUrl="http://localhost:8000"
              onRefresh={sessionRefreshTrigger}
            />
          </div>
        </div>
      )}

      {/* 使用指南 */}
      <div className={styles.guideSection}>
        <div className={styles.guideContainer}>
          <Heading as="h2" className={styles.guideTitle}>
            {translate({id: 'agent.guideTitle', message: '使用指南'})}
          </Heading>
          
          <div className={styles.guideGrid}>
            <div className={styles.guideStep}>
              <div className={styles.stepNumber}>1</div>
              <h3>{translate({id: 'agent.step1Title', message: '提出问题'})}</h3>
              <p>{translate({id: 'agent.step1Desc', message: '输入您关于微波遥感的问题，或上传相关文档进行分析'})}</p>
            </div>
            
            <div className={styles.guideStep}>
              <div className={styles.stepNumber}>2</div>
              <h3>{translate({id: 'agent.step2Title', message: 'AI分析'})}</h3>
              <p>{translate({id: 'agent.step2Desc', message: 'AI助手分析您的需求，提供专业答案或自动构建计算模型'})}</p>
            </div>
            
            <div className={styles.guideStep}>
              <div className={styles.stepNumber}>3</div>
              <h3>{translate({id: 'agent.step3Title', message: '获取结果'})}</h3>
              <p>{translate({id: 'agent.step3Desc', message: '获得详细解答、建模结果图表，以及相关参考文献'})}</p>
            </div>
          </div>

          <div className={styles.tipsSection}>
            <h3>{translate({id: 'agent.tipsTitle', message: '使用技巧'})}</h3>
            <ul className={styles.tipsList}>
              <li>{translate({id: 'agent.tip1', message: '描述问题时尽量具体和详细，这样AI能提供更准确的答案'})}</li>
              <li>{translate({id: 'agent.tip2', message: '支持上传 .txt, .md, .docx, .csv, .xlsx 格式的文档进行分析'})}</li>
              <li>{translate({id: 'agent.tip3', message: '使用 Ctrl+Enter 快捷键可以快速发送消息'})}</li>
              <li>{translate({id: 'agent.tip4', message: 'AI可以自动识别建模需求并提交计算任务，请耐心等待结果'})}</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
}

// 错误边界组件
class AgentErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true };
  }

  componentDidCatch(error, errorInfo) {
    console.error('Agent Page Error:', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <Layout
          title={translate({id: 'agent.title', message: 'RS Agent - 智能助手'})}
          description={translate({id: 'agent.description', message: 'RSHub智能助手，为您提供专业的微波遥感分析和建模服务'})}
        >
          <div style={{ 
            display: 'flex', 
            flexDirection: 'column', 
            alignItems: 'center', 
            justifyContent: 'center', 
            padding: '4rem 2rem',
            textAlign: 'center',
            minHeight: '500px'
          }}>
            <h1 style={{ color: '#B08EAD', marginBottom: '1rem' }}>页面加载出错</h1>
            <p style={{ color: '#6c757d', marginBottom: '2rem' }}>
              很抱歉，Agent页面遇到了问题。请刷新页面重试。
            </p>
            <button 
              onClick={() => window.location.reload()} 
              style={{
                padding: '12px 24px',
                background: 'linear-gradient(135deg, #B08EAD 0%, #85A0BF 100%)',
                color: 'white',
                border: 'none',
                borderRadius: '20px',
                cursor: 'pointer',
                fontSize: '16px',
                fontWeight: '600'
              }}
            >
              刷新页面
            </button>
          </div>
        </Layout>
      );
    }

    return this.props.children;
  }
}

// 主要导出组件
export default function Agent() {
  const [isClient, setIsClient] = useState(false);
  
  useEffect(() => {
    setIsClient(true);
  }, []);

  // 服务器端渲染时显示加载状态
  if (!isClient) {
    return (
      <Layout
        title={translate({id: 'agent.title', message: 'RS Agent - 智能助手'})}
        description={translate({id: 'agent.description', message: 'RSHub智能助手，为您提供专业的微波遥感分析和建模服务'})}
      >
        <div style={{ 
          display: 'flex', 
          flexDirection: 'column', 
          alignItems: 'center', 
          justifyContent: 'center', 
          padding: '4rem 2rem',
          textAlign: 'center',
          minHeight: '500px'
        }}>
          <h1 style={{ color: '#B08EAD', marginBottom: '1rem' }}>正在加载智能助手...</h1>
        </div>
      </Layout>
    );
  }

  return (
    <Layout
      title={translate({id: 'agent.title', message: 'RS Agent - 智能助手'})}
      description={translate({id: 'agent.description', message: 'RSHub智能助手，为您提供专业的微波遥感分析和建模服务'})}
    >
      <AgentErrorBoundary>
        <AgentInner />
      </AgentErrorBoundary>
    </Layout>
  );
} 