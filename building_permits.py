#!/usr/bin/env python3
"""
Calgary Building Permits Monitor

Queries City of Calgary Open Data Portal for building permits
Detects construction, renovation, and expansion activities
"""

import requests
from datetime import datetime, timedelta
from typing import List, Dict
import json

class BuildingPermitsMonitor:
    def __init__(self):
        # City of Calgary Open Data API
        self.api_base = "https://data.calgary.ca/resource/"

        # Building Permits dataset ID
        # You can find this at: https://data.calgary.ca/
        self.permits_endpoint = "c2es-76ed.json"  # Building Permits dataset

        self.headers = {
            'User-Agent': 'Calgary Lead Generator'
        }

        # Permit types that indicate buying signals
        self.signal_permit_types = {
            'new building': 50,
            'addition': 40,
            'alteration': 30,
            'renovation': 30,
            'demolition': 25,  # Often precedes new construction
            'tenant improvement': 25,
            'manufacturing': 40,
            'industrial': 40,
            'warehouse': 35,
            'office': 30
        }

    def search_permits_by_company(self, company_name: str, days_back: int = 365) -> List[Dict]:
        """
        Search building permits by company name

        Args:
            company_name: Name of company to search
            days_back: Number of days to search back

        Returns:
            List of permits found
        """
        permits = []

        try:
            # Calculate date range
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days_back)
            start_date_str = start_date.strftime('%Y-%m-%d')

            # Build query URL
            # Calgary Open Data uses SODA API
            url = f"{self.api_base}{self.permits_endpoint}"

            # Query parameters
            params = {
                '$where': f"issueddate >= '{start_date_str}'",
                '$limit': 100,
                '$order': 'issueddate DESC'
            }

            response = requests.get(url, params=params, headers=self.headers, timeout=15)

            if response.status_code == 200:
                all_permits = response.json()

                # Filter by company name
                company_lower = company_name.lower()
                for permit in all_permits:
                    # Check various fields for company name match
                    applicant = permit.get('applicant', '').lower()
                    contractor = permit.get('contractorname', '').lower()
                    owner = permit.get('ownername', '').lower()
                    description = permit.get('description', '').lower()

                    if (company_lower in applicant or
                        company_lower in contractor or
                        company_lower in owner or
                        company_lower in description):

                        permits.append({
                            'permit_number': permit.get('permitnum'),
                            'permit_type': permit.get('permittype'),
                            'permit_class': permit.get('permitclass'),
                            'description': permit.get('description'),
                            'applicant': permit.get('applicant'),
                            'contractor': permit.get('contractorname'),
                            'address': permit.get('originaladdress'),
                            'work_class': permit.get('workclassmapped'),
                            'issued_date': permit.get('issueddate'),
                            'estimated_cost': permit.get('estimatedprojectcost'),
                            'status': permit.get('statuscurrent')
                        })

        except Exception as e:
            print(f"Error searching permits: {e}")

        return permits

    def analyze_permits_for_signals(self, permits: List[Dict]) -> tuple[List[Dict], int]:
        """
        Analyze permits for buying signals

        Args:
            permits: List of permits

        Returns:
            Tuple of (signals found, total score)
        """
        signals_found = []
        total_score = 0

        for permit in permits:
            # Check permit type and description for keywords
            permit_text = (
                permit.get('permit_type', '') + ' ' +
                permit.get('description', '') + ' ' +
                permit.get('work_class', '')
            ).lower()

            permit_score = 0
            matched_keywords = []

            for keyword, score in self.signal_permit_types.items():
                if keyword in permit_text:
                    permit_score += score
                    matched_keywords.append(keyword)

            if permit_score > 0:
                signals_found.append({
                    'permit_number': permit.get('permit_number'),
                    'signal_type': 'building_permit',
                    'keywords': matched_keywords,
                    'score': min(permit_score, 50),  # Cap individual permit score
                    'description': permit.get('description'),
                    'permit_type': permit.get('permit_type'),
                    'address': permit.get('address'),
                    'issued_date': permit.get('issued_date'),
                    'estimated_cost': permit.get('estimated_cost')
                })

                total_score += min(permit_score, 50)

        # Cap total at 100
        total_score = min(total_score, 100)

        return signals_found, total_score

    def monitor_company_permits(self, company_name: str, days_back: int = 365) -> Dict:
        """
        Complete permit monitoring for a company

        Args:
            company_name: Company to monitor
            days_back: Days to search back

        Returns:
            Dict with permits and signal analysis
        """
        print(f"\n{'='*60}")
        print(f"BUILDING PERMITS: {company_name}")
        print(f"{'='*60}")

        # Search for permits
        print(f"🏗️ Searching Calgary building permits...")
        permits = self.search_permits_by_company(company_name, days_back)

        print(f"   Found {len(permits)} permits")

        # Analyze for signals
        signals, score = self.analyze_permits_for_signals(permits)

        result = {
            'company_name': company_name,
            'permits_found': len(permits),
            'permits': permits,
            'signal_score': score,
            'signals': signals,
            'search_date': datetime.now().isoformat()
        }

        print(f"   Signal Score: +{score} points from permits")
        print(f"{'='*60}\n")

        return result


# Convenience function
def check_building_permits(company_name: str, days_back: int = 365) -> Dict:
    """
    Check building permits for a company

    Args:
        company_name: Company to check
        days_back: Days to search back

    Returns:
        Dict with permit data and signals
    """
    monitor = BuildingPermitsMonitor()
    return monitor.monitor_company_permits(company_name, days_back)


# Test function
if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        company_name = " ".join(sys.argv[1:])
    else:
        company_name = "CMC"  # Partial match test

    result = check_building_permits(company_name, days_back=730)  # 2 years

    print("\n" + "="*60)
    print("BUILDING PERMITS RESULTS")
    print("="*60)
    print(f"\nCompany: {result['company_name']}")
    print(f"Permits Found: {result['permits_found']}")

    if result['permits']:
        print(f"\nRecent Permits:")
        for i, permit in enumerate(result['permits'][:5], 1):
            print(f"\n{i}. {permit['permit_type']}")
            print(f"   Permit #: {permit['permit_number']}")
            print(f"   Description: {permit['description']}")
            print(f"   Address: {permit['address']}")
            print(f"   Issued: {permit['issued_date']}")
            if permit.get('estimated_cost'):
                print(f"   Estimated Cost: ${permit['estimated_cost']}")

    if result['signals']:
        print(f"\nBuying Signals Detected:")
        for signal in result['signals']:
            print(f"\n• Building Permit Activity (+{signal['score']} points)")
            print(f"  Type: {signal['permit_type']}")
            print(f"  Keywords: {', '.join(signal['keywords'])}")
            print(f"  Description: {signal['description']}")

        print(f"\nTotal Signal Boost: +{result['signal_score']} points")
    else:
        print("\nNo building permits found with buying signals.")
