import React, { createContext, useContext, useState, useEffect } from 'react';

const UserAuthContext = createContext();

export const useUserAuth = () => {
  const context = useContext(UserAuthContext);
  if (!context) {
    throw new Error('useUserAuth must be used within a UserAuthProvider');
  }
  return context;
};

export const UserAuthProvider = ({ children }) => {
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [username, setUsername] = useState('');
  const [token, setToken] = useState('');

  useEffect(() => {
    // 检查本地存储中的登录状态
    if (typeof window === 'undefined') return; // 防止SSR错误
    
    const storedToken = localStorage.getItem('tokenTmp');
    const storedLoginStatus = localStorage.getItem('LoggedIn');
    
    if (storedToken && storedLoginStatus === 'True') {
      setToken(storedToken);
      setIsLoggedIn(true);
      
      // 获取用户信息
      fetch('https://rshub.zju.edu.cn/profile', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          tokenTmp: storedToken
        }),
      })
      .then(response => response.json())
      .then(data => {
        if (data.result) {
          setUsername(data.username);
        } else {
          // 如果token无效，清除登录状态
          logout();
        }
      })
      .catch(error => {
        console.error('Error fetching user profile:', error);
        logout();
      });
    }
  }, []);

  const login = (userToken, userData) => {
    setToken(userToken);
    setIsLoggedIn(true);
    setUsername(userData.username);
    
    // 确保在客户端环境下操作localStorage
    if (typeof window !== 'undefined' && localStorage) {
      localStorage.setItem('tokenTmp', userToken);
      localStorage.setItem('LoggedIn', 'True');
    }
  };

  const logout = () => {
    setToken('');
    setIsLoggedIn(false);
    setUsername('');
    
    // 确保在客户端环境下操作localStorage
    if (typeof window !== 'undefined' && localStorage) {
      localStorage.removeItem('tokenTmp');
      localStorage.removeItem('LoggedIn');
      localStorage.removeItem('realToken'); // 清除真正的token
    }
  };

  const value = {
    isLoggedIn,
    username,
    token,
    login,
    logout
  };

  return (
    <UserAuthContext.Provider value={value}>
      {children}
    </UserAuthContext.Provider>
  );
}; 