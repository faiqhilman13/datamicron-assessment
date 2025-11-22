#!/bin/bash

# Submit 5 feedbacks to trigger RL optimization
# Alternating between web search (positive) and internal KB (negative)

echo "Submitting 5 feedbacks to trigger RL optimization..."

for i in {1..5}; do
  echo "Submitting feedback $i..."

  if [ $((i % 2)) -eq 0 ]; then
    # Web search - positive feedback
    curl -s -X POST http://localhost:8000/api/feedback \
      -H "Content-Type: application/json" \
      -d "{
        \"response_id\": \"test_00$i\",
        \"query\": \"Test query $i\",
        \"answer\": \"Test answer $i\",
        \"sources\": [{\"type\": \"web\", \"title\": \"Web Result\", \"url\": \"https://test.com\", \"relevance_score\": 0.8, \"sentiment\": null}],
        \"feedback_type\": \"positive\",
        \"confidence\": 0.6,
        \"judge_scores\": {\"relevance\": 9, \"factuality\": 9, \"completeness\": 8},
        \"retrieval_method\": \"hybrid_search_with_reranking\",
        \"web_search_triggered\": true
      }" > /dev/null
  else
    # Internal KB - negative feedback
    curl -s -X POST http://localhost:8000/api/feedback \
      -H "Content-Type: application/json" \
      -d "{
        \"response_id\": \"test_00$i\",
        \"query\": \"Test query $i\",
        \"answer\": \"Test answer $i\",
        \"sources\": [{\"type\": \"internal\", \"title\": \"Article\", \"author\": \"Author\", \"url\": \"https://test.com\", \"relevance_score\": 0.7, \"sentiment\": \"Positive\"}],
        \"feedback_type\": \"negative\",
        \"confidence\": 0.8,
        \"judge_scores\": {\"relevance\": 5, \"factuality\": 5, \"completeness\": 4},
        \"retrieval_method\": \"hybrid_search_with_reranking\",
        \"web_search_triggered\": false
      }" > /dev/null
  fi

  echo "  ✓ Feedback $i submitted"
  sleep 0.5
done

echo ""
echo "=== Checking if RL adjusted parameters ==="
curl -s http://localhost:8000/api/rl/config | python3 -m json.tool
