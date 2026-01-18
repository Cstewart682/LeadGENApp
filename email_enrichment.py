#!/usr/bin/env python3
"""
Email Domain Enrichment Module

Uses Hunter.io and other services to enrich company data from email addresses
Provides: company size, social media, email patterns, confidence scores, and more
"""

import requests
from typing import Dict, Optional
import re

class EmailEnrichment:
    def __init__(self, hunter_api_key: Optional[str] = None):
        """
        Initialize email enrichment

        Args:
            hunter_api_key: Hunter.io API key (get free at hunter.io)
        """
        self.hunter_api_key = hunter_api_key
        self.hunter_available = hunter_api_key is not None

    def extract_domain(self, email: str) -> Optional[str]:
        """Extract domain from email address"""
        try:
            return email.split('@')[1].lower()
        except:
            return None

    def hunter_domain_search(self, domain: str) -> Dict:
        """
        Query Hunter.io for domain information

        Free tier: 50 requests/month

        Returns:
            Dict with company data
        """
        if not self.hunter_available:
            return {'error': 'Hunter.io API key not configured'}

        try:
            url = f"https://api.hunter.io/v2/domain-search"
            params = {
                'domain': domain,
                'api_key': self.hunter_api_key,
                'limit': 10  # Max emails to return
            }

            response = requests.get(url, params=params, timeout=10)
            data = response.json()

            if response.status_code != 200:
                return {'error': data.get('errors', [{'details': 'Unknown error'}])[0]['details']}

            # Parse response
            result = {
                'domain': domain,
                'company_name': data['data'].get('organization'),
                'emails_found': data['data'].get('total', 0),
                'email_list': [],
                'email_pattern': data['data'].get('pattern'),  # e.g., {first}.{last}
                'confidence': data['data'].get('confidence'),
                'website': data['data'].get('webmail', False),
                'company_size': None,
                'social_media': {},
                'raw_data': data['data']
            }

            # Extract emails
            for email_data in data['data'].get('emails', []):
                result['email_list'].append({
                    'email': email_data['value'],
                    'first_name': email_data.get('first_name'),
                    'last_name': email_data.get('last_name'),
                    'position': email_data.get('position'),
                    'confidence': email_data.get('confidence')
                })

            # Extract social media (if available)
            if 'twitter' in data['data']:
                result['social_media']['twitter'] = data['data']['twitter']
            if 'facebook' in data['data']:
                result['social_media']['facebook'] = data['data']['facebook']
            if 'linkedin' in data['data']:
                result['social_media']['linkedin'] = data['data']['linkedin']

            return result

        except Exception as e:
            return {'error': str(e)}

    def hunter_email_verifier(self, email: str) -> Dict:
        """
        Verify if an email address is valid using Hunter.io

        Returns:
            Dict with verification results
        """
        if not self.hunter_available:
            return {'error': 'Hunter.io API key not configured'}

        try:
            url = f"https://api.hunter.io/v2/email-verifier"
            params = {
                'email': email,
                'api_key': self.hunter_api_key
            }

            response = requests.get(url, params=params, timeout=10)
            data = response.json()

            if response.status_code != 200:
                return {'error': data.get('errors', [{'details': 'Unknown error'}])[0]['details']}

            result = {
                'email': email,
                'status': data['data'].get('status'),  # valid, invalid, accept_all, unknown
                'score': data['data'].get('score'),  # 0-100
                'result': data['data'].get('result'),  # deliverable, undeliverable, risky, unknown
                'disposable': data['data'].get('disposable'),
                'webmail': data['data'].get('webmail'),
                'accept_all': data['data'].get('accept_all'),
                'mx_records': data['data'].get('mx_records'),
                'smtp_server': data['data'].get('smtp_server'),
                'smtp_check': data['data'].get('smtp_check')
            }

            return result

        except Exception as e:
            return {'error': str(e)}

    def clearbit_enrichment(self, domain: str) -> Dict:
        """
        Use Clearbit's free Company API to get basic info

        No API key needed for basic lookup!
        """
        try:
            # Clearbit free logo/info endpoint
            url = f"https://company.clearbit.com/v1/domains/find?name={domain}"

            response = requests.get(url, timeout=10)

            if response.status_code == 200:
                data = response.json()
                return {
                    'company_name': data.get('name'),
                    'domain': data.get('domain'),
                    'logo': data.get('logo'),
                    'description': data.get('description'),
                    'location': data.get('location'),
                    'employees': data.get('metrics', {}).get('employees'),
                    'estimated_revenue': data.get('metrics', {}).get('estimatedAnnualRevenue'),
                    'industry': data.get('category', {}).get('industry'),
                    'sector': data.get('category', {}).get('sector'),
                    'founded_year': data.get('foundedYear'),
                    'twitter': data.get('twitter', {}).get('handle'),
                    'linkedin': data.get('linkedin', {}).get('handle'),
                    'facebook': data.get('facebook', {}).get('handle')
                }
            else:
                return {'error': 'Company not found in Clearbit'}

        except Exception as e:
            return {'error': str(e)}

    def basic_domain_info(self, domain: str) -> Dict:
        """
        Get basic info about a domain without APIs (DNS, WHOIS-style)
        """
        try:
            import socket

            # Try to get IP
            ip = socket.gethostbyname(domain)

            # Try to check if domain responds
            response = requests.head(f"https://{domain}", timeout=5, allow_redirects=True)

            return {
                'domain': domain,
                'ip_address': ip,
                'active': response.status_code < 500,
                'status_code': response.status_code,
                'ssl_valid': response.url.startswith('https')
            }

        except Exception as e:
            return {
                'domain': domain,
                'active': False,
                'error': str(e)
            }

    def enrich_email(self, email: str, use_hunter: bool = True, verify_email: bool = False) -> Dict:
        """
        Complete email enrichment combining multiple sources

        Args:
            email: Email address to enrich
            use_hunter: Use Hunter.io if available
            verify_email: Verify the email address (uses 1 credit)

        Returns:
            Dict with enriched data
        """
        domain = self.extract_domain(email)

        if not domain:
            return {'error': 'Invalid email address'}

        print(f"\n{'='*60}")
        print(f"EMAIL ENRICHMENT: {email}")
        print(f"{'='*60}")

        result = {
            'email': email,
            'domain': domain,
            'hunter_data': {},
            'clearbit_data': {},
            'domain_info': {},
            'verification': {},
            'signal_score': 0,
            'signals': []
        }

        # Get basic domain info (always free)
        print("📡 Checking domain...")
        result['domain_info'] = self.basic_domain_info(domain)

        if result['domain_info'].get('active'):
            result['signals'].append({
                'type': 'active_domain',
                'description': 'Domain is active and responding',
                'score': 5
            })
            result['signal_score'] += 5

        # Try Clearbit (free)
        print("🔍 Checking Clearbit...")
        clearbit = self.clearbit_enrichment(domain)
        if 'error' not in clearbit:
            result['clearbit_data'] = clearbit

            # Add signals based on company size
            if clearbit.get('employees'):
                emp_count = clearbit['employees']
                if emp_count >= 100:
                    result['signals'].append({
                        'type': 'large_company',
                        'description': f'Company has {emp_count}+ employees',
                        'score': 15
                    })
                    result['signal_score'] += 15
                elif emp_count >= 20:
                    result['signals'].append({
                        'type': 'medium_company',
                        'description': f'Company has {emp_count} employees',
                        'score': 10
                    })
                    result['signal_score'] += 10

            # Add signal for revenue
            if clearbit.get('estimated_revenue'):
                rev = clearbit['estimated_revenue']
                if rev and rev.replace('$', '').replace('M', '').replace('B', '').isdigit():
                    result['signals'].append({
                        'type': 'revenue_data',
                        'description': f'Estimated revenue: {rev}',
                        'score': 5
                    })
                    result['signal_score'] += 5

        # Try Hunter.io (if API key provided)
        if use_hunter and self.hunter_available:
            print("🎯 Checking Hunter.io...")
            hunter = self.hunter_domain_search(domain)

            if 'error' not in hunter:
                result['hunter_data'] = hunter

                # Add signal for number of emails found
                if hunter.get('emails_found', 0) > 5:
                    result['signals'].append({
                        'type': 'multiple_contacts',
                        'description': f'Found {hunter["emails_found"]} email addresses',
                        'score': 10
                    })
                    result['signal_score'] += 10

                # Verify the specific email if requested
                if verify_email:
                    print("✉️ Verifying email address...")
                    verification = self.hunter_email_verifier(email)
                    result['verification'] = verification

                    if verification.get('result') == 'deliverable':
                        result['signals'].append({
                            'type': 'verified_email',
                            'description': 'Email address verified as deliverable',
                            'score': 10
                        })
                        result['signal_score'] += 10
        else:
            print("⚠️ Hunter.io not configured (API key needed)")

        print(f"\n{'='*60}")
        print(f"ENRICHMENT COMPLETE")
        print(f"  Domain: {domain}")
        print(f"  Company: {result.get('clearbit_data', {}).get('company_name', 'Unknown')}")
        print(f"  Signal Boost: +{result['signal_score']} points")
        print(f"{'='*60}\n")

        return result


