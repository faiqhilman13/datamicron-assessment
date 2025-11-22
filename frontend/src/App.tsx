import { useState, useEffect } from 'react';
import { MessageSquare, BarChart3, Activity, TrendingUp } from 'lucide-react';
import ChatInterface from './components/ChatInterface';
import AnalyticsPanel from './components/AnalyticsPanel';
import { FeedbackStats } from './components/FeedbackStats';
import { api } from './api/client';

type Tab = 'chat' | 'analytics' | 'feedback';

function App() {
  const [activeTab, setActiveTab] = useState<Tab>('chat');
  const [healthStatus, setHealthStatus] = useState<string>('checking');

  useEffect(() => {
    checkHealth();
  }, []);

  const checkHealth = async () => {
    try {
      const health = await api.health();
      setHealthStatus(health.indexes_loaded ? 'healthy' : 'unhealthy');
    } catch (error) {
      setHealthStatus('error');
    }
  };

  return (
    <div className="min-h-screen bg-slate-900 text-white">
      {/* Header */}
      <header className="bg-gray-800 border-b border-gray-700 shadow-lg">
        <div className="container mx-auto px-4 py-4">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold text-white">
                Datamicron AI News Assistant
              </h1>
              <p className="text-sm text-gray-400 mt-1">
                Advanced RAG-powered news retrieval with hybrid search & reranking
              </p>
            </div>

            {/* Health Status */}
            <div className="flex items-center gap-2">
              <Activity
                className={`w-5 h-5 ${
                  healthStatus === 'healthy'
                    ? 'text-green-400'
                    : healthStatus === 'checking'
                    ? 'text-yellow-400'
                    : 'text-red-400'
                }`}
              />
              <span className="text-sm text-gray-300">
                {healthStatus === 'healthy'
                  ? 'All systems operational'
                  : healthStatus === 'checking'
                  ? 'Checking...'
                  : 'Service unavailable'}
              </span>
            </div>
          </div>

          {/* Tabs */}
          <div className="flex gap-2 mt-4">
            <button
              onClick={() => setActiveTab('chat')}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg transition-colors ${
                activeTab === 'chat'
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
              }`}
            >
              <MessageSquare className="w-5 h-5" />
              <span>News Q&A</span>
            </button>

            <button
              onClick={() => setActiveTab('analytics')}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg transition-colors ${
                activeTab === 'analytics'
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
              }`}
            >
              <BarChart3 className="w-5 h-5" />
              <span>Analytics</span>
            </button>

            <button
              onClick={() => setActiveTab('feedback')}
              className={`flex items-center gap-2 px-4 py-2 rounded-lg transition-colors ${
                activeTab === 'feedback'
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-700 text-gray-300 hover:bg-gray-600'
              }`}
            >
              <TrendingUp className="w-5 h-5" />
              <span>Feedback</span>
            </button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="container mx-auto px-4 py-6 h-[calc(100vh-180px)]">
        <div className="bg-gray-800 border border-gray-700 rounded-lg shadow-xl h-full">
          {activeTab === 'chat' && <ChatInterface />}
          {activeTab === 'analytics' && <AnalyticsPanel />}
          {activeTab === 'feedback' && (
            <div className="p-6 h-full overflow-y-auto">
              <FeedbackStats />
            </div>
          )}
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t border-gray-700 bg-gray-800 py-4">
        <div className="container mx-auto px-4 text-center text-sm text-gray-400">
          <p>
            Powered by OpenAI · Hybrid Search (Semantic + BM25) · Cross-Encoder Reranking · LLM-as-Judge
          </p>
        </div>
      </footer>
    </div>
  );
}

export default App;
