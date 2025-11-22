import React, { useState } from 'react';
import { ThumbsUp, ThumbsDown, Check } from 'lucide-react';
import { api, type ChatResponse } from '../api/client';

interface FeedbackButtonsProps {
  response: ChatResponse;
  query: string;
}

export const FeedbackButtons: React.FC<FeedbackButtonsProps> = ({ response, query }) => {
  const [feedback, setFeedback] = useState<'positive' | 'negative' | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [showThankYou, setShowThankYou] = useState(false);

  const handleFeedback = async (feedbackType: 'positive' | 'negative') => {
    if (feedback || isSubmitting) return; // Already submitted or submitting

    setIsSubmitting(true);

    try {
      await api.submitFeedback({
        response_id: response.response_id,
        query,
        answer: response.answer,
        sources: response.sources,
        feedback_type: feedbackType,
        confidence: response.confidence,
        judge_scores: response.judge_scores,
        retrieval_method: response.retrieval_method,
        web_search_triggered: response.web_search_triggered,
      });

      setFeedback(feedbackType);
      setShowThankYou(true);

      // Hide thank you message after 3 seconds
      setTimeout(() => setShowThankYou(false), 3000);
    } catch (error) {
      console.error('Error submitting feedback:', error);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="flex items-center gap-2 mt-4 pt-3 border-t border-gray-200">
      <span className="text-sm text-gray-600">Was this helpful?</span>

      <button
        onClick={() => handleFeedback('positive')}
        disabled={feedback !== null || isSubmitting}
        className={`p-2 rounded-lg transition-all ${
          feedback === 'positive'
            ? 'bg-green-100 text-green-700'
            : 'hover:bg-gray-100 text-gray-600 hover:text-green-600'
        } ${feedback !== null && feedback !== 'positive' ? 'opacity-50' : ''} disabled:cursor-not-allowed`}
        title="Thumbs up"
      >
        <ThumbsUp className="w-4 h-4" />
      </button>

      <button
        onClick={() => handleFeedback('negative')}
        disabled={feedback !== null || isSubmitting}
        className={`p-2 rounded-lg transition-all ${
          feedback === 'negative'
            ? 'bg-red-100 text-red-700'
            : 'hover:bg-gray-100 text-gray-600 hover:text-red-600'
        } ${feedback !== null && feedback !== 'negative' ? 'opacity-50' : ''} disabled:cursor-not-allowed`}
        title="Thumbs down"
      >
        <ThumbsDown className="w-4 h-4" />
      </button>

      {showThankYou && (
        <div className="flex items-center gap-1 text-sm text-green-600 animate-fade-in">
          <Check className="w-4 h-4" />
          <span>Thanks for your feedback!</span>
        </div>
      )}
    </div>
  );
};
