// src/react-app/pages/admin/AdminDashboard.tsx
// Main admin dashboard with overview and stats

import React, { useState, useEffect } from 'react';
import { useAdminAuth } from '../../context/AdminAuthContext';
import { adminApi, SystemStats, APIUsageStats } from '../../services/adminApi';
import StatsCard from '../../components/admin/StatsCard';

const AdminDashboard: React.FC = () => {
  const { admin, logout } = useAdminAuth();
  const [stats, setStats] = useState<SystemStats | null>(null);
  const [apiUsage, setApiUsage] = useState<APIUsageStats[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('dashboard');
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

  useEffect(() => {
    loadDashboardData();
    
    // Refresh every 30 seconds
    const interval = setInterval(loadDashboardData, 30000);
    return () => clearInterval(interval);
  }, []);

  const loadDashboardData = async () => {
    try {
      const data = await adminApi.getDashboardStats();
      setStats(data.system);
      setApiUsage(data.api_usage);
    } catch (error) {
      console.error('Failed to load dashboard data:', error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleLogout = async () => {
    await logout();
    window.location.href = '/admin/login';
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gray-900 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto mb-4"></div>
          <p className="text-gray-400">Loading dashboard...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-900">
      {/* Top Navigation */}
      <header className="bg-gray-800 border-b border-gray-700 sticky top-0 z-50">
        <div className="px-4 sm:px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3 sm:space-x-4">
              {/* Mobile Menu Button */}
              <button
                onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
                className="lg:hidden p-2 text-gray-400 hover:text-white transition"
              >
                <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  {isMobileMenuOpen ? (
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  ) : (
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6h16M4 12h16M4 18h16" />
                  )}
                </svg>
              </button>

              <div className="w-8 h-8 sm:w-10 sm:h-10 rounded-lg bg-gradient-to-br from-blue-500 to-purple-600 flex items-center justify-center flex-shrink-0">
                <svg className="w-5 h-5 sm:w-6 sm:h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6V4m0 2a2 2 0 100 4m0-4a2 2 0 110 4m-6 8a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4m6 6v10m6-2a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4" />
                </svg>
              </div>
              <div className="hidden sm:block">
                <h1 className="text-lg sm:text-xl font-bold text-white">AURION Admin</h1>
                <p className="text-xs sm:text-sm text-gray-400 truncate max-w-[150px] sm:max-w-none">{admin?.email}</p>
              </div>
            </div>
            
            <div className="flex items-center space-x-2 sm:space-x-4">
              <span className="hidden md:inline text-sm text-gray-400">
                Role: <span className="text-blue-400 font-medium">{admin?.role}</span>
              </span>
              <button
                onClick={handleLogout}
                className="px-3 py-1.5 sm:px-4 sm:py-2 bg-gray-700 text-white text-sm rounded-lg hover:bg-gray-600 transition"
              >
                <span className="hidden sm:inline">Logout</span>
                <svg className="w-5 h-5 sm:hidden" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
                </svg>
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Sidebar + Content Layout */}
      <div className="flex relative">
        {/* Sidebar - Desktop */}
        <aside className="hidden lg:block w-64 bg-gray-800 border-r border-gray-700 min-h-screen p-4 sticky top-[73px] h-[calc(100vh-73px)] overflow-y-auto">
          <nav className="space-y-2">
            {[
              { id: 'dashboard', label: 'Dashboard', icon: '📊' },
              { id: 'users', label: 'User Management', icon: '👥' },
              { id: 'api', label: 'API Management', icon: '🔌' },
              { id: 'memory', label: 'Memory Control', icon: '🧠' },
              { id: 'server', label: 'Server Control', icon: '🖥️' },
              { id: 'logs', label: 'Logs & Analytics', icon: '📝' },
              { id: 'settings', label: 'Settings', icon: '⚙️' },
            ].map((item) => (
              <button
                key={item.id}
                onClick={() => setActiveTab(item.id)}
                className={`w-full px-4 py-3 rounded-lg text-left transition ${
                  activeTab === item.id
                    ? 'bg-blue-600 text-white'
                    : 'text-gray-300 hover:bg-gray-700'
                }`}
              >
                <span className="mr-3">{item.icon}</span>
                {item.label}
              </button>
            ))}
          </nav>
        </aside>

        {/* Mobile Sidebar Overlay */}
        {isMobileMenuOpen && (
          <div className="lg:hidden fixed inset-0 z-40 bg-black bg-opacity-50" onClick={() => setIsMobileMenuOpen(false)}>
            <aside
              className="absolute left-0 top-0 bottom-0 w-64 bg-gray-800 border-r border-gray-700 p-4 overflow-y-auto"
              onClick={(e) => e.stopPropagation()}
            >
              <nav className="space-y-2">
                {[
                  { id: 'dashboard', label: 'Dashboard', icon: '📊' },
                  { id: 'users', label: 'User Management', icon: '👥' },
                  { id: 'api', label: 'API Management', icon: '🔌' },
                  { id: 'memory', label: 'Memory Control', icon: '🧠' },
                  { id: 'server', label: 'Server Control', icon: '🖥️' },
                  { id: 'logs', label: 'Logs & Analytics', icon: '📝' },
                  { id: 'settings', label: 'Settings', icon: '⚙️' },
                ].map((item) => (
                  <button
                    key={item.id}
                    onClick={() => {
                      setActiveTab(item.id);
                      setIsMobileMenuOpen(false);
                    }}
                    className={`w-full px-4 py-3 rounded-lg text-left transition ${
                      activeTab === item.id
                        ? 'bg-blue-600 text-white'
                        : 'text-gray-300 hover:bg-gray-700'
                    }`}
                  >
                    <span className="mr-3">{item.icon}</span>
                    {item.label}
                  </button>
                ))}
              </nav>
            </aside>
          </div>
        )}

        {/* Main Content */}
        <main className="flex-1 p-4 sm:p-6 lg:p-8">
          {activeTab === 'dashboard' && (
            <div className="space-y-6 sm:space-y-8">
              {/* Dashboard Header */}
              <div>
                <h2 className="text-xl sm:text-2xl font-bold text-white mb-2">Dashboard Overview</h2>
                <p className="text-sm sm:text-base text-gray-400">Real-time system statistics and monitoring</p>
              </div>

              {/* Stats Grid */}
              {stats && (
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 sm:gap-6">
                  <StatsCard
                    title="Total Users"
                    value={stats.total_users}
                    subtitle="Registered accounts"
                    color="blue"
                    icon={
                      <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z" />
                      </svg>
                    }
                  />

                  <StatsCard
                    title="Active Users"
                    value={stats.active_users}
                    subtitle="Last 7 days"
                    color="green"
                    icon={
                      <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                      </svg>
                    }
                  />

                  <StatsCard
                    title="CPU Usage"
                    value={`${stats.cpu_usage.toFixed(1)}%`}
                    subtitle="Current load"
                    color={stats.cpu_usage > 80 ? 'red' : stats.cpu_usage > 60 ? 'yellow' : 'green'}
                    icon={
                      <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 3v2m6-2v2M9 19v2m6-2v2M5 9H3m2 6H3m18-6h-2m2 6h-2M7 19h10a2 2 0 002-2V7a2 2 0 00-2-2H7a2 2 0 00-2 2v10a2 2 0 002 2zM9 9h6v6H9V9z" />
                      </svg>
                    }
                  />

                  <StatsCard
                    title="Memory"
                    value={`${stats.memory_usage.toFixed(1)}%`}
                    subtitle="System RAM"
                    color={stats.memory_usage > 80 ? 'red' : stats.memory_usage > 60 ? 'yellow' : 'purple'}
                    icon={
                      <svg className="w-6 h-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 3v2m6-2v2M9 19v2m6-2v2M5 9H3m2 6H3m18-6h-2m2 6h-2M7 19h10a2 2 0 002-2V7a2 2 0 00-2-2H7a2 2 0 00-2 2v10a2 2 0 002 2zM9 9h6v6H9V9z" />
                      </svg>
                    }
                  />
                </div>
              )}

              {/* API Usage Section */}
              <div className="bg-gray-800 rounded-xl border border-gray-700 p-4 sm:p-6">
                <h3 className="text-base sm:text-lg font-semibold text-white mb-4">API Usage Statistics</h3>
                <div className="space-y-4">
                  {apiUsage.map((api) => (
                    <div key={api.provider} className="space-y-2">
                      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-1 sm:gap-0">
                        <div>
                          <span className="text-white font-medium capitalize">{api.provider}</span>
                          <span className="text-gray-400 text-xs sm:text-sm ml-2">
                            {api.total_requests} requests
                          </span>
                        </div>
                        <span className={`text-xs sm:text-sm ${api.success_rate && api.success_rate > 90 ? 'text-green-400' : 'text-yellow-400'}`}>
                          {api.success_rate?.toFixed(1)}% success
                        </span>
                      </div>
                      <div className="w-full bg-gray-700 rounded-full h-2">
                        <div
                          className="bg-gradient-to-r from-blue-500 to-purple-600 h-2 rounded-full transition-all"
                          style={{ width: `${(api.successful_requests / api.total_requests) * 100 || 0}%` }}
                        ></div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Quick Actions */}
              <div className="bg-gray-800 rounded-xl border border-gray-700 p-4 sm:p-6">
                <h3 className="text-base sm:text-lg font-semibold text-white mb-4">Quick Actions</h3>
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3 sm:gap-4">
                  <button
                    onClick={() => setActiveTab('users')}
                    className="p-4 bg-gray-700 rounded-lg hover:bg-gray-600 transition text-left"
                  >
                    <div className="text-xl sm:text-2xl mb-2">👥</div>
                    <div className="text-white font-medium text-sm sm:text-base">Manage Users</div>
                    <div className="text-gray-400 text-xs sm:text-sm">View and edit users</div>
                  </button>

                  <button
                    onClick={() => setActiveTab('api')}
                    className="p-4 bg-gray-700 rounded-lg hover:bg-gray-600 transition text-left"
                  >
                    <div className="text-xl sm:text-2xl mb-2">🔌</div>
                    <div className="text-white font-medium text-sm sm:text-base">API Settings</div>
                    <div className="text-gray-400 text-xs sm:text-sm">Update API keys</div>
                  </button>

                  <button
                    onClick={() => setActiveTab('logs')}
                    className="p-4 bg-gray-700 rounded-lg hover:bg-gray-600 transition text-left"
                  >
                    <div className="text-xl sm:text-2xl mb-2">📝</div>
                    <div className="text-white font-medium text-sm sm:text-base">View Logs</div>
                    <div className="text-gray-400 text-xs sm:text-sm">System activity</div>
                  </button>
                </div>
              </div>
            </div>
          )}

          {/* Placeholder for other tabs */}
          {activeTab !== 'dashboard' && (
            <div className="bg-gray-800 rounded-xl border border-gray-700 p-6 sm:p-8 text-center">
              <div className="text-3xl sm:text-4xl mb-4">🚧</div>
              <h3 className="text-lg sm:text-xl font-semibold text-white mb-2">
                {activeTab.charAt(0).toUpperCase() + activeTab.slice(1)} Page
              </h3>
              <p className="text-sm sm:text-base text-gray-400">This page is under construction</p>
            </div>
          )}
        </main>
      </div>
    </div>
  );
};

export default AdminDashboard;
