#!/usr/bin/env python3
"""
Proxycurl API Integration
LinkedIn data scraping service (legal and respects ToS)
"""

import requests
from typing import Dict, List, Optional
import urllib.parse


class ProxycurlIntegration:
    """Proxycurl API client for LinkedIn data"""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        self.base_url = "https://nubela.co/proxycurl/api/v2"
        self.session = requests.Session()
        if api_key:
            self.session.headers.update({'Authorization': f'Bearer {api_key}'})

    def get_company_profile(self, linkedin_url: str) -> Dict:
        """
        Get LinkedIn company profile data

        Args:
            linkedin_url: LinkedIn company page URL
                         (e.g., 'https://linkedin.com/company/google')

        Returns:
            Dictionary with company profile data
        """
        if not self.api_key:
            return {'error': 'No Proxycurl API key provided'}

        try:
            url = f"{self.base_url}/linkedin/company"
            params = {
                'url': linkedin_url,
                'use_cache': 'if-present'  # Use cache to save credits
            }

            response = self.session.get(url, params=params, timeout=15)
            response.raise_for_status()

            data = response.json()

            return {
                'success': True,
                'company_name': data.get('name'),
                'description': data.get('description'),
                'website': data.get('website'),
                'industry': data.get('industry'),
                'company_size': data.get('company_size'),
                'company_size_on_linkedin': data.get('company_size_on_linkedin'),
                'headquarters': data.get('hq', {}),
                'company_type': data.get('company_type'),
                'founded_year': data.get('founded_year'),
                'specialties': data.get('specialities', []),
                'locations': data.get('locations', []),
                'follower_count': data.get('follower_count'),
                'tagline': data.get('tagline'),
                'universal_name_id': data.get('universal_name_id'),
                'profile_pic_url': data.get('profile_pic_url'),
                'background_cover_image_url': data.get('background_cover_image_url'),
                'updates': data.get('updates', []),
                'linkedin_internal_id': data.get('linkedin_internal_id')
            }

        except requests.exceptions.RequestException as e:
            return {'error': f'Proxycurl API request failed: {str(e)}'}
        except Exception as e:
            return {'error': f'Proxycurl company profile error: {str(e)}'}

    def get_person_profile(self, linkedin_url: str) -> Dict:
        """
        Get LinkedIn person profile data

        Args:
            linkedin_url: LinkedIn person profile URL
                         (e.g., 'https://linkedin.com/in/john-smith')

        Returns:
            Dictionary with person profile data
        """
        if not self.api_key:
            return {'error': 'No Proxycurl API key provided'}

        try:
            url = f"{self.base_url}/linkedin"
            params = {
                'url': linkedin_url,
                'use_cache': 'if-present',
                'skills': 'include'
            }

            response = self.session.get(url, params=params, timeout=15)
            response.raise_for_status()

            data = response.json()

            # Extract current job
            current_job = {}
            experiences = data.get('experiences', [])
            if experiences:
                for exp in experiences:
                    if exp.get('ends_at') is None:  # Current position
                        current_job = {
                            'title': exp.get('title'),
                            'company': exp.get('company'),
                            'company_linkedin_url': exp.get('company_linkedin_profile_url'),
                            'description': exp.get('description'),
                            'started': exp.get('starts_at')
                        }
                        break

            return {
                'success': True,
                'full_name': data.get('full_name'),
                'first_name': data.get('first_name'),
                'last_name': data.get('last_name'),
                'headline': data.get('headline'),
                'summary': data.get('summary'),
                'country': data.get('country'),
                'city': data.get('city'),
                'state': data.get('state'),
                'current_job': current_job,
                'experiences': experiences,
                'education': data.get('education', []),
                'skills': data.get('skills', []),
                'languages': data.get('languages', []),
                'profile_pic_url': data.get('profile_pic_url'),
                'connections': data.get('connections'),
                'follower_count': data.get('follower_count')
            }

        except requests.exceptions.RequestException as e:
            return {'error': f'Proxycurl API request failed: {str(e)}'}
        except Exception as e:
            return {'error': f'Proxycurl person profile error: {str(e)}'}

    def search_company(self, company_name: str, country: str = "CA") -> Dict:
        """
        Search for a company on LinkedIn

        Args:
            company_name: Company name to search
            country: Country code (default "CA" for Canada)

        Returns:
            Dictionary with search results
        """
        if not self.api_key:
            return {'error': 'No Proxycurl API key provided'}

        try:
            url = f"{self.base_url}/linkedin/company/search"
            params = {
                'company_name': company_name,
                'country': country,
                'enrich_profiles': 'skip'  # Don't enrich to save credits
            }

            response = self.session.get(url, params=params, timeout=15)
            response.raise_for_status()

            data = response.json()

            companies = []
            for company in data.get('companies', []):
                companies.append({
                    'name': company.get('name'),
                    'linkedin_url': company.get('linkedin_profile_url'),
                    'headline': company.get('headline'),
                    'location': company.get('location')
                })

            return {
                'success': True,
                'total_found': len(companies),
                'companies': companies
            }

        except requests.exceptions.RequestException as e:
            return {'error': f'Proxycurl API request failed: {str(e)}'}
        except Exception as e:
            return {'error': f'Proxycurl company search error: {str(e)}'}

    def get_company_employees(self, linkedin_company_url: str, limit: int = 10) -> Dict:
        """
        Get employee profiles from a company

        Args:
            linkedin_company_url: LinkedIn company page URL
            limit: Maximum number of employees to return

        Returns:
            Dictionary with list of employee profiles
        """
        if not self.api_key:
            return {'error': 'No Proxycurl API key provided'}

        try:
            url = f"{self.base_url}/linkedin/company/employees"
            params = {
                'url': linkedin_company_url,
                'resolve_numeric_id': 'false',
                'page_size': min(limit, 100)
            }

            response = self.session.get(url, params=params, timeout=20)
            response.raise_for_status()

            data = response.json()

            employees = []
            for employee in data.get('employees', [])[:limit]:
                employees.append({
                    'profile_url': employee.get('profile_url'),
                    'first_name': employee.get('first_name'),
                    'last_name': employee.get('last_name'),
                    'headline': employee.get('headline'),
                    'location': employee.get('location')
                })

            return {
                'success': True,
                'total_found': len(employees),
                'employees': employees,
                'next_page': data.get('next_page')
            }

        except requests.exceptions.RequestException as e:
            return {'error': f'Proxycurl API request failed: {str(e)}'}
        except Exception as e:
            return {'error': f'Proxycurl employee list error: {str(e)}'}


def test_proxycurl():
    """Test Proxycurl integration"""
    print("Testing Proxycurl Integration...")
    print("Note: This requires a valid API key\n")

    # Test with no API key
    pc = ProxycurlIntegration()
    result = pc.get_company_profile('https://linkedin.com/company/google')
    print(f"Test without API key: {result.get('error', 'Unexpected success')}\n")

    print("To use Proxycurl:")
    print("1. Sign up at https://nubela.co/proxycurl/")
    print("2. Get your API key from your dashboard")
    print("3. Add it to the Settings tab in the app")
    print("4. Pay-as-you-go pricing: ~$0.02-0.03 per profile")
    print("\nProxycurl provides LEGAL LinkedIn data without violating ToS!")


if __name__ == "__main__":
    test_proxycurl()
