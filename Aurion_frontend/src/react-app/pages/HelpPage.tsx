import { useState } from 'react';
import { useAuth } from '@/react-app/context/AuthContext';
import { useNavigate } from 'react-router';
import Sidebar from '@/react-app/components/Sidebar';
import { 
  HelpCircle, 
  Search, 
  MessageCircle, 
  FileText, 
  Video, 
  Mail,
  ChevronDown,
  ChevronRight,
  Sparkles,
  Book,
  Zap,
  Users,
  ExternalLink
} from 'lucide-react';

const faqData = [
  {
    category: 'Getting Started',
    icon: Sparkles,
    questions: [
      {
        question: 'How do I start a new chat with Aurion?',
        answer: 'Click the "New Chat" button in the sidebar or navigate to the chat page. You can also use the quick action buttons on the welcome screen to get started with specific topics.'
      },
      {
        question: 'Can I upload files to Aurion?',
        answer: 'Yes! Click the "+" button in the chat input area to upload images, documents, or other files. Aurion can analyze and discuss the content of your uploads.'
      },
      {
        question: 'How do I save my conversations?',
        answer: 'Conversations are automatically saved. You can also manually save specific conversations by clicking the save icon in the chat options menu.'
      }
    ]
  },
  {
    category: 'Features',
    icon: Zap,
    questions: [
      {
        question: 'What is the highlighting feature?',
        answer: 'Select any text in Aurion\'s responses to highlight it with different colors. This helps you organize and reference important information across conversations.'
      },
      {
        question: 'How does the Mini Agent work?',
        answer: 'Select text in any response and click the Mini Agent icon to ask follow-up questions about that specific content without affecting your main conversation.'
      },
      {
        question: 'Can I edit my messages after sending?',
        answer: 'Yes, hover over your messages to see the edit option. This allows you to refine your questions and get better responses.'
      }
    ]
  },
  {
    category: 'Tasks & Organization',
    icon: FileText,
    questions: [
      {
        question: 'How do I create and manage tasks?',
        answer: 'Use the Tasks page to create, organize, and track your tasks. You can set priorities, due dates, and mark tasks as complete.'
      },
      {
        question: 'Can I organize my chat history?',
        answer: 'Yes, use the History section in the sidebar to view recent and saved conversations. You can rename, pin, and organize your chats.'
      },
      {
        question: 'What are the different task priorities?',
        answer: 'Tasks can be set to Low, Medium, or High priority. High priority tasks are marked with a red flag for easy identification.'
      }
    ]
  },
  {
    category: 'Privacy & Security',
    icon: Users,
    questions: [
      {
        question: 'Is my data secure with Aurion?',
        answer: 'Yes, all your conversations and data are encrypted and stored securely. We follow industry-standard security practices to protect your information.'
      },
      {
        question: 'Can I delete my conversation history?',
        answer: 'Yes, you can delete individual conversations or bulk delete from the History section. You can also manage memory types in your Profile settings.'
      },
      {
        question: 'How long is my data retained?',
        answer: 'You can configure data retention settings in your Settings page. Options range from 1 month to forever, giving you full control over your data.'
      }
    ]
  }
];

const resourceLinks = [
  {
    title: 'User Guide',
    description: 'Comprehensive guide to using Aurion',
    icon: Book,
    url: '#'
  },
  {
    title: 'Video Tutorials',
    description: 'Watch step-by-step video guides',
    icon: Video,
    url: '#'
  },
  {
    title: 'Community Forum',
    description: 'Connect with other Aurion users',
    icon: Users,
    url: '#'
  },
  {
    title: 'API Documentation',
    description: 'Developer resources and API docs',
    icon: FileText,
    url: '#'
  }
];

