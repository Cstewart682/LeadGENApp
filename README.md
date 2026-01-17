# Calgary Industrial Lead Generator

## Complete User Guide

A tool to help you find and manage leads for industrial and manufacturing companies in Calgary. This guide assumes you have never used command line tools before.

---

## Table of Contents

1. [What This Program Does](#what-this-program-does)
2. [What You Need Before Starting](#what-you-need-before-starting)
3. [Installation - Windows](#installation---windows)
4. [Installation - Mac](#installation---mac)
5. [Starting the Program](#starting-the-program)
6. [Using the Program](#using-the-program)
7. [Setting Up Jobber Integration](#setting-up-jobber-integration)
8. [Importing LinkedIn Contacts](#importing-linkedin-contacts)
9. [Tender Monitoring](#tender-monitoring)
10. [Email Outreach](#email-outreach)
11. [Troubleshooting](#troubleshooting)
12. [Closing the Program](#closing-the-program)

---

## What This Program Does

This program helps you:

- **Build a list of potential customers** - Add companies manually or import from LinkedIn/CSV files
- **Find contact information** - Automatically scrape emails and phone numbers from company websites
- **Detect buying signals** - Scan websites for signs a company might be ready to buy (hiring, expanding, posting RFPs)
- **Track your outreach** - Know who you've contacted and when to follow up
- **Monitor tenders** - Get alerts about new government/public contracts
- **Sync with Jobber** - Push your leads to your Jobber CRM

---

## What You Need Before Starting

### Required Software

1. **Python** (version 3.8 or higher) - This is what runs the program
2. **A web browser** (Chrome, Firefox, Edge, Safari) - This is where you'll use the program

### Check if Python is Already Installed

**On Windows:**
1. Press the `Windows key` on your keyboard
2. Type `cmd` and press Enter (this opens Command Prompt)
3. Type `python --version` and press Enter
4. If you see something like `Python 3.11.4`, you have Python installed
5. If you see an error message, you need to install Python

**On Mac:**
1. Press `Command + Space` to open Spotlight
2. Type `Terminal` and press Enter
3. Type `python3 --version` and press Enter
4. If you see something like `Python 3.11.4`, you have Python installed
5. If you see an error, you need to install Python

---

## Installation - Windows

### Step 1: Install Python (if not already installed)

1. Open your web browser and go to: **https://www.python.org/downloads/**
2. Click the big yellow button that says **"Download Python 3.x.x"**
3. Open the downloaded file (usually in your Downloads folder)
4. **IMPORTANT:** Check the box that says **"Add Python to PATH"** at the bottom of the installer
5. Click **"Install Now"**
6. Wait for installation to complete
7. Click **"Close"**

### Step 2: Download the Lead Generator Program

1. Save the `calgary_lead_gen` folder to a location you can easily find
   - Recommended: Your Desktop or Documents folder
   - Example path: `C:\Users\YourName\Desktop\calgary_lead_gen`

### Step 3: Open Command Prompt

1. Press the `Windows key` on your keyboard
2. Type `cmd`
3. Click on **"Command Prompt"** in the search results

You should see a black window with white text.

### Step 4: Navigate to the Program Folder

In the Command Prompt, you need to "go to" the folder where you saved the program.

Type the following command and press Enter:

```
cd Desktop\calgary_lead_gen
```

If you saved it somewhere else, adjust the path. For example:
- Documents folder: `cd Documents\calgary_lead_gen`
- Downloads folder: `cd Downloads\calgary_lead_gen`

**How to know you're in the right place:**
- The text before the cursor should now show the folder path
- Example: `C:\Users\YourName\Desktop\calgary_lead_gen>`

### Step 5: Install Required Components

Type the following command and press Enter:

```
pip install -r requirements.txt
```

Wait for it to finish. You'll see text scrolling by - this is normal. When it's done, you'll see a new line ready for input.

If you see any red "ERROR" messages, see the Troubleshooting section.

### Step 6: Start the Program

Type the following command and press Enter:

```
python app.py
```

You should see:
```
==================================================
Calgary Industrial Lead Generator
==================================================

Open: http://localhost:5000
Press Ctrl+C to stop
```

### Step 7: Open the Program in Your Browser

1. Open your web browser (Chrome, Firefox, Edge)
2. In the address bar at the top, type: **localhost:5000**
3. Press Enter

You should now see the Lead Generator interface!

---

## Installation - Mac

### Step 1: Install Python (if not already installed)

Mac usually comes with Python, but you may need to install a newer version.

1. Open your web browser and go to: **https://www.python.org/downloads/**
2. Click the big yellow button that says **"Download Python 3.x.x"**
3. Open the downloaded file
4. Double-click the package file to run the installer
5. Follow the installation prompts
6. Click **"Close"** when finished

### Step 2: Download the Lead Generator Program

1. Save the `calgary_lead_gen` folder to a location you can easily find
   - Recommended: Your Desktop or Documents folder

### Step 3: Open Terminal

1. Press `Command + Space` to open Spotlight
2. Type `Terminal`
3. Press Enter

You should see a window with text.

### Step 4: Navigate to the Program Folder

Type the following command and press Enter:

```
cd ~/Desktop/calgary_lead_gen
```

If you saved it somewhere else:
- Documents folder: `cd ~/Documents/calgary_lead_gen`
- Downloads folder: `cd ~/Downloads/calgary_lead_gen`

### Step 5: Install Required Components

Type the following command and press Enter:

```
pip3 install -r requirements.txt
```

Wait for it to finish.

### Step 6: Start the Program

Type the following command and press Enter:

```
python3 app.py
```

### Step 7: Open the Program in Your Browser

1. Open your web browser (Safari, Chrome, Firefox)
2. In the address bar, type: **localhost:5000**
3. Press Enter

---

## Starting the Program

**Every time you want to use the program, follow these steps:**

### Windows:
1. Open Command Prompt (press Windows key, type `cmd`, press Enter)
2. Navigate to the folder: `cd Desktop\calgary_lead_gen` (or wherever you saved it)
3. Start the program: `python app.py`
4. Open browser and go to: `localhost:5000`

### Mac:
1. Open Terminal (Command + Space, type "Terminal", press Enter)
2. Navigate to the folder: `cd ~/Desktop/calgary_lead_gen`
3. Start the program: `python3 app.py`
4. Open browser and go to: `localhost:5000`

### Quick Tip for Windows Users - Create a Double-Click Shortcut:

You can create a shortcut to start the program faster:

1. Open Notepad (press Windows key, type "notepad", press Enter)
2. Paste the following text:
   ```
   cd /d C:\Users\YourName\Desktop\calgary_lead_gen
   python app.py
   pause
   ```
3. Replace `YourName` with your actual Windows username
4. Click **File** → **Save As**
5. Change "Save as type" to **All Files**
6. Name the file: `StartLeadGenerator.bat`
7. Save it to your Desktop
8. Double-click this file whenever you want to start the program

---

## Using the Program

### The Main Screen

When you open the program, you'll see:

- **Stats bar** at the top showing counts for leads, emails, follow-ups, etc.
- **Tabs** to switch between different features:
  - 📋 **Leads** - View and manage your list of companies
  - ➕ **Add** - Add new companies manually
  - 📁 **Import** - Import from LinkedIn or CSV files
  - 📧 **Outreach** - Track emails and generate drafts
  - 📢 **Tenders** - Monitor government contracts
  - 🔄 **Jobber** - Sync with Jobber CRM
  - ⚙️ **Settings** - Configure the program

### Adding a Company Manually

1. Click the **➕ Add** tab
2. Fill in the company information:
   - **Company Name** (required)
   - **Website** (recommended - enables auto-scraping)
   - **Industry** (helps with targeting)
   - **Contact Name/Title** (if known)
3. Click **"Add"** to save, or **"Add & Scrape"** to save and automatically find emails/phone numbers from their website

### Viewing and Editing Leads

1. Click the **📋 Leads** tab
2. Use the search box to find specific companies
3. Use filters to show only certain statuses or outreach stages
4. Click **"Edit"** on any lead to:
   - Update contact information
   - Add notes
   - Change status
   - Detect buying signals (if website is entered)
   - Delete the lead

### Understanding Buying Signals

The **Signal** score (0-100) indicates how likely a company is to be actively purchasing:

- **50+** (green) - High activity signals found (RFPs, expansion, new equipment)
- **20-49** (yellow) - Some activity (hiring, projects)
- **0-19** (gray) - No signals detected

To detect signals for a company:
1. Make sure the company has a website entered
2. Click **Edit** on the lead
3. Click **"🎯 Signals"** button

### Exporting Your Leads

1. Click the **📋 Leads** tab
2. Click the **📤 Export** button (top right of the lead list)
3. A CSV file will download that you can open in Excel

---

## Setting Up Jobber Integration

To sync leads with your Jobber account:

### Step 1: Get Jobber API Credentials

1. Go to **https://developer.getjobber.com/**
2. Sign up for a developer account (free)
3. Click **"Create New App"**
4. Fill in:
   - App Name: "Lead Generator" (or anything you want)
   - Redirect URI: `http://localhost:5000/oauth/jobber/callback`
5. Save and note your **Client ID** and **Client Secret**

### Step 2: Enter Credentials in the Program

1. Click the **⚙️ Settings** tab
2. Scroll to **"Jobber API"** section
3. Enter your **Client ID** and **Client Secret**
4. Click **"💾 Save"**

### Step 3: Sync Leads

1. Click the **🔄 Jobber** tab
2. Click **"Sync All Unsynced"** to push all leads to Jobber
3. Or, from the Leads tab:
   - Check the boxes next to leads you want to sync
   - Click **"🔄 Sync to Jobber"**

---

## Importing LinkedIn Contacts

### Step 1: Export Your LinkedIn Connections

1. Log into LinkedIn in your web browser
2. Click your **profile picture** (top right corner)
3. Click **"Settings & Privacy"**
4. Click **"Data privacy"** in the left menu
5. Click **"Get a copy of your data"**
6. Select **"Connections"** only (this makes the download faster)
7. Click **"Request archive"**
8. Wait for email from LinkedIn (can take 10 minutes to 24 hours)
9. Click the download link in the email
10. Unzip/extract the downloaded file
11. Find the file called **Connections.csv**

### Step 2: Import into Lead Generator

1. Click the **📁 Import** tab
2. In the "Import from LinkedIn" section, click the dashed box that says "Drop LinkedIn CSV here"
3. Select your **Connections.csv** file
4. Check/uncheck filtering options:
   - **"Only target titles"** - Only imports managers, directors, purchasing roles, etc.
   - This helps filter out irrelevant contacts
5. Click **"Import"**

Your LinkedIn connections will now appear in the Leads tab!

---

## Tender Monitoring

The program can check for government and public sector contract opportunities.

### Checking for Tenders

1. Click the **📢 Tenders** tab
2. Click **"🔄 Check"** to scan for new tenders
3. New (unread) tenders appear with a blue left border
4. Click on a tender to mark it as read
5. Click the tender title to open the full details on the source website

### Configuring Tender Keywords

1. Click the **⚙️ Settings** tab
2. Find **"Tender Keywords"** section
3. Enter keywords that match your services (separated by commas)
   - Example: `maintenance, hvac, plumbing, electrical, janitorial`
4. Enter locations to monitor
   - Example: `Alberta, Calgary, Edmonton`
5. Click **"💾 Save"**

Tenders matching more of your keywords will have higher relevance scores.

---

## Email Outreach

### Setting Up Your Email Templates

1. Click the **⚙️ Settings** tab
2. Fill in **"Your Info"** section:
   - Your Name
   - Your Company
   - Your Phone
   - Your Email
3. Click **"💾 Save"**

This information will be automatically inserted into email templates.

### Generating an Email Draft

1. Click the **📧 Outreach** tab
2. Under **"Draft Email"**:
   - Select a lead from the dropdown (only leads with email addresses appear)
   - Choose a template:
     - **First Touch** - Initial outreach email
     - **Follow-up 1** - Gentle follow-up
     - **Follow-up 2** - Final attempt
3. Click **"Generate"**
4. Review the email preview below
5. Click **"📋 Copy"** to copy the email to your clipboard
6. Open your email program (Outlook, Gmail, etc.)
7. Create a new email, paste the content, and send
8. Come back to Lead Generator and click **"✅ Mark Sent"** to update the lead status

### Tracking Follow-ups

When you mark an email as sent, the system automatically schedules a follow-up in 3 days. You'll see:

- **Due Follow-ups** count in the stats bar at the top
- List of due follow-ups in the Outreach tab
- Quick "Draft" button to create follow-up emails for each

---

## Troubleshooting

### "python is not recognized" (Windows)

**Cause:** Python wasn't added to PATH during installation.

**Fix:**
1. Go to Windows Settings → Apps → Installed Apps
2. Find Python and click Uninstall
3. Download Python again from https://www.python.org/downloads/
4. Run the installer
5. **CHECK the box "Add Python to PATH"** (this is critical!)
6. Complete installation
7. Close and reopen Command Prompt
8. Try again

### "pip is not recognized"

**Fix (Windows):**
```
python -m pip install -r requirements.txt
```

**Fix (Mac):**
```
python3 -m pip install -r requirements.txt
```

### "No module named flask" or similar errors

**Cause:** Required packages weren't installed properly.

**Fix:** Run the install command again:

Windows:
```
pip install -r requirements.txt
```

Mac:
```
pip3 install -r requirements.txt
```

### Program starts but browser shows "can't connect" or "refused to connect"

**Possible causes and fixes:**

1. **Wrong address** - Make sure you typed exactly: `localhost:5000` (no http://, no www)

2. **Program crashed** - Look at the Command Prompt/Terminal window for red error messages

3. **Port already in use** - Another program is using port 5000. Fix:
   - Open app.py in a text editor (Notepad)
   - Scroll to the very bottom
   - Find: `app.run(debug=True, port=5000)`
   - Change to: `app.run(debug=True, port=5001)`
   - Save the file
   - Restart the program
   - Use `localhost:5001` in your browser instead

### Tabs not working / nothing happens when clicking

1. Try refreshing the page (press F5 or Ctrl+R)
2. Try a different web browser
3. Clear your browser cache:
   - Chrome: Ctrl+Shift+Delete → Clear data
   - Firefox: Ctrl+Shift+Delete → Clear Now
   - Edge: Ctrl+Shift+Delete → Clear now

### Can't scrape websites / No emails found

**This is often normal.** Not all websites can be scraped because:
- The website doesn't display email addresses publicly
- The website blocks automated access
- The email is in an image (not text)

**Solution:** For these companies, you'll need to find contact info manually through:
- Their website's Contact page
- Phone call to reception
- LinkedIn

### Program window closes immediately on Windows

**Cause:** There's an error but the window closes before you can read it.

**Fix:** 
1. Don't double-click the .bat file
2. Instead, open Command Prompt manually:
   - Press Windows key
   - Type `cmd`
   - Press Enter
3. Navigate to the folder: `cd Desktop\calgary_lead_gen`
4. Run: `python app.py`
5. Now you can see any error messages

### "Address already in use" error

**Cause:** The program is already running in another window, or didn't shut down properly.

**Fix (Windows):**
1. Close all Command Prompt windows
2. Press Ctrl+Alt+Delete → Task Manager
3. Look for "Python" in the list
4. Click it and click "End Task"
5. Try starting the program again

**Fix (Mac):**
1. Close all Terminal windows
2. Open a new Terminal
3. Type: `pkill python`
4. Try starting the program again

---

## Closing the Program

### To stop the program:

1. Go to the Command Prompt/Terminal window (the black window where you typed `python app.py`)
2. Press **Ctrl + C** on your keyboard (hold Ctrl, then press C)
3. You might need to press it twice
4. The program will stop and you'll see a new prompt line
5. You can now close the Command Prompt/Terminal window
6. Close the browser tab

### Your Data is Safe

All your leads and settings are automatically saved to files in the `data` folder inside `calgary_lead_gen`:

- `leads.json` - Your lead database
- `config.json` - Your settings  
- `tenders.json` - Saved tender information

These files stay on your computer even when you close the program. The next time you start the program, all your data will still be there.

### Backing Up Your Data

To back up your leads:
1. Navigate to the `calgary_lead_gen` folder
2. Open the `data` folder
3. Copy the `leads.json` file to a safe location (USB drive, cloud storage, etc.)

---

## File Structure

Here's what each file in the program does:

```
calgary_lead_gen/
│
├── app.py                  # Main program - run this to start
├── requirements.txt        # List of required packages
├── config_template.py      # Example API configuration
├── README.md              # This instruction manual
│
├── jobber_integration.py  # Advanced Jobber sync features
├── tender_monitoring.py   # Advanced tender monitoring
├── linkedin_parser.py     # LinkedIn import utilities  
├── outreach_tracking.py   # Email template system
├── email_verification.py  # Email validation tools
├── api_integrations.py    # Third-party API connections
│
└── data/                  # Created automatically when you run the program
    ├── leads.json         # Your leads (companies and contacts)
    ├── config.json        # Your settings
    └── tenders.json       # Cached tender information
```

---

## Legal and Compliance Notes

### CASL Compliance (Canadian Anti-Spam Legislation)

When using this tool for email outreach, you must comply with Canadian law:

✅ **You CAN:**
- Send one-to-one business emails to publicly available addresses
- Email people you have met or have an existing relationship with
- Email someone who was referred to you

❌ **You CANNOT:**
- Add scraped emails to bulk marketing lists
- Send automated mass emails without consent
- Use misleading subject lines

### Required in Every Email:
- Clear identification of who you are and your company
- Your physical mailing address
- An easy way to unsubscribe or opt out

### Best Practices:
- Personalize each email
- Reference something specific about their company
- Keep it short and focused
- Follow up no more than 2-3 times

---

## Getting More Help

If you're stuck:

1. Read through the Troubleshooting section above
2. Make sure you have the latest version of all files
3. Try restarting the program
4. Try a different web browser
5. Restart your computer and try again

---

*Calgary Industrial Lead Generator - Version 1.0*
*Last Updated: January 2025*
