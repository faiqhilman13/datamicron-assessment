# RL System Tests

## Test 1: Verify RL Config Initialization

**Purpose:** Check that RL config is created with default values

```bash
# Check if config file exists
ls -la backend/data/rl_config.json

# View initial config
cat backend/data/rl_config.json | python3 -m json.tool

# Call API endpoint
curl -s http://localhost:8000/api/rl/config | python3 -m json.tool
```

**Expected Output:**
```json
{
  "config": {
    "web_search": {"confidence_threshold": 0.7},
    "confidence_weights": {"retrieval_eval": 0.5, "answer_quality": 0.5},
    "judge_weights": {"relevance": 0.4, "factuality": 0.4, "completeness": 0.2},
    "learning_rate": 0.1,
    "min_samples": 5
  }
}
```

---

## Test 2: Submit Feedback & Verify Storage

**Purpose:** Test feedback submission and check data is stored correctly

```bash
# Submit positive feedback
curl -X POST http://localhost:8000/api/feedback \
  -H "Content-Type: application/json" \
  -d '{
    "response_id": "test_001",
    "query": "Test query about Malaysian news",
    "answer": "Test answer with sources",
    "sources": [
      {
        "type": "internal",
        "title": "Test Article",
        "author": "Test Author",
        "url": "https://test.com",
        "relevance_score": 0.85,
        "sentiment": "Positive"
      }
    ],
    "feedback_type": "positive",
    "confidence": 0.75,
    "judge_scores": {
      "relevance": 9,
      "factuality": 8,
      "completeness": 9
    },
    "retrieval_method": "hybrid_search_with_reranking",
    "web_search_triggered": false
  }'

# Check feedback was saved
cat backend/data/feedback.json | python3 -m json.tool | tail -30

# Get feedback stats
curl -s http://localhost:8000/api/feedback/stats | python3 -m json.tool
```

**Expected Output:**
- Feedback file created/updated
- Stats show 1 total feedback, 1 positive

---

## Test 3: Trigger RL Optimization (5 Feedbacks)

**Purpose:** Test that RL optimization triggers after 5 feedbacks

**Script to submit 5 feedbacks:**
```bash
#!/bin/bash

# Submit 5 feedbacks simulating web search performing better than internal KB
for i in {1..5}; do
  # Alternate between web search (positive) and internal KB (negative)
  if [ $((i % 2)) -eq 0 ]; then
    # Web search - positive feedback
    curl -X POST http://localhost:8000/api/feedback \
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
      }"
  else
    # Internal KB - negative feedback
    curl -X POST http://localhost:8000/api/feedback \
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
      }"
  fi

  sleep 1
done

echo "\n\n=== Checking if RL adjusted parameters ==="
curl -s http://localhost:8000/api/rl/config | python3 -m json.tool
```

**Watch backend console logs for:**
```
[RL] Triggering optimization with 5 samples...
[RL] Made X adjustment(s)
  - web_search.confidence_threshold: 0.7 → 0.6X
    Reason: Web search outperforming...
```

**Expected:** Threshold should decrease (web search triggered more often)

---

## Test 4: Verify RL Parameters Are Used in Queries

**Purpose:** Confirm that learned RL parameters are actually used during query processing

```bash
# Ask a question that triggers the RL threshold check
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"query": "What is the latest news about Bank Negara Malaysia?"}' \
  | python3 -m json.tool
```

**Watch backend console logs for:**
```
[RL] Web search decision: confidence=0.XX, threshold=0.XX, trigger=True/False
[RL] Confidence calculation: retrieval=X.X, answer=X.X, final=0.XX
```

**Expected:**
- Logs show RL threshold being checked
- Threshold matches the learned value from config
- Confidence calculation uses RL weights

---

## Test 5: Test Performance Trend Analysis

**Purpose:** Verify performance tracking and trend detection

