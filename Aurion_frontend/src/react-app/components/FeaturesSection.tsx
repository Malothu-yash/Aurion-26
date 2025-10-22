import { 
  Brain, 
  MessageSquare, 
  Zap, 
  Shield, 
  Smartphone, 
  Globe, 
  Clock, 
  Heart,
  Sparkles,
  Bot,
  Users,
  TrendingUp
} from 'lucide-react';

const features = [
  {
    icon: Brain,
    title: 'Advanced AI Intelligence',
    description: 'Powered by cutting-edge neural networks for human-like conversations',
    gradient: 'var(--primary-gradient)',
    delay: '0.1s'
  },
  {
    icon: MessageSquare,
    title: 'Natural Conversations',
    description: 'Chat naturally with context-aware responses and emotional intelligence',
    gradient: 'var(--secondary-gradient)',
    delay: '0.2s'
  },
  {
    icon: Zap,
    title: 'Lightning Fast',
    description: 'Get instant responses with our optimized AI processing engine',
    gradient: 'var(--accent-gradient)',
    delay: '0.3s'
  },
  {
    icon: Shield,
    title: 'Privacy First',
    description: 'Your conversations are encrypted and protected with enterprise-grade security',
    gradient: 'var(--purple-gradient)',
    delay: '0.4s'
  },
  {
    icon: Smartphone,
    title: 'Cross-Platform',
    description: 'Available on all devices with seamless synchronization across platforms',
    gradient: 'var(--dark-gradient)',
    delay: '0.5s'
  },
  {
    icon: Globe,
    title: 'Multilingual Support',
    description: 'Communicate in over 100 languages with real-time translation',
    gradient: 'var(--aurora-gradient)',
    delay: '0.6s'
  }
];

const stats = [
  { icon: Users, value: '500K+', label: 'Happy Users', color: 'text-blue-400' },
  { icon: MessageSquare, value: '10M+', label: 'Messages Sent', color: 'text-purple-400' },
  { icon: Clock, value: '99.9%', label: 'Uptime', color: 'text-green-400' },
  { icon: TrendingUp, value: '4.9/5', label: 'User Rating', color: 'text-pink-400' }
];

export default function FeaturesSection() {
  return (
    <section id="features" className="py-20 relative overflow-hidden">
      {/* Background Elements */}
      <div className="absolute inset-0 overflow-hidden opacity-10">
        <div className="absolute top-20 left-10 w-72 h-72 bg-gradient-to-br from-purple-400 to-pink-400 rounded-full blur-3xl"></div>
        <div className="absolute bottom-20 right-10 w-96 h-96 bg-gradient-to-br from-blue-400 to-cyan-400 rounded-full blur-3xl"></div>
      </div>

      <div className="relative z-10 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        {/* Section Header */}
        <div className="text-center mb-20">
          <div className="inline-flex items-center space-x-2 glass px-4 py-2 rounded-full mb-6">
            <Sparkles className="w-4 h-4 text-yellow-400 animate-pulse" />
            <span className="text-sm font-medium text-gray-300">Powerful Features</span>
          </div>
          
          <h2 className="text-4xl md:text-6xl font-bold mb-6">
            <span className="gradient-text">Everything You Need</span><br />
            <span className="text-white">in One AI Assistant</span>
          </h2>
          
          <p className="text-xl text-gray-300 max-w-3xl mx-auto leading-relaxed">
            Discover the capabilities that make Aurion the most advanced AI chat assistant. 
            Built for efficiency, designed for humans.
          </p>
        </div>

        {/* Features Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8 mb-20">
          {features.map((feature, index) => (
            <div
              key={index}
              className="card-glass hover:scale-105 transition-all duration-500 animate-fade-in-up group"
              style={{ animationDelay: feature.delay }}
            >
              <div className="relative mb-6">
                <div 
                  className="w-16 h-16 rounded-2xl flex items-center justify-center mb-4 group-hover:scale-110 transition-transform duration-300"
                  style={{ background: feature.gradient }}
                >
                  <feature.icon className="w-8 h-8 text-white" />
                </div>
                <div className="absolute inset-0 w-16 h-16 rounded-2xl opacity-30 blur-lg group-hover:opacity-50 transition-opacity duration-300" 
                     style={{ background: feature.gradient }}></div>
              </div>
              
              <h3 className="text-xl font-bold text-white mb-3 group-hover:gradient-text transition-all duration-300">
                {feature.title}
              </h3>
              
              <p className="text-gray-400 leading-relaxed group-hover:text-gray-300 transition-colors duration-300">
                {feature.description}
              </p>
              
              {/* Hover Effect */}
              <div className="absolute inset-0 rounded-2xl opacity-0 group-hover:opacity-10 transition-opacity duration-300"
                   style={{ background: feature.gradient }}></div>
            </div>
          ))}
        </div>

        {/* Stats Section */}
        <div className="glass-dark rounded-3xl p-8 md:p-12">
          <div className="text-center mb-12">
            <h3 className="text-3xl md:text-4xl font-bold gradient-text mb-4">
              Trusted by Thousands
            </h3>
            <p className="text-gray-300 text-lg">
              Join our growing community of satisfied users
            </p>
          </div>
          
          <div className="grid grid-cols-2 md:grid-cols-4 gap-8">
            {stats.map((stat, index) => (
              <div 
                key={index}
                className="text-center animate-fade-in-up"
                style={{ animationDelay: `${0.7 + index * 0.1}s` }}
              >
                <div className="flex items-center justify-center mb-4">
                  <stat.icon className={`w-8 h-8 ${stat.color} animate-pulse`} />
                </div>
                <div className="text-3xl md:text-4xl font-bold text-white mb-2 animate-glow">
                  {stat.value}
                </div>
                <div className="text-gray-400 text-sm md:text-base">
                  {stat.label}
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* CTA Section */}
        <div className="text-center mt-20">
          <div className="inline-block p-8 glass rounded-3xl animate-scale-in">
            <Bot className="w-16 h-16 gradient-text mx-auto mb-6 animate-float" />
            <h3 className="text-2xl md:text-3xl font-bold text-white mb-4">
              Ready to Experience the Future?
            </h3>
            <p className="text-gray-300 mb-8 max-w-2xl">
              Join thousands of users who are already enjoying smarter conversations with Aurion.
            </p>
            <button className="btn-gradient-secondary text-lg px-8 py-4 hover:scale-105 transition-transform duration-300">
              <span className="flex items-center space-x-2">
                <Heart className="w-5 h-5" />
                <span>Start Your Journey</span>
              </span>
            </button>
          </div>
        </div>
      </div>
    </section>
  );
}
