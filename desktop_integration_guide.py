#!/usr/bin/env python3
"""
Desktop App Intelligence Integration

This module enhances the desktop app with full intelligence gathering and viewing.
It integrates: website scraping, news, permits, LinkedIn, and email enrichment.

INSTRUCTIONS:
1. Save this file as: desktop_app_enhanced.py
2. Replace your current desktop_app.py with this file
3. Or merge the changes into your existing desktop_app.py
"""

# Add this import at the top of desktop_app.py (around line 18)
# ============================================================================
# Add after the existing imports:

try:
    from unified_signal_scoring import UnifiedSignalScoring
    UNIFIED_SCORING_AVAILABLE = True
except ImportError:
    UNIFIED_SCORING_AVAILABLE = False
    print("⚠ Unified signal scoring not available")

# ============================================================================
# REPLACE the scrape_now() function in edit_lead() with this enhanced version:
# ============================================================================

def scrape_now_enhanced():
    """Enhanced scraping with full intelligence gathering"""
    if not lead.get('website'):
        messagebox.showwarning("Warning", "No website entered")
        return

    dialog.config(cursor="wait")
    dialog.update()

    # Use unified scoring if available
    if UNIFIED_SCORING_AVAILABLE:
        # Initialize unified scoring
        hunter_key = None  # TODO: Get from settings
        scorer = UnifiedSignalScoring(hunter_api_key=hunter_key)

        # Get email if available
        email = edit_vars.get('general_email', tk.StringVar()).get()
        if not email:
            email = lead.get('general_email')

        # Run comprehensive analysis
        result = scorer.calculate_unified_score(
            company_name=lead['company_name'],
            website=lead['website'],
            email=email,
            check_news=True,
            check_permits=True,
            check_linkedin=True,
            check_email_enrichment=bool(email)
        )

        # Update lead with comprehensive data
        lead['signal_score'] = result['total_score']
        lead['priority'] = result['priority']

        # Store ALL intelligence data
        lead['intelligence'] = {
            'last_updated': result['analysis_date'],
            'sources': result['sources'],
            'all_signals': result['all_signals']
        }

        # Extract emails and phones from website scraping
        if 'website' in result['sources'] and 'error' not in result['sources']['website']:
            website_data = result['sources']['website']

            # Get the actual scraper result (need to access it)
            # For now, run a quick scrape to get emails/phones
            from enhanced_scraper import scrape_website as enhanced_scrape
            scrape_result = enhanced_scrape(lead['website'])

            if scrape_result['emails'] and not edit_vars['general_email'].get():
                edit_vars['general_email'].set(scrape_result['emails'][0])

            if scrape_result['phones'] and not edit_vars['general_phone'].get():
                edit_vars['general_phone'].set(scrape_result['phones'][0])

            # Store all found contacts
            lead['all_emails'] = scrape_result['emails']
            lead['all_phones'] = scrape_result['phones']

        # Update buying signals
        if result['all_signals']:
            # Convert to old format for compatibility
            lead['buying_signals'] = []
            for signal in result['all_signals']:
                lead['buying_signals'].append({
                    'keyword': signal['type'],
                    'score': signal['score'],
                    'source': signal['source']
                })

        dialog.config(cursor="")

        # Show comprehensive results
        summary = f"✅ Intelligence Gathered!\n\n"
        summary += f"Total Score: {result['total_score']}/100\n"
        summary += f"Priority: {result['priority_label']}\n\n"

        if 'website' in result['sources']:
            ws = result['sources']['website']
            if 'error' not in ws:
                summary += f"📧 Emails: {ws.get('emails_found', 0)}\n"
                summary += f"📞 Phones: {ws.get('phones_found', 0)}\n"

        if 'news' in result['sources']:
            news = result['sources']['news']
            if 'error' not in news:
                summary += f"📰 News Articles: {news.get('articles_found', 0)}\n"

        if 'permits' in result['sources']:
            permits = result['sources']['permits']
            if 'error' not in permits:
                summary += f"🏗️ Building Permits: {permits.get('permits_found', 0)}\n"

        if 'linkedin' in result['sources']:
            li = result['sources']['linkedin']
            if 'error' not in li:
                summary += f"💼 LinkedIn Employees: {li.get('employees_found', 0)}\n"

        summary += f"\nView full details by clicking 'View Intelligence'"

        messagebox.showinfo("Intelligence Gathered", summary)

        # Save immediately
        save_json(DATA_DIR / "leads.json", self.leads)

    else:
        # Fallback to basic scraping
        result = scrape_website(lead['website'])
        if result['emails']:
            edit_vars['general_email'].set(result['emails'][0])
        if result['phones']:
            edit_vars['general_phone'].set(result['phones'][0])

        dialog.config(cursor="")
        messagebox.showinfo("Success", f"Found {len(result['emails'])} emails, {len(result['phones'])} phones")

