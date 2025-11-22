from openai import OpenAI
import pandas as pd
import json
from pathlib import Path
from typing import Dict, List
import os
from dotenv import load_dotenv
from datetime import datetime

load_dotenv()


class AnalyticsService:
    """Dataset analytics using OpenAI function calling"""

    def __init__(self, data_path: str):
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.model = os.getenv("LLM_MODEL", "gpt-4-turbo-preview")

        # Load data
        self.df = pd.read_csv(data_path)
        print(f"✓ Analytics service loaded with {len(self.df)} articles")

    def count_by_sentiment(self, sentiment: str = None) -> Dict:
        """
        Count articles by sentiment

        Args:
            sentiment: Optional filter (Positive/Negative/Neutral)

        Returns:
            Dictionary with counts
        """
        if sentiment:
            count = len(self.df[self.df['sentiment'].str.lower() == sentiment.lower()])
            return {
                "sentiment": sentiment,
                "count": int(count),
                "total": len(self.df)
            }
        else:
            counts = self.df['sentiment'].value_counts().to_dict()
            return {
                "counts": {k: int(v) for k, v in counts.items()},
                "total": len(self.df)
            }

    def count_by_date_range(self, start_date: str = None, end_date: str = None) -> Dict:
        """
        Count articles within date range

        Args:
            start_date: Start date (YYYY-MM-DD or DD-MM-YY)
            end_date: End date (YYYY-MM-DD or DD-MM-YY)

        Returns:
            Dictionary with count
        """
        df_filtered = self.df.copy()

        # Convert timestamp column to datetime
        df_filtered['datetime'] = pd.to_datetime(df_filtered['timestamp'], format='%d-%m-%y %H:%M', errors='coerce')

        if start_date:
            try:
                # Try multiple date formats
                for fmt in ['%Y-%m-%d', '%d-%m-%y', '%Y/%m/%d']:
                    try:
                        start_dt = datetime.strptime(start_date, fmt)
                        df_filtered = df_filtered[df_filtered['datetime'] >= start_dt]
                        break
                    except:
                        continue
            except:
                pass

        if end_date:
            try:
                for fmt in ['%Y-%m-%d', '%d-%m-%y', '%Y/%m/%d']:
                    try:
                        end_dt = datetime.strptime(end_date, fmt)
                        df_filtered = df_filtered[df_filtered['datetime'] <= end_dt]
                        break
                    except:
                        continue
            except:
                pass

        return {
            "count": len(df_filtered),
            "start_date": start_date,
            "end_date": end_date,
            "total": len(self.df)
        }

    def count_by_author(self, author: str = None) -> Dict:
        """
        Count articles by author/source

        Args:
            author: Optional author name to filter

        Returns:
            Dictionary with counts
        """
        if author:
            count = len(self.df[self.df['author'].str.contains(author, case=False, na=False)])
            return {
                "author": author,
                "count": int(count),
                "total": len(self.df)
            }
        else:
            counts = self.df['author'].value_counts().head(10).to_dict()
            return {
                "top_authors": {k: int(v) for k, v in counts.items()},
                "total": len(self.df)
            }

    def get_statistics(self) -> Dict:
        """
        Get overall dataset statistics

        Returns:
            Dictionary with various statistics
        """
        sentiment_counts = self.df['sentiment'].value_counts().to_dict()
        author_counts = len(self.df['author'].unique())

        # Get date range
        self.df['datetime'] = pd.to_datetime(self.df['timestamp'], format='%d-%m-%y %H:%M', errors='coerce')
        earliest = self.df['datetime'].min()
        latest = self.df['datetime'].max()

        return {
            "total_articles": len(self.df),
            "sentiment_distribution": {k: int(v) for k, v in sentiment_counts.items()},
            "unique_authors": int(author_counts),
            "date_range": {
                "earliest": earliest.strftime('%Y-%m-%d') if pd.notna(earliest) else None,
                "latest": latest.strftime('%Y-%m-%d') if pd.notna(latest) else None
            }
        }

    def process_query(self, query: str) -> Dict:
        """
        Process natural language analytics query using OpenAI function calling

        Args:
            query: Natural language question about the dataset

        Returns:
            Dictionary with answer and data
        """
        # Define available functions for OpenAI
        functions = [
            {
                "name": "count_by_sentiment",
                "description": "Count articles by sentiment (positive, negative, or neutral)",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "sentiment": {
                            "type": "string",
                            "description": "Sentiment to filter by: Positive, Negative, or Neutral. Leave empty for all sentiments.",
                            "enum": ["Positive", "Negative", "Neutral", ""]
                        }
                    }
                }
            },
            {
                "name": "count_by_date_range",
                "description": "Count articles within a specific date range",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "start_date": {
                            "type": "string",
                            "description": "Start date in format YYYY-MM-DD or DD-MM-YY"
                        },
                        "end_date": {
                            "type": "string",
                            "description": "End date in format YYYY-MM-DD or DD-MM-YY"
                        }
                    }
                }
            },
            {
                "name": "count_by_author",
                "description": "Count articles by author or news source",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "author": {
                            "type": "string",
                            "description": "Author name or news source to filter by. Leave empty for top authors."
                        }
                    }
                }
            },
            {
                "name": "get_statistics",
                "description": "Get overall dataset statistics including total articles, sentiment distribution, and date range",
                "parameters": {
                    "type": "object",
                    "properties": {}
                }
            }
        ]

        try:
            # Call OpenAI with function calling
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a helpful data analyst. Use the available functions to answer questions about the news dataset."},
                    {"role": "user", "content": query}
                ],
                functions=functions,
                function_call="auto",
                temperature=0.3
            )

            message = response.choices[0].message

            # Check if function was called
            if message.function_call:
                function_name = message.function_call.name
                function_args = json.loads(message.function_call.arguments)

                print(f"[Analytics] Calling function: {function_name}")
                print(f"[Analytics] Arguments: {function_args}")

                # Execute the appropriate function
                if function_name == "count_by_sentiment":
                    data = self.count_by_sentiment(**function_args)
                    query_type = "sentiment_count"
                elif function_name == "count_by_date_range":
                    data = self.count_by_date_range(**function_args)
                    query_type = "date_range_count"
                elif function_name == "count_by_author":
                    data = self.count_by_author(**function_args)
                    query_type = "author_count"
                elif function_name == "get_statistics":
                    data = self.get_statistics()
                    query_type = "overall_statistics"
                else:
                    data = {"error": "Unknown function"}
                    query_type = "unknown"

                # Generate natural language answer
                answer_response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": "You are a helpful data analyst. Provide a clear, concise natural language answer based on the data provided."},
                        {"role": "user", "content": f"Question: {query}\n\nData: {json.dumps(data)}\n\nProvide a natural language answer to the question based on this data."}
                    ],
                    temperature=0.5,
                    max_tokens=300
                )

                answer = answer_response.choices[0].message.content

                return {
                    "answer": answer,
                    "data": data,
                    "query_type": query_type
                }
            else:
                # No function called, use direct response
                return {
                    "answer": message.content,
                    "data": {},
                    "query_type": "general"
                }

        except Exception as e:
            print(f"Error processing analytics query: {e}")
            return {
                "answer": f"I encountered an error processing your query: {str(e)}",
                "data": {},
                "query_type": "error"
            }


def test_analytics():
    """Test analytics service"""
    from pathlib import Path

    base_dir = Path(__file__).parent.parent.parent
    data_path = base_dir / "data" / "news.csv"

    analytics = AnalyticsService(str(data_path))

    # Test queries
    queries = [
        "How many positive and negative news are there?",
        "How many articles are from June 2025?",
        "What are the overall statistics of the dataset?",
        "How many articles did FMT Reporters write?"
    ]

    for query in queries:
        print(f"\n{'='*80}")
        print(f"Query: {query}")
        print(f"{'='*80}")

        result = analytics.process_query(query)

        print(f"\nAnswer: {result['answer']}")
        print(f"\nData: {json.dumps(result['data'], indent=2)}")


if __name__ == "__main__":
    test_analytics()
