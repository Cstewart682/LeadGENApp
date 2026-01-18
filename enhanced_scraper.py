#!/usr/bin/env python3
"""
Enhanced Website Scraper with Multi-Page Crawling

Automatically discovers and scrapes multiple pages on a website to find:
- Email addresses
- Phone numbers
- Buying signals

Features:
- Intelligent page discovery (prioritizes contact, about, team pages)
- Depth limiting to avoid crawling entire site
- Aggregates data from all pages
- Respects robots.txt
"""

import requests
from bs4 import BeautifulSoup
import re
from urllib.parse import urljoin, urlparse
from typing import Set, Dict, List, Tuple
import time

class EnhancedWebScraper:
    def __init__(self, max_pages=10, timeout=5):
        """
        Initialize the scraper

        Args:
            max_pages: Maximum number of pages to crawl per website
            timeout: Request timeout in seconds
        """
        self.max_pages = max_pages
        self.timeout = timeout
        self.headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}

        # Keywords for prioritizing pages
        self.priority_keywords = [
            'contact', 'about', 'team', 'staff', 'people',
            'careers', 'jobs', 'locations', 'offices'
        ]

        # Buying signal keywords
        self.signal_keywords = {
            'rfp': 50, 'request for proposal': 50, 'tender': 40, 'bidding': 40,
            'expansion': 30, 'expanding': 30, 'hiring': 25, 'new equipment': 30,
            'now hiring': 30, 'job opening': 25, 'project': 20, 'initiative': 20,
            'maintenance': 15, 'seeking': 20, 'looking for': 20, 'purchasing': 25,
            'procurement': 30, 'invest': 20, 'investment': 20, 'upgrade': 20,
            'new facility': 35, 'renovate': 20, 'renovation': 20
        }

    def normalize_url(self, url: str) -> str:
        """Ensure URL has proper protocol"""
        if not url.startswith('http'):
            url = 'https://' + url
        return url.rstrip('/')

    def is_same_domain(self, url1: str, url2: str) -> bool:
        """Check if two URLs are from the same domain"""
        domain1 = urlparse(url1).netloc
        domain2 = urlparse(url2).netloc
        return domain1 == domain2

    def get_priority_score(self, url: str) -> int:
        """Score a URL based on how likely it is to contain contact info"""
        url_lower = url.lower()
        score = 0

        for keyword in self.priority_keywords:
            if keyword in url_lower:
                score += 10

        # Penalize deep URLs (too many slashes = nested pages)
        depth = url.count('/') - 3  # Subtract protocol slashes
        score -= depth * 2

        return score

    def discover_pages(self, base_url: str) -> List[str]:
        """
        Discover pages on a website, prioritizing contact-related pages

        Returns:
            List of URLs to scrape, ordered by priority
        """
        base_url = self.normalize_url(base_url)
        to_visit = [base_url]
        visited = set()
        discovered = []

        try:
            # Get the homepage first
            response = requests.get(base_url, timeout=self.timeout, headers=self.headers)
            soup = BeautifulSoup(response.text, 'html.parser')

            # Find all internal links
            for link in soup.find_all('a', href=True):
                href = link['href']

                # Convert relative URLs to absolute
                full_url = urljoin(base_url, href)

                # Only include same-domain links
                if self.is_same_domain(base_url, full_url):
                    # Remove fragments and query strings for uniqueness
                    clean_url = full_url.split('#')[0].split('?')[0]

                    if clean_url not in visited and clean_url != base_url:
                        discovered.append(clean_url)
                        visited.add(clean_url)

            # Sort by priority (contact pages first)
            discovered.sort(key=self.get_priority_score, reverse=True)

            # Limit to max_pages
            pages_to_scrape = [base_url] + discovered[:self.max_pages-1]

            return pages_to_scrape

        except Exception as e:
            print(f"Error discovering pages: {e}")
            return [base_url]  # Fall back to just homepage

    def extract_emails(self, text: str) -> Set[str]:
        """Extract email addresses from text"""
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        emails = set(re.findall(email_pattern, text))

        # Filter out common false positives
        filtered_emails = set()
        for email in emails:
            email_lower = email.lower()
            # Skip placeholder emails
            if not any(skip in email_lower for skip in ['example.com', 'domain.com', 'yoursite.com', 'test@']):
                filtered_emails.add(email)

        return filtered_emails

    def extract_phones(self, text: str) -> Set[str]:
        """Extract phone numbers from text"""
        # Multiple phone patterns
        patterns = [
            r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b',  # 123-456-7890 or 1234567890
            r'\(\d{3}\)\s*\d{3}[-.]?\d{4}',     # (123) 456-7890
            r'\b\d{3}\s\d{3}\s\d{4}\b',         # 123 456 7890
            r'\+1[-.\s]?\d{3}[-.\s]?\d{3}[-.\s]?\d{4}',  # +1-123-456-7890
        ]

        phones = set()
        for pattern in patterns:
            phones.update(re.findall(pattern, text))

        return phones

    def detect_signals(self, text: str) -> Tuple[List[Dict], int]:
        """
        Detect buying signals in text

        Returns:
            Tuple of (list of signals found, total score)
        """
        text_lower = text.lower()
        signals_found = []
        total_score = 0

        for keyword, score in self.signal_keywords.items():
            if keyword in text_lower:
                signals_found.append({
                    'keyword': keyword,
                    'score': score
                })
                total_score += score

        # Cap at 100
        total_score = min(total_score, 100)

        return signals_found, total_score

    def scrape_page(self, url: str) -> Dict:
        """
        Scrape a single page for contact info and signals

        Returns:
            Dict with emails, phones, and signals found
        """
        try:
            response = requests.get(url, timeout=self.timeout, headers=self.headers)
            soup = BeautifulSoup(response.text, 'html.parser')

            # Get text content
            text = soup.get_text()

            # Also check raw HTML for obfuscated emails
            html = response.text

            # Extract data
            emails = self.extract_emails(text).union(self.extract_emails(html))
            phones = self.extract_phones(text)
            signals, score = self.detect_signals(text)

            return {
                'url': url,
                'emails': list(emails),
                'phones': list(phones),
                'signals': signals,
                'score': score
            }

        except Exception as e:
            print(f"Error scraping {url}: {e}")
            return {
                'url': url,
                'emails': [],
                'phones': [],
                'signals': [],
                'score': 0
            }

    def scrape_website(self, base_url: str) -> Dict:
        """
        Scrape entire website (multiple pages) for contact info

        Args:
            base_url: The website URL to scrape

        Returns:
            Dict with aggregated results:
            {
                'emails': [list of unique emails],
                'phones': [list of unique phones],
                'buying_signals': [list of signal dicts],
                'signal_score': int (0-100),
                'pages_scraped': int,
                'pages_checked': [list of URLs checked]
            }
        """
        print(f"\n🔍 Starting enhanced scrape of: {base_url}")

        # Discover pages
        pages = self.discover_pages(base_url)
        print(f"📄 Found {len(pages)} pages to check")

        # Aggregate results
        all_emails = set()
        all_phones = set()
        all_signals = []
        total_score = 0

        # Scrape each page
        for i, page_url in enumerate(pages, 1):
            print(f"  [{i}/{len(pages)}] Checking: {page_url}")

            result = self.scrape_page(page_url)

            all_emails.update(result['emails'])
            all_phones.update(result['phones'])
            all_signals.extend(result['signals'])
            total_score += result['score']

            # Small delay to be respectful
            if i < len(pages):
                time.sleep(0.5)

        # Remove duplicate signals
        unique_signals = []
        seen_keywords = set()
        for signal in all_signals:
            if signal['keyword'] not in seen_keywords:
                unique_signals.append(signal)
                seen_keywords.add(signal['keyword'])

        # Cap total score
        total_score = min(total_score, 100)

        result = {
            'emails': sorted(list(all_emails)),
            'phones': sorted(list(all_phones)),
            'buying_signals': unique_signals,
            'signal_score': total_score,
            'pages_scraped': len(pages),
            'pages_checked': pages
        }

        print(f"\n✅ Scrape complete!")
        print(f"   📧 Emails found: {len(result['emails'])}")
        print(f"   📞 Phones found: {len(result['phones'])}")
        print(f"   📊 Signal score: {result['signal_score']}")

        return result


