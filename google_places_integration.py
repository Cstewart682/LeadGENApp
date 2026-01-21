#!/usr/bin/env python3
"""
Google Places API Integration
Provides local business data including phone numbers, addresses, reviews
"""

import requests
from typing import Dict, List, Optional
import urllib.parse


class GooglePlacesIntegration:
    """Google Places API client for local business data"""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key
        self.base_url = "https://maps.googleapis.com/maps/api/place"

    def find_place(self, company_name: str, location: str = "Calgary, AB") -> Dict:
        """
        Find a place by company name and location

        Args:
            company_name: Name of the company
            location: Location to search (default: Calgary, AB)

        Returns:
            Dictionary with place data including phone, address, reviews
        """
        if not self.api_key:
            return {'error': 'No Google Places API key provided'}

        try:
            # Step 1: Find Place from Text
            search_url = f"{self.base_url}/findplacefromtext/json"
            query = f"{company_name} {location}"

            params = {
                'input': query,
                'inputtype': 'textquery',
                'fields': 'place_id,name,formatted_address',
                'key': self.api_key
            }

            response = requests.get(search_url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            if data.get('status') != 'OK' or not data.get('candidates'):
                return {'error': f"Place not found: {data.get('status')}"}

            place_id = data['candidates'][0]['place_id']

            # Step 2: Get Place Details
            return self.get_place_details(place_id)

        except requests.exceptions.RequestException as e:
            return {'error': f'Google Places API request failed: {str(e)}'}
        except Exception as e:
            return {'error': f'Google Places error: {str(e)}'}

    def get_place_details(self, place_id: str) -> Dict:
        """
        Get detailed information about a place

        Args:
            place_id: Google Place ID

        Returns:
            Dictionary with detailed place information
        """
        if not self.api_key:
            return {'error': 'No Google Places API key provided'}

        try:
            details_url = f"{self.base_url}/details/json"

            fields = [
                'name', 'formatted_address', 'formatted_phone_number',
                'international_phone_number', 'website', 'rating',
                'user_ratings_total', 'opening_hours', 'photos',
                'reviews', 'types', 'business_status', 'url'
            ]

            params = {
                'place_id': place_id,
                'fields': ','.join(fields),
                'key': self.api_key
            }

            response = requests.get(details_url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            if data.get('status') != 'OK':
                return {'error': f"Could not get details: {data.get('status')}"}

            result = data.get('result', {})

            # Extract opening hours
            opening_hours = result.get('opening_hours', {})
            hours_text = opening_hours.get('weekday_text', [])

            # Extract reviews (top 5)
            reviews = []
            for review in result.get('reviews', [])[:5]:
                reviews.append({
                    'author': review.get('author_name'),
                    'rating': review.get('rating'),
                    'text': review.get('text'),
                    'time': review.get('relative_time_description')
                })

            return {
                'success': True,
                'place_id': place_id,
                'name': result.get('name'),
                'address': result.get('formatted_address'),
                'phone': result.get('formatted_phone_number'),
                'international_phone': result.get('international_phone_number'),
                'website': result.get('website'),
                'rating': result.get('rating'),
                'total_ratings': result.get('user_ratings_total'),
                'business_status': result.get('business_status'),
                'types': result.get('types', []),
                'google_maps_url': result.get('url'),
                'is_open_now': opening_hours.get('open_now'),
                'hours': hours_text,
                'reviews': reviews,
                'photo_count': len(result.get('photos', []))
            }

        except requests.exceptions.RequestException as e:
            return {'error': f'Google Places API request failed: {str(e)}'}
        except Exception as e:
            return {'error': f'Google Places details error: {str(e)}'}

    def search_nearby(self, location: str, business_type: str = "industrial", radius: int = 5000) -> Dict:
        """
        Search for nearby businesses

        Args:
            location: Location to search (e.g., "Calgary, AB")
            business_type: Type of business to search for
            radius: Search radius in meters (default 5000)

        Returns:
            Dictionary with list of nearby businesses
        """
        if not self.api_key:
            return {'error': 'No Google Places API key provided'}

        try:
            # First, geocode the location
            geocode_url = "https://maps.googleapis.com/maps/api/geocode/json"
            geocode_params = {
                'address': location,
                'key': self.api_key
            }

            geo_response = requests.get(geocode_url, params=geocode_params, timeout=10)
            geo_response.raise_for_status()
            geo_data = geo_response.json()

            if geo_data.get('status') != 'OK':
                return {'error': f"Could not geocode location: {geo_data.get('status')}"}

            lat_lng = geo_data['results'][0]['geometry']['location']

            # Search nearby
            nearby_url = f"{self.base_url}/nearbysearch/json"
            params = {
                'location': f"{lat_lng['lat']},{lat_lng['lng']}",
                'radius': radius,
                'keyword': business_type,
                'key': self.api_key
            }

            response = requests.get(nearby_url, params=params, timeout=15)
            response.raise_for_status()
            data = response.json()

            if data.get('status') not in ['OK', 'ZERO_RESULTS']:
                return {'error': f"Nearby search failed: {data.get('status')}"}

            businesses = []
            for place in data.get('results', [])[:20]:  # Limit to 20 results
                businesses.append({
                    'place_id': place.get('place_id'),
                    'name': place.get('name'),
                    'address': place.get('vicinity'),
                    'rating': place.get('rating'),
                    'user_ratings_total': place.get('user_ratings_total'),
                    'types': place.get('types', []),
                    'business_status': place.get('business_status')
                })

            return {
                'success': True,
                'total_found': len(businesses),
                'businesses': businesses
            }

        except requests.exceptions.RequestException as e:
            return {'error': f'Google Places API request failed: {str(e)}'}
        except Exception as e:
            return {'error': f'Google Places nearby search error: {str(e)}'}


def test_google_places():
    """Test Google Places integration"""
    print("Testing Google Places Integration...")
    print("Note: This requires a valid API key\n")

    # Test with no API key
    places = GooglePlacesIntegration()
    result = places.find_place("Test Company", "Calgary, AB")
    print(f"Test without API key: {result.get('error', 'Unexpected success')}\n")

    print("To use Google Places API:")
    print("1. Go to https://console.cloud.google.com")
    print("2. Create a project and enable Places API")
    print("3. Create credentials (API Key)")
    print("4. Add it to the Settings tab in the app")
    print("5. You get $200 credit per month (≈40,000 requests)")


if __name__ == "__main__":
    test_google_places()
