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
      {/* Header */}
      <div className="border-b border-gray-700 p-4 bg-gray-800">
        <h2 className="text-xl font-bold text-white mb-2">News Q&A Assistant</h2>
        <div className="flex items-center gap-2">
          <input
            type="checkbox"
            id="web-search"
            checked={enableWebSearch}
            onChange={(e) => setEnableWebSearch(e.target.checked)}
            className="rounded"
          />
          <label htmlFor="web-search" className="text-sm text-gray-300">
            Enable web search fallback
          </label>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 && (
          <div className="text-center text-gray-400 mt-8">
            <p className="text-lg mb-2">Ask me anything about Malaysian news!</p>
            <p className="text-sm">Try asking:</p>
            <ul className="text-sm mt-2 space-y-1">
              <li>"What are some initiatives launched by MCMC?"</li>
              <li>"Adakah SSM terbabit dengan kes-kes mahkamah?"</li>
              <li>"What is the status of the Malaysian economy in 2025?"</li>
            </ul>
          </div>
        )}

        {messages.map((message, index) => (
          <div
            key={index}
            className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
          >
            <div
              className={`max-w-3xl rounded-lg p-4 ${
                message.role === 'user'
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-800 text-gray-100 border border-gray-700'
              }`}
            >
              <div className="whitespace-pre-wrap">{message.content}</div>

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
        ))}

        {isLoading && (
          <div className="flex justify-start">
            <div className="bg-gray-800 border border-gray-700 rounded-lg p-4">
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
      <div className="border-t border-gray-700 p-4 bg-gray-800">
        <form onSubmit={handleSubmit} className="flex gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask a question about Malaysian news..."
            className="input-field flex-1"
            disabled={isLoading}
          />
          <button
            type="submit"
            disabled={!input.trim() || isLoading}
            className="btn-primary flex items-center gap-2"
          >
            <Send className="w-5 h-5" />
            Send
          </button>
        </form>
      </div>
    </div>
  );
}
