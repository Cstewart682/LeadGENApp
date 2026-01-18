#!/usr/bin/env python3
"""
Unified Signal Scoring System

Combines multiple data sources to calculate comprehensive buying signal scores:
- Website scraping (keywords across multiple pages)
- Google News monitoring
- Calgary Building Permits
- LinkedIn presence
- Email domain enrichment
"""

from typing import Dict, Optional
from datetime import datetime

# Import all modules
try:
    from enhanced_scraper import EnhancedWebScraper
    SCRAPER_AVAILABLE = True
except:
    SCRAPER_AVAILABLE = False

try:
    from news_monitor import NewsMonitor
    NEWS_AVAILABLE = True
except:
    NEWS_AVAILABLE = False

try:
    from building_permits import BuildingPermitsMonitor
    PERMITS_AVAILABLE = True
except:
    PERMITS_AVAILABLE = False

try:
    from linkedin_discovery import LinkedInDiscovery
    LINKEDIN_AVAILABLE = True
except:
    LINKEDIN_AVAILABLE = False

try:
    from email_enrichment import EmailEnrichment
    ENRICHMENT_AVAILABLE = True
except:
    ENRICHMENT_AVAILABLE = False


class UnifiedSignalScoring:
    def __init__(self, hunter_api_key: Optional[str] = None):
        """
        Initialize unified scoring system

        Args:
            hunter_api_key: Optional Hunter.io API key for email enrichment
        """
        self.hunter_api_key = hunter_api_key

        # Initialize modules
        if SCRAPER_AVAILABLE:
            self.scraper = EnhancedWebScraper(max_pages=10)
        if NEWS_AVAILABLE:
            self.news_monitor = NewsMonitor()
        if PERMITS_AVAILABLE:
            self.permits_monitor = BuildingPermitsMonitor()
        if LINKEDIN_AVAILABLE:
            self.linkedin_discovery = LinkedInDiscovery()
        if ENRICHMENT_AVAILABLE:
            self.email_enrichment = EmailEnrichment(hunter_api_key)

    def calculate_unified_score(
        self,
        company_name: str,
        website: Optional[str] = None,
        email: Optional[str] = None,
        check_news: bool = True,
        check_permits: bool = True,
        check_linkedin: bool = True,
        check_email_enrichment: bool = True,
        location: str = "Calgary"
    ) -> Dict:
        """
        Calculate comprehensive signal score from all available sources

        Args:
            company_name: Name of the company
            website: Company website URL (optional)
            email: Company email address (optional)
            check_news: Check Google News
            check_permits: Check building permits
            check_linkedin: Discover LinkedIn profiles
            check_email_enrichment: Enrich email domain data
            location: Location for news/permits (default: Calgary)

        Returns:
            Dict with unified scoring results
        """
        print(f"\n{'='*70}")
        print(f"UNIFIED SIGNAL SCORING: {company_name}")
        print(f"{'='*70}\n")

        result = {
            'company_name': company_name,
            'website': website,
            'email': email,
            'total_score': 0,
            'sources': {},
            'all_signals': [],
            'analysis_date': datetime.now().isoformat()
        }

        # 1. Website Scraping (if website provided)
        if website and SCRAPER_AVAILABLE:
            print("🌐 WEBSITE SCRAPING")
            print("-" * 70)
            try:
                website_data = self.scraper.scrape_website(website)
                result['sources']['website'] = {
                    'score': website_data['signal_score'],
                    'signals': website_data['buying_signals'],
                    'emails_found': len(website_data['emails']),
                    'phones_found': len(website_data['phones']),
                    'pages_scraped': website_data['pages_scraped']
                }
                result['total_score'] += website_data['signal_score']

                for signal in website_data['buying_signals']:
                    result['all_signals'].append({
                        'source': 'website',
                        'type': signal['keyword'],
                        'score': signal['score']
                    })

            except Exception as e:
                print(f"   ❌ Error: {e}")
                result['sources']['website'] = {'error': str(e)}

        # 2. Google News
        if check_news and NEWS_AVAILABLE:
            print("\n📰 NEWS MONITORING")
            print("-" * 70)
            try:
                news_data = self.news_monitor.monitor_company_news(company_name, location=location)
                result['sources']['news'] = {
                    'score': news_data['signal_score'],
                    'signals': news_data['signals'],
                    'articles_found': news_data['articles_found']
                }
                result['total_score'] += news_data['signal_score']

                for signal in news_data['signals']:
                    result['all_signals'].append({
                        'source': 'news',
                        'type': signal['keyword'],
                        'score': signal['score'],
                        'article': signal.get('article_title')
                    })

            except Exception as e:
                print(f"   ❌ Error: {e}")
                result['sources']['news'] = {'error': str(e)}

        # 3. Building Permits
        if check_permits and PERMITS_AVAILABLE:
            print("\n🏗️ BUILDING PERMITS")
            print("-" * 70)
            try:
                permits_data = self.permits_monitor.monitor_company_permits(company_name)
                result['sources']['permits'] = {
                    'score': permits_data['signal_score'],
                    'signals': permits_data['signals'],
                    'permits_found': permits_data['permits_found']
                }
                result['total_score'] += permits_data['signal_score']

                for signal in permits_data['signals']:
                    result['all_signals'].append({
                        'source': 'building_permit',
                        'type': 'permit_activity',
                        'score': signal['score'],
                        'details': signal.get('description')
                    })

            except Exception as e:
                print(f"   ❌ Error: {e}")
                result['sources']['permits'] = {'error': str(e)}

        # 4. LinkedIn Discovery
        if check_linkedin and LINKEDIN_AVAILABLE:
            print("\n💼 LINKEDIN DISCOVERY")
            print("-" * 70)
            try:
                linkedin_data = self.linkedin_discovery.discover_linkedin_info(company_name)
                result['sources']['linkedin'] = {
                    'score': linkedin_data['signal_score'],
                    'signals': linkedin_data['signals'],
                    'company_page': linkedin_data['company_page'],
                    'employees_found': linkedin_data['employee_count']
                }
                result['total_score'] += linkedin_data['signal_score']

                for signal in linkedin_data['signals']:
                    result['all_signals'].append({
                        'source': 'linkedin',
                        'type': signal['type'],
                        'score': signal['score']
                    })

            except Exception as e:
                print(f"   ❌ Error: {e}")
                result['sources']['linkedin'] = {'error': str(e)}

        # 5. Email Domain Enrichment
        if email and check_email_enrichment and ENRICHMENT_AVAILABLE:
            print("\n📧 EMAIL ENRICHMENT")
            print("-" * 70)
            try:
                enrichment_data = self.email_enrichment.enrich_email(
                    email,
                    use_hunter=(self.hunter_api_key is not None),
                    verify_email=False
                )
                result['sources']['email_enrichment'] = {
                    'score': enrichment_data['signal_score'],
                    'signals': enrichment_data['signals'],
                    'clearbit_data': enrichment_data.get('clearbit_data'),
                    'hunter_data': enrichment_data.get('hunter_data')
                }
                result['total_score'] += enrichment_data['signal_score']

                for signal in enrichment_data['signals']:
                    result['all_signals'].append({
                        'source': 'email_enrichment',
                        'type': signal['type'],
                        'score': signal['score']
                    })

            except Exception as e:
                print(f"   ❌ Error: {e}")
                result['sources']['email_enrichment'] = {'error': str(e)}

        # Cap total score at 100
        result['total_score'] = min(result['total_score'], 100)

        # Categorize the lead
        if result['total_score'] >= 70:
            result['priority'] = 'HIGH'
            result['priority_label'] = '🔥 Hot Lead'
        elif result['total_score'] >= 40:
            result['priority'] = 'MEDIUM'
            result['priority_label'] = '⚡ Warm Lead'
        else:
            result['priority'] = 'LOW'
            result['priority_label'] = '❄️ Cold Lead'

        # Summary
        print(f"\n{'='*70}")
        print(f"FINAL RESULTS")
        print(f"{'='*70}")
        print(f"  Total Signal Score: {result['total_score']}/100")
        print(f"  Priority: {result['priority_label']}")
        print(f"\n  Score Breakdown:")
        for source, data in result['sources'].items():
            if 'score' in data:
                print(f"    {source.title()}: +{data['score']} points")
        print(f"{'='*70}\n")

        return result


