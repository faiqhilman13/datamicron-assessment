import { useState } from 'react';
import { MessageSquare, BarChart3, TrendingUp, Plus } from 'lucide-react';
import ChatInterface from './components/ChatInterface';
import AnalyticsPanel from './components/AnalyticsPanel';
import { FeedbackStats } from './components/FeedbackStats';

type Tab = 'chat' | 'analytics' | 'feedback';

function App() {
  const [activeTab, setActiveTab] = useState<Tab>('chat');

  return (
    <div className="relative min-h-screen overflow-hidden bg-[#101014] text-white">
      {/* Vanta.js Background */}
      <div id="vanta-bg" className="absolute inset-0 z-0"></div>
      <div className="absolute top-1/2 left-1/2 w-[600px] h-[600px] -translate-x-1/2 -translate-y-1/2 bg-[#5E6AD2] opacity-10 blur-[100px] rounded-full pointer-events-none"></div>

      {/* Sidebar */}
      <div className="fixed top-0 left-0 h-full w-64 bg-[#15151B] border-r border-white/10 z-20 overflow-auto">
        {/* Logo */}
        <div className="p-5 flex items-center border-b border-white/10">
          <svg className="w-7 h-7" viewBox="0 0 24 24" fill="none">
            <path d="M12 2L2 7L12 12L22 7L12 2Z" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
            <path d="M2 17L12 22L22 17" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
            <path d="M2 12L12 17L22 12" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
          </svg>
          <span className="ml-3 text-lg font-medium">Datamicron AI</span>
        </div>

        {/* New Chat Button */}
        <div className="p-5">
          <button className="w-full bg-[#5E6AD2] hover:bg-opacity-90 text-white py-2 px-4 rounded-md flex items-center justify-center transition-all">
            <Plus className="w-5 h-5 mr-2" />
            New Chat
          </button>
        </div>

        {/* Navigation */}
        <div className="px-3 py-2 text-xs font-medium text-gray-400 uppercase">Sections</div>

        <div className="space-y-1 px-3">
          <button
            onClick={() => setActiveTab('chat')}
            className={`w-full flex items-center py-2 px-3 rounded-md transition-all ${
              activeTab === 'chat' ? 'bg-white/10' : 'hover:bg-white/5'
            }`}
          >
            <MessageSquare className="w-4 h-4 mr-3 text-gray-400" />
            <span>News Chat</span>
          </button>

          <button
            onClick={() => setActiveTab('analytics')}
            className={`w-full flex items-center py-2 px-3 rounded-md transition-all ${
              activeTab === 'analytics' ? 'bg-white/10' : 'hover:bg-white/5'
            }`}
          >
            <BarChart3 className="w-4 h-4 mr-3 text-gray-400" />
            <span>Analytics</span>
          </button>

          <button
            onClick={() => setActiveTab('feedback')}
            className={`w-full flex items-center py-2 px-3 rounded-md transition-all ${
              activeTab === 'feedback' ? 'bg-white/10' : 'hover:bg-white/5'
            }`}
          >
            <TrendingUp className="w-4 h-4 mr-3 text-gray-400" />
            <span>Feedback & RL</span>
          </button>
        </div>

        {/* Features */}
        <div className="px-3 py-2 mt-6 text-xs font-medium text-gray-400 uppercase">Features</div>

        <div className="space-y-1 px-3 mb-4">
          <div className="flex items-center py-2 px-3 text-sm text-gray-400">
            <svg className="w-4 h-4 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"></path>
            </svg>
            <span>Hybrid Search</span>
          </div>
          <div className="flex items-center py-2 px-3 text-sm text-gray-400">
            <svg className="w-4 h-4 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 10V3L4 14h7v7l9-11h-7z"></path>
            </svg>
            <span>Reranking</span>
          </div>
          <div className="flex items-center py-2 px-3 text-sm text-gray-400">
            <svg className="w-4 h-4 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M9.663 17h4.673M12 3v1m6.364 1.636l-.707.707M21 12h-1M4 12H3m3.343-5.657l-.707-.707m2.828 9.9a5 5 0 117.072 0l-.548.547A3.374 3.374 0 0014 18.469V19a2 2 0 11-4 0v-.531c0-.895-.356-1.754-.988-2.386l-.548-.547z"></path>
            </svg>
            <span>RL Optimization</span>
          </div>
        </div>
      </div>

      {/* Main Content */}
      <div className="ml-64 relative z-10">
        {/* Topbar */}
        <div className="h-16 border-b border-white/10 flex items-center justify-between px-6">
          <div className="flex items-center space-x-4">
            <span className="text-sm font-medium">
              {activeTab === 'chat' ? 'News Chat Interface' : activeTab === 'analytics' ? 'Analytics Dashboard' : 'Feedback System'}
            </span>
          </div>
          <div className="flex items-center space-x-3">
            <div className="text-xs text-gray-400">
              Powered by OpenAI & RAG
            </div>
          </div>
        </div>

        {/* Content Area */}
        <div className="h-[calc(100vh-4rem)]">
          {activeTab === 'chat' && <ChatInterface />}
          {activeTab === 'analytics' && <AnalyticsPanel />}
          {activeTab === 'feedback' && (
            <div className="p-6 h-full overflow-y-auto">
              <FeedbackStats />
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default App;
