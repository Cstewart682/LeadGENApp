#!/usr/bin/env python3
"""
Google News Monitoring Module

Searches Google News for company mentions and detects buying signals
from recent news articles, press releases, and announcements
"""

import requests
from bs4 import BeautifulSoup
from urllib.parse import quote_plus
from datetime import datetime, timedelta
from typing import List, Dict
import re

class NewsMonitor:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }

        # Keywords that indicate buying signals
        self.signal_keywords = {
            # High-value signals
            'awarded contract': 40,
            'wins contract': 40,
            'contract award': 40,
            'secures contract': 40,
            'expansion': 30,
            'expands': 30,
            'expanding': 30,
            'investment': 30,
            'invests': 30,
            'investing': 30,
            'new facility': 35,
            'new plant': 35,
            'new location': 30,
            'opens facility': 30,
            'procurement': 30,

            # Medium-value signals
            'hiring': 20,
            'now hiring': 25,
            'job opening': 20,
            'careers': 15,
            'new equipment': 25,
            'equipment purchase': 25,
            'upgrade': 20,
            'upgrades': 20,
            'upgrading': 20,
            'modernization': 20,
            'renovation': 20,
            'project': 15,

            # Executive changes (opportunity)
            'new ceo': 25,
            'new president': 25,
            'appoints': 20,
            'executive': 15,
        }

    def search_google_news(self, company_name: str, days_back: int = 90, location: str = "Calgary") -> List[Dict]:
        """
        Search Google News for recent articles about a company

        Args:
            company_name: Name of the company
            days_back: Number of days to search back
            location: Location filter

        Returns:
            List of news articles
        """
        articles = []

        try:
            # Build search query
            query = f'"{company_name}" {location}'
            search_url = f"https://www.google.com/search?q={quote_plus(query)}&tbm=nws"

            response = requests.get(search_url, headers=self.headers, timeout=10)
            soup = BeautifulSoup(response.text, 'html.parser')

            # Find news results
            for result in soup.find_all('div', class_='SoaBEf'):
                try:
                    # Extract title
                    title_elem = result.find('div', {'role': 'heading'})
                    title = title_elem.get_text() if title_elem else ''

                    # Extract link
                    link_elem = result.find('a', href=True)
                    link = link_elem['href'] if link_elem else ''

                    # Extract snippet
                    snippet_elem = result.find('div', class_='GI74Re')
                    snippet = snippet_elem.get_text() if snippet_elem else ''

                    # Extract date (if available)
                    date_elem = result.find('span', class_='OSrXXb')
                    date_text = date_elem.get_text() if date_elem else ''

                    if title and link:
                        articles.append({
                            'title': title,
                            'link': link,
                            'snippet': snippet,
                            'date': date_text,
                            'source': 'Google News'
                        })

                except Exception as e:
                    continue

        except Exception as e:
            print(f"Error searching Google News: {e}")

        return articles[:10]  # Return top 10 results

    def analyze_news_for_signals(self, articles: List[Dict]) -> tuple[List[Dict], int]:
        """
        Analyze news articles for buying signals

        Args:
            articles: List of news articles

        Returns:
            Tuple of (signals found, total score)
        """
        signals_found = []
        total_score = 0
        found_keywords = set()

        for article in articles:
            text = (article.get('title', '') + ' ' + article.get('snippet', '')).lower()

            for keyword, score in self.signal_keywords.items():
                if keyword in text and keyword not in found_keywords:
                    signals_found.append({
                        'keyword': keyword,
                        'score': score,
                        'article_title': article.get('title', ''),
                        'article_link': article.get('link', ''),
                        'context': article.get('snippet', '')[:150]
                    })
                    total_score += score
                    found_keywords.add(keyword)

        # Cap at 100
        total_score = min(total_score, 100)

        return signals_found, total_score

    def monitor_company_news(self, company_name: str, days_back: int = 90, location: str = "Calgary") -> Dict:
        """
        Complete news monitoring for a company

        Args:
            company_name: Name of the company
            days_back: Days to search back
            location: Location filter

        Returns:
            Dict with news analysis and signals
        """
        print(f"\n{'='*60}")
        print(f"NEWS MONITORING: {company_name}")
        print(f"{'='*60}")

        # Search news
        print(f"📰 Searching news for last {days_back} days...")
        articles = self.search_google_news(company_name, days_back, location)

        print(f"   Found {len(articles)} news articles")

        # Analyze for signals
        signals, score = self.analyze_news_for_signals(articles)

        result = {
            'company_name': company_name,
            'articles_found': len(articles),
            'articles': articles,
            'signal_score': score,
            'signals': signals,
            'search_date': datetime.now().isoformat()
        }

        print(f"   Signal Score: +{score} points from news")
        print(f"{'='*60}\n")

        return result


# Convenience function
def check_company_news(company_name: str, days_back: int = 90, location: str = "Calgary") -> Dict:
    """
    Check news for a company

    Args:
        company_name: Company to monitor
        days_back: Days to look back
        location: Location filter

    Returns:
        Dict with news and signals
    """
    monitor = NewsMonitor()
    return monitor.monitor_company_news(company_name, days_back, location)


# Test function
if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        company_name = " ".join(sys.argv[1:])
    else:
        company_name = "CMC Manufacturing"

    result = check_company_news(company_name)

    print("\n" + "="*60)
    print("NEWS MONITORING RESULTS")
    print("="*60)
    print(f"\nCompany: {result['company_name']}")
    print(f"Articles Found: {result['articles_found']}")

    if result['articles']:
        print(f"\nRecent News:")
        for i, article in enumerate(result['articles'][:5], 1):
            print(f"\n{i}. {article['title']}")
            print(f"   {article['link']}")
            if article.get('date'):
                print(f"   Date: {article['date']}")

    if result['signals']:
        print(f"\nBuying Signals Detected:")
        for signal in result['signals']:
            print(f"\n• {signal['keyword'].upper()} (+{signal['score']} points)")
            print(f"  Article: {signal['article_title']}")
            print(f"  Context: {signal['context']}")

        print(f"\nTotal Signal Boost: +{result['signal_score']} points")
    else:
        print("\nNo buying signals detected in recent news.")
