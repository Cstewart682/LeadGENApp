#!/usr/bin/env python3
"""
PeopleDataLabs (PDL) API Integration
Provides comprehensive B2B data enrichment
"""

import requests
from typing import Dict, List, Optional


class PeopleDataLabsIntegration:
    """PeopleDataLabs API client for company and person enrichment"""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        self.base_url = "https://api.peopledatalabs.com/v5"
        self.session = requests.Session()
        if api_key:
            self.session.headers.update({'X-Api-Key': api_key})

    def enrich_company(self, domain: str = None, company_name: str = None) -> Dict:
        """
        Enrich company data by domain or name

        Args:
            domain: Company domain (e.g., 'company.com')
            company_name: Company name (used if domain not provided)

        Returns:
            Dictionary with company data
        """
        if not self.api_key:
            return {'error': 'No PeopleDataLabs API key provided'}

        if not domain and not company_name:
            return {'error': 'Either domain or company_name required'}

        try:
            url = f"{self.base_url}/company/enrich"
            params = {}

            if domain:
                params['website'] = domain
            elif company_name:
                params['name'] = company_name

            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()

            data = response.json()

            if data.get('status') != 200:
                return {'error': f"PDL returned status {data.get('status')}"}

            company = data.get('data', {})

            return {
                'success': True,
                'company_name': company.get('name'),
                'display_name': company.get('display_name'),
                'website': company.get('website'),
                'size': company.get('size'),
                'employee_count': company.get('employee_count'),
                'industry': company.get('industry'),
                'industries': company.get('industries', []),
                'founded': company.get('founded'),
                'type': company.get('type'),
                'linkedin_url': company.get('linkedin_url'),
                'linkedin_id': company.get('linkedin_id'),
                'facebook_url': company.get('facebook_url'),
                'twitter_url': company.get('twitter_url'),
                'location': company.get('location', {}),
                'tags': company.get('tags', []),
                'summary': company.get('summary'),
                'employee_count_by_country': company.get('employee_count_by_country', {}),
            }

        except requests.exceptions.RequestException as e:
            return {'error': f'PDL API request failed: {str(e)}'}
        except Exception as e:
            return {'error': f'PDL enrichment error: {str(e)}'}

    def search_people(self, company_domain: str, limit: int = 10) -> Dict:
        """
        Search for people at a company

        Args:
            company_domain: Company domain
            limit: Max number of results (default 10)

        Returns:
            Dictionary with list of people
        """
        if not self.api_key:
            return {'error': 'No PeopleDataLabs API key provided'}

        try:
            url = f"{self.base_url}/person/search"
            query = {
                'query': {
                    'bool': {
                        'must': [
                            {'term': {'job_company_website': company_domain}}
                        ]
                    }
                },
                'size': limit
            }

            response = self.session.post(url, json=query, timeout=15)
            response.raise_for_status()

            data = response.json()

            if data.get('status') != 200:
                return {'error': f"PDL returned status {data.get('status')}"}

            people = []
            for person in data.get('data', []):
                people.append({
                    'full_name': person.get('full_name'),
                    'first_name': person.get('first_name'),
                    'last_name': person.get('last_name'),
                    'linkedin_url': person.get('linkedin_url'),
                    'linkedin_username': person.get('linkedin_username'),
                    'job_title': person.get('job_title'),
                    'job_title_role': person.get('job_title_role'),
                    'job_company_name': person.get('job_company_name'),
                    'emails': person.get('emails', []),
                    'phone_numbers': person.get('phone_numbers', []),
                    'location_name': person.get('location_name'),
                    'summary': person.get('summary'),
                    'skills': person.get('skills', []),
                })

            return {
                'success': True,
                'total_found': data.get('total', 0),
                'people_count': len(people),
                'people': people
            }

        except requests.exceptions.RequestException as e:
            return {'error': f'PDL API request failed: {str(e)}'}
        except Exception as e:
            return {'error': f'PDL people search error: {str(e)}'}

    def enrich_person(self, email: str = None, linkedin_url: str = None) -> Dict:
        """
        Enrich person data by email or LinkedIn URL

        Args:
            email: Email address
            linkedin_url: LinkedIn profile URL

        Returns:
            Dictionary with person data
        """
        if not self.api_key:
            return {'error': 'No PeopleDataLabs API key provided'}

        if not email and not linkedin_url:
            return {'error': 'Either email or linkedin_url required'}

        try:
            url = f"{self.base_url}/person/enrich"
            params = {}

            if email:
                params['email'] = email
            elif linkedin_url:
                params['profile'] = linkedin_url

            response = self.session.get(url, params=params, timeout=10)
            response.raise_for_status()

            data = response.json()

            if data.get('status') != 200:
                return {'error': f"PDL returned status {data.get('status')}"}

            person = data.get('data', {})

            return {
                'success': True,
                'full_name': person.get('full_name'),
                'first_name': person.get('first_name'),
                'last_name': person.get('last_name'),
                'job_title': person.get('job_title'),
                'job_company_name': person.get('job_company_name'),
                'job_company_website': person.get('job_company_website'),
                'linkedin_url': person.get('linkedin_url'),
                'emails': person.get('emails', []),
                'phone_numbers': person.get('phone_numbers', []),
                'location_name': person.get('location_name'),
            }

        except requests.exceptions.RequestException as e:
            return {'error': f'PDL API request failed: {str(e)}'}
        except Exception as e:
            return {'error': f'PDL person enrichment error: {str(e)}'}


def test_pdl():
    """Test PeopleDataLabs integration"""
    print("Testing PeopleDataLabs Integration...")
    print("Note: This requires a valid API key\n")

    # Test with no API key
    pdl = PeopleDataLabsIntegration()
    result = pdl.enrich_company(domain='google.com')
    print(f"Test without API key: {result.get('error', 'Unexpected success')}\n")

    print("To use PeopleDataLabs:")
    print("1. Sign up at https://www.peopledatalabs.com/signup")
    print("2. Get your API key from your dashboard")
    print("3. Add it to the Settings tab in the app")
    print("4. You get 1,000 free enrichment credits per month")


if __name__ == "__main__":
    test_pdl()