# ============================================================================
# ADD this new function to view intelligence details:
# ============================================================================

def view_intelligence():
    """Display comprehensive intelligence data"""
    if not lead.get('intelligence'):
        messagebox.showinfo("No Data", "No intelligence data available.\n\nClick 'Enhanced Scrape' to gather intelligence.")
        return

    # Create intelligence viewer window
    intel_window = tk.Toplevel(dialog)
    intel_window.title(f"Intelligence: {lead['company_name']}")
    intel_window.geometry("800x600")

    # Create notebook for different intelligence sources
    notebook = ttk.Notebook(intel_window)
    notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    intel_data = lead['intelligence']

    # Overview Tab
    overview_tab = tk.Frame(notebook)
    notebook.add(overview_tab, text="📊 Overview")

    overview_text = scrolledtext.ScrolledText(overview_tab, wrap=tk.WORD, font=("Arial", 10))
    overview_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    overview_content = f"""INTELLIGENCE SUMMARY
{'='*60}

Company: {lead['company_name']}
Website: {lead.get('website', 'N/A')}
Last Updated: {intel_data.get('last_updated', 'Unknown')}

SIGNAL SCORE: {lead.get('signal_score', 0)}/100
Priority: {lead.get('priority', 'Unknown')}

{'='*60}
SCORE BREAKDOWN:
{'='*60}

"""

    for source, data in intel_data.get('sources', {}).items():
        if isinstance(data, dict) and 'score' in data:
            overview_content += f"\n{source.upper()}: +{data['score']} points\n"

            if source == 'website':
                overview_content += f"  • Pages Scraped: {data.get('pages_scraped', 0)}\n"
                overview_content += f"  • Emails Found: {data.get('emails_found', 0)}\n"
                overview_content += f"  • Phones Found: {data.get('phones_found', 0)}\n"

            elif source == 'news':
                overview_content += f"  • Articles Found: {data.get('articles_found', 0)}\n"

            elif source == 'permits':
                overview_content += f"  • Permits Found: {data.get('permits_found', 0)}\n"

            elif source == 'linkedin':
                overview_content += f"  • Company Page: {'Found' if data.get('company_page') else 'Not Found'}\n"
                overview_content += f"  • Employees Found: {data.get('employees_found', 0)}\n"

            elif source == 'email_enrichment':
                cb = data.get('clearbit_data', {})
                if cb and 'error' not in cb:
                    overview_content += f"  • Company Size: {cb.get('employees', 'Unknown')} employees\n"
                    overview_content += f"  • Industry: {cb.get('industry', 'Unknown')}\n"

    overview_content += f"\n\n{'='*60}\n"
    overview_content += f"ALL SIGNALS DETECTED ({len(intel_data.get('all_signals', []))}):\n"
    overview_content += f"{'='*60}\n\n"

    for signal in intel_data.get('all_signals', []):
        overview_content += f"• [{signal['source'].upper()}] {signal['type']} (+{signal['score']})\n"

    overview_text.insert(1.0, overview_content)
    overview_text.config(state=tk.DISABLED)

    # News Tab
    if 'news' in intel_data.get('sources', {}):
        news_data = intel_data['sources']['news']
        if 'signals' in news_data and news_data['signals']:
            news_tab = tk.Frame(notebook)
            notebook.add(news_tab, text="📰 News")

            news_text = scrolledtext.ScrolledText(news_tab, wrap=tk.WORD, font=("Arial", 10))
            news_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

            news_content = f"NEWS MONITORING RESULTS\n{'='*60}\n\n"

            for signal in news_data['signals']:
                news_content += f"SIGNAL: {signal['keyword'].upper()} (+{signal['score']} points)\n"
                news_content += f"Article: {signal.get('article_title', 'N/A')}\n"
                news_content += f"Link: {signal.get('article_link', 'N/A')}\n"
                news_content += f"Context: {signal.get('context', 'N/A')}\n"
                news_content += f"\n{'-'*60}\n\n"

            news_text.insert(1.0, news_content)
            news_text.config(state=tk.DISABLED)

    # Building Permits Tab
    if 'permits' in intel_data.get('sources', {}):
        permits_data = intel_data['sources']['permits']
        if 'signals' in permits_data and permits_data['signals']:
            permits_tab = tk.Frame(notebook)
            notebook.add(permits_tab, text="🏗️ Permits")

            permits_text = scrolledtext.ScrolledText(permits_tab, wrap=tk.WORD, font=("Arial", 10))
            permits_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

            permits_content = f"BUILDING PERMITS FOUND\n{'='*60}\n\n"

            for signal in permits_data['signals']:
                permits_content += f"PERMIT: {signal.get('permit_number', 'Unknown')}\n"
                permits_content += f"Type: {signal.get('permit_type', 'N/A')}\n"
                permits_content += f"Description: {signal.get('description', 'N/A')}\n"
                permits_content += f"Address: {signal.get('address', 'N/A')}\n"
                permits_content += f"Issued: {signal.get('issued_date', 'N/A')}\n"
                if signal.get('estimated_cost'):
                    permits_content += f"Estimated Cost: ${signal['estimated_cost']}\n"
                permits_content += f"Signal Score: +{signal['score']} points\n"
                permits_content += f"\n{'-'*60}\n\n"

            permits_text.insert(1.0, permits_content)
            permits_text.config(state=tk.DISABLED)

    # LinkedIn Tab
    if 'linkedin' in intel_data.get('sources', {}):
        linkedin_data = intel_data['sources']['linkedin']
        linkedin_tab = tk.Frame(notebook)
        notebook.add(linkedin_tab, text="💼 LinkedIn")

        linkedin_text = scrolledtext.ScrolledText(linkedin_tab, wrap=tk.WORD, font=("Arial", 10))
        linkedin_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        linkedin_content = f"LINKEDIN DISCOVERY\n{'='*60}\n\n"

        if linkedin_data.get('company_page'):
            linkedin_content += f"Company Page:\n{linkedin_data['company_page']}\n\n"
        else:
            linkedin_content += "Company Page: Not found\n\n"

        # Note: Employee profiles are discovered but not stored to respect privacy
        linkedin_content += f"Employees Found: {linkedin_data.get('employees_found', 0)}\n\n"

        if linkedin_data.get('signals'):
            linkedin_content += f"Signals:\n"
            for signal in linkedin_data['signals']:
                linkedin_content += f"  • {signal.get('description', 'Unknown')} (+{signal['score']})\n"

        linkedin_text.insert(1.0, linkedin_content)
        linkedin_text.config(state=tk.DISABLED)

    # Close button
    btn_frame = tk.Frame(intel_window)
    btn_frame.pack(fill=tk.X, padx=10, pady=10)

    tk.Button(btn_frame, text="Close", command=intel_window.destroy,
             bg="#6c757d", fg="white", padx=20, pady=8).pack(side=tk.RIGHT)

