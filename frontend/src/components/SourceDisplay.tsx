import { ExternalLink, FileText, Globe } from 'lucide-react';
import type { Source } from '../api/client';

interface SourceDisplayProps {
  sources: Source[];
}

export default function SourceDisplay({ sources }: SourceDisplayProps) {
  return (
    <div className="border-t border-gray-700 pt-3">
      <h4 className="text-sm font-semibold text-gray-300 mb-2">Sources:</h4>
      <div className="space-y-2">
        {sources.map((source, index) => (
          <div
            key={index}
            className="text-sm bg-gray-900 border border-gray-700 rounded p-3"
          >
            <div className="flex items-start justify-between gap-2">
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-1">
                  {source.type === 'internal' ? (
                    <FileText className="w-4 h-4 text-green-400" />
                  ) : (
                    <Globe className="w-4 h-4 text-blue-400" />
                  )}

                  <span
                    className={`badge ${
                      source.type === 'internal' ? 'badge-internal' : 'badge-web'
                    }`}
                  >
                    {source.type === 'internal' ? 'Internal KB' : 'Web Search'}
                  </span>
                </div>

                <div className="font-medium text-gray-200">{source.title}</div>

                {source.author && (
                  <div className="text-gray-400 text-xs mt-1">By {source.author}</div>
                )}

                {source.sentiment && (
                  <div className="text-gray-400 text-xs mt-1">
                    Sentiment: {source.sentiment}
                  </div>
                )}
              </div>

              <div className="flex flex-col items-end gap-1">
                <div className="text-xs text-gray-400">
                  Score: {(source.relevance_score * 100).toFixed(0)}%
                </div>

                {source.url && (
                  <a
                    href={source.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-blue-400 hover:text-blue-300 transition-colors"
                  >
                    <ExternalLink className="w-4 h-4" />
                  </a>
                )}
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
