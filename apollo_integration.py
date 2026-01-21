#!/usr/bin/env python3
"""
Apollo.io API Integration
Provides contact and company enrichment via Apollo.io API
"""

import requests
from typing import Dict, List, Optional
import time


class ApolloIntegration:
    """Apollo.io API client for contact enrichment"""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        self.base_url = "https://api.apollo.io/v1"
        self.session = requests.Session()
        if api_key:
            self.session.headers.update({'X-Api-Key': api_key})

    def enrich_company(self, domain: str) -> Dict:
        """
        Enrich company data by domain

        Args:
            domain: Company domain (e.g., 'company.com')

        Returns:
            Dictionary with company data including:
            - name, industry, employee_count, revenue
            - phone, website, social media links
            - technologies used
        """
        if not self.api_key:
            return {'error': 'No Apollo API key provided'}

        try:
            url = f"{self.base_url}/organizations/enrich"
            params = {'domain': domain}

            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()

            data = response.json()

            if 'organization' not in data:
                return {'error': 'No organization data found'}

            org = data['organization']

            return {
                'success': True,
                'company_name': org.get('name'),
                'industry': org.get('industry'),
                'employee_count': org.get('employee_count'),
                'estimated_revenue': org.get('estimated_num_employees'),
                'phone': org.get('phone'),
                'website': org.get('website_url'),
                'linkedin_url': org.get('linkedin_url'),
                'facebook_url': org.get('facebook_url'),
                'twitter_url': org.get('twitter_url'),
                'technologies': org.get('technologies', []),
                'description': org.get('short_description'),
                'founded_year': org.get('founded_year'),
                'street_address': org.get('street_address'),
                'city': org.get('city'),
                'state': org.get('state'),
                'postal_code': org.get('postal_code'),
                'country': org.get('country')
            }

        except requests.exceptions.RequestException as e:
            return {'error': f'Apollo API request failed: {str(e)}'}
        except Exception as e:
            return {'error': f'Apollo enrichment error: {str(e)}'}

    def find_contacts(self, domain: str, limit: int = 10) -> Dict:
        """
        Find contacts (emails and people) at a company

        Args:
            domain: Company domain
            limit: Maximum number of contacts to return (default 10)

        Returns:
            Dictionary with list of contacts including:
            - email, first_name, last_name, title
            - phone numbers, LinkedIn URL
        """
        if not self.api_key:
            return {'error': 'No Apollo API key provided'}

        try:
            url = f"{self.base_url}/mixed_people/search"
            payload = {
                'organization_domains': [domain],
                'page': 1,
                'per_page': limit
            }

            response = self.session.post(url, json=payload, timeout=15)
            response.raise_for_status()

            data = response.json()

            contacts = []
            for person in data.get('people', []):
                contact = {
                    'email': person.get('email'),
                    'first_name': person.get('first_name'),
                    'last_name': person.get('last_name'),
                    'name': person.get('name'),
                    'title': person.get('title'),
                    'seniority': person.get('seniority'),
                    'departments': person.get('departments', []),
                    'phone_numbers': person.get('phone_numbers', []),
                    'linkedin_url': person.get('linkedin_url'),
                    'email_status': person.get('email_status'),  # verified, etc.
                }
                contacts.append(contact)

            return {
                'success': True,
                'contacts_found': len(contacts),
                'contacts': contacts,
                'total_available': data.get('pagination', {}).get('total_entries', 0)
            }

        except requests.exceptions.RequestException as e:
            return {'error': f'Apollo API request failed: {str(e)}'}
        except Exception as e:
            return {'error': f'Apollo contact search error: {str(e)}'}

    def verify_email(self, email: str) -> Dict:
        """
        Verify an email address

        Args:
            email: Email address to verify

        Returns:
            Dictionary with verification status
        """
        if not self.api_key:
            return {'error': 'No Apollo API key provided'}

        try:
            url = f"{self.base_url}/emailer_campaigns/email_accounts/verify_email"
            payload = {'email': email}

            response = self.session.post(url, json=payload, timeout=10)
            response.raise_for_status()

            data = response.json()

            return {
                'success': True,
                'email': email,
                'status': data.get('status'),
                'is_valid': data.get('is_valid', False),
                'is_deliverable': data.get('is_deliverable', False)
            }

        except requests.exceptions.RequestException as e:
            return {'error': f'Apollo API request failed: {str(e)}'}
        except Exception as e:
            return {'error': f'Apollo email verification error: {str(e)}'}


def test_apollo():
    """Test Apollo.io integration"""
    print("Testing Apollo.io Integration...")
    print("Note: This requires a valid API key\n")

    # Test with no API key
    apollo = ApolloIntegration()
    result = apollo.enrich_company('google.com')
    print(f"Test without API key: {result.get('error', 'Unexpected success')}\n")

    print("To use Apollo.io:")
    print("1. Sign up at https://app.apollo.io")
    print("2. Get your API key from Settings > API")
    print("3. Add it to the Settings tab in the app")
    print("4. You get 50 free enrichment credits per month")


if __name__ == "__main__":
    test_apollo()
