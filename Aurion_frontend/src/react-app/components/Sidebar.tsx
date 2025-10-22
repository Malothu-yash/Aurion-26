import { useState } from 'react';
import { useAuth } from '@/react-app/context/AuthContext';
import { useNavigate, useLocation } from 'react-router';
import { 
  Sparkles, 
  Plus, 
  ChevronDown, 
  ChevronRight, 
  Clock, 
   
  CheckCircle, 
  Circle, 
  Edit3, 
  Trash2, 
  Share, 
  Archive,
  Pin,
  User,
  Settings,
  HelpCircle,
  LogOut,
  CheckSquare as TasksIcon
} from 'lucide-react';

interface ChatSession {
  id: string;
  title: string;
  is_pinned: boolean;
  is_saved: boolean;
  updated_at: string;
}

interface Task {
  id: string;
  title: string;
  status: 'pending' | 'completed';
  created_at: string;
}

export default function Sidebar() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  
  const [isTasksExpanded, setIsTasksExpanded] = useState(true);
  const [isHistoryExpanded, setIsHistoryExpanded] = useState(true);
  const [isProfileOpen, setIsProfileOpen] = useState(false);
  const [activeTaskTab, setActiveTaskTab] = useState<'pending' | 'completed'>('pending');
  const [activeHistoryTab, setActiveHistoryTab] = useState<'recent' | 'saved'>('recent');
  const [sessions, setSessions] = useState<ChatSession[]>([]);
  const [tasks, setTasks] = useState<Task[]>([]);
  const [hoveredItem, setHoveredItem] = useState<string | null>(null);

  // Note: Removed fetchSessions and fetchTasks calls since these endpoints don't exist yet
  // Backend only has /api/v1/chat/stream for now
  // Sessions and tasks are stored locally for demo purposes

  const createNewChat = () => {
    // Navigate to new chat page without backend call
    navigate('/chat');
  };

  const handleLogout = () => {
    if (window.confirm('Are you sure you want to logout?')) {
      logout();
      navigate('/');
    }
  };

  const deleteSession = (sessionId: string) => {
    if (window.confirm('Are you sure you want to delete this conversation?')) {
      // Remove from local state (no backend yet)
      setSessions(prev => prev.filter(s => s.id !== sessionId));
      if (location.pathname.includes(sessionId)) {
        navigate('/chat');
      }
    }
  };

  const toggleTaskStatus = (taskId: string, currentStatus: string) => {
    const newStatus = currentStatus === 'pending' ? 'completed' : 'pending';
    // Update local state (no backend yet)
    setTasks(prev => prev.map(task => 
      task.id === taskId ? { ...task, status: newStatus as 'pending' | 'completed' } : task
    ));
  };

  const deleteTask = (taskId: string) => {
    if (window.confirm('Are you sure you want to delete this task?')) {
      // Remove from local state (no backend yet)
      setTasks(prev => prev.filter(t => t.id !== taskId));
    }
  };

  const filteredTasks = tasks.filter(task => task.status === activeTaskTab);
  const filteredSessions = activeHistoryTab === 'saved' 
    ? sessions.filter(s => s.is_saved)
    : sessions.slice(0, 10); // Recent 10

  return (
    <div className="w-80 h-screen bg-gradient-to-b from-purple-950/40 via-violet-950/30 to-black border-r border-orange-500/20 flex flex-col">
      {/* Header */}
      <div className="p-6 border-b border-orange-500/20">
        <div className="flex items-center space-x-3 mb-6">
          <div className="relative">
            <Sparkles className="w-8 h-8 gradient-text-aurora animate-glow" />
            <div className="absolute inset-0 animate-pulse">
              <Sparkles className="w-8 h-8 text-orange-400 opacity-30" />
            </div>
          </div>
          <span className="text-2xl font-bold gradient-text-aurora">Aurion</span>
        </div>
        
        <button 
          onClick={createNewChat}
          className="w-full btn-gradient-aurora flex items-center justify-center space-x-2 hover:scale-105 transition-transform duration-300"
        >
          <Plus className="w-5 h-5" />
          <span>New Chat</span>
        </button>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto custom-scrollbar">
        {/* Tasks Section */}
        <div className="p-4">
          <button
            onClick={() => setIsTasksExpanded(!isTasksExpanded)}
            className="w-full flex items-center justify-between text-white hover:text-orange-300 transition-colors duration-200 mb-3"
          >
            <div className="flex items-center space-x-2">
              <TasksIcon className="w-5 h-5" />
              <span className="font-semibold">Tasks</span>
            </div>
            {isTasksExpanded ? <ChevronDown className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
          </button>

          {isTasksExpanded && (
            <div className="space-y-3">
              <div className="flex space-x-1 bg-purple-900/30 rounded-lg p-1">
                <button
                  onClick={() => setActiveTaskTab('pending')}
                  className={`flex-1 py-2 px-3 rounded-md text-sm font-medium transition-all duration-200 ${
                    activeTaskTab === 'pending'
                      ? 'bg-orange-500 text-white shadow-lg'
                      : 'text-gray-300 hover:text-white'
                  }`}
                >
                  Pending
                </button>
                <button
                  onClick={() => setActiveTaskTab('completed')}
                  className={`flex-1 py-2 px-3 rounded-md text-sm font-medium transition-all duration-200 ${
                    activeTaskTab === 'completed'
                      ? 'bg-green-500 text-white shadow-lg'
                      : 'text-gray-300 hover:text-white'
                  }`}
                >
                  Completed
                </button>
              </div>

              <div className="space-y-2 max-h-40 overflow-y-auto">
                {filteredTasks.map((task) => (
                  <div
                    key={task.id}
                    className="group flex items-center space-x-3 p-3 rounded-lg bg-purple-900/20 hover:bg-purple-900/40 transition-all duration-200 cursor-pointer"
                    onMouseEnter={() => setHoveredItem(task.id)}
                    onMouseLeave={() => setHoveredItem(null)}
                  >
                    <button
                      onClick={() => toggleTaskStatus(task.id, task.status)}
                      className="flex-shrink-0"
                    >
                      {task.status === 'completed' ? (
                        <CheckCircle className="w-4 h-4 text-green-400" />
                      ) : (
                        <Circle className="w-4 h-4 text-gray-400 hover:text-orange-400" />
                      )}
                    </button>
                    <span className={`flex-1 text-sm truncate ${
                      task.status === 'completed' ? 'text-gray-400 line-through' : 'text-gray-200'
                    }`}>
                      {task.title}
                    </span>
                    
                    {hoveredItem === task.id && (
                      <div className="flex items-center space-x-1 opacity-0 group-hover:opacity-100 transition-opacity duration-200">
                        <button className="p-1 hover:text-orange-400 transition-colors">
                          <Edit3 className="w-3 h-3" />
                        </button>
                        <button 
                          onClick={() => deleteTask(task.id)}
                          className="p-1 hover:text-red-400 transition-colors"
                        >
                          <Trash2 className="w-3 h-3" />
                        </button>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* History Section */}
        <div className="p-4">
          <button
            onClick={() => setIsHistoryExpanded(!isHistoryExpanded)}
            className="w-full flex items-center justify-between text-white hover:text-orange-300 transition-colors duration-200 mb-3"
          >
            <div className="flex items-center space-x-2">
              <Clock className="w-5 h-5" />
              <span className="font-semibold">History</span>
            </div>
            {isHistoryExpanded ? <ChevronDown className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
          </button>

          {isHistoryExpanded && (
            <div className="space-y-3">
              <div className="flex space-x-1 bg-purple-900/30 rounded-lg p-1">
                <button
                  onClick={() => setActiveHistoryTab('recent')}
                  className={`flex-1 py-2 px-3 rounded-md text-sm font-medium transition-all duration-200 ${
                    activeHistoryTab === 'recent'
                      ? 'bg-purple-500 text-white shadow-lg'
                      : 'text-gray-300 hover:text-white'
                  }`}
                >
                  Recent
                </button>
                <button
                  onClick={() => setActiveHistoryTab('saved')}
                  className={`flex-1 py-2 px-3 rounded-md text-sm font-medium transition-all duration-200 ${
                    activeHistoryTab === 'saved'
                      ? 'bg-violet-500 text-white shadow-lg'
                      : 'text-gray-300 hover:text-white'
                  }`}
                >
                  Saved
                </button>
              </div>

              <div className="space-y-2 max-h-60 overflow-y-auto">
                {filteredSessions.map((session) => (
                  <div
                    key={session.id}
                    className="group flex items-center space-x-3 p-3 rounded-lg bg-purple-900/20 hover:bg-purple-900/40 transition-all duration-200 cursor-pointer"
                    onMouseEnter={() => setHoveredItem(session.id)}
                    onMouseLeave={() => setHoveredItem(null)}
                    onClick={() => navigate(`/chat/${session.id}`)}
                  >
                    <span className="flex-1 text-sm text-gray-200 truncate">
                      {session.title}
                    </span>
                    
                    {hoveredItem === session.id && (
                      <div className="flex items-center space-x-1 opacity-0 group-hover:opacity-100 transition-opacity duration-200">
                        <button className="p-1 hover:text-blue-400 transition-colors">
                          <Share className="w-3 h-3" />
                        </button>
                        <button className="p-1 hover:text-green-400 transition-colors">
                          <Edit3 className="w-3 h-3" />
                        </button>
                        <button className="p-1 hover:text-yellow-400 transition-colors">
                          <Pin className="w-3 h-3" />
                        </button>
                        <button className="p-1 hover:text-purple-400 transition-colors">
                          <Archive className="w-3 h-3" />
                        </button>
                        <button 
                          onClick={(e) => {
                            e.stopPropagation();
                            deleteSession(session.id);
                          }}
                          className="p-1 hover:text-red-400 transition-colors"
                        >
                          <Trash2 className="w-3 h-3" />
                        </button>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Profile Section */}
      <div className="p-4 border-t border-orange-500/20">
        <div className="relative">
          <button
            onClick={() => setIsProfileOpen(!isProfileOpen)}
            className="w-full flex items-center space-x-3 p-3 rounded-lg bg-purple-900/20 hover:bg-purple-900/40 transition-all duration-200"
          >
            <div className="w-10 h-10 rounded-full border-2 border-orange-400/50 bg-gradient-to-br from-orange-400 to-purple-600 flex items-center justify-center">
              <User className="w-6 h-6 text-white" />
            </div>
            <div className="flex-1 text-left">
              <div className="font-medium text-white truncate">
                {user?.display_name || user?.email}
              </div>
              <div className="text-sm text-gray-400 truncate">
                {user?.email}
              </div>
            </div>
            <ChevronDown className={`w-4 h-4 text-gray-400 transition-transform duration-200 ${
              isProfileOpen ? 'rotate-180' : ''
            }`} />
          </button>

          {isProfileOpen && (
            <div className="absolute bottom-full left-0 right-0 mb-2 bg-purple-950/90 backdrop-blur-lg border border-orange-500/20 rounded-lg shadow-xl animate-fade-in-up">
              <div className="p-2 space-y-1">
                <button
                  onClick={() => navigate('/tasks')}
                  className="w-full flex items-center space-x-3 p-3 rounded-lg hover:bg-purple-900/40 transition-colors duration-200 text-gray-300 hover:text-white"
                >
                  <TasksIcon className="w-4 h-4" />
                  <span>Tasks</span>
                </button>
                <button
                  onClick={() => navigate('/profile')}
                  className="w-full flex items-center space-x-3 p-3 rounded-lg hover:bg-purple-900/40 transition-colors duration-200 text-gray-300 hover:text-white"
                >
                  <User className="w-4 h-4" />
                  <span>Profile</span>
                </button>
                <button
                  onClick={() => navigate('/settings')}
                  className="w-full flex items-center space-x-3 p-3 rounded-lg hover:bg-purple-900/40 transition-colors duration-200 text-gray-300 hover:text-white"
                >
                  <Settings className="w-4 h-4" />
                  <span>Settings</span>
                </button>
                <button
                  onClick={() => navigate('/help')}
                  className="w-full flex items-center space-x-3 p-3 rounded-lg hover:bg-purple-900/40 transition-colors duration-200 text-gray-300 hover:text-white"
                >
                  <HelpCircle className="w-4 h-4" />
                  <span>Help</span>
                </button>
                <hr className="border-orange-500/20 my-2" />
                <button
                  onClick={handleLogout}
                  className="w-full flex items-center space-x-3 p-3 rounded-lg hover:bg-red-900/40 transition-colors duration-200 text-gray-300 hover:text-red-300"
                >
                  <LogOut className="w-4 h-4" />
                  <span>Logout</span>
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
