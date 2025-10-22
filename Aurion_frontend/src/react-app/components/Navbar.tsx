import { useState, useEffect } from 'react';
import { useAuth } from '@/react-app/context/AuthContext';
import { useNavigate } from 'react-router';
import { Menu, X, Sparkles, MessageCircle, LogIn, UserPlus } from 'lucide-react';
import AuthModal from './AuthModal';

export default function Navbar() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [isMenuOpen, setIsMenuOpen] = useState(false);
  const [isScrolled, setIsScrolled] = useState(false);
  const [isAuthModalOpen, setIsAuthModalOpen] = useState(false);

  useEffect(() => {
    const handleScroll = () => {
      setIsScrolled(window.scrollY > 20);
    };

    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  const toggleMenu = () => {
    setIsMenuOpen(!isMenuOpen);
  };

  const handleAuthSuccess = (userData: any) => {
    console.log('✅ Authenticated user:', userData);
    // Auth context already handles storage and navigation
    setIsAuthModalOpen(false);
  };

  return (
    <nav className={`fixed top-0 w-full z-50 transition-all duration-300 ${
      isScrolled ? 'glass-dark shadow-lg' : 'bg-transparent'
    }`}>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          {/* Logo */}
          <div className="flex items-center space-x-3 animate-fade-in-left">
            <div className="relative">
              <Sparkles className="w-8 h-8 gradient-text animate-glow" />
              <div className="absolute inset-0 animate-pulse">
                <Sparkles className="w-8 h-8 text-purple-400 opacity-30" />
              </div>
            </div>
            <span className="text-2xl font-bold gradient-text">Aurion</span>
          </div>

          {/* Desktop Navigation */}
          <div className="hidden md:block">
            <div className="flex items-center space-x-8">
              <a href="#home" className="text-gray-300 hover:text-white transition-colors duration-300 hover:underline decoration-purple-400">
                Home
              </a>
              <a href="#features" className="text-gray-300 hover:text-white transition-colors duration-300 hover:underline decoration-blue-400">
                Features
              </a>
              <a href="#about" className="text-gray-300 hover:text-white transition-colors duration-300 hover:underline decoration-pink-400">
                About
              </a>
              <a href="#pricing" className="text-gray-300 hover:text-white transition-colors duration-300 hover:underline decoration-green-400">
                Pricing
              </a>
              {user ? (
                <button 
                  onClick={() => navigate('/chat')}
                  className="group relative bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-500 hover:to-blue-500 text-white flex items-center space-x-2 px-6 py-2.5 rounded-lg font-semibold shadow-lg hover:shadow-purple-500/50 transition-all duration-300 hover:scale-105"
                >
                  <MessageCircle className="w-4 h-4 group-hover:rotate-12 transition-transform" />
                  <span>Open Chat</span>
                </button>
              ) : (
                <>
                  <button 
                    onClick={() => setIsAuthModalOpen(true)}
                    className="group relative text-gray-300 hover:text-white flex items-center space-x-2 px-5 py-2.5 rounded-xl font-medium border-2 border-gray-600 hover:border-purple-500 bg-gray-800/50 hover:bg-gray-700/70 backdrop-blur-sm transition-all duration-300 hover:scale-105"
                  >
                    <LogIn className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
                    <span>Login</span>
                  </button>
                  <button 
                    onClick={() => setIsAuthModalOpen(true)}
                    className="group relative bg-gradient-to-r from-blue-600 via-purple-600 to-pink-600 hover:from-blue-500 hover:via-purple-500 hover:to-pink-500 text-white flex items-center space-x-2 px-6 py-2.5 rounded-xl font-semibold shadow-lg hover:shadow-2xl hover:shadow-purple-500/50 transition-all duration-300 hover:scale-105"
                  >
                    <UserPlus className="w-4 h-4 group-hover:scale-110 transition-transform" />
                    <span>Sign Up</span>
                    <div className="absolute inset-0 rounded-xl bg-white/20 opacity-0 group-hover:opacity-100 transition-opacity blur-xl"></div>
                  </button>
                </>
              )}
            </div>
          </div>

          {/* Mobile menu button */}
          <div className="md:hidden">
            <button
              onClick={toggleMenu}
              className="text-gray-300 hover:text-white p-2 rounded-lg transition-colors duration-200"
            >
              {isMenuOpen ? (
                <X className="w-6 h-6" />
              ) : (
                <Menu className="w-6 h-6" />
              )}
            </button>
          </div>
        </div>
      </div>

      {/* Mobile Navigation */}
      {isMenuOpen && (
        <div className="md:hidden animate-fade-in-down">
          <div className="glass-dark mx-4 my-2 rounded-2xl border border-white/10">
            <div className="px-6 py-4 space-y-4">
              <a href="#home" className="block text-gray-300 hover:text-white transition-colors duration-300 py-2">
                Home
              </a>
              <a href="#features" className="block text-gray-300 hover:text-white transition-colors duration-300 py-2">
                Features
              </a>
              <a href="#about" className="block text-gray-300 hover:text-white transition-colors duration-300 py-2">
                About
              </a>
              <a href="#pricing" className="block text-gray-300 hover:text-white transition-colors duration-300 py-2">
                Pricing
              </a>
              <div className="pt-4 space-y-3">
                {user ? (
                  <button 
                    onClick={() => {
                      navigate('/chat');
                      setIsMenuOpen(false);
                    }}
                    className="group w-full bg-gradient-to-r from-purple-600 to-blue-600 hover:from-purple-500 hover:to-blue-500 text-white flex items-center justify-center space-x-2 px-6 py-3 rounded-lg font-semibold shadow-lg transition-all duration-300"
                  >
                    <MessageCircle className="w-4 h-4 group-hover:rotate-12 transition-transform" />
                    <span>Open Chat</span>
                  </button>
                ) : (
                  <>
                    <button 
                      onClick={() => {
                        setIsAuthModalOpen(true);
                        setIsMenuOpen(false);
                      }}
                      className="group w-full text-white flex items-center justify-center space-x-2 px-6 py-3 rounded-xl font-medium border-2 border-gray-600 hover:border-purple-500 bg-gray-800/50 hover:bg-gray-700/70 backdrop-blur-sm transition-all duration-300"
                    >
                      <LogIn className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
                      <span>Login</span>
                    </button>
                    <button 
                      onClick={() => {
                        setIsAuthModalOpen(true);
                        setIsMenuOpen(false);
                      }}
                      className="group relative w-full bg-gradient-to-r from-blue-600 via-purple-600 to-pink-600 hover:from-blue-500 hover:via-purple-500 hover:to-pink-500 text-white flex items-center justify-center space-x-2 px-6 py-3 rounded-xl font-semibold shadow-lg hover:shadow-2xl hover:shadow-purple-500/50 transition-all duration-300"
                    >
                      <UserPlus className="w-4 h-4 group-hover:scale-110 transition-transform" />
                      <span>Sign Up</span>
                      <div className="absolute inset-0 rounded-xl bg-white/20 opacity-0 group-hover:opacity-100 transition-opacity blur-xl"></div>
                    </button>
                  </>
                )}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Auth Modal */}
      <AuthModal 
        isOpen={isAuthModalOpen} 
        onClose={() => setIsAuthModalOpen(false)}
        onSuccess={handleAuthSuccess}
      />
    </nav>
  );
}