# Convenience function
def enrich_email(email: str, hunter_api_key: Optional[str] = None, verify: bool = False) -> Dict:
    """
    Enrich an email address with company data

    Args:
        email: Email address to enrich
        hunter_api_key: Optional Hunter.io API key
        verify: Verify the email (uses Hunter credit)

    Returns:
        Dict with enriched data
    """
    enricher = EmailEnrichment(hunter_api_key)
    return enricher.enrich_email(email, use_hunter=True, verify_email=verify)


# Test function
if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        test_email = sys.argv[1]
    else:
        test_email = "info@cmcmanufacturing.com"

    # For testing: You can pass API key as second argument
    api_key = sys.argv[2] if len(sys.argv) > 2 else None

    result = enrich_email(test_email, hunter_api_key=api_key)

    print("\n" + "="*60)
    print("EMAIL ENRICHMENT RESULTS")
    print("="*60)
    print(f"\nEmail: {result['email']}")
    print(f"Domain: {result['domain']}")

    # Clearbit data
    if result['clearbit_data'] and 'error' not in result['clearbit_data']:
        cb = result['clearbit_data']
        print(f"\nCompany Info (Clearbit):")
        print(f"  Name: {cb.get('company_name', 'N/A')}")
        print(f"  Industry: {cb.get('industry', 'N/A')}")
        print(f"  Employees: {cb.get('employees', 'N/A')}")
        print(f"  Revenue: {cb.get('estimated_revenue', 'N/A')}")
        print(f"  Location: {cb.get('location', 'N/A')}")

        if cb.get('twitter') or cb.get('linkedin'):
            print(f"\n  Social Media:")
            if cb.get('twitter'):
                print(f"    Twitter: @{cb['twitter']}")
            if cb.get('linkedin'):
                print(f"    LinkedIn: {cb['linkedin']}")

    # Hunter data
    if result['hunter_data'] and 'error' not in result['hunter_data']:
        h = result['hunter_data']
        print(f"\nHunter.io Data:")
        print(f"  Emails Found: {h.get('emails_found', 0)}")
        print(f"  Email Pattern: {h.get('email_pattern', 'N/A')}")

        if h.get('email_list'):
            print(f"\n  Contact Emails:")
            for email_info in h['email_list'][:5]:
                print(f"    • {email_info['email']}")
                if email_info.get('position'):
                    print(f"      {email_info['position']}")

    # Signals
    if result['signals']:
        print(f"\nSignals Detected:")
        for signal in result['signals']:
            print(f"  • {signal['description']} (+{signal['score']} points)")
        print(f"\nTotal Signal Boost: +{result['signal_score']} points")