```bash
# Submit 10 more feedbacks with improving positive rate
#!/bin/bash

# First batch: 50% positive rate
for i in {1..5}; do
  if [ $i -le 2 ]; then
    feedback_type="positive"
  else
    feedback_type="negative"
  fi

  curl -X POST http://localhost:8000/api/feedback \
    -H "Content-Type: application/json" \
    -d "{
      \"response_id\": \"batch1_$i\",
      \"query\": \"Query $i\",
      \"answer\": \"Answer $i\",
      \"sources\": [],
      \"feedback_type\": \"$feedback_type\",
      \"confidence\": 0.7,
      \"judge_scores\": {\"relevance\": 7, \"factuality\": 7, \"completeness\": 7},
      \"retrieval_method\": \"hybrid_search_with_reranking\",
      \"web_search_triggered\": false
    }"
  sleep 0.5
done

# Second batch: 80% positive rate (improvement!)
for i in {1..5}; do
  if [ $i -le 4 ]; then
    feedback_type="positive"
  else
    feedback_type="negative"
  fi

  curl -X POST http://localhost:8000/api/feedback \
    -H "Content-Type: application/json" \
    -d "{
      \"response_id\": \"batch2_$i\",
      \"query\": \"Query $i\",
      \"answer\": \"Answer $i\",
      \"sources\": [],
      \"feedback_type\": \"$feedback_type\",
      \"confidence\": 0.75,
      \"judge_scores\": {\"relevance\": 8, \"factuality\": 8, \"completeness\": 8},
      \"retrieval_method\": \"hybrid_search_with_reranking\",
      \"web_search_triggered\": false
    }"
  sleep 0.5
done

# Check performance trend
echo "\n\n=== Performance Trend ==="
curl -s http://localhost:8000/api/rl/config | python3 -m json.tool | grep -A 10 "performance_trend"
```

**Expected Output:**
```json
"performance_trend": {
  "status": "success",
  "recent_positive_rate": 0.80,
  "older_positive_rate": 0.50,
  "improvement": 0.30,
  "improvement_percent": 30.0,
  "trend": "improving"
}
```

---

## Quick Test Script (All-in-One)

Save as `test_rl.sh`:

```bash
#!/bin/bash

echo "======================================"
echo "RL System Test Suite"
echo "======================================"

echo "\n[Test 1] Checking RL Config..."
curl -s http://localhost:8000/api/rl/config | python3 -m json.tool | head -20

echo "\n\n[Test 2] Submitting test feedback..."
curl -s -X POST http://localhost:8000/api/feedback \
  -H "Content-Type: application/json" \
  -d '{
    "response_id": "test_001",
    "query": "Test",
    "answer": "Test answer",
    "sources": [{"type": "internal", "title": "Test", "author": "Test", "url": "", "relevance_score": 0.8, "sentiment": "Positive"}],
    "feedback_type": "positive",
    "confidence": 0.7,
    "judge_scores": {"relevance": 8, "factuality": 8, "completeness": 8},
    "retrieval_method": "hybrid",
    "web_search_triggered": false
  }' | python3 -m json.tool

echo "\n\n[Test 3] Checking feedback stats..."
curl -s http://localhost:8000/api/feedback/stats | python3 -m json.tool

echo "\n\n[Test 4] Testing query with RL (watch console logs)..."
curl -s -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"query": "What are the latest Malaysian news?"}' \
  | python3 -m json.tool | head -30

echo "\n\n[Test 5] Checking recommendations..."
curl -s http://localhost:8000/api/feedback/recommendations | python3 -m json.tool

echo "\n\n======================================"
echo "Tests Complete!"
echo "Check backend console for RL logs"
echo "======================================"
```

**Run with:**
```bash
chmod +x test_rl.sh
./test_rl.sh
```

---

## Expected Console Output Patterns

When RL is working correctly, you should see:

```
✓ RL Config initialized (threshold: 0.70)
[RL] Web search decision: confidence=0.65, threshold=0.70, trigger=True
[RL] Confidence calculation: retrieval=7.0, answer=8.5, final=0.77
[RL] Triggering optimization with 5 samples...
[RL] Made 1 adjustment(s)
  - web_search.confidence_threshold: 0.7 → 0.63
    Reason: Web search outperforming (75% vs 40%)
```

---

## Troubleshooting

**If RL doesn't trigger:**
- Check that you have at least 5 feedbacks
- Verify `min_samples` in config is set to 5
- Check backend console for errors

**If parameters don't change:**
- Ensure feedback patterns are significant (>15% difference)
- Check learning_rate in config (should be 0.1)
- Verify enough samples for statistical significance

**If API errors:**
- Check backend is running: `curl http://localhost:8000/api/rl/config`
- Verify feedback.json and rl_config.json exist in data/
- Check backend console for error traces
