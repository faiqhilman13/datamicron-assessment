"""
Reinforcement Learning Optimizer

This module implements active reinforcement learning that adjusts the RAG system
based on user feedback and LLM judge scores.
"""

from typing import Dict, List, Optional, Tuple
import json
from pathlib import Path
from datetime import datetime
from collections import defaultdict
import numpy as np


class RLConfig:
    """Dynamic configuration that adjusts based on feedback"""

    def __init__(self, config_path: str = "data/rl_config.json"):
        self.config_path = Path(config_path)
        self.config_path.parent.mkdir(parents=True, exist_ok=True)

        # Default configuration
        self.default_config = {
            "version": 1,
            "last_updated": datetime.now().isoformat(),
            "web_search": {
                "confidence_threshold": 0.7,  # Trigger web search if confidence < this
                "judge_threshold": 5,  # Trigger if LLM judge score < this
                "enabled": True
            },
            "confidence_weights": {
                "retrieval_eval": 0.5,  # Weight for retrieval adequacy
                "answer_quality": 0.5   # Weight for answer quality
            },
            "judge_weights": {
                "relevance": 0.4,
                "factuality": 0.4,
                "completeness": 0.2
            },
            "reranking": {
                "min_score_threshold": -12.0,  # Filter docs below this rerank score
                "top_k": 5  # Number of docs to use for generation
            },
            "learning_rate": 0.1,  # How aggressively to adjust (0-1)
            "min_samples": 5,  # Minimum feedback samples before adjusting
            "performance_history": []
        }

        # Load or initialize config
        self.config = self._load_config()

        print(f"✓ RL Config initialized (threshold: {self.config['web_search']['confidence_threshold']:.2f})")

    def _load_config(self) -> Dict:
        """Load configuration from file or create default"""
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r') as f:
                    loaded_config = json.load(f)
                    # Merge with defaults to ensure all keys exist
                    merged = self.default_config.copy()
                    merged.update(loaded_config)
                    return merged
            except Exception as e:
                print(f"Warning: Error loading RL config, using defaults: {e}")
                return self.default_config.copy()
        else:
            self._save_config(self.default_config)
            return self.default_config.copy()

    def _save_config(self, config: Dict):
        """Save configuration to file"""
        config['last_updated'] = datetime.now().isoformat()
        config['version'] = config.get('version', 1) + 1

        with open(self.config_path, 'w') as f:
            json.dump(config, f, indent=2)

    def get(self, key: str, default=None):
        """Get configuration value by dot-notation key"""
        keys = key.split('.')
        value = self.config
        for k in keys:
            if isinstance(value, dict):
                value = value.get(k, default)
            else:
                return default
        return value

    def update(self, updates: Dict):
        """Update configuration and save"""
        self.config.update(updates)
        self._save_config(self.config)
        print(f"✓ RL Config updated: {list(updates.keys())}")


