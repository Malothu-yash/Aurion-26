import { useState, useEffect } from 'react';
import { useAuth } from '@/react-app/context/AuthContext';
import { useNavigate } from 'react-router';
import { 
  MessageCircle, 
  ArrowRight, 
  Play,
  Star,
  Users,
  LogIn
} from 'lucide-react';
import AuthModal from './AuthModal';

export default function HeroSection() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [typedText, setTypedText] = useState('');
  const [currentIndex, setCurrentIndex] = useState(0);
  const [isAuthModalOpen, setIsAuthModalOpen] = useState(false);
  const phrases = [
    'AI Chat Assistant',
    'Smart Conversations',
    'Intelligent Support',
    'Next-Gen AI'
  ];

  const handleAuthSuccess = (userData: any) => {
    console.log('✅ Authenticated user:', userData);
    // Auth context handles everything, just close modal
    setIsAuthModalOpen(false);
  };

  useEffect(() => {
    const currentPhrase = phrases[currentIndex];
    let charIndex = 0;
    let isDeleting = false;

    const typeWriter = setInterval(() => {
      if (!isDeleting && charIndex < currentPhrase.length) {
        setTypedText(currentPhrase.slice(0, charIndex + 1));
        charIndex++;
      } else if (isDeleting && charIndex > 0) {
        setTypedText(currentPhrase.slice(0, charIndex - 1));
        charIndex--;
      } else if (!isDeleting && charIndex === currentPhrase.length) {
        setTimeout(() => {
          isDeleting = true;
        }, 2000);
      } else if (isDeleting && charIndex === 0) {
        setCurrentIndex((prev) => (prev + 1) % phrases.length);
        isDeleting = false;
      }
    }, isDeleting ? 50 : 100);

    return () => clearInterval(typeWriter);
  }, [currentIndex]);

  return (
    <section id="home" className="relative min-h-screen flex items-center justify-center overflow-hidden">
      {/* Animated Background Elements */}
      <div className="absolute inset-0 overflow-hidden">
        <div className="floating-element top-20 left-10">
          <div className="floating-circle"></div>
        </div>
        <div className="floating-element top-40 right-20">
          <div className="floating-square"></div>
        </div>
        <div className="floating-element bottom-20 left-1/4">
          <div className="floating-circle" style={{ animationDelay: '2s' }}></div>
        </div>
        <div className="floating-element top-1/3 right-1/4">
          <div className="floating-square" style={{ animationDelay: '3s' }}></div>
        </div>
      </div>

      {/* Main Content */}
      <div className="relative z-10 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center mt-40">
        <div className="animate-fade-in-up">
          {/* Main Heading */}
          <h1 className="text-6xl md:text-7xl lg:text-8xl font-bold mb-8 leading-tight">
            <span className="block gradient-text mb-4">AURION</span>
            <span className="block text-white text-4xl md:text-5xl lg:text-6xl">Your Intelligent </span>
            <span className="gradient-text-secondary text-4xl md:text-5xl lg:text-6xl">
              {typedText}
              <span className="animate-pulse">|</span>
            </span>
          </h1>

          {/* Subtitle */}
          <p className="text-lg md:text-xl text-gray-300 mb-12 max-w-3xl mx-auto leading-relaxed">
            Powered by cutting-edge AI with multi-tier intelligence, autonomous task execution, 
            and seamless calendar integration. Your personal AI assistant that actually understands you.
          </p>

          {/* CTA Buttons */}
          <div className="flex flex-col sm:flex-row items-center justify-center gap-4 mb-16">
            {user ? (
              // If user is logged in, show "Open Chat" button
              <button 
                onClick={() => navigate('/chat')}
                className="group relative btn-gradient flex items-center space-x-3 text-lg px-8 py-4 animate-scale-in hover:scale-105 transition-all duration-300"
              >
                <MessageCircle className="w-5 h-5 group-hover:rotate-12 transition-transform" />
                <span>Open Chat</span>
                <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
              </button>
            ) : (
              // If user is not logged in, show "Get Started" and "Sign In" buttons
              <>
                <button 
                  onClick={() => setIsAuthModalOpen(true)}
                  className="group relative bg-gradient-to-r from-blue-600 via-purple-600 to-pink-600 hover:from-blue-500 hover:via-purple-500 hover:to-pink-500 text-white flex items-center space-x-2 px-8 py-4 rounded-xl font-semibold shadow-lg hover:shadow-2xl hover:shadow-purple-500/50 transition-all duration-300 hover:scale-105 animate-scale-in"
                >
                  <MessageCircle className="w-5 h-5 group-hover:rotate-12 transition-transform" />
                  <span>Get Started</span>
                  <ArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
                  <div className="absolute inset-0 rounded-xl bg-white/20 opacity-0 group-hover:opacity-100 transition-opacity blur-xl"></div>
                </button>
                
                <button 
                  onClick={() => setIsAuthModalOpen(true)}
                  className="group relative bg-gray-800/50 hover:bg-gray-700/70 border-2 border-gray-600 hover:border-purple-500 text-white flex items-center space-x-2 px-8 py-4 rounded-xl font-semibold backdrop-blur-sm transition-all duration-300 hover:scale-105 animate-scale-in"
                  style={{ animationDelay: '0.1s' }}
                >
                  <LogIn className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
                  <span>Sign In</span>
                </button>
              </>
            )}
            
            {/* Watch Demo Button */}
            <button 
              className="group relative bg-transparent border-2 border-gray-600 hover:border-blue-500 text-white flex items-center space-x-2 px-8 py-4 rounded-xl font-semibold backdrop-blur-sm transition-all duration-300 hover:scale-105 hover:bg-blue-500/10 animate-scale-in" 
              style={{ animationDelay: '0.2s' }}
            >
              <Play className="w-5 h-5 group-hover:scale-110 transition-transform" />
              <span>Watch Demo</span>
            </button>
          </div>

          {/* Stats */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8 max-w-4xl mx-auto">
            <div className="card-glass animate-fade-in-up" style={{ animationDelay: '0.3s' }}>
              <div className="flex items-center justify-center mb-4">
                <Users className="w-8 h-8 gradient-text" />
              </div>
              <div className="text-3xl font-bold gradient-text mb-2">10K+</div>
              <div className="text-gray-400">Active Users</div>
            </div>
            <div className="card-glass animate-fade-in-up" style={{ animationDelay: '0.4s' }}>
              <div className="flex items-center justify-center mb-4">
                <MessageCircle className="w-8 h-8 gradient-text-secondary" />
              </div>
              <div className="text-3xl font-bold gradient-text-secondary mb-2">1M+</div>
              <div className="text-gray-400">Conversations</div>
            </div>
            <div className="card-glass animate-fade-in-up" style={{ animationDelay: '0.5s' }}>
              <div className="flex items-center justify-center mb-4">
                <Star className="w-8 h-8 gradient-text-accent" />
              </div>
              <div className="text-3xl font-bold gradient-text-accent mb-2">4.9/5</div>
              <div className="text-gray-400">User Rating</div>
            </div>
          </div>
        </div>
      </div>

      {/* Scroll Indicator */}
      <div className="absolute bottom-8 left-1/2 transform -translate-x-1/2 animate-float">
        <div className="w-6 h-10 border-2 border-white/30 rounded-full flex justify-center">
          <div className="w-1 h-3 bg-white rounded-full mt-2 animate-pulse"></div>
        </div>
      </div>

      {/* Auth Modal */}
      <AuthModal 
        isOpen={isAuthModalOpen} 
        onClose={() => setIsAuthModalOpen(false)}
        onSuccess={handleAuthSuccess}
      />
    </section>
  );
}
