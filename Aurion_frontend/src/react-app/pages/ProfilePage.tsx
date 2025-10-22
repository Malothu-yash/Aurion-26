import { useState, useEffect } from 'react';
import { useAuth } from '@/react-app/context/AuthContext';
import { useNavigate } from 'react-router';
import Sidebar from '@/react-app/components/Sidebar';
import { 
  User, 
  Mail, 
  Calendar, 
  Trash2, 
  Brain, 
  Clock, 
  Database,
  AlertTriangle,
  Shield,
  Sparkles,
  Edit3,
  Save,
  X
} from 'lucide-react';

export default function ProfilePage() {
  const { user, logout, isAuthenticated } = useAuth();
  const navigate = useNavigate();
  const [isEditing, setIsEditing] = useState(false);
  const [displayName, setDisplayName] = useState('');
  const [showDeleteConfirm, setShowDeleteConfirm] = useState<string | null>(null);

  useEffect(() => {
    if (!isAuthenticated) {
      navigate('/');
      return;
    }
    if (user) {
      setDisplayName(user.display_name || '');
    }
  }, [isAuthenticated, user, navigate]);

  const handleSaveProfile = async () => {
    try {
      // Update user profile API call would go here
      console.log('Saving profile:', { displayName });
      setIsEditing(false);
    } catch (error) {
      console.error('Failed to save profile:', error);
    }
  };

  const handleDeleteMemories = async (type: string) => {
    if (!window.confirm(`Are you sure you want to delete all ${type} memories? This action cannot be undone.`)) {
      return;
    }

    try {
      // Delete memories API call would go here
      console.log('Deleting memories:', type);
      setShowDeleteConfirm(null);
    } catch (error) {
      console.error('Failed to delete memories:', error);
    }
  };

  const handleDeleteAccount = async () => {
    if (!window.confirm('Are you sure you want to delete your account? This will permanently remove all your data and cannot be undone.')) {
      return;
    }

    if (!window.confirm('This is your final warning. Are you absolutely sure you want to delete your account permanently?')) {
      return;
    }

    try {
      // Delete account API call would go here
      console.log('Deleting account');
      await logout();
      navigate('/');
    } catch (error) {
      console.error('Failed to delete account:', error);
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

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  return (
    <div className="h-screen bg-gradient-to-br from-violet-950/20 via-purple-950/10 to-black flex">
      <Sidebar />
      
      <div className="flex-1 overflow-y-auto">
        {/* Header */}
        <div className="h-16 border-b border-orange-500/20 flex items-center px-6">
          <div className="flex items-center space-x-3">
            <User className="w-6 h-6 gradient-text-aurora" />
            <h1 className="text-xl font-semibold text-white">Profile</h1>
          </div>
        </div>

        <div className="max-w-4xl mx-auto p-6 space-y-8">
          {/* Profile Information */}
          <div className="glass-aurora rounded-2xl p-8">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-2xl font-bold text-white">Profile Information</h2>
              {!isEditing ? (
                <button
                  onClick={() => setIsEditing(true)}
                  className="flex items-center space-x-2 btn-gradient-aurora"
                >
                  <Edit3 className="w-4 h-4" />
                  <span>Edit</span>
                </button>
              ) : (
                <div className="flex space-x-2">
                  <button
                    onClick={handleSaveProfile}
                    className="flex items-center space-x-2 btn-gradient-aurora"
                  >
                    <Save className="w-4 h-4" />
                    <span>Save</span>
                  </button>
                  <button
                    onClick={() => {
                      setIsEditing(false);
                      setDisplayName(user.display_name || user.email.split('@')[0]);
                    }}
                    className="flex items-center space-x-2 px-4 py-2 bg-gray-700 text-gray-300 rounded-xl hover:bg-gray-600 transition-colors duration-200"
                  >
                    <X className="w-4 h-4" />
                    <span>Cancel</span>
                  </button>
                </div>
              )}
            </div>

            <div className="flex items-center space-x-6 mb-8">
              <div className="w-24 h-24 rounded-full border-4 border-orange-400/50 bg-gradient-to-br from-orange-400 to-purple-600 flex items-center justify-center">
                <User className="w-12 h-12 text-white" />
              </div>
              <div className="flex-1">
                {isEditing ? (
                  <input
                    type="text"
                    value={displayName}
                    onChange={(e) => setDisplayName(e.target.value)}
                    className="text-2xl font-bold bg-purple-900/40 border border-orange-500/20 rounded-xl px-4 py-2 text-white focus:outline-none focus:border-orange-400/40 w-full"
                  />
                ) : (
                  <h3 className="text-2xl font-bold text-white mb-2">{displayName}</h3>
                )}
                <div className="flex items-center space-x-2 text-gray-300 mb-2">
                  <Mail className="w-4 h-4" />
                  <span>{user.email}</span>
                </div>
                <div className="flex items-center space-x-2 text-gray-400 text-sm">
                  <Calendar className="w-4 h-4" />
                  <span>Joined {formatDate(user.created_at)}</span>
                </div>
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="bg-purple-900/20 rounded-xl p-4">
                <div className="flex items-center space-x-2 mb-2">
                  <Shield className="w-5 h-5 text-green-400" />
                  <span className="font-semibold text-white">Account Status</span>
                </div>
                <p className="text-gray-300">Verified & Active</p>
              </div>
              
              <div className="bg-purple-900/20 rounded-xl p-4">
                <div className="flex items-center space-x-2 mb-2">
                  <Clock className="w-5 h-5 text-blue-400" />
                  <span className="font-semibold text-white">Joined</span>
                </div>
                <p className="text-gray-300">{formatDate(user.created_at)}</p>
              </div>
            </div>
          </div>

          {/* Memory Management */}
          <div className="glass-aurora rounded-2xl p-8">
            <div className="flex items-center space-x-3 mb-6">
              <Brain className="w-6 h-6 text-purple-400" />
              <h2 className="text-2xl font-bold text-white">Memory Management</h2>
            </div>
            
            <p className="text-gray-300 mb-6">
              Manage your AI conversation memories. Deleting memories will remove them permanently and cannot be undone.
            </p>

            <div className="space-y-4">
              {[
                {
                  type: 'short-term',
                  title: 'Short-term Memory',
                  description: 'Recent conversation context and temporary data',
                  icon: Clock,
                  color: 'text-blue-400'
                },
                {
                  type: 'long-term',
                  title: 'Long-term Memory',
                  description: 'Persistent knowledge and learned preferences',
                  icon: Database,
                  color: 'text-green-400'
                },
                {
                  type: 'semantic',
                  title: 'Semantic Memory',
                  description: 'Facts, concepts, and general knowledge about you',
                  icon: Brain,
                  color: 'text-purple-400'
                }
              ].map((memory) => (
                <div key={memory.type} className="flex items-center justify-between p-4 bg-purple-900/20 rounded-xl">
                  <div className="flex items-center space-x-4">
                    <memory.icon className={`w-6 h-6 ${memory.color}`} />
                    <div>
                      <h3 className="font-semibold text-white">{memory.title}</h3>
                      <p className="text-sm text-gray-400">{memory.description}</p>
                    </div>
                  </div>
                  
                  <button
                    onClick={() => setShowDeleteConfirm(memory.type)}
                    className="flex items-center space-x-2 px-4 py-2 bg-red-900/40 text-red-300 rounded-lg hover:bg-red-900/60 transition-colors duration-200"
                  >
                    <Trash2 className="w-4 h-4" />
                    <span>Delete</span>
                  </button>
                </div>
              ))}
            </div>
          </div>

          {/* Danger Zone */}
          <div className="glass-aurora rounded-2xl p-8 border border-red-500/30">
            <div className="flex items-center space-x-3 mb-6">
              <AlertTriangle className="w-6 h-6 text-red-400" />
              <h2 className="text-2xl font-bold text-red-300">Danger Zone</h2>
            </div>
            
            <div className="bg-red-900/20 rounded-xl p-6">
              <h3 className="text-lg font-semibold text-red-300 mb-2">Delete Account</h3>
              <p className="text-gray-300 mb-4">
                Permanently delete your account and all associated data. This action cannot be undone.
              </p>
              <button
                onClick={handleDeleteAccount}
                className="flex items-center space-x-2 px-6 py-3 bg-red-600 text-white rounded-xl hover:bg-red-700 transition-colors duration-200"
              >
                <Trash2 className="w-4 h-4" />
                <span>Delete Account</span>
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Delete Confirmation Modal */}
      {showDeleteConfirm && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4">
          <div className="glass-aurora rounded-2xl p-6 w-full max-w-md">
            <div className="flex items-center space-x-3 mb-4">
              <AlertTriangle className="w-6 h-6 text-red-400" />
              <h3 className="text-lg font-semibold text-white">Confirm Deletion</h3>
            </div>
            
            <p className="text-gray-300 mb-6">
              Are you sure you want to delete all {showDeleteConfirm.replace('-', ' ')} memories? 
              This action cannot be undone.
            </p>
            
            <div className="flex space-x-4">
              <button
                onClick={() => setShowDeleteConfirm(null)}
                className="flex-1 px-4 py-3 bg-gray-700 text-gray-300 rounded-xl hover:bg-gray-600 transition-colors duration-200"
              >
                Cancel
              </button>
              <button
                onClick={() => handleDeleteMemories(showDeleteConfirm)}
                className="flex-1 px-4 py-3 bg-red-600 text-white rounded-xl hover:bg-red-700 transition-colors duration-200"
              >
                Delete
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
