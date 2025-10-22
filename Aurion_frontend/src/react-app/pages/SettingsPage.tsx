import { useState, useEffect } from 'react';
import { useAuth } from '@/react-app/context/AuthContext';
import { useNavigate } from 'react-router';
import Sidebar from '@/react-app/components/Sidebar';
import { 
  Settings, 
  Moon, 
  Sun, 
  Volume2, 
  VolumeX, 
  Bell, 
  BellOff, 
  Eye, 
  EyeOff,
  Sparkles,
  Palette,
  Languages,
  Shield,
  Save,
  RefreshCw
} from 'lucide-react';

export default function SettingsPage() {
  const { user } = useAuth();
  const navigate = useNavigate();
  
  // Settings state
  const [isDarkMode, setIsDarkMode] = useState(true);
  const [soundEnabled, setSoundEnabled] = useState(true);
  const [notificationsEnabled, setNotificationsEnabled] = useState(true);
  const [showTypingIndicator, setShowTypingIndicator] = useState(true);
  const [language, setLanguage] = useState('en');
  const [colorTheme, setColorTheme] = useState('aurora');
  const [fontSize, setFontSize] = useState('medium');
  const [autoSave, setAutoSave] = useState(true);
  const [dataRetention, setDataRetention] = useState('1year');

  useEffect(() => {
    if (!user) {
      navigate('/');
      return;
    }
    
    // Load settings from localStorage or API
    loadSettings();
  }, [user, navigate]);

  const loadSettings = () => {
    // Load settings from localStorage
    const savedSettings = localStorage.getItem('aurion-settings');
    if (savedSettings) {
      const settings = JSON.parse(savedSettings);
      setIsDarkMode(settings.isDarkMode ?? true);
      setSoundEnabled(settings.soundEnabled ?? true);
      setNotificationsEnabled(settings.notificationsEnabled ?? true);
      setShowTypingIndicator(settings.showTypingIndicator ?? true);
      setLanguage(settings.language ?? 'en');
      setColorTheme(settings.colorTheme ?? 'aurora');
      setFontSize(settings.fontSize ?? 'medium');
      setAutoSave(settings.autoSave ?? true);
      setDataRetention(settings.dataRetention ?? '1year');
    }
  };

  const saveSettings = async () => {
    const settings = {
      isDarkMode,
      soundEnabled,
      notificationsEnabled,
      showTypingIndicator,
      language,
      colorTheme,
      fontSize,
      autoSave,
      dataRetention
    };

    // Save to localStorage
    localStorage.setItem('aurion-settings', JSON.stringify(settings));
    
    // In production, also save to backend
    try {
      // API call to save settings would go here
      console.log('Settings saved:', settings);
    } catch (error) {
      console.error('Failed to save settings:', error);
    }
  };

  const resetSettings = () => {
    if (window.confirm('Are you sure you want to reset all settings to default?')) {
      setIsDarkMode(true);
      setSoundEnabled(true);
      setNotificationsEnabled(true);
      setShowTypingIndicator(true);
      setLanguage('en');
      setColorTheme('aurora');
      setFontSize('medium');
      setAutoSave(true);
      setDataRetention('1year');
      
      localStorage.removeItem('aurion-settings');
    }
  };

  if (!user) {
    return (
      <div className="h-screen flex items-center justify-center bg-gradient-to-br from-violet-900 via-purple-900/10 to-black">
        <div className="text-center">
          <Sparkles className="w-16 h-16 gradient-text-aurora animate-spin mx-auto mb-4" />
          <p className="text-gray-300">Please sign in to continue</p>
        </div>
      </div>
    );
  }

  return (
    <div className="h-screen bg-gradient-to-br from-violet-950/20 via-purple-950/10 to-black flex">
      <Sidebar />
      
      <div className="flex-1 overflow-y-auto">
        {/* Header */}
        <div className="h-16 border-b border-orange-500/20 flex items-center justify-between px-6">
          <div className="flex items-center space-x-3">
            <Settings className="w-6 h-6 gradient-text-aurora" />
            <h1 className="text-xl font-semibold text-white">Settings</h1>
          </div>
          
          <div className="flex space-x-3">
            <button
              onClick={resetSettings}
              className="flex items-center space-x-2 px-4 py-2 bg-gray-700 text-gray-300 rounded-xl hover:bg-gray-600 transition-colors duration-200"
            >
              <RefreshCw className="w-4 h-4" />
              <span>Reset</span>
            </button>
            <button
              onClick={saveSettings}
              className="flex items-center space-x-2 btn-gradient-aurora"
            >
              <Save className="w-4 h-4" />
              <span>Save Settings</span>
            </button>
          </div>
        </div>

        <div className="max-w-4xl mx-auto p-6 space-y-8">
          {/* Appearance Settings */}
          <div className="glass-aurora rounded-2xl p-8">
            <div className="flex items-center space-x-3 mb-6">
              <Palette className="w-6 h-6 text-purple-400" />
              <h2 className="text-2xl font-bold text-white">Appearance</h2>
            </div>

            <div className="space-y-6">
              {/* Theme Toggle */}
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="font-semibold text-white mb-1">Dark Mode</h3>
                  <p className="text-gray-400 text-sm">Choose between light and dark theme</p>
                </div>
                <button
                  onClick={() => setIsDarkMode(!isDarkMode)}
                  className={`relative w-14 h-8 rounded-full transition-colors duration-200 ${
                    isDarkMode ? 'bg-purple-600' : 'bg-gray-600'
                  }`}
                >
                  <div className={`absolute top-1 left-1 w-6 h-6 rounded-full bg-white transition-transform duration-200 flex items-center justify-center ${
                    isDarkMode ? 'translate-x-6' : 'translate-x-0'
                  }`}>
                    {isDarkMode ? <Moon className="w-3 h-3 text-purple-600" /> : <Sun className="w-3 h-3 text-orange-500" />}
                  </div>
                </button>
              </div>

              {/* Color Theme */}
              <div>
                <h3 className="font-semibold text-white mb-3">Color Theme</h3>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                  {[
                    { id: 'aurora', name: 'Aurora', colors: ['from-orange-400', 'to-purple-600'] },
                    { id: 'ocean', name: 'Ocean', colors: ['from-blue-400', 'to-cyan-600'] },
                    { id: 'forest', name: 'Forest', colors: ['from-green-400', 'to-emerald-600'] },
                    { id: 'sunset', name: 'Sunset', colors: ['from-pink-400', 'to-orange-600'] }
                  ].map((theme) => (
                    <button
                      key={theme.id}
                      onClick={() => setColorTheme(theme.id)}
                      className={`p-3 rounded-xl transition-all duration-200 ${
                        colorTheme === theme.id
                          ? 'bg-purple-900/60 border-2 border-orange-400'
                          : 'bg-purple-900/20 border-2 border-transparent hover:bg-purple-900/40'
                      }`}
                    >
                      <div className={`w-full h-8 rounded-lg bg-gradient-to-r ${theme.colors[0]} ${theme.colors[1]} mb-2`}></div>
                      <span className="text-white text-sm font-medium">{theme.name}</span>
                    </button>
                  ))}
                </div>
              </div>

              {/* Font Size */}
              <div>
                <h3 className="font-semibold text-white mb-3">Font Size</h3>
                <select
                  value={fontSize}
                  onChange={(e) => setFontSize(e.target.value)}
                  className="w-full px-4 py-3 bg-purple-900/40 border border-orange-500/20 rounded-xl text-white focus:outline-none focus:border-orange-400/40"
                >
                  <option value="small">Small</option>
                  <option value="medium">Medium</option>
                  <option value="large">Large</option>
                  <option value="xlarge">Extra Large</option>
                </select>
              </div>
            </div>
          </div>

          {/* Audio & Notifications */}
          <div className="glass-aurora rounded-2xl p-8">
            <div className="flex items-center space-x-3 mb-6">
              <Bell className="w-6 h-6 text-blue-400" />
              <h2 className="text-2xl font-bold text-white">Audio & Notifications</h2>
            </div>

            <div className="space-y-6">
              {/* Sound Effects */}
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="font-semibold text-white mb-1">Sound Effects</h3>
                  <p className="text-gray-400 text-sm">Play sounds for message notifications</p>
                </div>
                <button
                  onClick={() => setSoundEnabled(!soundEnabled)}
                  className={`relative w-14 h-8 rounded-full transition-colors duration-200 ${
                    soundEnabled ? 'bg-green-600' : 'bg-gray-600'
                  }`}
                >
                  <div className={`absolute top-1 left-1 w-6 h-6 rounded-full bg-white transition-transform duration-200 flex items-center justify-center ${
                    soundEnabled ? 'translate-x-6' : 'translate-x-0'
                  }`}>
                    {soundEnabled ? <Volume2 className="w-3 h-3 text-green-600" /> : <VolumeX className="w-3 h-3 text-gray-600" />}
                  </div>
                </button>
              </div>

              {/* Push Notifications */}
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="font-semibold text-white mb-1">Push Notifications</h3>
                  <p className="text-gray-400 text-sm">Receive notifications for important updates</p>
                </div>
                <button
                  onClick={() => setNotificationsEnabled(!notificationsEnabled)}
                  className={`relative w-14 h-8 rounded-full transition-colors duration-200 ${
                    notificationsEnabled ? 'bg-blue-600' : 'bg-gray-600'
                  }`}
                >
                  <div className={`absolute top-1 left-1 w-6 h-6 rounded-full bg-white transition-transform duration-200 flex items-center justify-center ${
                    notificationsEnabled ? 'translate-x-6' : 'translate-x-0'
                  }`}>
                    {notificationsEnabled ? <Bell className="w-3 h-3 text-blue-600" /> : <BellOff className="w-3 h-3 text-gray-600" />}
                  </div>
                </button>
              </div>

              {/* Typing Indicator */}
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="font-semibold text-white mb-1">Typing Indicator</h3>
                  <p className="text-gray-400 text-sm">Show when Aurion is thinking</p>
                </div>
                <button
                  onClick={() => setShowTypingIndicator(!showTypingIndicator)}
                  className={`relative w-14 h-8 rounded-full transition-colors duration-200 ${
                    showTypingIndicator ? 'bg-purple-600' : 'bg-gray-600'
                  }`}
                >
                  <div className={`absolute top-1 left-1 w-6 h-6 rounded-full bg-white transition-transform duration-200 flex items-center justify-center ${
                    showTypingIndicator ? 'translate-x-6' : 'translate-x-0'
                  }`}>
                    {showTypingIndicator ? <Eye className="w-3 h-3 text-purple-600" /> : <EyeOff className="w-3 h-3 text-gray-600" />}
                  </div>
                </button>
              </div>
            </div>
          </div>

          {/* Language & Region */}
          <div className="glass-aurora rounded-2xl p-8">
            <div className="flex items-center space-x-3 mb-6">
              <Languages className="w-6 h-6 text-green-400" />
              <h2 className="text-2xl font-bold text-white">Language & Region</h2>
            </div>

            <div>
              <h3 className="font-semibold text-white mb-3">Interface Language</h3>
              <select
                value={language}
                onChange={(e) => setLanguage(e.target.value)}
                className="w-full px-4 py-3 bg-purple-900/40 border border-orange-500/20 rounded-xl text-white focus:outline-none focus:border-orange-400/40"
              >
                <option value="en">English</option>
                <option value="es">Español</option>
                <option value="fr">Français</option>
                <option value="de">Deutsch</option>
                <option value="ja">日本語</option>
                <option value="zh">中文</option>
              </select>
            </div>
          </div>

          {/* Privacy & Data */}
          <div className="glass-aurora rounded-2xl p-8">
            <div className="flex items-center space-x-3 mb-6">
              <Shield className="w-6 h-6 text-red-400" />
              <h2 className="text-2xl font-bold text-white">Privacy & Data</h2>
            </div>

            <div className="space-y-6">
              {/* Auto Save */}
              <div className="flex items-center justify-between">
                <div>
                  <h3 className="font-semibold text-white mb-1">Auto Save Conversations</h3>
                  <p className="text-gray-400 text-sm">Automatically save chat history</p>
                </div>
                <button
                  onClick={() => setAutoSave(!autoSave)}
                  className={`relative w-14 h-8 rounded-full transition-colors duration-200 ${
                    autoSave ? 'bg-green-600' : 'bg-gray-600'
                  }`}
                >
                  <div className={`absolute top-1 left-1 w-6 h-6 rounded-full bg-white transition-transform duration-200 ${
                    autoSave ? 'translate-x-6' : 'translate-x-0'
                  }`}></div>
                </button>
              </div>

              {/* Data Retention */}
              <div>
                <h3 className="font-semibold text-white mb-3">Data Retention Period</h3>
                <select
                  value={dataRetention}
                  onChange={(e) => setDataRetention(e.target.value)}
                  className="w-full px-4 py-3 bg-purple-900/40 border border-orange-500/20 rounded-xl text-white focus:outline-none focus:border-orange-400/40"
                >
                  <option value="1month">1 Month</option>
                  <option value="3months">3 Months</option>
                  <option value="6months">6 Months</option>
                  <option value="1year">1 Year</option>
                  <option value="forever">Forever</option>
                </select>
                <p className="text-gray-400 text-sm mt-2">
                  How long to keep your conversation history and data
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
