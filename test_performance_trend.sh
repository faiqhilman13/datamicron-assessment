#!/bin/bash

echo "======================================"
echo "Test 5: Performance Trend Analysis"
echo "======================================"

echo ""
echo "Batch 1: Submitting 5 feedbacks with 40% positive rate..."

# First batch: 2 positive, 3 negative (40% positive)
for i in {1..5}; do
  if [ $i -le 2 ]; then
    feedback_type="positive"
  else
    feedback_type="negative"
  fi

  curl -s -X POST http://localhost:8000/api/feedback \
    -H "Content-Type: application/json" \
    -d "{
      \"response_id\": \"batch1_$i\",
      \"query\": \"Query $i\",
      \"answer\": \"Answer $i\",
      \"sources\": [{\"type\": \"internal\", \"title\": \"Article\", \"author\": \"Author\", \"url\": \"https://test.com\", \"relevance_score\": 0.7, \"sentiment\": \"Positive\"}],
      \"feedback_type\": \"$feedback_type\",
      \"confidence\": 0.7,
      \"judge_scores\": {\"relevance\": 7, \"factuality\": 7, \"completeness\": 7},
      \"retrieval_method\": \"hybrid_search_with_reranking\",
      \"web_search_triggered\": false
    }" > /dev/null

  echo "  ✓ Batch 1 - Feedback $i ($feedback_type)"
  sleep 0.5
done

echo ""
echo "Batch 2: Submitting 5 feedbacks with 80% positive rate (improvement!)..."

# Second batch: 4 positive, 1 negative (80% positive)
for i in {1..5}; do
  if [ $i -le 4 ]; then
    feedback_type="positive"
  else
    feedback_type="negative"
  fi

  curl -s -X POST http://localhost:8000/api/feedback \
    -H "Content-Type: application/json" \
    -d "{
      \"response_id\": \"batch2_$i\",
      \"query\": \"Query $i\",
      \"answer\": \"Answer $i\",
      \"sources\": [{\"type\": \"internal\", \"title\": \"Article\", \"author\": \"Author\", \"url\": \"https://test.com\", \"relevance_score\": 0.75, \"sentiment\": \"Positive\"}],
      \"feedback_type\": \"$feedback_type\",
      \"confidence\": 0.75,
      \"judge_scores\": {\"relevance\": 8, \"factuality\": 8, \"completeness\": 8},
      \"retrieval_method\": \"hybrid_search_with_reranking\",
      \"web_search_triggered\": false
    }" > /dev/null

  echo "  ✓ Batch 2 - Feedback $i ($feedback_type)"
  sleep 0.5
done

echo ""
echo "=== Performance Trend Analysis ==="
curl -s http://localhost:8000/api/rl/config | python3 -m json.tool
