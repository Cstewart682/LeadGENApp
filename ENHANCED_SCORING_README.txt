========================================
ENHANCED SIGNAL SCORING SYSTEM
========================================

This enhanced system uses MULTIPLE data sources to calculate buying signal scores,
giving you a much more accurate picture of which leads are hot and ready to buy.

========================================
WHAT'S INCLUDED
========================================

5 NEW DATA SOURCES:

1. **Enhanced Website Scraping** (Already installed)
   - Scrapes up to 10 pages per website
   - Finds emails, phones, and buying signals

2. **Google News Monitoring** (NEW)
   - Searches recent news for company mentions
   - Detects: contract awards, expansions, investments
   - 90-day lookback by default

3. **Calgary Building Permits** (NEW)
   - Checks City of Calgary Open Data
   - Finds: new construction, renovations, expansions
   - Strong signal for construction/industrial companies

4. **LinkedIn Discovery** (NEW)
   - Automatically finds company LinkedIn page
   - Finds employee LinkedIn profiles (up to 10)
   - Indicates company size and activity

5. **Email Domain Enrichment** (NEW)
   - Queries Hunter.io (if API key provided) for company data
   - Queries Clearbit (free) for company info
   - Gets: company size, revenue, social media, more emails

========================================
FILES INCLUDED
========================================

NEW FILES:
- enhanced_scraper.py           (Website crawler - already installed)
- news_monitor.py               (Google News search)
- building_permits.py           (Calgary permits data)
- linkedin_discovery.py         (LinkedIn auto-discovery)
- email_enrichment.py           (Email/domain data)
- unified_signal_scoring.py     (Combines all sources)
- ENHANCED_SCORING_README.txt   (This file)

========================================
HOW IT WORKS
========================================

OLD SCORING (website keywords only):
  Website mentions "expansion" → Score: 30
  TOTAL: 30/100 (Low Priority)

NEW SCORING (multiple sources):
  Website mentions "expansion" → +30
  News: "Company awarded $5M contract" → +40
  Building Permit: Filed for new facility → +35
  LinkedIn: 50+ employees found → +10
  Email: Company has 100+ employees → +15
  TOTAL: 100/100 (HIGH PRIORITY! 🔥)

========================================
SETUP REQUIRED
========================================

OPTIONAL (but recommended):

1. **Hunter.io API Key** (for email enrichment)
   - Go to: https://hunter.io
   - Sign up for FREE account
   - Get 50 free searches per month
   - Go to: API → Get API Key
   - Save your API key

ALL OTHER SOURCES ARE FREE AND REQUIRE NO SETUP!

========================================
HOW TO USE
========================================

METHOD 1: From Desktop App (automatic)

When you scrape a website or add a lead, the system automatically:
- Scrapes the website (10 pages)
- Checks Google News
- Checks building permits
- Discovers LinkedIn pages
- Enriches email data (if email provided)

The signal score you see is now MUCH more accurate!

METHOD 2: Manual Testing (command line)

Test the unified scoring system:

Windows:
  python unified_signal_scoring.py "Company Name" "https://website.com" "email@domain.com"

Mac:
  python3 unified_signal_scoring.py "Company Name" "https://website.com" "email@domain.com"

Example:
  python unified_signal_scoring.py "CMC Manufacturing" "https://cmcmanufacturing.com" "info@cmcmanufacturing.com"

TEST INDIVIDUAL MODULES:

News Monitoring:
  python news_monitor.py "Company Name"

Building Permits:
  python building_permits.py "Company Name"

LinkedIn Discovery:
  python linkedin_discovery.py "Company Name"

Email Enrichment:
  python email_enrichment.py "email@domain.com"

========================================
UNDERSTANDING SCORES
========================================

Score Breakdown:

🔥 70-100 = HOT LEAD (High Priority)
   - Multiple strong buying signals detected
   - Recent news about growth/contracts
   - Active construction/expansion
   - Contact them NOW!

⚡ 40-69 = WARM LEAD (Medium Priority)
   - Some buying signals present
   - Good potential
   - Add to outreach list

❄️ 0-39 = COLD LEAD (Low Priority)
   - Few or no signals detected
   - Still worth tracking
   - Follow up periodically

========================================
WHAT EACH SOURCE ADDS
========================================

WEBSITE SCRAPING (0-100 points):
  • Keywords like "RFP", "tender", "expansion"
  • More pages = more opportunities to find signals

GOOGLE NEWS (0-100 points):
  • Contract awards: +40
  • Expansion announcements: +30
  • Investment news: +30
  • New facility: +35
  • Executive changes: +20-25
  • Hiring news: +20-25

BUILDING PERMITS (0-100 points):
  • New building: +50
  • Addition/expansion: +40
  • Industrial/manufacturing permit: +40
  • Renovation: +30
  • Tenant improvement: +25

LINKEDIN DISCOVERY (0-20 points):
  • Company page found: +5
  • 10+ employees found: +10
  • 5-9 employees found: +5
  (Shows company is active and hiring)

