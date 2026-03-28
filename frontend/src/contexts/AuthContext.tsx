'use client';

import React, { createContext, useContext, useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { authAPI } from '@/lib/api';

interface User {
  _id: string;
  name: string;
  email: string;
  interests: string[];
  profile_photo?: string;
  streak_days: number;
  join_date: string;
  active_time?: number;
  last_session_time?: number;
  last_session_update?: string;
}

interface AuthContextType {
  user: User | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (data: {
    name: string;
    email: string;
    password: string;
    confirm_password: string;
    interests?: string[];
  }) => Promise<void>;
  logout: () => void;
  updateUser: (data: Partial<User>) => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

// Helper function to normalize user data
const normalizeUser = (userData: any): User => {
  // Ensure interests is always an array
  let interests = userData.interests || [];
  
  // If interests is a string, try to parse it
  if (typeof interests === 'string') {
    try {
      interests = JSON.parse(interests);
    } catch {
      // If parsing fails, split by comma
      interests = interests.split(',').map((s: string) => s.trim()).filter(Boolean);
    }
  }
  
  // Ensure it's an array
  if (!Array.isArray(interests)) {
    interests = [];
  }
  
  return {
    ...userData,
    interests
  };
};

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);
  const [sessionStartTime, setSessionStartTime] = useState<number | null>(null);
  const router = useRouter();

  // Track user active time
  useEffect(() => {
    if (!user) return;

    let activeTime = 0;
    let isActive = true;
    let lastActivityTime = Date.now();

    // Track activity - send update every 60 seconds
    const activityInterval = setInterval(() => {
      if (isActive) {
        activeTime += 60; // 60 seconds
        
        // Send update to backend (not a session end)
        authAPI.updateActiveTime(60, false).catch(err => {
          console.error('Failed to update active time:', err);
        });
      }
    }, 60000); // Every 60 seconds

    // Detect user activity
    const handleActivity = () => {
      isActive = true;
      lastActivityTime = Date.now();
    };

    // Check for inactivity (no activity for 5 minutes)
    const inactivityCheck = setInterval(() => {
      if (Date.now() - lastActivityTime > 300000) { // 5 minutes
        isActive = false;
      }
    }, 10000); // Check every 10 seconds

    // Add event listeners for user activity
    window.addEventListener('mousemove', handleActivity);
    window.addEventListener('keydown', handleActivity);
    window.addEventListener('click', handleActivity);
    window.addEventListener('scroll', handleActivity);

    return () => {
      clearInterval(activityInterval);
      clearInterval(inactivityCheck);
      window.removeEventListener('mousemove', handleActivity);
      window.removeEventListener('keydown', handleActivity);
      window.removeEventListener('click', handleActivity);
      window.removeEventListener('scroll', handleActivity);
      
      // Send final update when component unmounts
      if (activeTime > 0) {
        authAPI.updateActiveTime(activeTime, false).catch(() => {});
      }
    };
  }, [user]);

  useEffect(() => {
    // Check if user is logged in
    const checkAuth = async () => {
      const token = localStorage.getItem('access_token');
      
      if (token) {
        try {
          console.log('🔍 Checking authentication with token...');
          const response = await authAPI.getProfile();
          console.log('✅ Auth check successful:', response.data);
          setUser(normalizeUser(response.data));
          
          // Initialize session start time
          const now = Date.now();
          localStorage.setItem('session_start_time', now.toString());
          setSessionStartTime(now);
          console.log('⏱️ Session started at:', new Date(now).toLocaleString());
        } catch (error: any) {
          console.error('❌ Auth check failed:', error);
          console.error('❌ Error details:', error.response?.data);
          
          // Clear invalid tokens
          localStorage.removeItem('access_token');
          localStorage.removeItem('refresh_token');
          setUser(null);
          
          // Show alert to user
          if (typeof window !== 'undefined') {
            alert('Your session has expired. Please log in again.');
          }
        }
      }
      
      setLoading(false);
    };

    checkAuth();
  }, []);

  const login = async (email: string, password: string) => {
    try {
      console.log('🔐 Attempting login for:', email);
      const response = await authAPI.login(email, password);
      console.log('✅ Login response:', response.data);
      
      const { user, tokens } = response.data;
      
      localStorage.setItem('access_token', tokens.access);
      localStorage.setItem('refresh_token', tokens.refresh);
      
      // Track session start time
      const loginTime = Date.now();
      setSessionStartTime(loginTime);
      localStorage.setItem('session_start_time', loginTime.toString());
      console.log('⏱️ Session started at:', new Date(loginTime).toLocaleString());
      
      setUser(normalizeUser(user));
      console.log('✅ User logged in successfully');
    } catch (error: any) {
      console.error('❌ Login error:', error);
      console.error('❌ Error response:', error.response?.data);
      
      const errorMessage = error.response?.data?.error || 
                           error.response?.data?.message ||
                           error.message || 
                           'Login failed. Please check your credentials.';
      throw new Error(errorMessage);
    }
  };

  const register = async (data: {
    name: string;
    email: string;
    password: string;
    confirm_password: string;
    interests?: string[];
  }) => {
    try {
      console.log('📝 Attempting registration for:', data.email);
      const response = await authAPI.register(data);
      console.log('✅ Registration response:', response.data);
      
      const { user, tokens } = response.data;
      
      localStorage.setItem('access_token', tokens.access);
      localStorage.setItem('refresh_token', tokens.refresh);
      
      // Track session start time
      const loginTime = Date.now();
      setSessionStartTime(loginTime);
      localStorage.setItem('session_start_time', loginTime.toString());
      console.log('⏱️ Session started at:', new Date(loginTime).toLocaleString());
      
      setUser(normalizeUser(user));
      console.log('✅ User registered successfully');
    } catch (error: any) {
      console.error('❌ Registration error:', error);
      console.error('❌ Error response:', error.response?.data);
      
      const errorMessage = error.response?.data?.error || 
                           error.response?.data?.message ||
                           error.message || 
                           'Registration failed. Please try again.';
      throw new Error(errorMessage);
    }
  };

  const logout = async () => {
    // Calculate total session duration from login to logout
    const startTime = sessionStartTime || parseInt(localStorage.getItem('session_start_time') || '0');
    if (startTime > 0) {
      const sessionDuration = Math.floor((Date.now() - startTime) / 1000); // in seconds
      console.log('⏱️ Total session duration:', sessionDuration, 'seconds (', Math.floor(sessionDuration / 60), 'minutes)');
      
      // Send entire session time to backend and mark as session end
      try {
        await authAPI.updateActiveTime(sessionDuration, true);
        console.log('✅ Session time saved and session ended successfully');
      } catch (error) {
        console.error('❌ Failed to save session time:', error);
      }
    }
    
    // Clear session data
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('session_start_time');
    setUser(null);
    setSessionStartTime(null);
    router.push('/');
  };

  const updateUser = (data: Partial<User>) => {
    setUser((prev) => (prev ? { ...prev, ...data } : null));
  };

  return (
    <AuthContext.Provider value={{ user, loading, login, register, logout, updateUser }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
