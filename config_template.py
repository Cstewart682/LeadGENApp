# Calgary Lead Generator - Configuration
# 
# Copy this file to config.py and fill in your API keys
# 
# NEVER commit config.py to version control!

# ============================================================================
# YOUR COMPANY INFO (for email templates)
# ============================================================================

YOUR_NAME = "Your Name"
YOUR_COMPANY = "Your Company Name"
YOUR_PHONE = "(403) 555-0000"
YOUR_EMAIL = "you@yourcompany.com"

# ============================================================================
# JOBBER CRM INTEGRATION
# ============================================================================
# Set up at: https://developer.getjobber.com/
# 1. Create a developer account
# 2. Create an app in Developer Center
# 3. Copy Client ID and Client Secret

JOBBER_CLIENT_ID = ""
JOBBER_CLIENT_SECRET = ""
JOBBER_REDIRECT_URI = "http://localhost:5000/oauth/callback"

# ============================================================================
# GOOGLE PLACES API
# ============================================================================
# Get your key: https://console.cloud.google.com/apis/credentials
# Enable: Places API, Geocoding API
# Free tier: $200/month credit (~11,000 place searches)

GOOGLE_API_KEY = ""

# ============================================================================
# HUNTER.IO
# ============================================================================
# Get your key: https://hunter.io/api_keys
# Free tier: 25 domain searches/month, 50 verifications/month

HUNTER_API_KEY = ""

# ============================================================================
# APOLLO.IO
# ============================================================================
# Get your key: https://app.apollo.io/#/settings/integrations/api
# Free tier: 10,000 records/month (with limitations)

APOLLO_API_KEY = ""

# ============================================================================
# ZEROBOUNCE (Email Verification)
# ============================================================================
# Get your key: https://www.zerobounce.net/members/apikey
# Pricing: ~$15 per 1,000 verifications

ZEROBOUNCE_API_KEY = ""

# ============================================================================
# NEVERBOUNCE (Email Verification)
# ============================================================================
# Get your key: https://app.neverbounce.com/settings/api
# Pricing: ~$8 per 1,000 verifications

NEVERBOUNCE_API_KEY = ""

# ============================================================================
# CLEARBIT
# ============================================================================
# Get your key: https://clearbit.com
# Paid plans only (starts ~$99/month)

CLEARBIT_API_KEY = ""

# ============================================================================
# OPENCORPORATES
# ============================================================================
# Optional - works without key but with rate limits
# Get your key: https://opencorporates.com/api_accounts

OPENCORPORATES_API_KEY = ""

# ============================================================================
# EMAIL ALERTS (for tender notifications)
# ============================================================================
# For Gmail: Use an App Password, not your regular password
# https://support.google.com/accounts/answer/185833

SMTP_HOST = "smtp.gmail.com"
SMTP_PORT = 587
SMTP_USER = ""  # your-email@gmail.com
SMTP_PASSWORD = ""  # App password
ALERT_RECIPIENTS = []  # ["you@company.com", "colleague@company.com"]

# ============================================================================
# TENDER MONITORING SETTINGS
# ============================================================================

# Keywords to match in tender titles/descriptions
TENDER_KEYWORDS = [
    'maintenance', 'repair', 'hvac', 'plumbing', 'electrical',
    'mechanical', 'facilities', 'janitorial', 'cleaning',
    'landscaping', 'snow removal', 'equipment', 'service',
    'preventive maintenance', 'building', 'construction'
]

# Locations to monitor
TENDER_LOCATIONS = ['Alberta', 'Calgary', 'Edmonton', 'Red Deer']

# Minimum relevance score to alert (0-100)
TENDER_MIN_RELEVANCE = 20

# ============================================================================
# LINKEDIN IMPORT SETTINGS
# ============================================================================

# Target titles to filter from LinkedIn imports
LINKEDIN_TARGET_TITLES = [
    'Plant Manager', 'Operations Manager', 'Purchasing Manager',
    'Maintenance Manager', 'Facilities Manager', 'Engineering Manager',
    'Procurement', 'Buyer', 'Director of Operations', 'VP Operations',
    'General Manager', 'Owner', 'President'
]

# Target locations
LINKEDIN_TARGET_LOCATIONS = ['Calgary', 'Alberta', 'AB']
