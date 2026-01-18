#!/usr/bin/env python3
"""
LinkedIn Discovery Module

Automatically finds LinkedIn pages for companies and their employees
using Google search (no LinkedIn API needed - respects ToS)
"""

import requests
from bs4 import BeautifulSoup
from urllib.parse import quote_plus, urlparse
import re
import time
from typing import List, Dict

class LinkedInDiscovery:
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }

    def search_google(self, query: str, num_results: int = 5) -> List[str]:
        """
        Search Google and return URLs from results

        Args:
            query: Search query
            num_results: Number of results to return

        Returns:
            List of URLs
        """
        urls = []
        try:
            # Google search URL
            search_url = f"https://www.google.com/search?q={quote_plus(query)}&num={num_results}"

            response = requests.get(search_url, headers=self.headers, timeout=10)
            soup = BeautifulSoup(response.text, 'html.parser')

            # Find all links in search results
            for link in soup.find_all('a', href=True):
                href = link['href']

                # Google wraps URLs in /url?q=...
                if '/url?q=' in href:
                    # Extract the actual URL
                    url = href.split('/url?q=')[1].split('&')[0]
                    if url.startswith('http') and 'google.com' not in url:
                        urls.append(url)

            return urls[:num_results]

        except Exception as e:
            print(f"Google search error: {e}")
            return []

    def find_company_page(self, company_name: str) -> Dict:
        """
        Find LinkedIn company page

        Args:
            company_name: Name of the company

        Returns:
            Dict with company page info
        """
        print(f"🔍 Searching for {company_name} LinkedIn company page...")

        # Search for company page
        query = f"{company_name} site:linkedin.com/company"
        urls = self.search_google(query, num_results=3)

        # Filter to only actual LinkedIn company pages
        company_pages = []
        for url in urls:
            if 'linkedin.com/company/' in url:
                company_pages.append(url)

        result = {
            'company_name': company_name,
            'company_page': company_pages[0] if company_pages else None,
            'found': len(company_pages) > 0
        }

        if result['found']:
            print(f"   ✓ Found: {result['company_page']}")
        else:
            print(f"   ✗ No company page found")

        return result

    def find_employee_profiles(self, company_name: str, max_profiles: int = 10) -> List[str]:
        """
        Find LinkedIn profiles of employees at a company

        Args:
            company_name: Name of the company
            max_profiles: Maximum number of profiles to return

        Returns:
            List of LinkedIn profile URLs
        """
        print(f"🔍 Searching for {company_name} employee profiles...")

        # Search for employee profiles
        query = f"{company_name} site:linkedin.com/in"
        urls = self.search_google(query, num_results=max_profiles * 2)

        # Filter to only actual LinkedIn profile pages
        profiles = []
        for url in urls:
            if 'linkedin.com/in/' in url:
                # Clean the URL
                clean_url = url.split('?')[0]  # Remove query params
                if clean_url not in profiles:
                    profiles.append(clean_url)

        profiles = profiles[:max_profiles]

        print(f"   ✓ Found {len(profiles)} employee profiles")

        return profiles

    def discover_linkedin_info(self, company_name: str, max_employees: int = 10) -> Dict:
        """
        Complete LinkedIn discovery for a company

        Args:
            company_name: Name of the company
            max_employees: Maximum number of employee profiles to find

        Returns:
            Dict with all LinkedIn information
        """
        print(f"\n{'='*60}")
        print(f"LINKEDIN DISCOVERY: {company_name}")
        print(f"{'='*60}")

        result = {
            'company_name': company_name,
            'company_page': None,
            'employee_profiles': [],
            'employee_count': 0,
            'signal_score': 0,
            'signals': []
        }

        # Find company page
        company_info = self.find_company_page(company_name)
        result['company_page'] = company_info['company_page']

        if company_info['found']:
            result['signals'].append({
                'type': 'linkedin_presence',
                'description': 'Company has active LinkedIn page',
                'score': 5
            })
            result['signal_score'] += 5

        # Small delay to avoid rate limiting
        time.sleep(1)

        # Find employee profiles
        profiles = self.find_employee_profiles(company_name, max_employees)
        result['employee_profiles'] = profiles
        result['employee_count'] = len(profiles)

        # Score based on number of employees found (indicates company size/activity)
        if len(profiles) >= 10:
            result['signals'].append({
                'type': 'large_company',
                'description': f'Found {len(profiles)}+ employees on LinkedIn',
                'score': 10
            })
            result['signal_score'] += 10
        elif len(profiles) >= 5:
            result['signals'].append({
                'type': 'medium_company',
                'description': f'Found {len(profiles)} employees on LinkedIn',
                'score': 5
            })
            result['signal_score'] += 5

        print(f"\n{'='*60}")
        print(f"RESULTS:")
        print(f"  Company Page: {'Found' if result['company_page'] else 'Not Found'}")
        print(f"  Employees Found: {result['employee_count']}")
        print(f"  Signal Score: +{result['signal_score']} points")
        print(f"{'='*60}\n")

        return result


# Convenience function
def discover_linkedin(company_name: str, max_employees: int = 10) -> Dict:
    """
    Discover LinkedIn information for a company

    Args:
        company_name: Name of the company
        max_employees: Maximum employee profiles to find

    Returns:
        Dict with LinkedIn information and signal scores
    """
    discoverer = LinkedInDiscovery()
    return discoverer.discover_linkedin_info(company_name, max_employees)


# Test function
if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        company_name = " ".join(sys.argv[1:])
    else:
        company_name = "CMC Manufacturing"

    result = discover_linkedin(company_name)

    print("\n" + "="*60)
    print("LINKEDIN DISCOVERY RESULTS")
    print("="*60)
    print(f"\nCompany: {result['company_name']}")

    if result['company_page']:
        print(f"\nCompany Page:")
        print(f"  {result['company_page']}")

    if result['employee_profiles']:
        print(f"\nEmployee Profiles ({len(result['employee_profiles'])}):")
        for i, profile in enumerate(result['employee_profiles'][:5], 1):
            print(f"  {i}. {profile}")
        if len(result['employee_profiles']) > 5:
            print(f"  ... and {len(result['employee_profiles']) - 5} more")

    if result['signals']:
        print(f"\nSignals Detected:")
        for signal in result['signals']:
            print(f"  • {signal['description']} (+{signal['score']} points)")
        print(f"\nTotal Signal Boost: +{result['signal_score']} points")
