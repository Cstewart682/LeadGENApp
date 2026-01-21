#!/usr/bin/env python3
"""
Multi-Source Contact Enrichment
Aggregates data from multiple APIs with intelligent fallback logic
"""

from typing import Dict, List, Optional
from datetime import datetime

# Import all integration modules
try:
    from apollo_integration import ApolloIntegration
    APOLLO_AVAILABLE = True
except ImportError:
    APOLLO_AVAILABLE = False

try:
    from peopledatalabs_integration import PeopleDataLabsIntegration
    PDL_AVAILABLE = True
except ImportError:
    PDL_AVAILABLE = False

try:
    from google_places_integration import GooglePlacesIntegration
    GOOGLE_PLACES_AVAILABLE = True
except ImportError:
    GOOGLE_PLACES_AVAILABLE = False

try:
    from zerobounce_integration import ZeroBounceIntegration
    ZEROBOUNCE_AVAILABLE = True
except ImportError:
    ZEROBOUNCE_AVAILABLE = False

try:
    from proxycurl_integration import ProxycurlIntegration
    PROXYCURL_AVAILABLE = True
except ImportError:
    PROXYCURL_AVAILABLE = False


class MultiSourceEnrichment:
    """
    Unified contact enrichment using multiple data sources with fallback
    """

    def __init__(self, api_keys: Dict[str, str]):
        """
        Initialize with API keys for all services

        Args:
            api_keys: Dictionary with keys like:
                - apollo_api_key
                - pdl_api_key
                - google_places_api_key
                - zerobounce_api_key
                - proxycurl_api_key
        """
        self.api_keys = api_keys

        # Initialize clients
        self.apollo = None
        self.pdl = None
        self.google_places = None
        self.zerobounce = None
        self.proxycurl = None

        if APOLLO_AVAILABLE and api_keys.get('apollo_api_key'):
            self.apollo = ApolloIntegration(api_keys['apollo_api_key'])

        if PDL_AVAILABLE and api_keys.get('pdl_api_key'):
            self.pdl = PeopleDataLabsIntegration(api_keys['pdl_api_key'])

        if GOOGLE_PLACES_AVAILABLE and api_keys.get('google_places_api_key'):
            self.google_places = GooglePlacesIntegration(api_keys['google_places_api_key'])

        if ZEROBOUNCE_AVAILABLE and api_keys.get('zerobounce_api_key'):
            self.zerobounce = ZeroBounceIntegration(api_keys['zerobounce_api_key'])

        if PROXYCURL_AVAILABLE and api_keys.get('proxycurl_api_key'):
            self.proxycurl = ProxycurlIntegration(api_keys['proxycurl_api_key'])

    def enrich_company(self, company_name: str, domain: str = None, location: str = "Calgary, AB") -> Dict:
        """
        Enrich company data from all available sources

        Args:
            company_name: Company name
            domain: Company domain (e.g., 'company.com')
            location: Company location

        Returns:
            Aggregated data from all sources
        """
        enriched_data = {
            'company_name': company_name,
            'domain': domain,
            'enrichment_date': datetime.now().isoformat(),
            'sources_used': [],
            'data': {}
        }

        # Try Google Places first (best for local businesses)
        if self.google_places:
            try:
                google_data = self.google_places.find_place(company_name, location)
                if google_data.get('success'):
                    enriched_data['sources_used'].append('google_places')
                    enriched_data['data']['google_places'] = {
                        'phone': google_data.get('phone'),
                        'address': google_data.get('address'),
                        'website': google_data.get('website') or domain,
                        'rating': google_data.get('rating'),
                        'total_ratings': google_data.get('total_ratings'),
                        'hours': google_data.get('hours', []),
                        'reviews_summary': len(google_data.get('reviews', []))
                    }
                    # Update domain if found
                    if not domain and google_data.get('website'):
                        domain = google_data['website'].replace('https://', '').replace('http://', '').split('/')[0]
            except Exception as e:
                print(f"Google Places error: {e}")

        # Try Apollo.io (excellent for B2B data)
        if self.apollo and domain:
            try:
                apollo_data = self.apollo.enrich_company(domain)
                if apollo_data.get('success'):
                    enriched_data['sources_used'].append('apollo')
                    enriched_data['data']['apollo'] = {
                        'employee_count': apollo_data.get('employee_count'),
                        'industry': apollo_data.get('industry'),
                        'phone': apollo_data.get('phone'),
                        'technologies': apollo_data.get('technologies', []),
                        'linkedin_url': apollo_data.get('linkedin_url'),
                        'founded_year': apollo_data.get('founded_year'),
                        'address': f"{apollo_data.get('city', '')}, {apollo_data.get('state', '')}"
                    }
            except Exception as e:
                print(f"Apollo error: {e}")

        # Try PeopleDataLabs (comprehensive B2B database)
        if self.pdl and domain:
            try:
                pdl_data = self.pdl.enrich_company(domain=domain)
                if pdl_data.get('success'):
                    enriched_data['sources_used'].append('peopledatalabs')
                    enriched_data['data']['peopledatalabs'] = {
                        'employee_count': pdl_data.get('employee_count'),
                        'size': pdl_data.get('size'),
                        'industry': pdl_data.get('industry'),
                        'founded': pdl_data.get('founded'),
                        'linkedin_url': pdl_data.get('linkedin_url'),
                        'facebook_url': pdl_data.get('facebook_url'),
                        'twitter_url': pdl_data.get('twitter_url'),
                        'summary': pdl_data.get('summary')
                    }
            except Exception as e:
                print(f"PeopleDataLabs error: {e}")

        # Try Proxycurl for LinkedIn data (if we have LinkedIn URL)
        linkedin_url = None
        if enriched_data['data'].get('apollo', {}).get('linkedin_url'):
            linkedin_url = enriched_data['data']['apollo']['linkedin_url']
        elif enriched_data['data'].get('peopledatalabs', {}).get('linkedin_url'):
            linkedin_url = enriched_data['data']['peopledatalabs']['linkedin_url']

        if self.proxycurl and linkedin_url:
            try:
                proxycurl_data = self.proxycurl.get_company_profile(linkedin_url)
                if proxycurl_data.get('success'):
                    enriched_data['sources_used'].append('proxycurl')
                    enriched_data['data']['proxycurl'] = {
                        'company_size': proxycurl_data.get('company_size'),
                        'follower_count': proxycurl_data.get('follower_count'),
                        'description': proxycurl_data.get('description'),
                        'specialties': proxycurl_data.get('specialties', []),
                        'locations': proxycurl_data.get('locations', [])
                    }
            except Exception as e:
                print(f"Proxycurl error: {e}")

        # Aggregate and normalize data
        enriched_data['aggregated'] = self._aggregate_company_data(enriched_data['data'])

        return enriched_data

    def find_contacts(self, company_name: str, domain: str, limit: int = 10) -> Dict:
        """
        Find contact information from all available sources

        Args:
            company_name: Company name
            domain: Company domain
            limit: Maximum contacts per source

        Returns:
            Aggregated contact data from all sources
        """
        contacts_data = {
            'company_name': company_name,
            'domain': domain,
            'enrichment_date': datetime.now().isoformat(),
            'sources_used': [],
            'all_contacts': []
        }

        # Try Apollo.io first (best email finder)
        if self.apollo:
            try:
                apollo_contacts = self.apollo.find_contacts(domain, limit=limit)
                if apollo_contacts.get('success'):
                    contacts_data['sources_used'].append('apollo')
                    for contact in apollo_contacts.get('contacts', []):
                        if contact.get('email'):
                            contacts_data['all_contacts'].append({
                                'source': 'apollo',
                                'email': contact['email'],
                                'name': contact.get('name') or f"{contact.get('first_name', '')} {contact.get('last_name', '')}".strip(),
                                'title': contact.get('title'),
                                'phone': contact.get('phone_numbers', [None])[0] if contact.get('phone_numbers') else None,
                                'linkedin_url': contact.get('linkedin_url'),
                                'verified': contact.get('email_status') == 'verified'
                            })
            except Exception as e:
                print(f"Apollo contacts error: {e}")

        # Try PeopleDataLabs
        if self.pdl:
            try:
                pdl_contacts = self.pdl.search_people(domain, limit=limit)
                if pdl_contacts.get('success'):
                    contacts_data['sources_used'].append('peopledatalabs')
                    for person in pdl_contacts.get('people', []):
                        # Get first email if available
                        emails = person.get('emails', [])
                        email = emails[0].get('address') if emails else None

                        if email:
                            contacts_data['all_contacts'].append({
                                'source': 'peopledatalabs',
                                'email': email,
                                'name': person.get('full_name'),
                                'title': person.get('job_title'),
                                'phone': person.get('phone_numbers', [None])[0] if person.get('phone_numbers') else None,
                                'linkedin_url': person.get('linkedin_url'),
                                'verified': False
                            })
            except Exception as e:
                print(f"PeopleDataLabs contacts error: {e}")

        # Deduplicate contacts by email
        seen_emails = set()
        unique_contacts = []
        for contact in contacts_data['all_contacts']:
            email = contact.get('email', '').lower()
            if email and email not in seen_emails:
                seen_emails.add(email)
                unique_contacts.append(contact)

        contacts_data['all_contacts'] = unique_contacts
        contacts_data['total_contacts'] = len(unique_contacts)

        return contacts_data

    def validate_emails(self, emails: List[str]) -> Dict:
        """
        Validate email addresses using ZeroBounce

        Args:
            emails: List of emails to validate

        Returns:
            Validation results for each email
        """
        if not self.zerobounce:
            return {'error': 'ZeroBounce not available'}

        try:
            results = self.zerobounce.validate_batch(emails)
            return results
        except Exception as e:
            return {'error': f'Email validation error: {str(e)}'}

    def _aggregate_company_data(self, data: Dict) -> Dict:
        """
        Aggregate and normalize company data from multiple sources

        Args:
            data: Dictionary with data from different sources

        Returns:
            Normalized aggregated data
        """
        aggregated = {}

        # Get best phone number (prefer Google Places for local businesses)
        phones = []
        if data.get('google_places', {}).get('phone'):
            phones.append(data['google_places']['phone'])
        if data.get('apollo', {}).get('phone'):
            phones.append(data['apollo']['phone'])
        aggregated['phones'] = list(set(phones))

        # Get best address
        addresses = []
        if data.get('google_places', {}).get('address'):
            addresses.append(data['google_places']['address'])
        if data.get('apollo', {}).get('address'):
            addresses.append(data['apollo']['address'])
        aggregated['addresses'] = addresses

        # Get employee count (use most specific)
        employee_count = None
        if data.get('apollo', {}).get('employee_count'):
            employee_count = data['apollo']['employee_count']
        elif data.get('peopledatalabs', {}).get('employee_count'):
            employee_count = data['peopledatalabs']['employee_count']
        aggregated['employee_count'] = employee_count

        # Get industry
        industries = []
        if data.get('apollo', {}).get('industry'):
            industries.append(data['apollo']['industry'])
        if data.get('peopledatalabs', {}).get('industry'):
            industries.append(data['peopledatalabs']['industry'])
        aggregated['industries'] = list(set(industries))

        # Get social media URLs
        aggregated['linkedin_url'] = (
            data.get('apollo', {}).get('linkedin_url') or
            data.get('peopledatalabs', {}).get('linkedin_url')
        )
        aggregated['facebook_url'] = data.get('peopledatalabs', {}).get('facebook_url')
        aggregated['twitter_url'] = data.get('peopledatalabs', {}).get('twitter_url')

        # Get technologies (from Apollo)
        aggregated['technologies'] = data.get('apollo', {}).get('technologies', [])

        # Get rating (from Google)
        aggregated['google_rating'] = data.get('google_places', {}).get('rating')
        aggregated['google_reviews'] = data.get('google_places', {}).get('total_ratings')

        return aggregated


def test_multi_source():
    """Test multi-source enrichment"""
    print("Testing Multi-Source Enrichment...")
    print("Note: This requires API keys for the services you want to use\n")

    # Test with no API keys
    enricher = MultiSourceEnrichment({})
    result = enricher.enrich_company("Google", "google.com")

    print(f"Sources used: {result.get('sources_used', [])}")
    print("\nTo use multi-source enrichment:")
    print("1. Get API keys for the services you want")
    print("2. Add them to the Settings tab in the app")
    print("3. The app will automatically use all available sources")
    print("4. Fallback logic ensures you get data even if one API fails")


if __name__ == "__main__":
    test_multi_source()
