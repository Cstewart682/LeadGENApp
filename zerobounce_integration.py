#!/usr/bin/env python3
"""
ZeroBounce API Integration
Email validation and verification service
"""

import requests
from typing import Dict, List, Optional


class ZeroBounceIntegration:
    """ZeroBounce API client for email validation"""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        self.base_url = "https://api.zerobounce.net/v2"

    def validate_email(self, email: str, ip_address: str = None) -> Dict:
        """
        Validate a single email address

        Args:
            email: Email address to validate
            ip_address: Optional IP address for additional validation

        Returns:
            Dictionary with validation results including:
            - status (valid, invalid, catch-all, etc.)
            - sub_status (more detailed status)
            - free_email (boolean)
            - score (0-10, toxicity score)
        """
        if not self.api_key:
            return {'error': 'No ZeroBounce API key provided'}

        try:
            url = f"{self.base_url}/validate"
            params = {
                'api_key': self.api_key,
                'email': email
            }

            if ip_address:
                params['ip_address'] = ip_address

            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()

            data = response.json()

            # Check for API errors
            if 'error' in data:
                return {'error': f"ZeroBounce API error: {data['error']}"}

            return {
                'success': True,
                'email': email,
                'status': data.get('status'),  # valid, invalid, catch-all, unknown, spamtrap, abuse, do_not_mail
                'sub_status': data.get('sub_status'),
                'free_email': data.get('free_email', False),
                'did_you_mean': data.get('did_you_mean'),  # Suggested correction
                'account': data.get('account'),  # Email account part
                'domain': data.get('domain'),  # Email domain part
                'domain_age_days': data.get('domain_age_days'),
                'smtp_provider': data.get('smtp_provider'),
                'mx_found': data.get('mx_found'),
                'mx_record': data.get('mx_record'),
                'firstname': data.get('firstname'),
                'lastname': data.get('lastname'),
                'gender': data.get('gender'),
                'country': data.get('country'),
                'region': data.get('region'),
                'city': data.get('city'),
                'zipcode': data.get('zipcode'),
                'processed_at': data.get('processed_at')
            }

        except requests.exceptions.RequestException as e:
            return {'error': f'ZeroBounce API request failed: {str(e)}'}
        except Exception as e:
            return {'error': f'ZeroBounce validation error: {str(e)}'}

    def validate_batch(self, emails: List[str]) -> Dict:
        """
        Validate multiple email addresses (up to 100 at once)

        Args:
            emails: List of email addresses to validate

        Returns:
            Dictionary with validation results for each email
        """
        if not self.api_key:
            return {'error': 'No ZeroBounce API key provided'}

        if len(emails) > 100:
            return {'error': 'Maximum 100 emails per batch request'}

        results = {}
        valid_count = 0
        invalid_count = 0

        # Validate each email (ZeroBounce free tier doesn't support true batch)
        for email in emails:
            result = self.validate_email(email)
            results[email] = result

            if result.get('success') and result.get('status') == 'valid':
                valid_count += 1
            elif result.get('success'):
                invalid_count += 1

        return {
            'success': True,
            'total': len(emails),
            'valid': valid_count,
            'invalid': invalid_count,
            'results': results
        }

    def get_credits(self) -> Dict:
        """
        Get remaining API credits

        Returns:
            Dictionary with credit information
        """
        if not self.api_key:
            return {'error': 'No ZeroBounce API key provided'}

        try:
            url = f"{self.base_url}/getcredits"
            params = {'api_key': self.api_key}

            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()

            data = response.json()

            if 'error' in data:
                return {'error': f"ZeroBounce API error: {data['error']}"}

            return {
                'success': True,
                'credits': data.get('Credits')
            }

        except requests.exceptions.RequestException as e:
            return {'error': f'ZeroBounce API request failed: {str(e)}'}
        except Exception as e:
            return {'error': f'ZeroBounce credits check error: {str(e)}'}

    def is_valid_email(self, email: str) -> bool:
        """
        Simple helper to check if email is valid

        Args:
            email: Email address to check

        Returns:
            Boolean - True if valid, False otherwise
        """
        result = self.validate_email(email)
        return result.get('success', False) and result.get('status') == 'valid'

    def get_email_status_summary(self, email: str) -> str:
        """
        Get a simple text summary of email validation status

        Args:
            email: Email to validate

        Returns:
            String describing the status
        """
        result = self.validate_email(email)

        if not result.get('success'):
            return f"❌ Error: {result.get('error', 'Unknown error')}"

        status = result.get('status', 'unknown')
        sub_status = result.get('sub_status', '')
        is_free = result.get('free_email', False)

        if status == 'valid':
            free_text = " (Free email)" if is_free else ""
            return f"✅ Valid{free_text}"
        elif status == 'invalid':
            return f"❌ Invalid: {sub_status}"
        elif status == 'catch-all':
            return f"⚠️ Catch-all domain (accepts all emails)"
        elif status == 'unknown':
            return f"❓ Unknown (could not verify)"
        elif status == 'spamtrap':
            return f"🚨 Spam trap - do not email!"
        elif status == 'abuse':
            return f"⚠️ Known complainer"
        elif status == 'do_not_mail':
            return f"🚫 Do not mail"
        else:
            return f"Status: {status}"


def test_zerobounce():
    """Test ZeroBounce integration"""
    print("Testing ZeroBounce Integration...")
    print("Note: This requires a valid API key\n")

    # Test with no API key
    zb = ZeroBounceIntegration()
    result = zb.validate_email('test@example.com')
    print(f"Test without API key: {result.get('error', 'Unexpected success')}\n")

    print("To use ZeroBounce:")
    print("1. Sign up at https://www.zerobounce.net/members/signup")
    print("2. Get your API key from your dashboard")
    print("3. Add it to the Settings tab in the app")
    print("4. You get 100 free validations per month")
    print("\nEmail validation helps prevent bounces and improve deliverability!")


if __name__ == "__main__":
    test_zerobounce()