export default function HelpPage() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [searchTerm, setSearchTerm] = useState('');
  const [expandedCategories, setExpandedCategories] = useState<Set<string>>(new Set(['Getting Started']));
  const [expandedQuestions, setExpandedQuestions] = useState<Set<string>>(new Set());

  if (!user) {
    navigate('/');
    return null;
  }

  const toggleCategory = (category: string) => {
    const newExpanded = new Set(expandedCategories);
    if (newExpanded.has(category)) {
      newExpanded.delete(category);
    } else {
      newExpanded.add(category);
    }
    setExpandedCategories(newExpanded);
  };

  const toggleQuestion = (questionId: string) => {
    const newExpanded = new Set(expandedQuestions);
    if (newExpanded.has(questionId)) {
      newExpanded.delete(questionId);
    } else {
      newExpanded.add(questionId);
    }
    setExpandedQuestions(newExpanded);
  };

  const filteredFAQ = faqData.map(category => ({
    ...category,
    questions: category.questions.filter(q => 
      q.question.toLowerCase().includes(searchTerm.toLowerCase()) ||
      q.answer.toLowerCase().includes(searchTerm.toLowerCase())
    )
  })).filter(category => category.questions.length > 0);

  return (
    <div className="h-screen bg-gradient-to-br from-violet-950/20 via-purple-950/10 to-black flex">
      <Sidebar />
      
      <div className="flex-1 overflow-y-auto">
        {/* Header */}
        <div className="h-16 border-b border-orange-500/20 flex items-center px-6">
          <div className="flex items-center space-x-3">
            <HelpCircle className="w-6 h-6 gradient-text-aurora" />
            <h1 className="text-xl font-semibold text-white">Help & Support</h1>
          </div>
        </div>

        <div className="max-w-4xl mx-auto p-6 space-y-8">
          {/* Welcome Section */}
          <div className="glass-aurora rounded-2xl p-8 text-center">
            <Sparkles className="w-16 h-16 gradient-text-aurora animate-glow mx-auto mb-4" />
            <h2 className="text-3xl font-bold text-white mb-4">How can we help you?</h2>
            <p className="text-gray-300 text-lg mb-6">
              Find answers to common questions or get in touch with our support team
            </p>
            
            {/* Search */}
            <div className="relative max-w-md mx-auto">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
              <input
                type="text"
                placeholder="Search for help..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full pl-10 pr-4 py-3 bg-purple-900/40 border border-orange-500/20 rounded-xl text-white placeholder-gray-400 focus:outline-none focus:border-orange-400/40 transition-colors duration-200"
              />
            </div>
          </div>

          {/* Quick Actions */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {resourceLinks.map((resource, index) => (
              <a
                key={index}
                href={resource.url}
                className="group glass-aurora rounded-xl p-6 hover:scale-105 transition-all duration-300 text-center"
              >
                <resource.icon className="w-8 h-8 text-orange-400 mx-auto mb-3 group-hover:scale-110 transition-transform duration-300" />
                <h3 className="font-semibold text-white mb-2 group-hover:gradient-text-aurora transition-all duration-300">
                  {resource.title}
                </h3>
                <p className="text-gray-400 text-sm group-hover:text-gray-300 transition-colors duration-300">
                  {resource.description}
                </p>
                <ExternalLink className="w-4 h-4 text-gray-500 mx-auto mt-2 opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
              </a>
            ))}
          </div>

          {/* FAQ Section */}
          <div className="glass-aurora rounded-2xl p-8">
            <h2 className="text-2xl font-bold text-white mb-6 flex items-center space-x-3">
              <MessageCircle className="w-6 h-6 text-blue-400" />
              <span>Frequently Asked Questions</span>
            </h2>

            <div className="space-y-4">
              {filteredFAQ.map((category, categoryIndex) => (
                <div key={categoryIndex} className="border border-orange-500/20 rounded-xl overflow-hidden">
                  <button
                    onClick={() => toggleCategory(category.category)}
                    className="w-full flex items-center justify-between p-4 bg-purple-900/20 hover:bg-purple-900/40 transition-colors duration-200"
                  >
                    <div className="flex items-center space-x-3">
                      <category.icon className="w-5 h-5 text-orange-400" />
                      <span className="font-semibold text-white">{category.category}</span>
                      <span className="text-sm text-gray-400">({category.questions.length})</span>
                    </div>
                    {expandedCategories.has(category.category) ? (
                      <ChevronDown className="w-5 h-5 text-gray-400" />
                    ) : (
                      <ChevronRight className="w-5 h-5 text-gray-400" />
                    )}
                  </button>

                  {expandedCategories.has(category.category) && (
                    <div className="bg-purple-900/10">
                      {category.questions.map((faq, questionIndex) => {
                        const questionId = `${categoryIndex}-${questionIndex}`;
                        return (
                          <div key={questionIndex} className="border-t border-orange-500/10">
                            <button
                              onClick={() => toggleQuestion(questionId)}
                              className="w-full text-left p-4 hover:bg-purple-900/20 transition-colors duration-200"
                            >
                              <div className="flex items-center justify-between">
                                <span className="font-medium text-white">{faq.question}</span>
                                {expandedQuestions.has(questionId) ? (
                                  <ChevronDown className="w-4 h-4 text-gray-400 flex-shrink-0 ml-2" />
                                ) : (
                                  <ChevronRight className="w-4 h-4 text-gray-400 flex-shrink-0 ml-2" />
                                )}
                              </div>
                            </button>
                            
                            {expandedQuestions.has(questionId) && (
                              <div className="px-4 pb-4">
                                <p className="text-gray-300 leading-relaxed">{faq.answer}</p>
                              </div>
                            )}
                          </div>
                        );
                      })}
                    </div>
                  )}
                </div>
              ))}
            </div>

            {filteredFAQ.length === 0 && searchTerm && (
              <div className="text-center py-8">
                <Search className="w-12 h-12 text-gray-600 mx-auto mb-4" />
                <h3 className="text-lg font-semibold text-gray-400 mb-2">No results found</h3>
                <p className="text-gray-500">Try searching with different keywords</p>
              </div>
            )}
          </div>

          {/* Contact Support */}
          <div className="glass-aurora rounded-2xl p-8">
            <h2 className="text-2xl font-bold text-white mb-6 flex items-center space-x-3">
              <Mail className="w-6 h-6 text-green-400" />
              <span>Still need help?</span>
            </h2>
            
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div className="text-center p-6 bg-purple-900/20 rounded-xl">
                <Mail className="w-8 h-8 text-blue-400 mx-auto mb-3" />
                <h3 className="font-semibold text-white mb-2">Email Support</h3>
                <p className="text-gray-400 text-sm mb-4">Get help via email</p>
                <a 
                  href="mailto:support@aurion.app"
                  className="btn-gradient-aurora inline-block"
                >
                  Contact Support
                </a>
              </div>
              
              <div className="text-center p-6 bg-purple-900/20 rounded-xl">
                <MessageCircle className="w-8 h-8 text-green-400 mx-auto mb-3" />
                <h3 className="font-semibold text-white mb-2">Live Chat</h3>
                <p className="text-gray-400 text-sm mb-4">Chat with our team</p>
                <button className="btn-gradient-aurora">
                  Start Chat
                </button>
              </div>
              
              <div className="text-center p-6 bg-purple-900/20 rounded-xl">
                <Users className="w-8 h-8 text-purple-400 mx-auto mb-3" />
                <h3 className="font-semibold text-white mb-2">Community</h3>
                <p className="text-gray-400 text-sm mb-4">Join our community</p>
                <button className="btn-gradient-aurora">
                  Join Forum
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
