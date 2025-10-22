import React from 'react';

interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
}

interface ErrorBoundaryProps {
  children: React.ReactNode;
  fallback?: React.ComponentType<{ error: Error; retry: () => void }>;
}

class MiniAgentErrorBoundary extends React.Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = { hasError: false, error: null };
  }
  
  static getDerivedStateFromError(error: Error): ErrorBoundaryState {
    return { hasError: true, error };
  }
  
  componentDidCatch(error: Error, errorInfo: React.ErrorInfo) {
    console.error('Mini Agent Error:', error, errorInfo);
    // Send to error tracking service if available
    if (typeof window !== 'undefined' && (window as any).gtag) {
      (window as any).gtag('event', 'exception', {
        description: error.message,
        fatal: false
      });
    }
  }
  
  render() {
    if (this.state.hasError) {
      const FallbackComponent = this.props.fallback || DefaultErrorFallback;
      return (
        <FallbackComponent 
          error={this.state.error!} 
          retry={() => this.setState({ hasError: false, error: null })}
        />
      );
    }
    
    return this.props.children;
  }
}

const DefaultErrorFallback: React.FC<{ error: Error; retry: () => void }> = ({ error, retry }) => (
  <div className="mini-agent-error p-4 bg-red-50 border border-red-200 rounded-lg m-2">
    <h3 className="text-red-800 font-semibold text-sm">Mini Agent Error</h3>
    <p className="text-red-600 mt-2 text-xs">Something went wrong with the Mini Agent.</p>
    <button 
      onClick={retry}
      className="mt-3 px-3 py-1 bg-red-600 text-white rounded text-xs hover:bg-red-700 transition-colors"
    >
      Retry
    </button>
  </div>
);

export default MiniAgentErrorBoundary;
