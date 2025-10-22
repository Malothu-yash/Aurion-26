// src/react-app/components/AuthModal.tsx
// Beautiful authentication modal with glassmorphism and smooth animations

import React, { useState, useEffect, useRef } from 'react';
import { X, Mail, Lock, User, Briefcase, Heart, CheckCircle, LogIn, UserPlus } from 'lucide-react';
import { useNavigate } from 'react-router';
import { useAuth } from '@/react-app/context/AuthContext';
import axios from 'axios';
import { ENV } from '@/config/env';

interface AuthModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess?: (user: any) => void;
}

type AuthView = 'login' | 'signup' | 'otp' | 'profile' | 'forgot' | 'reset';

const API_BASE = ENV.AUTH_BASE;

const AuthModal: React.FC<AuthModalProps> = ({ isOpen, onClose, onSuccess }) => {
  const navigate = useNavigate();
  const { login: authLogin } = useAuth();
  const [currentView, setCurrentView] = useState<AuthView>('login');
  const [isVisible, setIsVisible] = useState(false);
  const [rememberMe, setRememberMe] = useState(true);
  
  // Form states
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [otp, setOtp] = useState(['', '', '', '']);
  const [displayName, setDisplayName] = useState('');
  const [role, setRole] = useState('');
  const [hobbies, setHobbies] = useState<string[]>([]);
  
  // UI states
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [otpTimer, setOtpTimer] = useState(60);
  const [canResend, setCanResend] = useState(false);
  const [showSuccess, setShowSuccess] = useState(false);
  const [otpPurpose, setOtpPurpose] = useState<'signup' | 'forgot_password'>('signup');
  
  const otpInputsRef = useRef<(HTMLInputElement | null)[]>([]);
  const timerIntervalRef = useRef<NodeJS.Timeout | null>(null);

  // Animation on mount
  useEffect(() => {
    if (isOpen) {
      setIsVisible(true);
      document.body.style.overflow = 'hidden';
    } else {
      setIsVisible(false);
      document.body.style.overflow = 'unset';
    }
    
    return () => {
      document.body.style.overflow = 'unset';
    };
  }, [isOpen]);

  // OTP Timer
  useEffect(() => {
    if (currentView === 'otp' && otpTimer > 0) {
      timerIntervalRef.current = setInterval(() => {
        setOtpTimer((prev) => {
          if (prev <= 1) {
            setCanResend(true);
            if (timerIntervalRef.current) clearInterval(timerIntervalRef.current);
            return 0;
          }
          return prev - 1;
        });
      }, 1000);
    }
    
    return () => {
      if (timerIntervalRef.current) clearInterval(timerIntervalRef.current);
    };
  }, [currentView, otpTimer]);

  // Focus first OTP input
  useEffect(() => {
    if (currentView === 'otp' && otpInputsRef.current[0]) {
      otpInputsRef.current[0]?.focus();
    }
  }, [currentView]);

  // Reset form
  const resetForm = () => {
    setEmail('');
    setPassword('');
    setConfirmPassword('');
    setOtp(['', '', '', '']);
    setDisplayName('');
    setRole('');
    setHobbies([]);
    setError('');
    setLoading(false);
    setOtpTimer(60);
    setCanResend(false);
    setShowSuccess(false);
  };

  // Handle OTP input
  const handleOtpChange = (index: number, value: string) => {
    if (!/^\d*$/.test(value)) return;
    
    const newOtp = [...otp];
    newOtp[index] = value.slice(-1);
    setOtp(newOtp);
    
    // Auto-focus next input
    if (value && index < 3) {
      otpInputsRef.current[index + 1]?.focus();
    }
  };

  // Handle OTP paste
  const handleOtpPaste = (e: React.ClipboardEvent) => {
    e.preventDefault();
    const pastedData = e.clipboardData.getData('text').replace(/\D/g, '').slice(0, 4);
    const newOtp = pastedData.split('').concat(['', '', '', '']).slice(0, 4);
    setOtp(newOtp);
    
    if (pastedData.length === 4) {
      otpInputsRef.current[3]?.focus();
    }
  };

  // Handle OTP backspace
  const handleOtpKeyDown = (index: number, e: React.KeyboardEvent) => {
    if (e.key === 'Backspace' && !otp[index] && index > 0) {
      otpInputsRef.current[index - 1]?.focus();
    }
  };

  // API Calls
  const handleLogin = async () => {
    setError('');
    setLoading(true);
    
    try {
      // Check if this is admin login
      const isAdminEmail = email === 'rathodvamshi369@gmail.com';
      
      if (isAdminEmail) {
        // Try admin login endpoint
        try {
          console.log('🔐 Attempting admin login for:', email);
          const adminResponse = await axios.post(`${ENV.ADMIN_BASE}/login`, {
            email,
            password
          });
          
          console.log('✅ Admin login response:', adminResponse.data);
          
          if (adminResponse.data.success) {
            setShowSuccess(true);
            
            // Store admin token
            localStorage.setItem('admin_token', adminResponse.data.token);
            localStorage.setItem('admin_data', JSON.stringify({
              admin_id: adminResponse.data.admin_id,
              email: adminResponse.data.email,
              role: adminResponse.data.role
            }));
            
            setTimeout(() => {
              onClose();
              resetForm();
              
              // Redirect to admin dashboard
              navigate('/admin/dashboard');
            }, 1500);
            return;
          }
        } catch (adminErr: any) {
          // Admin login failed - show detailed error instead of falling back
          console.error('❌ Admin login error:', adminErr.response?.data || adminErr.message);
          
          // Don't fall through - show admin-specific error
          setError(
            adminErr.response?.data?.detail || 
            'Admin login failed. Please check your credentials or ensure the backend is running.'
          );
          setLoading(false);
          return; // Don't try regular login for admin email
        }
      }
      
      // Regular user login
      const response = await axios.post(`${API_BASE}/login`, {
        email,
        password
      });
      
      if (response.data.success) {
        setShowSuccess(true);
        
        // Store user in auth context with persistent storage
        authLogin(response.data.user, rememberMe);
        
        setTimeout(() => {
          onSuccess?.(response.data.user);
          onClose();
          resetForm();
          
          // Redirect to chat page
          navigate('/chat');
        }, 1500);
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Login failed');
    } finally {
      setLoading(false);
    }
  };

  const handleSignupStep1 = async () => {
    setError('');
    
    if (password !== confirmPassword) {
      setError('Passwords do not match');
      return;
    }
    
    if (password.length < 8) {
      setError('Password must be at least 8 characters');
      return;
    }
    
    setLoading(true);
    
    try {
      const response = await axios.post(`${API_BASE}/signup/step1`, {
        email,
        password,
        confirm_password: confirmPassword
      });
      
      if (response.data.success) {
        setOtpPurpose('signup');
        setCurrentView('otp');
        setOtpTimer(60);
        setCanResend(false);
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Signup failed');
    } finally {
      setLoading(false);
    }
  };

  const handleVerifyOtp = async () => {
    setError('');
    const otpCode = otp.join('');
    
    if (otpCode.length !== 4) {
      setError('Please enter the complete 4-digit OTP');
      return;
    }
    
    setLoading(true);
    
    try {
      const response = await axios.post(`${API_BASE}/verify-otp`, {
        email,
        otp: otpCode,
        purpose: otpPurpose
      });
      
      if (response.data.success) {
        if (otpPurpose === 'signup') {
          setCurrentView('profile');
        } else {
          setCurrentView('reset');
        }
        setOtp(['', '', '', '']);
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Invalid OTP');
    } finally {
      setLoading(false);
    }
  };

  const handleResendOtp = async () => {
    setError('');
    setLoading(true);
    
    try {
      await axios.post(`${API_BASE}/resend-otp`, {
        email,
        purpose: otpPurpose
      });
      
      setOtpTimer(60);
      setCanResend(false);
      setOtp(['', '', '', '']);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to resend OTP');
    } finally {
      setLoading(false);
    }
  };

  const handleCompleteSignup = async () => {
    setError('');
    
    if (!displayName || !role || hobbies.length === 0) {
      setError('Please complete all fields');
      return;
    }
    
    setLoading(true);
    
    try {
      const response = await axios.post(`${API_BASE}/signup/step2`, {
        email,
        password,
        display_name: displayName,
        role,
        hobbies
      });
      
      if (response.data.success) {
        setShowSuccess(true);
        setTimeout(() => {
          setCurrentView('login');
          resetForm();
        }, 2000);
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to complete signup');
    } finally {
      setLoading(false);
    }
  };

  const handleForgotPassword = async () => {
    setError('');
    
    if (!email) {
      setError('Please enter your email');
      return;
    }
    
    setLoading(true);
    
    try {
      await axios.post(`${API_BASE}/forgot-password`, { email });
      setOtpPurpose('forgot_password');
      setCurrentView('otp');
      setOtpTimer(60);
      setCanResend(false);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to send OTP');
    } finally {
      setLoading(false);
    }
  };

  const handleResetPassword = async () => {
    setError('');
    
    if (password !== confirmPassword) {
      setError('Passwords do not match');
      return;
    }
    
    if (password.length < 8) {
      setError('Password must be at least 8 characters');
      return;
    }
    
    setLoading(true);
    
    try {
      const response = await axios.post(`${API_BASE}/reset-password`, {
        email,
        new_password: password,
        confirm_password: confirmPassword
      });
      
      if (response.data.success) {
        setShowSuccess(true);
        setTimeout(() => {
          setCurrentView('login');
          resetForm();
        }, 2000);
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to reset password');
    } finally {
      setLoading(false);
    }
  };

  // Hobby options
  const hobbyOptions = [
    'Reading', 'Gaming', 'Coding', 'Music', 'Sports', 'Art',
    'Travel', 'Cooking', 'Photography', 'Fitness', 'Writing', 'Dancing'
  ];

  const toggleHobby = (hobby: string) => {
    setHobbies((prev) =>
      prev.includes(hobby) ? prev.filter((h) => h !== hobby) : [...prev, hobby]
    );
  };

  if (!isOpen) return null;

  return (
    <div
      className={`fixed inset-0 z-50 flex items-center justify-center transition-all duration-300 ${
        isVisible ? 'opacity-100' : 'opacity-0'
      }`}
    >
      {/* Backdrop */}
      <div
        className={`absolute inset-0 bg-black/60 backdrop-blur-md transition-all duration-300 ${
          isVisible ? 'backdrop-blur-md' : 'backdrop-blur-none'
        }`}
        onClick={onClose}
      />

      {/* Modal */}
      <div
        className={`relative bg-white/10 backdrop-blur-xl border border-white/20 rounded-2xl shadow-2xl w-full max-w-md mx-4 max-h-[90vh] overflow-y-auto transform transition-all duration-300 ${
          isVisible ? 'scale-100 opacity-100' : 'scale-95 opacity-0'
        }`}
        style={{ backdropFilter: 'blur(14px)' }}
      >
        {/* Close button */}
        <button
          onClick={onClose}
          className="absolute top-4 right-4 text-gray-300 hover:text-white transition-colors z-10"
        >
          <X className="w-6 h-6" />
        </button>

        {/* Success Animation */}
        {showSuccess && (
          <div className="absolute inset-0 flex items-center justify-center bg-black/80 backdrop-blur-xl rounded-2xl z-20">
            <div className="text-center">
              <CheckCircle className="w-20 h-20 text-green-400 mx-auto mb-4 animate-bounce" />
              <p className="text-2xl font-bold text-white">Success!</p>
            </div>
          </div>
        )}

        {/* Header Tabs */}
        {(currentView === 'login' || currentView === 'signup') && (
          <div className="flex border-b border-white/10">
            <button
              onClick={() => { setCurrentView('login'); setError(''); }}
              className={`flex-1 py-4 text-center font-semibold transition-all duration-300 ${
                currentView === 'login'
                  ? 'text-white border-b-2 border-blue-500 bg-white/5'
                  : 'text-gray-400 hover:text-white hover:bg-white/5'
              }`}
            >
              <LogIn className="w-5 h-5 inline mr-2" />
              Login
            </button>
            <button
              onClick={() => { setCurrentView('signup'); setError(''); }}
              className={`flex-1 py-4 text-center font-semibold transition-all duration-300 ${
                currentView === 'signup'
                  ? 'text-white border-b-2 border-purple-500 bg-white/5'
                  : 'text-gray-400 hover:text-white hover:bg-white/5'
              }`}
            >
              <UserPlus className="w-5 h-5 inline mr-2" />
              Sign up
            </button>
          </div>
        )}

        {/* Content */}
        <div className="p-8">
          {/* Login Form */}
          {currentView === 'login' && (
            <div className="space-y-6 animate-slideIn">
              <h2 className="text-3xl font-bold text-white text-center mb-8">
                Welcome Back
              </h2>

              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">
                    <Mail className="w-4 h-4 inline mr-2" />
                    Email
                  </label>
                  <input
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    className="w-full px-4 py-3 bg-white/10 border border-white/20 rounded-xl text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 transition-all"
                    placeholder="your@email.com"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">
                    <Lock className="w-4 h-4 inline mr-2" />
                    Password
                  </label>
                  <input
                    type="password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    onKeyPress={(e) => e.key === 'Enter' && handleLogin()}
                    className="w-full px-4 py-3 bg-white/10 border border-white/20 rounded-xl text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 transition-all"
                    placeholder="••••••••"
                  />
                </div>

                <div className="flex items-center justify-between">
                  <label className="flex items-center space-x-2 cursor-pointer">
                    <input
                      type="checkbox"
                      checked={rememberMe}
                      onChange={(e) => setRememberMe(e.target.checked)}
                      className="w-4 h-4 rounded border-white/20 bg-white/10 text-blue-600 focus:ring-2 focus:ring-blue-500"
                    />
                    <span className="text-sm text-gray-300">Remember me</span>
                  </label>
                  
                  <button
                    onClick={() => setCurrentView('forgot')}
                    className="text-sm text-blue-400 hover:text-blue-300 transition-colors"
                  >
                    Forgot password?
                  </button>
                </div>
              </div>

              {error && (
                <div className="p-3 bg-red-500/20 border border-red-500/50 rounded-lg text-red-300 text-sm">
                  {error}
                </div>
              )}

              <button
                onClick={handleLogin}
                disabled={loading}
                className="w-full py-3 bg-gradient-to-r from-blue-600 via-purple-600 to-pink-600 hover:from-blue-500 hover:via-purple-500 hover:to-pink-500 text-white font-semibold rounded-xl shadow-lg hover:shadow-2xl hover:shadow-purple-500/50 transition-all duration-300 hover:scale-105 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {loading ? 'Logging in...' : 'Login'}
              </button>

              <div className="relative my-6">
                <div className="absolute inset-0 flex items-center">
                  <div className="w-full border-t border-white/20" />
                </div>
                <div className="relative flex justify-center text-sm">
                  <span className="px-4 bg-transparent text-gray-400">Or sign in with</span>
                </div>
              </div>

              <button
                className="w-full py-3 bg-white/10 hover:bg-white/20 text-white font-medium rounded-xl border border-white/20 transition-all duration-300 hover:scale-105 flex items-center justify-center space-x-2"
              >
                <svg className="w-5 h-5" viewBox="0 0 24 24">
                  <path fill="currentColor" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
                  <path fill="currentColor" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
                  <path fill="currentColor" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
                  <path fill="currentColor" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
                </svg>
                <span>Sign in with Google</span>
              </button>
            </div>
          )}

          {/* Signup Form */}
          {currentView === 'signup' && (
            <div className="space-y-6 animate-slideIn">
              <h2 className="text-3xl font-bold text-white text-center mb-8">
                Create Account
              </h2>

              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">
                    <Mail className="w-4 h-4 inline mr-2" />
                    Email
                  </label>
                  <input
                    type="email"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    className="w-full px-4 py-3 bg-white/10 border border-white/20 rounded-xl text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-purple-500 transition-all"
                    placeholder="your@email.com"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">
                    <Lock className="w-4 h-4 inline mr-2" />
                    Password
                  </label>
                  <input
                    type="password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    className="w-full px-4 py-3 bg-white/10 border border-white/20 rounded-xl text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-purple-500 transition-all"
                    placeholder="••••••••"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">
                    <Lock className="w-4 h-4 inline mr-2" />
                    Confirm Password
                  </label>
                  <input
                    type="password"
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    onKeyPress={(e) => e.key === 'Enter' && handleSignupStep1()}
                    className="w-full px-4 py-3 bg-white/10 border border-white/20 rounded-xl text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-purple-500 transition-all"
                    placeholder="••••••••"
                  />
                </div>
              </div>

              {error && (
                <div className="p-3 bg-red-500/20 border border-red-500/50 rounded-lg text-red-300 text-sm">
                  {error}
                </div>
              )}

              <button
                onClick={handleSignupStep1}
                disabled={loading}
                className="w-full py-3 bg-gradient-to-r from-blue-600 via-purple-600 to-pink-600 hover:from-blue-500 hover:via-purple-500 hover:to-pink-500 text-white font-semibold rounded-xl shadow-lg hover:shadow-2xl hover:shadow-purple-500/50 transition-all duration-300 hover:scale-105 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {loading ? 'Sending OTP...' : 'Sign Up'}
              </button>

              <div className="relative my-6">
                <div className="absolute inset-0 flex items-center">
                  <div className="w-full border-t border-white/20" />
                </div>
                <div className="relative flex justify-center text-sm">
                  <span className="px-4 bg-transparent text-gray-400">Or sign up with</span>
                </div>
              </div>

              <button
                className="w-full py-3 bg-white/10 hover:bg-white/20 text-white font-medium rounded-xl border border-white/20 transition-all duration-300 hover:scale-105 flex items-center justify-center space-x-2"
              >
                <svg className="w-5 h-5" viewBox="0 0 24 24">
                  <path fill="currentColor" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
                  <path fill="currentColor" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
                  <path fill="currentColor" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
                  <path fill="currentColor" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
                </svg>
                <span>Sign up with Google</span>
              </button>
            </div>
          )}

          {/* OTP Verification */}
          {currentView === 'otp' && (
            <div className="space-y-6 animate-slideIn text-center">
              <h2 className="text-3xl font-bold text-white mb-2">
                Verify OTP
              </h2>
              <p className="text-gray-300 mb-8">
                Enter the 4-digit code sent to <br />
                <span className="font-semibold text-white">{email}</span>
              </p>

              <div className="flex justify-center space-x-3 mb-6">
                {otp.map((digit, index) => (
                  <input
                    key={index}
                    ref={(el) => { otpInputsRef.current[index] = el; }}
                    type="text"
                    inputMode="numeric"
                    maxLength={1}
                    value={digit}
                    onChange={(e) => handleOtpChange(index, e.target.value)}
                    onKeyDown={(e) => handleOtpKeyDown(index, e)}
                    onPaste={index === 0 ? handleOtpPaste : undefined}
                    className="w-14 h-14 text-center text-2xl font-bold bg-white/10 border-2 border-white/20 rounded-xl text-white focus:outline-none focus:ring-2 focus:ring-purple-500 focus:border-purple-500 transition-all"
                  />
                ))}
              </div>

              <div className="text-lg font-mono text-gray-300">
                {Math.floor(otpTimer / 60)}:{String(otpTimer % 60).padStart(2, '0')}
              </div>

              {error && (
                <div className="p-3 bg-red-500/20 border border-red-500/50 rounded-lg text-red-300 text-sm">
                  {error}
                </div>
              )}

              <div className="flex space-x-3">
                <button
                  onClick={() => {
                    setCurrentView(otpPurpose === 'signup' ? 'signup' : 'forgot');
                    setOtp(['', '', '', '']);
                    setError('');
                  }}
                  className="flex-1 py-3 bg-white/10 hover:bg-white/20 text-white font-medium rounded-xl border border-white/20 transition-all duration-300 hover:scale-105"
                >
                  Back
                </button>
                <button
                  onClick={handleVerifyOtp}
                  disabled={loading}
                  className="flex-1 py-3 bg-gradient-to-r from-blue-600 via-purple-600 to-pink-600 hover:from-blue-500 hover:via-purple-500 hover:to-pink-500 text-white font-semibold rounded-xl shadow-lg hover:shadow-2xl hover:shadow-purple-500/50 transition-all duration-300 hover:scale-105 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {loading ? 'Verifying...' : 'Verify'}
                </button>
              </div>

              <button
                onClick={handleResendOtp}
                disabled={!canResend || loading}
                className="text-sm text-blue-400 hover:text-blue-300 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {canResend ? 'Resend OTP' : 'Resend OTP (wait)'}
              </button>
            </div>
          )}

          {/* Profile Setup */}
          {currentView === 'profile' && (
            <div className="space-y-6 animate-slideIn">
              <h2 className="text-3xl font-bold text-white text-center mb-8">
                Complete Profile
              </h2>

              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">
                    <User className="w-4 h-4 inline mr-2" />
                    Display Name
                  </label>
                  <input
                    type="text"
                    value={displayName}
                    onChange={(e) => setDisplayName(e.target.value)}
                    className="w-full px-4 py-3 bg-white/10 border border-white/20 rounded-xl text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-purple-500 transition-all"
                    placeholder="Your Name"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">
                    <Briefcase className="w-4 h-4 inline mr-2" />
                    Role
                  </label>
                  <select
                    value={role}
                    onChange={(e) => setRole(e.target.value)}
                    className="w-full px-4 py-3 bg-white/10 border border-white/20 rounded-xl text-white focus:outline-none focus:ring-2 focus:ring-purple-500 transition-all"
                  >
                    <option value="" className="bg-gray-800">Select your role</option>
                    <option value="Student" className="bg-gray-800">Student</option>
                    <option value="Professional" className="bg-gray-800">Professional</option>
                    <option value="Developer" className="bg-gray-800">Developer</option>
                    <option value="Designer" className="bg-gray-800">Designer</option>
                    <option value="Other" className="bg-gray-800">Other</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">
                    <Heart className="w-4 h-4 inline mr-2" />
                    Hobbies
                  </label>
                  <ul className="grid grid-cols-2 gap-2">
                    {hobbyOptions.map((hobby) => (
                      <li key={hobby}>
                        <button
                          type="button"
                          onClick={() => toggleHobby(hobby)}
                          className={`w-full px-3 py-2 rounded-lg text-sm font-medium transition-all duration-200 ${
                            hobbies.includes(hobby)
                              ? 'bg-gradient-to-r from-blue-600 to-purple-600 text-white shadow-lg'
                              : 'bg-white/10 text-gray-300 hover:bg-white/20'
                          }`}
                        >
                          {hobby}
                        </button>
                      </li>
                    ))}
                  </ul>
                </div>
              </div>

              {error && (
                <div className="p-3 bg-red-500/20 border border-red-500/50 rounded-lg text-red-300 text-sm">
                  {error}
                </div>
              )}

              <button
                onClick={handleCompleteSignup}
                disabled={loading}
                className="w-full py-3 bg-gradient-to-r from-blue-600 via-purple-600 to-pink-600 hover:from-blue-500 hover:via-purple-500 hover:to-pink-500 text-white font-semibold rounded-xl shadow-lg hover:shadow-2xl hover:shadow-purple-500/50 transition-all duration-300 hover:scale-105 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {loading ? 'Creating Account...' : 'Complete'}
              </button>
            </div>
          )}

          {/* Forgot Password */}
          {currentView === 'forgot' && (
            <div className="space-y-6 animate-slideIn">
              <h2 className="text-3xl font-bold text-white text-center mb-8">
                Forgot Password
              </h2>

              <div>
                <label className="block text-sm font-medium text-gray-300 mb-2">
                  <Mail className="w-4 h-4 inline mr-2" />
                  Email
                </label>
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && handleForgotPassword()}
                  className="w-full px-4 py-3 bg-white/10 border border-white/20 rounded-xl text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 transition-all"
                  placeholder="your@email.com"
                />
              </div>

              {error && (
                <div className="p-3 bg-red-500/20 border border-red-500/50 rounded-lg text-red-300 text-sm">
                  {error}
                </div>
              )}

              <div className="flex space-x-3">
                <button
                  onClick={() => {
                    setCurrentView('login');
                    setError('');
                  }}
                  className="flex-1 py-3 bg-white/10 hover:bg-white/20 text-white font-medium rounded-xl border border-white/20 transition-all duration-300 hover:scale-105"
                >
                  Back
                </button>
                <button
                  onClick={handleForgotPassword}
                  disabled={loading}
                  className="flex-1 py-3 bg-gradient-to-r from-blue-600 via-purple-600 to-pink-600 hover:from-blue-500 hover:via-purple-500 hover:to-pink-500 text-white font-semibold rounded-xl shadow-lg hover:shadow-2xl hover:shadow-purple-500/50 transition-all duration-300 hover:scale-105 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {loading ? 'Sending...' : 'Send OTP'}
                </button>
              </div>
            </div>
          )}

          {/* Reset Password */}
          {currentView === 'reset' && (
            <div className="space-y-6 animate-slideIn">
              <h2 className="text-3xl font-bold text-white text-center mb-8">
                Reset Password
              </h2>

              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">
                    <Lock className="w-4 h-4 inline mr-2" />
                    New Password
                  </label>
                  <input
                    type="password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    className="w-full px-4 py-3 bg-white/10 border border-white/20 rounded-xl text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-purple-500 transition-all"
                    placeholder="••••••••"
                  />
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-300 mb-2">
                    <Lock className="w-4 h-4 inline mr-2" />
                    Confirm Password
                  </label>
                  <input
                    type="password"
                    value={confirmPassword}
                    onChange={(e) => setConfirmPassword(e.target.value)}
                    onKeyPress={(e) => e.key === 'Enter' && handleResetPassword()}
                    className="w-full px-4 py-3 bg-white/10 border border-white/20 rounded-xl text-white placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-purple-500 transition-all"
                    placeholder="••••••••"
                  />
                </div>
              </div>

              {error && (
                <div className="p-3 bg-red-500/20 border border-red-500/50 rounded-lg text-red-300 text-sm">
                  {error}
                </div>
              )}

              <button
                onClick={handleResetPassword}
                disabled={loading}
                className="w-full py-3 bg-gradient-to-r from-blue-600 via-purple-600 to-pink-600 hover:from-blue-500 hover:via-purple-500 hover:to-pink-500 text-white font-semibold rounded-xl shadow-lg hover:shadow-2xl hover:shadow-purple-500/50 transition-all duration-300 hover:scale-105 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {loading ? 'Resetting...' : 'Reset Password'}
              </button>
            </div>
          )}
        </div>
      </div>

      <style>{`
        @keyframes slideIn {
          from {
            opacity: 0;
            transform: translateY(-10px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }
        
        .animate-slideIn {
          animation: slideIn 0.3s ease-out;
        }
        
        /* Custom scrollbar */
        .overflow-y-auto::-webkit-scrollbar {
          width: 6px;
        }
        
        .overflow-y-auto::-webkit-scrollbar-track {
          background: rgba(255, 255, 255, 0.1);
          border-radius: 10px;
        }
        
        .overflow-y-auto::-webkit-scrollbar-thumb {
          background: rgba(255, 255, 255, 0.3);
          border-radius: 10px;
        }
        
        .overflow-y-auto::-webkit-scrollbar-thumb:hover {
          background: rgba(255, 255, 255, 0.5);
        }
      `}</style>
    </div>
  );
};

export default AuthModal;