class RLOptimizer:
    """
    Reinforcement Learning Optimizer

    Analyzes user feedback and LLM judge scores to automatically
    adjust system parameters for better performance.
    """

    def __init__(self, config_path: str = "data/rl_config.json"):
        self.config = RLConfig(config_path)

    def get_config(self) -> Dict:
        """Get current RL configuration"""
        return self.config.config.copy()

    def should_trigger_web_search(self, confidence: float, judge_score: float) -> bool:
        """
        Determine if web search should be triggered based on current thresholds

        Args:
            confidence: System confidence score (0-1)
            judge_score: LLM judge adequacy score (0-10)

        Returns:
            True if web search should be triggered
        """
        conf_threshold = self.config.get('web_search.confidence_threshold', 0.7)
        judge_threshold = self.config.get('web_search.judge_threshold', 5)

        return confidence < conf_threshold or judge_score < judge_threshold

    def calculate_weighted_confidence(
        self,
        retrieval_score: float,
        answer_score: float
    ) -> float:
        """
        Calculate weighted confidence based on learned weights

        Args:
            retrieval_score: Retrieval adequacy score (0-10)
            answer_score: Answer quality score (0-10)

        Returns:
            Weighted confidence (0-1)
        """
        weights = self.config.get('confidence_weights', {})
        w_retrieval = weights.get('retrieval_eval', 0.5)
        w_answer = weights.get('answer_quality', 0.5)

        # Normalize scores to 0-1
        retrieval_norm = retrieval_score / 10.0
        answer_norm = answer_score / 10.0

        confidence = (w_retrieval * retrieval_norm) + (w_answer * answer_norm)

        return max(0.0, min(1.0, confidence))

    def calculate_weighted_judge_score(self, judge_scores: Dict) -> float:
        """
        Calculate weighted judge score based on learned weights

        Args:
            judge_scores: Dict with relevance, factuality, completeness

        Returns:
            Weighted overall score (0-10)
        """
        weights = self.config.get('judge_weights', {})

        weighted_score = (
            weights.get('relevance', 0.4) * judge_scores.get('relevance', 5) +
            weights.get('factuality', 0.4) * judge_scores.get('factuality', 5) +
            weights.get('completeness', 0.2) * judge_scores.get('completeness', 5)
        )

        return max(0.0, min(10.0, weighted_score))

    def update_from_feedback(self, feedback_data: List[Dict]) -> Dict:
        """
        Analyze feedback and update RL configuration

        This is the core RL mechanism that learns from user feedback.

        Args:
            feedback_data: List of feedback entries

        Returns:
            Dict with adjustments made
        """
        if len(feedback_data) < self.config.get('min_samples', 5):
            return {
                "status": "insufficient_data",
                "message": f"Need at least {self.config.get('min_samples', 5)} samples",
                "current_samples": len(feedback_data)
            }

        adjustments = {
            "timestamp": datetime.now().isoformat(),
            "changes": []
        }

        # Analyze web search effectiveness
        web_adjustment = self._analyze_web_search_performance(feedback_data)
        if web_adjustment:
            adjustments["changes"].append(web_adjustment)

        # Analyze confidence calibration
        confidence_adjustment = self._analyze_confidence_calibration(feedback_data)
        if confidence_adjustment:
            adjustments["changes"].append(confidence_adjustment)

        # Analyze judge score correlation
        judge_adjustment = self._analyze_judge_correlation(feedback_data)
        if judge_adjustment:
            adjustments["changes"].append(judge_adjustment)

        # Save performance metrics
        self._record_performance(feedback_data)

        return adjustments

    def _analyze_web_search_performance(self, feedback_data: List[Dict]) -> Optional[Dict]:
        """
        Analyze if web search threshold should be adjusted

        Returns adjustment dict or None
        """
        web_feedback = [f for f in feedback_data if f.get('web_search_triggered')]
        internal_feedback = [f for f in feedback_data if not f.get('web_search_triggered')]

        if len(web_feedback) < 3 or len(internal_feedback) < 3:
            return None

        web_positive_rate = sum(1 for f in web_feedback if f['feedback_type'] == 'positive') / len(web_feedback)
        internal_positive_rate = sum(1 for f in internal_feedback if f['feedback_type'] == 'positive') / len(internal_feedback)

        current_threshold = self.config.get('web_search.confidence_threshold', 0.7)
        learning_rate = self.config.get('learning_rate', 0.1)

        adjustment_needed = False
        new_threshold = current_threshold

        # If web search performs significantly better, lower threshold (use it more)
        if web_positive_rate > internal_positive_rate + 0.15:
            delta = (web_positive_rate - internal_positive_rate) * learning_rate
            new_threshold = max(0.5, current_threshold - delta)
            adjustment_needed = True
            reason = f"Web search outperforming ({web_positive_rate:.1%} vs {internal_positive_rate:.1%})"

        # If internal KB performs better, raise threshold (trust it more)
        elif internal_positive_rate > web_positive_rate + 0.15:
            delta = (internal_positive_rate - web_positive_rate) * learning_rate
            new_threshold = min(0.9, current_threshold + delta)
            adjustment_needed = True
            reason = f"Internal KB outperforming ({internal_positive_rate:.1%} vs {web_positive_rate:.1%})"

        if adjustment_needed:
            self.config.update({
                'web_search': {
                    **self.config.config['web_search'],
                    'confidence_threshold': new_threshold
                }
            })

            return {
                "parameter": "web_search.confidence_threshold",
                "old_value": current_threshold,
                "new_value": new_threshold,
                "reason": reason,
                "impact": "Web search will be " + ("triggered more often" if new_threshold < current_threshold else "triggered less often")
            }

        return None

    def _analyze_confidence_calibration(self, feedback_data: List[Dict]) -> Optional[Dict]:
        """
        Analyze if confidence weights should be adjusted

        High confidence responses should correlate with positive feedback
        """
        # Group feedback by confidence ranges
        ranges = {
            'high': [f for f in feedback_data if f.get('confidence', 0) >= 0.7],
            'medium': [f for f in feedback_data if 0.3 <= f.get('confidence', 0) < 0.7],
            'low': [f for f in feedback_data if f.get('confidence', 0) < 0.3]
        }

        # Check if high confidence is actually reliable
        if len(ranges['high']) >= 3:
            high_conf_positive_rate = sum(
                1 for f in ranges['high'] if f['feedback_type'] == 'positive'
            ) / len(ranges['high'])

            # If high confidence doesn't correlate with positive feedback, adjust weights
            if high_conf_positive_rate < 0.6:
                # Reduce reliance on current confidence calculation
                current_weights = self.config.get('confidence_weights', {})
                learning_rate = self.config.get('learning_rate', 0.1)

                # Shift weight towards answer quality (more reliable indicator)
                new_weights = {
                    'retrieval_eval': max(0.3, current_weights.get('retrieval_eval', 0.5) - learning_rate),
                    'answer_quality': min(0.7, current_weights.get('answer_quality', 0.5) + learning_rate)
                }

                self.config.update({
                    'confidence_weights': new_weights
                })

                return {
                    "parameter": "confidence_weights",
                    "old_value": current_weights,
                    "new_value": new_weights,
                    "reason": f"High confidence responses only {high_conf_positive_rate:.1%} positive",
                    "impact": "Confidence now relies more on answer quality than retrieval"
                }

        return None

    def _analyze_judge_correlation(self, feedback_data: List[Dict]) -> Optional[Dict]:
        """
        Analyze which judge criteria correlate best with user feedback

        Adjust judge weights to emphasize criteria that match user preferences
        """
        if len(feedback_data) < 10:
            return None

        # Calculate correlation between each judge metric and user feedback
        correlations = {}

        for metric in ['relevance', 'factuality', 'completeness']:
            scores = []
            feedback_values = []

            for f in feedback_data:
                judge_scores = f.get('judge_scores', {})
                if metric in judge_scores:
                    scores.append(judge_scores[metric])
                    feedback_values.append(1 if f['feedback_type'] == 'positive' else 0)

            if len(scores) >= 10:
                # Simple correlation: average score for positive vs negative feedback
                positive_avg = np.mean([scores[i] for i, fv in enumerate(feedback_values) if fv == 1])
                negative_avg = np.mean([scores[i] for i, fv in enumerate(feedback_values) if fv == 0])
                correlations[metric] = positive_avg - negative_avg

        if not correlations:
            return None

        # Adjust weights towards metrics with strongest correlation
        current_weights = self.config.get('judge_weights', {})
        learning_rate = self.config.get('learning_rate', 0.1) * 0.5  # More conservative

        # Normalize correlations to determine new weights
        total_corr = sum(abs(v) for v in correlations.values())
        if total_corr > 0:
            target_weights = {k: abs(v) / total_corr for k, v in correlations.items()}

            # Blend current weights with target weights
            new_weights = {}
            for metric in ['relevance', 'factuality', 'completeness']:
                current = current_weights.get(metric, 1/3)
                target = target_weights.get(metric, 1/3)
                new_weights[metric] = current * (1 - learning_rate) + target * learning_rate

            # Normalize to sum to 1.0
            total = sum(new_weights.values())
            new_weights = {k: v/total for k, v in new_weights.items()}

            # Only update if change is significant
            max_change = max(abs(new_weights[k] - current_weights.get(k, 0)) for k in new_weights)
            if max_change > 0.05:
                self.config.update({
                    'judge_weights': new_weights
                })

                return {
                    "parameter": "judge_weights",
                    "old_value": current_weights,
                    "new_value": new_weights,
                    "reason": f"Adjusting based on user feedback correlation",
                    "correlations": correlations,
                    "impact": f"{max(correlations, key=correlations.get)} is most important to users"
                }

        return None

    def _record_performance(self, feedback_data: List[Dict]):
        """Record performance metrics for tracking improvement over time"""
        if not feedback_data:
            return

        positive_rate = sum(1 for f in feedback_data if f['feedback_type'] == 'positive') / len(feedback_data)

        performance_entry = {
            "timestamp": datetime.now().isoformat(),
            "total_feedback": len(feedback_data),
            "positive_rate": positive_rate,
            "avg_confidence": np.mean([f.get('confidence', 0) for f in feedback_data]),
            "web_search_usage": sum(1 for f in feedback_data if f.get('web_search_triggered')) / len(feedback_data)
        }

        history = self.config.get('performance_history', [])
        history.append(performance_entry)

        # Keep only last 50 entries
        if len(history) > 50:
            history = history[-50:]

        self.config.update({
            'performance_history': history
        })

    def get_performance_trend(self) -> Dict:
        """Get performance improvement trend"""
        history = self.config.get('performance_history', [])

        if len(history) < 2:
            return {
                "status": "insufficient_data",
                "message": "Need at least 2 data points for trend analysis"
            }

        # Compare recent vs older performance
        recent = history[-5:] if len(history) >= 5 else history[-len(history)//2:]
        older = history[:5] if len(history) >= 10 else history[:len(history)//2]

        recent_positive_rate = np.mean([h['positive_rate'] for h in recent])
        older_positive_rate = np.mean([h['positive_rate'] for h in older])

        improvement = recent_positive_rate - older_positive_rate

        return {
            "status": "success",
            "recent_positive_rate": recent_positive_rate,
            "older_positive_rate": older_positive_rate,
            "improvement": improvement,
            "improvement_percent": improvement * 100,
            "trend": "improving" if improvement > 0.02 else "stable" if improvement > -0.02 else "declining",
            "total_data_points": len(history)
        }


def test_rl_optimizer():
    """Test RL optimizer with simulated feedback"""
    optimizer = RLOptimizer("data/test_rl_config.json")

    # Simulate feedback data
    feedback_data = [
        # Web search responses getting better feedback
        {"feedback_type": "positive", "web_search_triggered": True, "confidence": 0.5, "judge_scores": {"relevance": 9, "factuality": 9, "completeness": 8}},
        {"feedback_type": "positive", "web_search_triggered": True, "confidence": 0.6, "judge_scores": {"relevance": 8, "factuality": 9, "completeness": 7}},
        {"feedback_type": "positive", "web_search_triggered": True, "confidence": 0.55, "judge_scores": {"relevance": 9, "factuality": 8, "completeness": 8}},
        {"feedback_type": "positive", "web_search_triggered": True, "confidence": 0.6, "judge_scores": {"relevance": 8, "factuality": 9, "completeness": 9}},

        # Internal KB responses getting worse feedback
        {"feedback_type": "negative", "web_search_triggered": False, "confidence": 0.8, "judge_scores": {"relevance": 5, "factuality": 4, "completeness": 5}},
        {"feedback_type": "negative", "web_search_triggered": False, "confidence": 0.75, "judge_scores": {"relevance": 6, "factuality": 5, "completeness": 4}},
        {"feedback_type": "positive", "web_search_triggered": False, "confidence": 0.85, "judge_scores": {"relevance": 7, "factuality": 7, "completeness": 6}},
        {"feedback_type": "negative", "web_search_triggered": False, "confidence": 0.8, "judge_scores": {"relevance": 5, "factuality": 6, "completeness": 5}},
    ]

    print("\n=== Testing RL Optimizer ===\n")
    print(f"Initial config: {json.dumps(optimizer.get_config()['web_search'], indent=2)}")

    # Apply feedback
    adjustments = optimizer.update_from_feedback(feedback_data)

    print(f"\n=== Adjustments Made ===\n{json.dumps(adjustments, indent=2)}")
    print(f"\nNew config: {json.dumps(optimizer.get_config()['web_search'], indent=2)}")

    # Test trend analysis
    trend = optimizer.get_performance_trend()
    print(f"\n=== Performance Trend ===\n{json.dumps(trend, indent=2)}")


if __name__ == "__main__":
    test_rl_optimizer()
