import { TrendingUp, CheckCircle2, AlertCircle } from 'lucide-react';
import type { JudgeScores } from '../api/client';

interface ConfidenceScoreProps {
  confidence: number;
  judgeScores: JudgeScores;
  webSearchTriggered: boolean;
}

export default function ConfidenceScore({
  confidence,
  judgeScores,
  webSearchTriggered,
}: ConfidenceScoreProps) {
  const confidencePercent = (confidence * 100).toFixed(0);
  const isHighConfidence = confidence >= 0.7;

  return (
    <div className="border-t border-gray-700 pt-3 space-y-2">
      {/* Overall Confidence */}
      <div className="flex items-center gap-2">
        {isHighConfidence ? (
          <CheckCircle2 className="w-4 h-4 text-green-400" />
        ) : (
          <AlertCircle className="w-4 h-4 text-yellow-400" />
        )}
        <span className="text-sm text-gray-300">
          Confidence: {confidencePercent}%
        </span>

        {webSearchTriggered && (
          <span className="badge badge-web text-xs ml-2">
            Web search used
          </span>
        )}
      </div>

      {/* Judge Scores */}
      <div className="flex gap-3 text-xs text-gray-400">
        <div className="flex items-center gap-1">
          <TrendingUp className="w-3 h-3" />
          <span>Relevance: {judgeScores.relevance}/10</span>
        </div>
        <div className="flex items-center gap-1">
          <TrendingUp className="w-3 h-3" />
          <span>Factuality: {judgeScores.factuality}/10</span>
        </div>
        <div className="flex items-center gap-1">
          <TrendingUp className="w-3 h-3" />
          <span>Completeness: {judgeScores.completeness}/10</span>
        </div>
      </div>
    </div>
  );
}
