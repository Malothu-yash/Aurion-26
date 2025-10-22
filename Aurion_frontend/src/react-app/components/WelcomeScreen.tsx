import { useState } from 'react';
import { 
  Sparkles, 
  MessageSquare, 
  Code, 
  FileText, 
  Image, 
  Brain, 
  Zap, 
  Coffee,
  Lightbulb,
  BookOpen,
  Target
} from 'lucide-react';

interface WelcomeScreenProps {
  onSendMessage: (message: string) => void;
}

const welcomeQuotes = [
  "The best way to predict the future is to create it.",
  "Intelligence is the ability to adapt to change.",
  "Innovation distinguishes between a leader and a follower.",
  "The only way to do great work is to love what you do.",
  "Creativity is intelligence having fun."
];

const quickActions = [
  {
    icon: MessageSquare,
    title: "Chat & Conversation",
    description: "Have natural conversations on any topic",
    gradient: "from-purple-500 to-violet-600",
    prompt: "Let's have a conversation about something interesting!"
  },
  {
    icon: Code,
    title: "Code & Development",
    description: "Get help with programming and technical questions",
    gradient: "from-orange-500 to-red-500",
    prompt: "I need help with coding. Can you assist me with programming?"
  },
  {
    icon: FileText,
    title: "Writing & Content",
    description: "Create, edit, and improve your written content",
    gradient: "from-green-500 to-emerald-600",
    prompt: "Help me write something creative and engaging."
  },
  {
    icon: Image,
    title: "Creative Projects",
    description: "Brainstorm ideas and creative solutions",
    gradient: "from-pink-500 to-rose-600",
    prompt: "I want to work on a creative project. Let's brainstorm ideas!"
  },
  {
    icon: Brain,
    title: "Learning & Education",
    description: "Learn new concepts and deepen understanding",
    gradient: "from-blue-500 to-cyan-600",
    prompt: "I'd like to learn something new today. What would you recommend?"
  },
  {
    icon: Target,
    title: "Problem Solving",
    description: "Analyze problems and find effective solutions",
    gradient: "from-indigo-500 to-purple-600",
    prompt: "I have a problem I need to solve. Can you help me think through it?"
  }
];

export default function WelcomeScreen({ onSendMessage }: WelcomeScreenProps) {
  const [selectedQuote] = useState(() => 
    welcomeQuotes[Math.floor(Math.random() * welcomeQuotes.length)]
  );

  return (
    <div className="max-w-4xl mx-auto text-center space-y-12 animate-fade-in-up">
      {/* Welcome Header */}
      <div className="space-y-6">
        <div className="relative mb-8">
          <Sparkles className="w-20 h-20 gradient-text-aurora animate-glow mx-auto" />
          <div className="absolute inset-0 animate-pulse">
            <Sparkles className="w-20 h-20 text-orange-400 opacity-30 mx-auto" />
          </div>
        </div>
        
        <h1 className="text-5xl font-bold mb-4">
          <span className="gradient-text-aurora">Welcome to Aurion</span>
        </h1>
        
        <p className="text-2xl text-gray-300 mb-8 max-w-3xl mx-auto leading-relaxed">
          Your next-generation AI assistant is ready to help you with anything you need
        </p>

        {/* Inspirational Quote */}
        <div className="glass-aurora rounded-2xl p-6 max-w-2xl mx-auto">
          <div className="flex items-center justify-center mb-4">
            <Lightbulb className="w-6 h-6 text-orange-400 animate-pulse" />
          </div>
          <blockquote className="text-lg italic text-gray-200 font-medium">
            "{selectedQuote}"
          </blockquote>
        </div>
      </div>

      {/* Quick Actions Grid */}
      <div className="space-y-6">
        <h2 className="text-2xl font-semibold text-white mb-8 flex items-center justify-center space-x-2">
          <Zap className="w-6 h-6 text-orange-400" />
          <span>What can I help you with today?</span>
        </h2>
        
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {quickActions.map((action, index) => (
            <button
              key={index}
              onClick={() => onSendMessage(action.prompt)}
              className="group p-6 glass-aurora rounded-2xl hover:scale-105 transition-all duration-300 text-left hover:shadow-aurora"
              style={{ animationDelay: `${index * 0.1}s` }}
            >
              <div className={`w-12 h-12 rounded-xl bg-gradient-to-br ${action.gradient} flex items-center justify-center mb-4 group-hover:scale-110 transition-transform duration-300`}>
                <action.icon className="w-6 h-6 text-white" />
              </div>
              
              <h3 className="text-lg font-semibold text-white mb-2 group-hover:gradient-text-aurora transition-all duration-300">
                {action.title}
              </h3>
              
              <p className="text-gray-400 text-sm leading-relaxed group-hover:text-gray-300 transition-colors duration-300">
                {action.description}
              </p>
              
              <div className="mt-4 flex items-center text-orange-400 text-sm font-medium opacity-0 group-hover:opacity-100 transition-opacity duration-300">
                <span>Get started</span>
                <Sparkles className="w-4 h-4 ml-2" />
              </div>
            </button>
          ))}
        </div>
      </div>

      {/* Additional Features */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mt-12">
        <div className="glass-aurora rounded-xl p-6 text-center">
          <Coffee className="w-8 h-8 text-orange-400 mx-auto mb-3" />
          <h3 className="font-semibold text-white mb-2">Always Available</h3>
          <p className="text-gray-400 text-sm">24/7 assistance whenever you need it</p>
        </div>
        
        <div className="glass-aurora rounded-xl p-6 text-center">
          <Brain className="w-8 h-8 text-purple-400 mx-auto mb-3" />
          <h3 className="font-semibold text-white mb-2">Smart & Adaptive</h3>
          <p className="text-gray-400 text-sm">Learns from context to provide better help</p>
        </div>
        
        <div className="glass-aurora rounded-xl p-6 text-center">
          <BookOpen className="w-8 h-8 text-green-400 mx-auto mb-3" />
          <h3 className="font-semibold text-white mb-2">Comprehensive Knowledge</h3>
          <p className="text-gray-400 text-sm">Access to vast information across all domains</p>
        </div>
      </div>

      {/* Tips */}
      <div className="text-center text-gray-400 text-sm space-y-2">
        <p>💡 <strong>Pro tip:</strong> Be specific with your questions for the best results</p>
        <p>🎯 You can ask me to explain, create, analyze, or help with almost anything</p>
        <p>✨ Try starting with "Help me..." or "Can you explain..." for guided assistance</p>
      </div>
    </div>
  );
}
