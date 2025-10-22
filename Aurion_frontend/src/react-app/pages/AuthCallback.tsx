import { useEffect } from 'react';
import { useAuth } from '@getmocha/users-service/react';
import { useNavigate } from 'react-router';
import { Sparkles } from 'lucide-react';

export default function AuthCallback() {
  const { exchangeCodeForSessionToken } = useAuth();
  const navigate = useNavigate();

  useEffect(() => {
    const handleCallback = async () => {
      try {
        await exchangeCodeForSessionToken();
        navigate('/chat');
      } catch (error) {
        console.error('Authentication failed:', error);
        navigate('/');
      }
    };

    handleCallback();
  }, [exchangeCodeForSessionToken, navigate]);

  return (
    <div className="min-h-screen bg-gradient-to-br from-violet-900 via-purple-900/10 to-black flex items-center justify-center">
      <div className="text-center">
        <div className="relative mb-8">
          <Sparkles className="w-16 h-16 gradient-text-aurora animate-spin mx-auto" />
          <div className="absolute inset-0 animate-pulse">
            <Sparkles className="w-16 h-16 text-orange-400 opacity-30 mx-auto" />
          </div>
        </div>
        <h1 className="text-3xl font-bold gradient-text-aurora mb-4">
          Completing Authentication...
        </h1>
        <p className="text-gray-300 text-lg">
          Please wait while we securely log you in
        </p>
        <div className="flex justify-center mt-8">
          <div className="spinner-aurora"></div>
        </div>
      </div>
    </div>
  );
}
