import React from 'react';
import { UserAuthProvider } from '../components/UserAuthContext';

export default function Root({children}) {
  return (
    <UserAuthProvider>
      {children}
    </UserAuthProvider>
  );
} 