# Convenience function
def calculate_signal_score(
    company_name: str,
    website: Optional[str] = None,
    email: Optional[str] = None,
    hunter_api_key: Optional[str] = None,
    **kwargs
) -> Dict:
    """
    Calculate unified signal score for a company

    Args:
        company_name: Company name
        website: Company website (optional)
        email: Company email (optional)
        hunter_api_key: Hunter.io API key (optional)
        **kwargs: Additional options (check_news, check_permits, etc.)

    Returns:
        Dict with comprehensive scoring results
    """
    scorer = UnifiedSignalScoring(hunter_api_key)
    return scorer.calculate_unified_score(company_name, website, email, **kwargs)


# Test function
if __name__ == "__main__":
    import sys

    # Parse command line arguments
    if len(sys.argv) > 1:
        company_name = sys.argv[1]
    else:
        company_name = "CMC Manufacturing"

    website = sys.argv[2] if len(sys.argv) > 2 else "https://cmcmanufacturing.com"
    email = sys.argv[3] if len(sys.argv) > 3 else "info@cmcmanufacturing.com"
    hunter_key = sys.argv[4] if len(sys.argv) > 4 else None

    result = calculate_signal_score(
        company_name=company_name,
        website=website,
        email=email,
        hunter_api_key=hunter_key
    )

    # Display summary
    print("\n" + "="*70)
    print("COMPREHENSIVE SIGNAL ANALYSIS")
    print("="*70)
    print(f"\nCompany: {result['company_name']}")
    print(f"Total Score: {result['total_score']}/100")
    print(f"Priority: {result['priority_label']}")

    print(f"\n{'Signals Detected:':<30} {len(result['all_signals'])}")

    if result['all_signals']:
        print(f"\nTop Signals:")
        sorted_signals = sorted(result['all_signals'], key=lambda x: x['score'], reverse=True)
        for i, signal in enumerate(sorted_signals[:10], 1):
            print(f"  {i}. [{signal['source'].upper()}] {signal['type']} (+{signal['score']})")

    print("\n" + "="*70)
