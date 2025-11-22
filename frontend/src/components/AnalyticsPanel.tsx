import { useState } from 'react';
import { BarChart3, Send, Loader2 } from 'lucide-react';
import { api } from '../api/client';
import type { AnalyticsResponse } from '../api/client';

export default function AnalyticsPanel() {
  const [query, setQuery] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [result, setResult] = useState<AnalyticsResponse | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!query.trim() || isLoading) return;

    setIsLoading(true);

    try {
      const response = await api.analytics({ query: query.trim() });
      setResult(response);
    } catch (error) {
      console.error('Error:', error);
      setResult({
        answer: 'Sorry, I encountered an error processing your analytics query.',
        data: {},
        query_type: 'error',
      });
    } finally {
      setIsLoading(false);
    }
  };

  const exampleQueries = [
    'How many positive and negative news are there?',
    'How many articles are from August 2025?',
    'What are the overall statistics of the dataset?',
    'Who are the top authors?',
  ];

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="border-b border-gray-700 p-4 bg-gray-800">
        <div className="flex items-center gap-2">
          <BarChart3 className="w-6 h-6 text-blue-400" />
          <h2 className="text-xl font-bold text-white">Dataset Analytics</h2>
        </div>
        <p className="text-sm text-gray-400 mt-1">
          Ask questions about the news dataset statistics
        </p>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-4">
        {/* Example Queries */}
        {!result && (
          <div className="mb-6">
            <h3 className="text-sm font-semibold text-gray-300 mb-3">
              Example Questions:
            </h3>
            <div className="grid gap-2">
              {exampleQueries.map((example, index) => (
                <button
                  key={index}
                  onClick={() => setQuery(example)}
                  className="text-left px-4 py-2 bg-gray-800 border border-gray-700 rounded-lg hover:border-blue-500 transition-colors text-sm text-gray-300"
                >
                  {example}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Result */}
        {result && (
          <div className="space-y-4">
            {/* Answer */}
            <div className="card">
              <h3 className="text-sm font-semibold text-gray-300 mb-2">Answer:</h3>
              <p className="text-gray-100">{result.answer}</p>
            </div>

            {/* Data */}
            {Object.keys(result.data).length > 0 && (
              <div className="card">
                <h3 className="text-sm font-semibold text-gray-300 mb-2">Data:</h3>
                <div className="bg-gray-900 border border-gray-700 rounded p-3 overflow-x-auto">
                  <pre className="text-xs text-gray-300">
                    {JSON.stringify(result.data, null, 2)}
                  </pre>
                </div>
              </div>
            )}

            {/* Query Type */}
            <div className="text-xs text-gray-400">
              Query type: {result.query_type}
            </div>

            {/* Ask Another Question */}
            <button
              onClick={() => {
                setResult(null);
                setQuery('');
              }}
              className="btn-secondary w-full"
            >
              Ask Another Question
            </button>
          </div>
        )}
      </div>

      {/* Input */}
      <div className="border-t border-gray-700 p-4 bg-gray-800">
        <form onSubmit={handleSubmit} className="flex gap-2">
          <input
            type="text"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            placeholder="e.g., How many positive news are there?"
            className="input-field flex-1"
            disabled={isLoading}
          />
          <button
            type="submit"
            disabled={!query.trim() || isLoading}
            className="btn-primary flex items-center gap-2"
          >
            {isLoading ? (
              <Loader2 className="w-5 h-5 animate-spin" />
            ) : (
              <Send className="w-5 h-5" />
            )}
            Ask
          </button>
        </form>
      </div>
    </div>
  );
}