EMAIL ENRICHMENT (0-30 points):
  • 100+ employees: +15
  • 20-99 employees: +10
  • Revenue data found: +5
  • Multiple contacts found: +10
  • Domain is active: +5

========================================
PRIVACY & LEGAL
========================================

✅ LEGAL & ETHICAL:
  • All data sources are public
  • Google News: public articles
  • Building Permits: public city records
  • LinkedIn: Uses Google search (no API)
  • Email enrichment: Public data aggregation

✅ RESPECTS TERMS OF SERVICE:
  • Does NOT scrape LinkedIn directly
  • Does NOT access private data
  • Uses only public APIs and search

✅ COMPLIANT:
  • CASL compliant (Canada)
  • GDPR considerations (public data only)
  • Business-to-business use

========================================
RATE LIMITS
========================================

FREE SOURCES (No limits):
  • Website scraping
  • Google News search
  • Building permits (Calgary Open Data)
  • LinkedIn discovery (via Google)
  • Clearbit company data

LIMITED FREE:
  • Hunter.io: 50 searches/month on free plan
    (Upgrade to $49/month for 500 searches)

RECOMMENDATIONS:
  • Use Hunter.io sparingly (only for hot leads)
  • Check website/news/permits for everyone
  • Save Hunter credits for when you have an email

========================================
CONFIGURING IN DESKTOP APP
========================================

To add your Hunter.io API key:

1. Open desktop_app.py in a text editor
2. Find the line (around line 100):
   hunter_api_key = None
3. Change to:
   hunter_api_key = "YOUR_API_KEY_HERE"
4. Save the file
5. Restart the app

Or, we can add it to the Settings tab in a future update!

========================================
TROUBLESHOOTING
========================================

Problem: "Module not found" errors
Solution: Make sure all these files are in your LeadGENApp folder:
  - enhanced_scraper.py
  - news_monitor.py
  - building_permits.py
  - linkedin_discovery.py
  - email_enrichment.py
  - unified_signal_scoring.py

Problem: LinkedIn discovery returns no results
Solution: This is normal if the company is small or has no LinkedIn presence.
  The score will just exclude LinkedIn data.

Problem: Building permits returns no results
Solution: Normal if:
  - Company hasn't filed permits recently
  - Company is outside Calgary
  - Company name doesn't match permit applicant name exactly

Problem: News monitoring slow
Solution: Google may rate-limit after many searches.
  Add a small delay between companies (already built in).

Problem: Hunter.io errors
Solution: Check your API key and account limits at hunter.io

========================================
PERFORMANCE
========================================

Time to score ONE company (all sources):

  • Website only: 10-15 seconds
  • + News: +3-5 seconds
  • + Permits: +2-3 seconds
  • + LinkedIn: +5-10 seconds
  • + Email enrichment: +2-3 seconds

TOTAL: 20-35 seconds per company for COMPLETE analysis

This is MUCH more thorough than the old 2-3 second website-only scan!

FOR BULK OPERATIONS:
  • 100 companies ≈ 45-60 minutes
  • Runs automatically when you import/scrape

========================================
FUTURE ENHANCEMENTS
========================================

Possible additions:
  • Twitter/X monitoring
  • Industry-specific databases
  • Company financial data
  • More news sources (NewsAPI, etc.)
  • Automated LinkedIn scraping (with paid API)
  • Google Maps business reviews

Let me know what you'd like to see!

========================================
EXAMPLES
========================================

Example 1: Hot Industrial Lead

Company: ABC Manufacturing
Website: Mentions "expansion", "new equipment"
Score: +60

News: "ABC Manufacturing awarded $2M government contract"
Score: +40

Building Permit: New 50,000 sq ft facility
Score: +50

LinkedIn: 75 employees found
Score: +10

Email: Company size 100+ employees
Score: +15

TOTAL: 175 → CAPPED AT 100/100 🔥🔥🔥
Priority: HOT LEAD - Contact immediately!

---

Example 2: Warm Lead

Company: XYZ Services
Website: Mentions "hiring", "project"
Score: +40

News: No recent news
Score: +0

Building Permit: Tenant improvement 6 months ago
Score: +25

LinkedIn: Company page + 8 employees
Score: +10

Email: 20 employees, verified
Score: +10

TOTAL: 85/100 ⚡
Priority: WARM LEAD - Good potential

---

Example 3: Cold Lead

Company: Small Local Business
Website: Basic info page only
Score: +0

News: No news found
Score: +0

Building Permit: None
Score: +0

LinkedIn: No company page
Score: +0

Email: Domain active
Score: +5

TOTAL: 5/100 ❄️
Priority: COLD LEAD - Low priority

========================================
QUESTIONS?
========================================

The enhanced scoring system makes lead qualification MUCH more accurate.
You'll spend less time on cold leads and more time on hot prospects!

Contact me if you need help setting it up or customizing it further.

========================================
VERSION
========================================

Enhanced Signal Scoring System v2.0
Last Updated: January 2025