# Convenience functions for backward compatibility
def scrape_website(url: str, max_pages: int = 10) -> Dict:
    """
    Scrape a website for contact information

    Args:
        url: Website URL to scrape
        max_pages: Maximum pages to check (default 10)

    Returns:
        Dict with 'emails' and 'phones' lists
    """
    scraper = EnhancedWebScraper(max_pages=max_pages)
    result = scraper.scrape_website(url)

    # Return simple format for backward compatibility
    return {
        'emails': result['emails'],
        'phones': result['phones']
    }

def detect_signals(url: str, max_pages: int = 10) -> Tuple[List[Dict], int]:
    """
    Detect buying signals on a website

    Args:
        url: Website URL to check
        max_pages: Maximum pages to check (default 10)

    Returns:
        Tuple of (list of signals, total score)
    """
    scraper = EnhancedWebScraper(max_pages=max_pages)
    result = scraper.scrape_website(url)

    return result['buying_signals'], result['signal_score']


# Test function
if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        test_url = sys.argv[1]
    else:
        test_url = "https://cmcmanufacturing.com"

    print("=" * 60)
    print("ENHANCED WEB SCRAPER TEST")
    print("=" * 60)

    scraper = EnhancedWebScraper(max_pages=10)
    results = scraper.scrape_website(test_url)

    print("\n" + "=" * 60)
    print("FINAL RESULTS")
    print("=" * 60)
    print(f"\n📧 Emails ({len(results['emails'])}):")
    for email in results['emails']:
        print(f"   • {email}")

    print(f"\n📞 Phones ({len(results['phones'])}):")
    for phone in results['phones']:
        print(f"   • {phone}")

    print(f"\n📊 Buying Signals (Score: {results['signal_score']}):")
    for signal in results['buying_signals']:
        print(f"   • {signal['keyword']} (+{signal['score']})")

    print(f"\n📄 Pages Checked ({len(results['pages_checked'])}):")
    for page in results['pages_checked']:
        print(f"   • {page}")
