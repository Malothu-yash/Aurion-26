import { useState, useEffect } from 'react';
import { useAuth } from '@/react-app/context/AuthContext';
import { useNavigate } from 'react-router';
import Sidebar from '@/react-app/components/Sidebar';
import { 
  Plus, 
  Calendar, 
  Flag, 
  CheckCircle, 
  Circle, 
  Edit3, 
  Trash2, 
  Search,
  
  Sparkles,
  Target,
  Clock,
  AlertCircle
} from 'lucide-react';

interface Task {
  id: string;
  title: string;
  description?: string;
  status: 'pending' | 'completed';
  priority: 'low' | 'medium' | 'high';
  due_date?: string;
  tags: string[];
  created_at: string;
  updated_at: string;
}

export default function TasksPage() {
  const { user, isAuthenticated } = useAuth();
  const navigate = useNavigate();
  const [tasks, setTasks] = useState<Task[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterStatus, setFilterStatus] = useState<'all' | 'pending' | 'completed'>('all');
  const [filterPriority, setFilterPriority] = useState<'all' | 'low' | 'medium' | 'high'>('all');
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [editingTask, setEditingTask] = useState<Task | null>(null);

  useEffect(() => {
    // Protected by ProtectedRoute, but double-check
    if (!isAuthenticated) {
      navigate('/');
      return;
    }
    fetchTasks();
  }, [isAuthenticated, navigate]);

  const fetchTasks = async () => {
    try {
      setLoading(true);
      const response = await fetch('/api/tasks');
      if (response.ok) {
        const data = await response.json();
        setTasks(data);
      }
    } catch (error) {
      console.error('Failed to fetch tasks:', error);
    } finally {
      setLoading(false);
    }
  };

  const createTask = async (taskData: Partial<Task>) => {
    try {
      const response = await fetch('/api/tasks', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(taskData)
      });
      if (response.ok) {
        fetchTasks();
        setShowCreateModal(false);
      }
    } catch (error) {
      console.error('Failed to create task:', error);
    }
  };

  const updateTask = async (taskId: string, updates: Partial<Task>) => {
    try {
      const response = await fetch(`/api/tasks/${taskId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(updates)
      });
      if (response.ok) {
        fetchTasks();
        setEditingTask(null);
      }
    } catch (error) {
      console.error('Failed to update task:', error);
    }
  };

  const deleteTask = async (taskId: string) => {
    if (!window.confirm('Are you sure you want to delete this task?')) return;
    
    try {
      const response = await fetch(`/api/tasks/${taskId}`, {
        method: 'DELETE'
      });
      if (response.ok) {
        fetchTasks();
      }
    } catch (error) {
      console.error('Failed to delete task:', error);
    }
  };

  const toggleTaskStatus = async (taskId: string, currentStatus: string) => {
    const newStatus = currentStatus === 'pending' ? 'completed' : 'pending';
    await updateTask(taskId, { status: newStatus });
  };

  const filteredTasks = tasks.filter(task => {
    const matchesSearch = task.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         task.description?.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesStatus = filterStatus === 'all' || task.status === filterStatus;
    const matchesPriority = filterPriority === 'all' || task.priority === filterPriority;
    
    return matchesSearch && matchesStatus && matchesPriority;
  });

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'high': return 'text-red-400 bg-red-900/20';
      case 'medium': return 'text-orange-400 bg-orange-900/20';
      case 'low': return 'text-green-400 bg-green-900/20';
      default: return 'text-gray-400 bg-gray-900/20';
    }
  };

  const getPriorityIcon = (priority: string) => {
    switch (priority) {
      case 'high': return AlertCircle;
      case 'medium': return Flag;
      case 'low': return Circle;
      default: return Circle;
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
      
      <div className="flex-1 flex flex-col">
        {/* Header */}
        <div className="h-16 border-b border-orange-500/20 flex items-center justify-between px-6">
          <div className="flex items-center space-x-3">
            <Target className="w-6 h-6 gradient-text-aurora" />
            <h1 className="text-xl font-semibold text-white">Tasks</h1>
          </div>
          
          <button
            onClick={() => setShowCreateModal(true)}
            className="btn-gradient-aurora flex items-center space-x-2 hover:scale-105 transition-transform duration-300"
          >
            <Plus className="w-4 h-4" />
            <span>New Task</span>
          </button>
        </div>

        {/* Filters */}
        <div className="p-6 border-b border-orange-500/20">
          <div className="flex flex-col lg:flex-row gap-4">
            {/* Search */}
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
              <input
                type="text"
                placeholder="Search tasks..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full pl-10 pr-4 py-3 bg-purple-900/40 border border-orange-500/20 rounded-xl text-white placeholder-gray-400 focus:outline-none focus:border-orange-400/40 transition-colors duration-200"
              />
            </div>

            {/* Status Filter */}
            <select
              value={filterStatus}
              onChange={(e) => setFilterStatus(e.target.value as any)}
              className="px-4 py-3 bg-purple-900/40 border border-orange-500/20 rounded-xl text-white focus:outline-none focus:border-orange-400/40 transition-colors duration-200"
            >
              <option value="all">All Status</option>
              <option value="pending">Pending</option>
              <option value="completed">Completed</option>
            </select>

            {/* Priority Filter */}
            <select
              value={filterPriority}
              onChange={(e) => setFilterPriority(e.target.value as any)}
              className="px-4 py-3 bg-purple-900/40 border border-orange-500/20 rounded-xl text-white focus:outline-none focus:border-orange-400/40 transition-colors duration-200"
            >
              <option value="all">All Priority</option>
              <option value="high">High</option>
              <option value="medium">Medium</option>
              <option value="low">Low</option>
            </select>
          </div>
        </div>

        {/* Tasks List */}
        <div className="flex-1 overflow-y-auto p-6">
          {loading ? (
            <div className="flex items-center justify-center h-64">
              <div className="spinner-aurora"></div>
            </div>
          ) : filteredTasks.length === 0 ? (
            <div className="text-center py-12">
              <Target className="w-16 h-16 text-gray-600 mx-auto mb-4" />
              <h3 className="text-xl font-semibold text-gray-400 mb-2">No tasks found</h3>
              <p className="text-gray-500 mb-6">Create your first task to get started!</p>
              <button
                onClick={() => setShowCreateModal(true)}
                className="btn-gradient-aurora"
              >
                Create Task
              </button>
            </div>
          ) : (
            <div className="space-y-4">
              {filteredTasks.map((task) => {
                const PriorityIcon = getPriorityIcon(task.priority);
                return (
                  <div
                    key={task.id}
                    className="group glass-aurora rounded-xl p-6 hover:scale-105 transition-all duration-300"
                  >
                    <div className="flex items-start space-x-4">
                      <button
                        onClick={() => toggleTaskStatus(task.id, task.status)}
                        className="flex-shrink-0 mt-1"
                      >
                        {task.status === 'completed' ? (
                          <CheckCircle className="w-6 h-6 text-green-400" />
                        ) : (
                          <Circle className="w-6 h-6 text-gray-400 hover:text-orange-400 transition-colors duration-200" />
                        )}
                      </button>

                      <div className="flex-1 min-w-0">
                        <div className="flex items-start justify-between">
                          <div className="flex-1 min-w-0">
                            <h3 className={`text-lg font-semibold mb-2 ${
                              task.status === 'completed' 
                                ? 'text-gray-400 line-through' 
                                : 'text-white'
                            }`}>
                              {task.title}
                            </h3>
                            
                            {task.description && (
                              <p className={`text-sm mb-3 ${
                                task.status === 'completed' 
                                  ? 'text-gray-500' 
                                  : 'text-gray-300'
                              }`}>
                                {task.description}
                              </p>
                            )}

                            <div className="flex items-center space-x-4 text-sm">
                              <div className={`flex items-center space-x-1 px-2 py-1 rounded-lg ${getPriorityColor(task.priority)}`}>
                                <PriorityIcon className="w-3 h-3" />
                                <span className="capitalize">{task.priority}</span>
                              </div>
                              
                              {task.due_date && (
                                <div className="flex items-center space-x-1 text-gray-400">
                                  <Calendar className="w-3 h-3" />
                                  <span>{new Date(task.due_date).toLocaleDateString()}</span>
                                </div>
                              )}
                              
                              <div className="flex items-center space-x-1 text-gray-400">
                                <Clock className="w-3 h-3" />
                                <span>{new Date(task.created_at).toLocaleDateString()}</span>
                              </div>
                            </div>

                            {task.tags.length > 0 && (
                              <div className="flex flex-wrap gap-2 mt-3">
                                {task.tags.map((tag, index) => (
                                  <span
                                    key={index}
                                    className="px-2 py-1 bg-purple-900/40 text-purple-300 text-xs rounded-lg"
                                  >
                                    #{tag}
                                  </span>
                                ))}
                              </div>
                            )}
                          </div>

                          <div className="flex items-center space-x-2 opacity-0 group-hover:opacity-100 transition-opacity duration-200">
                            <button
                              onClick={() => setEditingTask(task)}
                              className="p-2 rounded-lg bg-purple-900/40 text-gray-400 hover:text-orange-400 hover:bg-purple-900/60 transition-all duration-200"
                            >
                              <Edit3 className="w-4 h-4" />
                            </button>
                            <button
                              onClick={() => deleteTask(task.id)}
                              className="p-2 rounded-lg bg-purple-900/40 text-gray-400 hover:text-red-400 hover:bg-purple-900/60 transition-all duration-200"
                            >
                              <Trash2 className="w-4 h-4" />
                            </button>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>
      </div>

      {/* Create/Edit Task Modal would go here */}
      {(showCreateModal || editingTask) && (
        <TaskModal
          task={editingTask}
          onClose={() => {
            setShowCreateModal(false);
            setEditingTask(null);
          }}
          onSave={editingTask ? 
            (updates) => updateTask(editingTask.id, updates) : 
            createTask
          }
        />
      )}
    </div>
  );
}

// Task Modal Component (simplified)
function TaskModal({ task, onClose, onSave }: {
  task?: Task | null;
  onClose: () => void;
  onSave: (data: Partial<Task>) => void;
}) {
  const [title, setTitle] = useState(task?.title || '');
  const [description, setDescription] = useState(task?.description || '');
  const [priority, setPriority] = useState(task?.priority || 'medium');
  const [dueDate, setDueDate] = useState(task?.due_date || '');

  const handleSave = () => {
    if (!title.trim()) return;
    
    onSave({
      title,
      description: description || undefined,
      priority,
      due_date: dueDate || undefined,
      tags: []
    });
  };

  return (
    <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4">
      <div className="glass-aurora rounded-2xl p-6 w-full max-w-md">
        <h2 className="text-xl font-semibold text-white mb-6">
          {task ? 'Edit Task' : 'Create New Task'}
        </h2>
        
        <div className="space-y-4">
          <input
            type="text"
            placeholder="Task title..."
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            className="w-full px-4 py-3 bg-purple-900/40 border border-orange-500/20 rounded-xl text-white placeholder-gray-400 focus:outline-none focus:border-orange-400/40"
          />
          
          <textarea
            placeholder="Description (optional)..."
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            className="w-full px-4 py-3 bg-purple-900/40 border border-orange-500/20 rounded-xl text-white placeholder-gray-400 focus:outline-none focus:border-orange-400/40 resize-none h-24"
          />
          
          <select
            value={priority}
            onChange={(e) => setPriority(e.target.value as any)}
            className="w-full px-4 py-3 bg-purple-900/40 border border-orange-500/20 rounded-xl text-white focus:outline-none focus:border-orange-400/40"
          >
            <option value="low">Low Priority</option>
            <option value="medium">Medium Priority</option>
            <option value="high">High Priority</option>
          </select>
          
          <input
            type="date"
            value={dueDate}
            onChange={(e) => setDueDate(e.target.value)}
            className="w-full px-4 py-3 bg-purple-900/40 border border-orange-500/20 rounded-xl text-white focus:outline-none focus:border-orange-400/40"
          />
        </div>
        
        <div className="flex space-x-4 mt-6">
          <button
            onClick={onClose}
            className="flex-1 px-4 py-3 bg-gray-700 text-gray-300 rounded-xl hover:bg-gray-600 transition-colors duration-200"
          >
            Cancel
          </button>
          <button
            onClick={handleSave}
            disabled={!title.trim()}
            className="flex-1 btn-gradient-aurora disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {task ? 'Update' : 'Create'}
          </button>
        </div>
      </div>
    </div>
  );
}
