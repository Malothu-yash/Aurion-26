import { useState, useEffect } from 'react';
import { Volume2, VolumeX, Play, Pause, RotateCcw, Settings, Mic } from 'lucide-react';

interface SpeakerFeatureProps {
  text: string;
  onStart?: () => void;
  onEnd?: () => void;
  onError?: (error: string) => void;
}

export function SpeakerFeature({ text, onStart, onEnd, onError }: SpeakerFeatureProps) {
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [isPaused, setIsPaused] = useState(false);
  const [isSupported, setIsSupported] = useState(false);
  const [currentUtterance, setCurrentUtterance] = useState<SpeechSynthesisUtterance | null>(null);
  const [showVoiceOptions, setShowVoiceOptions] = useState(false);
  const [voices, setVoices] = useState<SpeechSynthesisVoice[]>([]);
  const [selectedVoice, setSelectedVoice] = useState<SpeechSynthesisVoice | null>(null);
  const [speechRate, setSpeechRate] = useState(0.9);
  const [speechPitch, setSpeechPitch] = useState(1);
  const [speechVolume, setSpeechVolume] = useState(0.8);

  useEffect(() => {
    // Check if speech synthesis is supported
    setIsSupported('speechSynthesis' in window);
    
    if ('speechSynthesis' in window) {
      // Load available voices
      const loadVoices = () => {
        const availableVoices = window.speechSynthesis.getVoices();
        setVoices(availableVoices);
        
        // Set default voice (prefer English voices)
        const englishVoice = availableVoices.find(voice => 
          voice.lang.startsWith('en') && voice.default
        ) || availableVoices.find(voice => voice.lang.startsWith('en')) || availableVoices[0];
        
        setSelectedVoice(englishVoice);
      };
      
      loadVoices();
      
      // Some browsers load voices asynchronously
      if (window.speechSynthesis.onvoiceschanged !== undefined) {
        window.speechSynthesis.onvoiceschanged = loadVoices;
      }
    }
  }, []);

  useEffect(() => {
    // Clean up on unmount
    return () => {
      if (currentUtterance) {
        window.speechSynthesis.cancel();
      }
    };
  }, [currentUtterance]);

  const speak = () => {
    if (!isSupported || !text.trim()) return;

    // Cancel any existing speech
    window.speechSynthesis.cancel();

    const utterance = new SpeechSynthesisUtterance(text);
    
    // Configure voice settings
    utterance.rate = speechRate;
    utterance.pitch = speechPitch;
    utterance.volume = speechVolume;
    
    // Set voice if available
    if (selectedVoice) {
      utterance.voice = selectedVoice;
    }

    // Set up event handlers
    utterance.onstart = () => {
      setIsSpeaking(true);
      setIsPaused(false);
      onStart?.();
    };

    utterance.onend = () => {
      setIsSpeaking(false);
      setIsPaused(false);
      setCurrentUtterance(null);
      onEnd?.();
    };

    utterance.onerror = (event) => {
      setIsSpeaking(false);
      setIsPaused(false);
      setCurrentUtterance(null);
      onError?.(`Speech synthesis error: ${event.error}`);
    };

    utterance.onpause = () => {
      setIsPaused(true);
    };

    utterance.onresume = () => {
      setIsPaused(false);
    };

    setCurrentUtterance(utterance);
    window.speechSynthesis.speak(utterance);
  };

  const pause = () => {
    if (isSpeaking && !isPaused) {
      window.speechSynthesis.pause();
    }
  };

  const resume = () => {
    if (isSpeaking && isPaused) {
      window.speechSynthesis.resume();
    }
  };

  const stop = () => {
    window.speechSynthesis.cancel();
    setIsSpeaking(false);
    setIsPaused(false);
    setCurrentUtterance(null);
  };

  if (!isSupported) {
    return (
      <div className="flex items-center space-x-2 text-gray-500">
        <VolumeX className="w-4 h-4" />
        <span className="text-xs">Speech not supported</span>
      </div>
    );
  }

  return (
    <div className="flex items-center space-x-2">
      {!isSpeaking ? (
        <div className="flex items-center space-x-1">
          <button
            onClick={speak}
            className="p-2 rounded-lg hover:bg-green-900/30 transition-all duration-200 text-green-400 hover:text-green-300 group"
            title="Read aloud"
          >
            <Volume2 className="w-4 h-4 group-hover:scale-110 transition-transform duration-200" />
          </button>
          
          {/* Voice Settings Button */}
          <div className="relative">
            <button
              onClick={() => setShowVoiceOptions(!showVoiceOptions)}
              className="p-1 rounded-lg hover:bg-green-900/30 transition-all duration-200 text-green-400 hover:text-green-300"
              title="Voice settings"
            >
              <Settings className="w-3 h-3" />
            </button>
            
            {/* Voice Options Panel */}
            {showVoiceOptions && (
              <div className="absolute bottom-full right-0 mb-2 bg-purple-950/95 backdrop-blur-lg border border-orange-500/30 rounded-xl shadow-2xl p-3 animate-fade-in-up min-w-64">
                <div className="flex items-center space-x-2 mb-3">
                  <Mic className="w-4 h-4 text-green-400" />
                  <span className="text-sm font-medium text-white">Voice Settings</span>
                </div>
                
                {/* Voice Selection */}
                <div className="mb-3">
                  <label className="text-xs text-gray-400 mb-1 block">Voice</label>
                  <select
                    value={selectedVoice?.name || ''}
                    onChange={(e) => {
                      const voice = voices.find(v => v.name === e.target.value);
                      setSelectedVoice(voice || null);
                    }}
                    className="w-full bg-purple-900/50 border border-orange-500/30 rounded-lg px-2 py-1 text-white text-sm focus:outline-none focus:border-orange-400/60"
                  >
                    {voices.map((voice) => (
                      <option key={voice.name} value={voice.name}>
                        {voice.name} ({voice.lang})
                      </option>
                    ))}
                  </select>
                </div>
                
                {/* Rate Control */}
                <div className="mb-3">
                  <label className="text-xs text-gray-400 mb-1 block">Speed: {speechRate.toFixed(1)}x</label>
                  <input
                    type="range"
                    min="0.5"
                    max="2"
                    step="0.1"
                    value={speechRate}
                    onChange={(e) => setSpeechRate(parseFloat(e.target.value))}
                    className="w-full"
                  />
                </div>
                
                {/* Pitch Control */}
                <div className="mb-3">
                  <label className="text-xs text-gray-400 mb-1 block">Pitch: {speechPitch.toFixed(1)}</label>
                  <input
                    type="range"
                    min="0.5"
                    max="2"
                    step="0.1"
                    value={speechPitch}
                    onChange={(e) => setSpeechPitch(parseFloat(e.target.value))}
                    className="w-full"
                  />
                </div>
                
                {/* Volume Control */}
                <div>
                  <label className="text-xs text-gray-400 mb-1 block">Volume: {Math.round(speechVolume * 100)}%</label>
                  <input
                    type="range"
                    min="0"
                    max="1"
                    step="0.1"
                    value={speechVolume}
                    onChange={(e) => setSpeechVolume(parseFloat(e.target.value))}
                    className="w-full"
                  />
                </div>
              </div>
            )}
          </div>
        </div>
      ) : (
        <div className="flex items-center space-x-1">
          {isPaused ? (
            <button
              onClick={resume}
              className="p-1 rounded-lg hover:bg-green-900/30 transition-all duration-200 text-green-400 hover:text-green-300"
              title="Resume"
            >
              <Play className="w-3 h-3" />
            </button>
          ) : (
            <button
              onClick={pause}
              className="p-1 rounded-lg hover:bg-green-900/30 transition-all duration-200 text-green-400 hover:text-green-300"
              title="Pause"
            >
              <Pause className="w-3 h-3" />
            </button>
          )}
          <button
            onClick={stop}
            className="p-1 rounded-lg hover:bg-red-900/30 transition-all duration-200 text-red-400 hover:text-red-300"
            title="Stop"
          >
            <RotateCcw className="w-3 h-3" />
          </button>
        </div>
      )}

      {/* Speaking indicator */}
      {isSpeaking && (
        <div className="flex items-center space-x-1 text-green-400">
          <div className="w-2 h-2 bg-green-400 rounded-full animate-pulse" />
          <span className="text-xs">Speaking...</span>
        </div>
      )}
    </div>
  );
}

