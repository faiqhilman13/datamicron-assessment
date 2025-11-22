import React, { useState, useEffect } from 'react';
import { TrendingUp, ThumbsUp, ThumbsDown, AlertCircle } from 'lucide-react';
import { api, type FeedbackStats as FeedbackStatsType } from '../api/client';

export const FeedbackStats: React.FC = () => {
  const [stats, setStats] = useState<FeedbackStatsType | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadStats = async () => {
    setIsLoading(true);
    setError(null);

    try {
      const data = await api.getFeedbackStats();
      setStats(data);
    } catch (err) {
      setError('Failed to load feedback statistics');
      console.error('Error loading feedback stats:', err);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadStats();
  }, []);

  if (isLoading) {
    return (
      <div className="bg-gray-800 border border-gray-700 rounded-lg p-6">
        <p className="text-gray-400">Loading feedback stats...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-gray-800 border border-red-700 rounded-lg p-6">
        <div className="flex items-center gap-2 text-red-400">
          <AlertCircle className="w-5 h-5" />
          <p>{error}</p>
        </div>
      </div>
    );
  }

  if (!stats || stats.total_feedback === 0) {
    return (
      <div className="bg-gray-800 border border-gray-700 rounded-lg p-6">
        <h3 className="text-lg font-semibold text-white mb-2 flex items-center gap-2">
          <TrendingUp className="w-5 h-5" />
          Feedback Statistics
        </h3>
        <p className="text-gray-400">No feedback collected yet. Start getting feedback on responses!</p>
      </div>
    );
  }

  const positiveRate = (stats.positive_rate * 100).toFixed(1);

  return (
    <div className="bg-gray-800 border border-gray-700 rounded-lg p-6">
      <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
        <TrendingUp className="w-5 h-5" />
        Feedback Statistics
      </h3>

      {/* Overall Stats */}
      <div className="grid grid-cols-3 gap-4 mb-6">
        <div className="bg-gray-900 rounded-lg p-4">
          <div className="text-2xl font-bold text-white">{stats.total_feedback}</div>
          <div className="text-sm text-gray-400">Total Responses</div>
        </div>

        <div className="bg-gray-900 rounded-lg p-4">
          <div className="flex items-center gap-2 text-2xl font-bold text-green-500">
            <ThumbsUp className="w-5 h-5" />
            {stats.positive}
          </div>
          <div className="text-sm text-gray-400">Positive</div>
        </div>

        <div className="bg-gray-900 rounded-lg p-4">
          <div className="flex items-center gap-2 text-2xl font-bold text-red-500">
            <ThumbsDown className="w-5 h-5" />
            {stats.negative}
          </div>
          <div className="text-sm text-gray-400">Negative</div>
        </div>
      </div>

      {/* Positive Rate */}
      <div className="mb-6">
        <div className="flex justify-between items-center mb-2">
          <span className="text-sm text-gray-400">Positive Rate</span>
          <span className="text-sm font-semibold text-white">{positiveRate}%</span>
        </div>
        <div className="w-full bg-gray-700 rounded-full h-2">
          <div
            className="bg-green-500 h-2 rounded-full transition-all"
            style={{ width: `${positiveRate}%` }}
          />
        </div>
      </div>

      {/* Web Search vs Internal KB */}
      {stats.web_search_feedback && (
        <div className="space-y-3">
          <h4 className="text-sm font-semibold text-gray-300">Performance by Source</h4>

          <div className="bg-gray-900 rounded-lg p-3">
            <div className="flex justify-between items-center mb-1">
              <span className="text-sm text-gray-400">Web Search</span>
              <span className="text-sm font-semibold text-white">
                {stats.web_search_feedback.web_search?.total || 0} responses
              </span>
            </div>
            <div className="w-full bg-gray-700 rounded-full h-2">
              <div
                className="bg-blue-500 h-2 rounded-full transition-all"
                style={{
                  width: `${(stats.web_search_feedback.web_search?.positive_rate || 0) * 100}%`,
                }}
              />
            </div>
            <div className="text-xs text-gray-500 mt-1">
              {((stats.web_search_feedback.web_search?.positive_rate || 0) * 100).toFixed(1)}%
              positive
            </div>
          </div>

          <div className="bg-gray-900 rounded-lg p-3">
            <div className="flex justify-between items-center mb-1">
              <span className="text-sm text-gray-400">Internal KB</span>
              <span className="text-sm font-semibold text-white">
                {stats.web_search_feedback.internal_kb?.total || 0} responses
              </span>
            </div>
            <div className="w-full bg-gray-700 rounded-full h-2">
              <div
                className="bg-purple-500 h-2 rounded-full transition-all"
                style={{
                  width: `${(stats.web_search_feedback.internal_kb?.positive_rate || 0) * 100}%`,
                }}
              />
            </div>
            <div className="text-xs text-gray-500 mt-1">
              {((stats.web_search_feedback.internal_kb?.positive_rate || 0) * 100).toFixed(1)}%
              positive
            </div>
          </div>
        </div>
      )}

      <button
        onClick={loadStats}
        className="mt-4 w-full btn-primary text-sm py-2"
      >
        Refresh Stats
      </button>
    </div>
  );
};