# ============================================================================
# UPDATE the button section in edit_lead() to include new buttons:
# ============================================================================

# Replace the existing button section with this:
"""
tk.Button(btn_frame, text="💾 Save", command=save_changes,
         bg="#1a3a5c", fg="white", padx=15, pady=5).pack(side=tk.LEFT, padx=5)
tk.Button(btn_frame, text="🔍 Basic Scrape", command=scrape_now,
         bg="#28a745", fg="white", padx=15, pady=5).pack(side=tk.LEFT, padx=5)
tk.Button(btn_frame, text="🎯 Enhanced Scrape", command=scrape_now_enhanced,
         bg="#007bff", fg="white", padx=15, pady=5).pack(side=tk.LEFT, padx=5)
tk.Button(btn_frame, text="📊 View Intelligence", command=view_intelligence,
         bg="#ffc107", padx=15, pady=5).pack(side=tk.LEFT, padx=5)
tk.Button(btn_frame, text="❌ Cancel", command=dialog.destroy,
         bg="#6c757d", fg="white", padx=15, pady=5).pack(side=tk.LEFT, padx=5)
"""

print("="*70)
print("DESKTOP APP INTELLIGENCE INTEGRATION GUIDE")
print("="*70)
print("\nThis file shows you how to integrate the intelligence system.")
print("\nMAIN CHANGES NEEDED:")
print("1. Add import for UnifiedSignalScoring at top of desktop_app.py")
print("2. Replace scrape_now() function with scrape_now_enhanced()")
print("3. Add view_intelligence() function")
print("4. Update button section to include new buttons")
print("\nOR: I can create a fully integrated desktop_app.py for you!")
print("="*70)
