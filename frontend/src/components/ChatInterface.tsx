import { useState, useRef, useEffect } from 'react';
import { Send, Loader2 } from 'lucide-react';
import { api } from '../api/client';
import type { ChatResponse } from '../api/client';
import SourceDisplay from './SourceDisplay';
import ConfidenceScore from './ConfidenceScore';
import { FeedbackButtons } from './FeedbackButtons';

interface Message {
  role: 'user' | 'assistant';
  content: string;
  response?: ChatResponse;
  query?: string; // Store the original query for feedback
}

export default function ChatInterface() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [enableWebSearch, setEnableWebSearch] = useState(true);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!input.trim() || isLoading) return;

    const userMessage: Message = {
      role: 'user',
      content: input.trim(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);

    try {
      const response = await api.chat({
        query: userMessage.content,
        enable_web_search: enableWebSearch,
      });

      const assistantMessage: Message = {
        role: 'assistant',
        content: response.answer,
        response,
        query: userMessage.content, // Store query for feedback
      };

      setMessages((prev) => [...prev, assistantMessage]);
    } catch (error) {
      console.error('Error:', error);

      const errorMessage: Message = {
        role: 'assistant',
        content: 'Sorry, I encountered an error processing your question. Please try again.',
      };

      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-full">
      {/* Messages */}
      <div className="flex-1 overflow-y-auto px-6 py-8">
        {messages.length === 0 && (
          <div className="text-center text-gray-400 mt-16">
            <div className="w-16 h-16 rounded-full bg-[#5E6AD2] flex items-center justify-center mx-auto mb-4">
              <svg className="w-10 h-10" viewBox="0 0 24 24" fill="none">
                <path d="M12 2L2 7L12 12L22 7L12 2Z" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                <path d="M2 17L12 22L22 17" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                <path d="M2 12L12 17L22 12" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
              </svg>
            </div>
            <p className="text-xl mb-2 font-medium">Ask me anything about Malaysian news!</p>
            <p className="text-sm text-gray-500 mb-4">Powered by RAG, Hybrid Search & Reinforcement Learning</p>
            <div className="max-w-md mx-auto text-left space-y-2 mt-6">
              <p className="text-sm text-gray-400">Try asking:</p>
              <div className="space-y-2">
                <div className="bg-[#1E1E26] p-3 rounded-lg text-sm">"What are some initiatives launched by MCMC?"</div>
                <div className="bg-[#1E1E26] p-3 rounded-lg text-sm">"Adakah SSM terbabit dengan kes-kes mahkamah?"</div>
                <div className="bg-[#1E1E26] p-3 rounded-lg text-sm">"What is the status of the Malaysian economy in 2025?"</div>
              </div>
            </div>
          </div>
        )}

        {messages.map((message, index) => (
          <div key={index} className="flex mb-6">
            {message.role === 'assistant' && (
              <div className="w-8 h-8 rounded-full bg-[#5E6AD2] flex items-center justify-center mr-4 flex-shrink-0">
                <svg className="w-5 h-5" viewBox="0 0 24 24" fill="none">
                  <path d="M12 2L2 7L12 12L22 7L12 2Z" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                  <path d="M2 17L12 22L22 17" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                  <path d="M2 12L12 17L22 12" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                </svg>
              </div>
            )}

            <div className={`flex-1 ${message.role === 'user' ? 'flex justify-end' : ''}`}>
              <div
                className={`rounded-lg p-4 ${
                  message.role === 'user'
                    ? 'bg-[#5E6AD2] bg-opacity-20 max-w-3xl'
                    : 'bg-[#1E1E26] max-w-3xl'
                }`}
              >
                <div className="whitespace-pre-wrap text-gray-300">{message.content}</div>

                {/* Show sources and metrics for assistant messages */}
                {message.role === 'assistant' && message.response && (
                  <div className="mt-4 space-y-3">
                    <ConfidenceScore
                      confidence={message.response.confidence}
                      judgeScores={message.response.judge_scores}
                      webSearchTriggered={message.response.web_search_triggered}
                    />

                    {message.response.sources.length > 0 && (
                      <SourceDisplay sources={message.response.sources} />
                    )}

                    {/* Feedback buttons */}
                    {message.query && (
                      <FeedbackButtons response={message.response} query={message.query} />
                    )}
                  </div>
                )}
              </div>
            </div>

            {message.role === 'user' && (
              <div className="w-8 h-8 rounded-full bg-[#2A2A35] flex items-center justify-center ml-4 flex-shrink-0">
                <span className="text-sm font-medium">U</span>
              </div>
            )}
          </div>
        ))}

        {isLoading && (
          <div className="flex mb-6">
            <div className="w-8 h-8 rounded-full bg-[#5E6AD2] flex items-center justify-center mr-4 flex-shrink-0">
              <svg className="w-5 h-5" viewBox="0 0 24 24" fill="none">
                <path d="M12 2L2 7L12 12L22 7L12 2Z" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                <path d="M2 17L12 22L22 17" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                <path d="M2 12L12 17L22 12" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
              </svg>
            </div>
            <div className="bg-[#1E1E26] rounded-lg p-4 max-w-3xl">
              <div className="flex items-center gap-2 text-gray-400">
                <Loader2 className="w-5 h-5 animate-spin" />
                <span>Thinking...</span>
              </div>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div className="h-32 border-t border-white/10 px-6 py-4">
        <div className="bg-[#1E1E26] border border-white/10 rounded-lg p-3">
          <form onSubmit={handleSubmit}>
            <textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault();
                  handleSubmit(e);
                }
              }}
              placeholder="Type your message..."
              className="w-full bg-transparent outline-none resize-none text-gray-300 placeholder-gray-500"
              rows={2}
              disabled={isLoading}
            />
            <div className="flex justify-between items-center mt-2">
              <div className="flex items-center gap-2">
                <input
                  type="checkbox"
                  id="web-search"
                  checked={enableWebSearch}
                  onChange={(e) => setEnableWebSearch(e.target.checked)}
                  className="rounded"
                />
                <label htmlFor="web-search" className="text-xs text-gray-400">
                  Web search
                </label>
              </div>
              <button
                type="submit"
                disabled={!input.trim() || isLoading}
                className="bg-[#5E6AD2] hover:bg-opacity-90 disabled:opacity-50 disabled:cursor-not-allowed text-white py-2 px-4 rounded-md flex items-center transition-all"
              >
                <span>Send</span>
                <Send className="w-4 h-4 ml-2" />
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  );
}