interface SpeakerButtonProps {
  text: string;
  className?: string;
  size?: 'sm' | 'md' | 'lg';
}

export function SpeakerButton({ text, className = '', size = 'md' }: SpeakerButtonProps) {
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [isSupported, setIsSupported] = useState(false);
  const [selectedVoice, setSelectedVoice] = useState<SpeechSynthesisVoice | null>(null);

  useEffect(() => {
    setIsSupported('speechSynthesis' in window);
    
    if ('speechSynthesis' in window) {
      // Load available voices
      const loadVoices = () => {
        const availableVoices = window.speechSynthesis.getVoices();
        // Set default voice (prefer English voices)
        const englishVoice = availableVoices.find(voice => 
          voice.lang.startsWith('en') && voice.default
        ) || availableVoices.find(voice => voice.lang.startsWith('en')) || availableVoices[0];
        setSelectedVoice(englishVoice);
      };
      loadVoices();
      if (window.speechSynthesis.onvoiceschanged !== undefined) {
        window.speechSynthesis.onvoiceschanged = loadVoices;
      }
    }
  }, []);

  const handleSpeak = () => {
    if (!isSupported || !text.trim()) return;

    window.speechSynthesis.cancel();
    const utterance = new SpeechSynthesisUtterance(text);
    
    utterance.rate = 0.9;
    utterance.pitch = 1;
    utterance.volume = 0.8;
    
    // Use selected voice if available
    if (selectedVoice) {
      utterance.voice = selectedVoice;
    }

    utterance.onstart = () => setIsSpeaking(true);
    utterance.onend = () => setIsSpeaking(false);
    utterance.onerror = () => setIsSpeaking(false);

    window.speechSynthesis.speak(utterance);
  };

  if (!isSupported) return null;

  const sizeClasses = {
    sm: 'w-4 h-4',
    md: 'w-5 h-5',
    lg: 'w-6 h-6',
  };

  return (
    <button
      onClick={handleSpeak}
      className={`p-2 rounded-lg hover:bg-green-900/30 transition-all duration-200 text-green-400 hover:text-green-300 group ${className}`}
      title="Read aloud"
      disabled={!text.trim()}
    >
      <Volume2 className={`${sizeClasses[size]} group-hover:scale-110 transition-transform duration-200 ${isSpeaking ? 'animate-pulse' : ''}`} />
    </button>
  );
}
