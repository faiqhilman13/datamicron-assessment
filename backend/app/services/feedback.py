from typing import List, Dict, Optional, Literal
from datetime import datetime
import json
import os
from pathlib import Path
from collections import defaultdict
from .rl_optimizer import RLOptimizer


class FeedbackService:
    """Service for collecting and analyzing user feedback"""

    def __init__(self, feedback_file: str = "data/feedback.json"):
        """
        Initialize feedback service

        Args:
            feedback_file: Path to JSON file storing feedback data
        """
        self.feedback_file = Path(feedback_file)
        self.feedback_file.parent.mkdir(parents=True, exist_ok=True)

        # Initialize feedback file if it doesn't exist
        if not self.feedback_file.exists():
            self._save_feedback([])

        # Initialize RL optimizer
        self.rl_optimizer = RLOptimizer()

        print(f"✓ Feedback service initialized (storage: {self.feedback_file})")

    def _load_feedback(self) -> List[Dict]:
        """Load all feedback from storage"""
        try:
            with open(self.feedback_file, 'r') as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            return []

    def _save_feedback(self, feedback_data: List[Dict]):
        """Save feedback to storage"""
        with open(self.feedback_file, 'w') as f:
            json.dump(feedback_data, f, indent=2, ensure_ascii=False)

    def submit_feedback(
        self,
        response_id: str,
        query: str,
        answer: str,
        sources: List[Dict],
        feedback_type: Literal["positive", "negative"],
        confidence: float,
        judge_scores: Dict,
        retrieval_method: str,
        web_search_triggered: bool,
        comment: Optional[str] = None
    ) -> Dict:
        """
        Submit user feedback for a response

        Args:
            response_id: Unique identifier for the response
            query: User's original query
            answer: AI's answer
            sources: Sources used in the response
            feedback_type: "positive" or "negative"
            confidence: System confidence score
            judge_scores: LLM judge scores
            retrieval_method: Method used for retrieval
            web_search_triggered: Whether web search was used
            comment: Optional user comment

        Returns:
            Confirmation dict with feedback_id
        """
        feedback_data = self._load_feedback()

        feedback_entry = {
            "feedback_id": f"fb_{len(feedback_data) + 1}_{int(datetime.now().timestamp())}",
            "response_id": response_id,
            "timestamp": datetime.now().isoformat(),
            "query": query,
            "answer": answer,
            "sources": sources,
            "feedback_type": feedback_type,
            "confidence": confidence,
            "judge_scores": judge_scores,
            "retrieval_method": retrieval_method,
            "web_search_triggered": web_search_triggered,
            "comment": comment
        }

        feedback_data.append(feedback_entry)
        self._save_feedback(feedback_data)

        print(f"✓ Feedback recorded: {feedback_type} for response {response_id}")

        # Trigger RL optimization if we have enough samples
        min_samples = self.rl_optimizer.config.get('min_samples', 5)
        if len(feedback_data) >= min_samples and len(feedback_data) % min_samples == 0:
            print(f"\n[RL] Triggering optimization with {len(feedback_data)} samples...")
            adjustments = self.rl_optimizer.update_from_feedback(feedback_data)
            if adjustments.get('changes'):
                print(f"[RL] Made {len(adjustments['changes'])} adjustment(s)")
                for change in adjustments['changes']:
                    print(f"  - {change['parameter']}: {change['old_value']} → {change['new_value']}")
                    print(f"    Reason: {change['reason']}")

        return {
            "status": "success",
            "feedback_id": feedback_entry["feedback_id"],
            "message": f"{feedback_type.capitalize()} feedback recorded"
        }

    def get_feedback_stats(self) -> Dict:
        """
        Get overall feedback statistics

        Returns:
            Dict with aggregated feedback stats
        """
        feedback_data = self._load_feedback()

        if not feedback_data:
            return {
                "total_feedback": 0,
                "positive": 0,
                "negative": 0,
                "positive_rate": 0.0
            }

        positive = sum(1 for f in feedback_data if f["feedback_type"] == "positive")
        negative = sum(1 for f in feedback_data if f["feedback_type"] == "negative")

        return {
            "total_feedback": len(feedback_data),
            "positive": positive,
            "negative": negative,
            "positive_rate": positive / len(feedback_data) if feedback_data else 0.0,
            "web_search_feedback": self._analyze_web_search_feedback(feedback_data),
            "confidence_correlation": self._analyze_confidence_correlation(feedback_data)
        }

    def _analyze_web_search_feedback(self, feedback_data: List[Dict]) -> Dict:
        """Analyze feedback for web search vs internal KB"""
        web_positive = sum(1 for f in feedback_data
                          if f.get("web_search_triggered") and f["feedback_type"] == "positive")
        web_total = sum(1 for f in feedback_data if f.get("web_search_triggered"))

        internal_positive = sum(1 for f in feedback_data
                               if not f.get("web_search_triggered") and f["feedback_type"] == "positive")
        internal_total = sum(1 for f in feedback_data if not f.get("web_search_triggered"))

        return {
            "web_search": {
                "total": web_total,
                "positive": web_positive,
                "positive_rate": web_positive / web_total if web_total > 0 else 0.0
            },
            "internal_kb": {
                "total": internal_total,
                "positive": internal_positive,
                "positive_rate": internal_positive / internal_total if internal_total > 0 else 0.0
            }
        }

    def _analyze_confidence_correlation(self, feedback_data: List[Dict]) -> Dict:
        """Analyze correlation between system confidence and user feedback"""
        if not feedback_data:
            return {"correlation": "insufficient_data"}

        # Group by confidence ranges
        ranges = {
            "low (0-0.3)": {"positive": 0, "total": 0},
            "medium (0.3-0.7)": {"positive": 0, "total": 0},
            "high (0.7-1.0)": {"positive": 0, "total": 0}
        }

        for f in feedback_data:
            conf = f.get("confidence", 0.5)
            if conf < 0.3:
                range_key = "low (0-0.3)"
            elif conf < 0.7:
                range_key = "medium (0.3-0.7)"
            else:
                range_key = "high (0.7-1.0)"

            ranges[range_key]["total"] += 1
            if f["feedback_type"] == "positive":
                ranges[range_key]["positive"] += 1

        # Calculate positive rates
        for range_key in ranges:
            total = ranges[range_key]["total"]
            ranges[range_key]["positive_rate"] = (
                ranges[range_key]["positive"] / total if total > 0 else 0.0
            )

        return ranges

    def get_failed_queries(self, limit: int = 10) -> List[Dict]:
        """
        Get queries with negative feedback for retraining

        Args:
            limit: Maximum number of failed queries to return

        Returns:
            List of queries with negative feedback
        """
        feedback_data = self._load_feedback()

        negative_feedback = [
            {
                "query": f["query"],
                "answer": f["answer"],
                "timestamp": f["timestamp"],
                "confidence": f.get("confidence", 0),
                "judge_scores": f.get("judge_scores", {}),
                "comment": f.get("comment")
            }
            for f in feedback_data
            if f["feedback_type"] == "negative"
        ]

        # Sort by most recent
        negative_feedback.sort(key=lambda x: x["timestamp"], reverse=True)

        return negative_feedback[:limit]

    def get_adjustment_recommendations(self) -> Dict:
        """
        Get recommendations for adjusting retrieval based on feedback

        Returns:
            Dict with recommended adjustments
        """
        feedback_data = self._load_feedback()

        if len(feedback_data) < 10:
            return {
                "status": "insufficient_data",
                "message": "Need at least 10 feedback entries for recommendations",
                "current_feedback_count": len(feedback_data)
            }

        stats = self.get_feedback_stats()

        recommendations = []

        # Recommend web search threshold adjustment
        web_stats = stats["web_search_feedback"]["web_search"]
        internal_stats = stats["web_search_feedback"]["internal_kb"]

        if web_stats["total"] > 5 and internal_stats["total"] > 5:
            if web_stats["positive_rate"] > internal_stats["positive_rate"] + 0.2:
                recommendations.append({
                    "type": "web_search_threshold",
                    "action": "decrease",
                    "reason": f"Web search has {web_stats['positive_rate']:.1%} positive rate vs {internal_stats['positive_rate']:.1%} for internal KB",
                    "suggested_threshold": 0.6  # Lower threshold = trigger web search more often
                })
            elif internal_stats["positive_rate"] > web_stats["positive_rate"] + 0.2:
                recommendations.append({
                    "type": "web_search_threshold",
                    "action": "increase",
                    "reason": f"Internal KB has {internal_stats['positive_rate']:.1%} positive rate vs {web_stats['positive_rate']:.1%} for web search",
                    "suggested_threshold": 0.9  # Higher threshold = trust internal KB more
                })

        # Recommend confidence calibration
        conf_corr = stats["confidence_correlation"]
        if conf_corr.get("high (0.7-1.0)", {}).get("total", 0) > 3:
            high_conf_rate = conf_corr["high (0.7-1.0)"]["positive_rate"]
            if high_conf_rate < 0.6:
                recommendations.append({
                    "type": "confidence_calibration",
                    "action": "recalibrate",
                    "reason": f"High confidence responses only have {high_conf_rate:.1%} positive rate",
                    "suggestion": "Consider adjusting confidence calculation weights"
                })

        return {
            "status": "success",
            "total_feedback": len(feedback_data),
            "recommendations": recommendations
        }


def test_feedback_service():
    """Test feedback service"""
    service = FeedbackService("data/test_feedback.json")

    # Submit test feedback
    result = service.submit_feedback(
        response_id="resp_123",
        query="Test query",
        answer="Test answer",
        sources=[],
        feedback_type="positive",
        confidence=0.8,
        judge_scores={"relevance": 9, "factuality": 8, "completeness": 9},
        retrieval_method="hybrid",
        web_search_triggered=False
    )

    print(f"\nFeedback submitted: {result}")

    # Get stats
    stats = service.get_feedback_stats()
    print(f"\nFeedback stats: {json.dumps(stats, indent=2)}")


if __name__ == "__main__":
    test_feedback_service()
