from openai import OpenAI
from typing import List, Dict, Tuple
import os
import json
from dotenv import load_dotenv

load_dotenv()


class LLMJudge:
    """LLM-as-a-Judge for evaluating retrieval quality and answer quality"""

    def __init__(self):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.model = os.getenv("LLM_MODEL", "gpt-4-turbo-preview")
        self.judge_threshold = float(os.getenv("JUDGE_THRESHOLD", "6.0"))

    def evaluate_retrieval_adequacy(self, query: str, documents: List[Dict]) -> Dict:
        """
        Evaluate if retrieved documents are adequate to answer the query

        Returns:
            {
                "is_adequate": bool,
                "confidence": float (0-10),
                "reasoning": str,
                "needs_web_search": bool
            }
        """
        # Prepare document summaries for evaluation
        doc_summaries = []
        for i, doc in enumerate(documents[:3], 1):  # Only top 3 for evaluation
            doc_summaries.append(f"{i}. {doc['title']}\n   Summary: {doc['summary'][:200]}")

        docs_text = "\n\n".join(doc_summaries)

        prompt = f"""You are an expert judge evaluating whether retrieved documents can adequately answer a user's question.

User Question: {query}

Retrieved Documents:
{docs_text}

Evaluate the retrieval quality and provide:
1. A confidence score (0-10) indicating how well these documents can answer the question
   - 0-3: Very poor, documents are irrelevant
   - 4-6: Mediocre, documents have some relevance but may not fully answer
   - 7-8: Good, documents likely contain the answer
   - 9-10: Excellent, documents clearly contain comprehensive information

2. Brief reasoning for your score
3. Whether web search is needed (if score < 7)

Respond in JSON format:
{{
    "confidence": <score>,
    "reasoning": "<brief explanation>",
    "needs_web_search": <true/false>
}}"""

        try:
            print(f"  → Asking LLM judge to evaluate retrieval adequacy...")
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                response_format={"type": "json_object"}
            )

            result = json.loads(response.choices[0].message.content)

            # Ensure needs_web_search aligns with threshold
            confidence = result.get("confidence", 5)
            result["is_adequate"] = confidence >= self.judge_threshold
            result["needs_web_search"] = confidence < self.judge_threshold

            print(f"    ✓ Judge confidence: {confidence}/10")
            print(f"    Reasoning: {result.get('reasoning', 'N/A')[:100]}...")
            print(f"    Web search needed: {result['needs_web_search']}")

            return result

        except Exception as e:
            print(f"Error in retrieval evaluation: {e}")
            # Default to conservative: assume web search needed
            return {
                "is_adequate": False,
                "confidence": 5,
                "reasoning": "Error during evaluation",
                "needs_web_search": True
            }

    def evaluate_answer_quality(
        self,
        query: str,
        answer: str,
        sources: List[Dict]
    ) -> Dict:
        """
        Evaluate the quality of generated answer

        Returns:
            {
                "relevance": int (0-10),
                "factuality": int (0-10),
                "completeness": int (0-10),
                "overall_score": float (0-10),
                "feedback": str
            }
        """
        # Prepare sources for context
        source_summaries = []
        for i, src in enumerate(sources[:3], 1):
            source_summaries.append(f"{i}. {src.get('title', 'N/A')}")

        sources_text = "\n".join(source_summaries)

        prompt = f"""You are an expert judge evaluating the quality of an AI-generated answer.

User Question: {query}

AI Answer: {answer}

Sources Used:
{sources_text}

Evaluate the answer on three criteria (0-10 scale each):

1. **Relevance**: Does the answer directly address the user's question?
2. **Factuality**: Is the answer factually accurate and supported by the sources?
3. **Completeness**: Does the answer fully address all aspects of the question?

Provide scores and brief feedback.

Respond in JSON format:
{{
    "relevance": <score>,
    "factuality": <score>,
    "completeness": <score>,
    "feedback": "<brief feedback>"
}}"""

        try:
            print(f"  → Asking LLM judge to evaluate answer quality...")
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                response_format={"type": "json_object"}
            )

            result = json.loads(response.choices[0].message.content)

            # Calculate overall score
            relevance = result.get("relevance", 5)
            factuality = result.get("factuality", 5)
            completeness = result.get("completeness", 5)

            result["overall_score"] = (relevance + factuality + completeness) / 3

            print(f"    ✓ Answer quality scores:")
            print(f"      Relevance: {relevance}/10")
            print(f"      Factuality: {factuality}/10")
            print(f"      Completeness: {completeness}/10")
            print(f"      Overall: {result['overall_score']:.1f}/10")
            print(f"    Feedback: {result.get('feedback', 'N/A')[:100]}...")

            return result

        except Exception as e:
            print(f"Error in answer evaluation: {e}")
            return {
                "relevance": 5,
                "factuality": 5,
                "completeness": 5,
                "overall_score": 5.0,
                "feedback": "Error during evaluation"
            }

    def verify_source_attribution(
        self,
        answer: str,
        sources: List[Dict]
    ) -> Dict:
        """
        Verify that the answer correctly attributes information to sources

        Returns:
            {
                "has_citations": bool,
                "citations_accurate": bool,
                "feedback": str
            }
        """
        source_titles = [src.get('title', '') for src in sources]
        sources_text = "\n".join([f"- {title}" for title in source_titles])

        prompt = f"""You are verifying source attribution in an AI answer.

Answer: {answer}

Available Sources:
{sources_text}

Check:
1. Does the answer include citations or references to sources?
2. Are the citations accurate (matching the available sources)?

Respond in JSON format:
{{
    "has_citations": <true/false>,
    "citations_accurate": <true/false>,
    "feedback": "<brief explanation>"
}}"""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                response_format={"type": "json_object"}
            )

            result = json.loads(response.choices[0].message.content)
            return result

        except Exception as e:
            print(f"Error in citation verification: {e}")
            return {
                "has_citations": False,
                "citations_accurate": False,
                "feedback": "Error during verification"
            }


def test_llm_judge():
    """Test LLM judge functionality"""
    judge = LLMJudge()

    # Test retrieval adequacy
    query = "What are some initiatives launched by MCMC?"
    mock_docs = [
        {
            "title": "MCMC cadang bangun sistem amaran bencana lebih efisien",
            "summary": "MCMC plans to develop a disaster warning system that sends notifications directly to residents in affected areas."
        },
        {
            "title": "Sistem amaran bencana mudah alih lebih pantas sedang diusahakan",
            "summary": "Ministry of Communications proposes push notification project for disaster warnings in Budget 2026."
        }
    ]

    print("Testing Retrieval Adequacy Evaluation:")
    print("=" * 80)
    result = judge.evaluate_retrieval_adequacy(query, mock_docs)
    print(json.dumps(result, indent=2))

    # Test answer quality
    print("\n\nTesting Answer Quality Evaluation:")
    print("=" * 80)
    answer = "MCMC has launched several initiatives including a disaster warning system with push notifications."
    result = judge.evaluate_answer_quality(query, answer, mock_docs)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    test_llm_judge()
