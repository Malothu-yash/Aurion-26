import { useState, useRef } from 'react';
import { 
  Send, 
  Plus, 
  Camera, 
  Image, 
  FileText, 
  Mic, 
  X,
  
} from 'lucide-react';

interface ChatInputProps {
  onSendMessage: (message: string, attachments?: any[]) => void;
  disabled?: boolean;
}

interface Attachment {
  id: string;
  name: string;
  type: string;
  size: number;
  url?: string;
  file?: File;
}

export default function ChatInput({ onSendMessage, disabled }: ChatInputProps) {
  const [message, setMessage] = useState('');
  const [attachments, setAttachments] = useState<Attachment[]>([]);
  const [showUploadMenu, setShowUploadMenu] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const handleSend = () => {
    if ((!message.trim() && attachments.length === 0) || disabled) return;
    
    onSendMessage(message, attachments);
    setMessage('');
    setAttachments([]);
    setShowUploadMenu(false);
    
    // Reset textarea height
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const handleTextareaChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setMessage(e.target.value);
    
    // Auto-resize textarea
    const textarea = e.target;
    textarea.style.height = 'auto';
    textarea.style.height = Math.min(textarea.scrollHeight, 120) + 'px';
  };

  const handleFileUpload = async (files: FileList | null) => {
    if (!files) return;
    
    for (let i = 0; i < files.length; i++) {
      const file = files[i];
      const attachment: Attachment = {
        id: crypto.randomUUID(),
        name: file.name,
        type: file.type,
        size: file.size,
        file: file,
        url: URL.createObjectURL(file)
      };
      
      setAttachments(prev => [...prev, attachment]);
    }
    
    setShowUploadMenu(false);
  };

  const removeAttachment = (id: string) => {
    setAttachments(prev => {
      const updated = prev.filter(att => att.id !== id);
      // Revoke URL to prevent memory leaks
      const removed = prev.find(att => att.id === id);
      if (removed?.url) {
        URL.revokeObjectURL(removed.url);
      }
      return updated;
    });
  };

  const startVoiceRecording = () => {
    setIsRecording(true);
    // Voice recording implementation would go here
    // For now, just simulate
    setTimeout(() => {
      setIsRecording(false);
      setMessage(prev => prev + "Voice message transcribed");
    }, 2000);
  };

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const getFileIcon = (type: string) => {
    if (type.startsWith('image/')) return Image;
    if (type.startsWith('video/')) return Camera;
    return FileText;
  };

  return (
    <div className="relative">
      {/* Attachments Preview */}
      {attachments.length > 0 && (
        <div className="mb-4 flex flex-wrap gap-2">
          {attachments.map((attachment) => {
            const IconComponent = getFileIcon(attachment.type);
            return (
              <div
                key={attachment.id}
                className="group relative bg-purple-900/40 rounded-lg p-3 max-w-xs cursor-pointer hover:bg-purple-900/60 transition-colors duration-200"
                onClick={() => attachment.url && window.open(attachment.url, '_blank')}
              >
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    removeAttachment(attachment.id);
                  }}
                  className="absolute -top-2 -right-2 w-6 h-6 bg-red-500 rounded-full flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity duration-200 hover:bg-red-600"
                >
                  <X className="w-3 h-3 text-white" />
                </button>
                
                <div className="flex items-center space-x-3">
                  {attachment.type.startsWith('image/') && attachment.url ? (
                    <img
                      src={attachment.url}
                      alt={attachment.name}
                      className="w-12 h-12 rounded object-cover"
                    />
                  ) : (
                    <div className="w-12 h-12 bg-orange-500/20 rounded flex items-center justify-center">
                      <IconComponent className="w-6 h-6 text-orange-400" />
                    </div>
                  )}
                  
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-white truncate">
                      {attachment.name}
                    </p>
                    <p className="text-xs text-gray-400">
                      {formatFileSize(attachment.size)}
                    </p>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* Upload Menu */}
      {showUploadMenu && (
        <div className="absolute bottom-full left-0 mb-2 bg-purple-950/90 backdrop-blur-lg border border-orange-500/20 rounded-xl shadow-xl p-2 min-w-48 animate-fade-in-up">
          <button
            onClick={() => {
              fileInputRef.current?.click();
              setShowUploadMenu(false);
            }}
            className="w-full flex items-center space-x-3 p-3 rounded-lg hover:bg-purple-900/40 transition-colors duration-200 text-gray-300 hover:text-white"
          >
            <Camera className="w-5 h-5 text-orange-400" />
            <span>Camera</span>
          </button>
          
          <button
            onClick={() => {
              const input = document.createElement('input');
              input.type = 'file';
              input.accept = 'image/*';
              input.multiple = true;
              input.onchange = (e) => handleFileUpload((e.target as HTMLInputElement).files);
              input.click();
              setShowUploadMenu(false);
            }}
            className="w-full flex items-center space-x-3 p-3 rounded-lg hover:bg-purple-900/40 transition-colors duration-200 text-gray-300 hover:text-white"
          >
            <Image className="w-5 h-5 text-green-400" />
            <span>Photos</span>
          </button>
          
          <button
            onClick={() => {
              const input = document.createElement('input');
              input.type = 'file';
              input.multiple = true;
              input.onchange = (e) => handleFileUpload((e.target as HTMLInputElement).files);
              input.click();
              setShowUploadMenu(false);
            }}
            className="w-full flex items-center space-x-3 p-3 rounded-lg hover:bg-purple-900/40 transition-colors duration-200 text-gray-300 hover:text-white"
          >
            <FileText className="w-5 h-5 text-blue-400" />
            <span>Files</span>
          </button>
        </div>
      )}

      {/* Main Input Container */}
      <div className="relative glass-aurora rounded-2xl border border-orange-500/20 focus-within:border-orange-400/40 transition-colors duration-200">
        <div className="flex items-end space-x-3 p-4">
          {/* Upload Button */}
          <button
            onClick={() => setShowUploadMenu(!showUploadMenu)}
            className={`flex-shrink-0 w-10 h-10 rounded-xl flex items-center justify-center transition-all duration-200 ${
              showUploadMenu
                ? 'bg-orange-500 text-white shadow-lg'
                : 'bg-purple-900/40 text-gray-400 hover:text-orange-400 hover:bg-purple-900/60'
            }`}
          >
            {showUploadMenu ? <X className="w-5 h-5" /> : <Plus className="w-5 h-5" />}
          </button>

          {/* Text Input */}
          <div className="flex-1">
            <textarea
              ref={textareaRef}
              value={message}
              onChange={handleTextareaChange}
              onKeyDown={handleKeyDown}
              placeholder="Type your message here..."
              disabled={disabled}
              className="w-full bg-transparent text-white placeholder-gray-400 resize-none focus:outline-none min-h-[2.5rem] max-h-[7.5rem] leading-relaxed"
              style={{ height: 'auto' }}
            />
          </div>

          {/* Voice Input Button */}
          <button
            onClick={startVoiceRecording}
            disabled={disabled}
            className={`flex-shrink-0 w-10 h-10 rounded-xl flex items-center justify-center transition-all duration-200 ${
              isRecording
                ? 'bg-red-500 text-white animate-pulse'
                : 'bg-purple-900/40 text-gray-400 hover:text-red-400 hover:bg-purple-900/60'
            }`}
          >
            <Mic className="w-5 h-5" />
          </button>

          {/* Send Button */}
          <button
            onClick={handleSend}
            disabled={disabled || (!message.trim() && attachments.length === 0)}
            className={`flex-shrink-0 w-10 h-10 rounded-xl flex items-center justify-center transition-all duration-200 ${
              disabled || (!message.trim() && attachments.length === 0)
                ? 'bg-gray-700 text-gray-500 cursor-not-allowed'
                : 'bg-gradient-to-r from-orange-500 to-purple-600 text-white hover:scale-105 hover:shadow-lg shadow-orange-500/25'
            }`}
          >
            <Send className="w-5 h-5" />
          </button>
        </div>
      </div>

      {/* Hidden file input */}
      <input
        ref={fileInputRef}
        type="file"
        accept="image/*"
        capture="environment"
        onChange={(e) => handleFileUpload(e.target.files)}
        className="hidden"
      />
    </div>
  );
}
