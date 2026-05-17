import os
import sys
import json
import requests
from datetime import datetime

# Ingest Environment Variables Safely
PROXYCURL_API_KEY = os.environ.get("PROXYCURL_API_KEY", "").strip()
SLACK_WEBHOOK_URL = os.environ.get("SLACK_WEBHOOK_URL", "").strip()
GOVWIN_API_KEY = os.environ.get("GOVWIN_API_KEY", "").strip()

# Target Parameters for OpenText Relevance Filtering
TARGET_KEYWORDS = [
    "opentext", "document management", "ecm", "records management", 
    "information governance", "digital transformation", "cloud storage"
]

TARGET_ROLES = [
    "cio", "chief information officer", "city clerk", "county clerk", 
    "procurement director", "it director", "purchasing agent"
]

# High-Value State Agencies & Municipalities to Monitor
TARGET_PROFILES = [
    # State Agencies
    {"agency": "Texas Department of Transportation (TxDOT)", "linkedin_id": "texas-department-of-transportation"},
    {"agency": "Texas Health and Human Services (HHS)", "linkedin_id": "texas-health-and-human-services"},
    {"agency": "Texas Department of Insurance (TDI)", "linkedin_id": "texas-department-of-insurance"},
    {"agency": "Texas DIR", "linkedin_id": "texas-department-of-information-resources"},
    {"agency": "Texas Department of Public Safety (DPS)", "linkedin_id": "texas-department-of-public-safety"},
    {"agency": "Texas Department of Licensing and Regulation (TDLR)", "linkedin_id": "tdlr"},
    {"agency": "Texas Department of Agriculture (TDA)", "linkedin_id": "texas-department-of-agriculture"},
    # Major Counties & Cities
    {"agency": "Harris County", "linkedin_id": "harris-county"},
    {"agency": "Travis County", "linkedin_id": "travis-county"},
    {"agency": "Dallas County", "linkedin_id": "dallas-county-government"},
    {"agency": "Bexar County", "linkedin_id": "bexar-county-information-technology"},
    {"agency": "City of Houston", "linkedin_id": "city-of-houston"},
    {"agency": "City of Austin", "linkedin_id": "city-of-austin"},
    {"agency": "City of Frisco", "linkedin_id": "city-of-frisco-government"}
]

def fetch_texas_dir_contracts():
    """Queries Texas Open Data Portal (Socrata API) for live Cooperative Technology Contracts"""
    print("📡 Fetching live Texas DIR Cooperative Contracts...")
    url = "https://data.texas.gov/resource/vipt-h4ye.json?$limit=10&$order=last_updated DESC"
    
    try:
        response = requests.get(url, timeout=15)
        if response.status_code == 200:
            contracts = response.json()
            compiled_contracts = []
            for item in contracts:
                desc = item.get("rfo_description", "N/A")
                # Look for software/records management relevance keywords
                if any(kw in desc.lower() for kw in TARGET_KEYWORDS):
                    compiled_contracts.append({
                        "rfo_description": desc,
                        "vendor": item.get("primary_vendor_name", "N/A"),
                        "contract_id": item.get("contract_number", "N/A")
                    })
            return compiled_contracts
        print(f"⚠️ DIR Portal responded with status code: {response.status_code}")
        return []
    except Exception as e:
        print(f"❌ Failed to fetch DIR open dataset: {str(e)}")
        return []

def fetch_govwin_signals():
    """Queries GovWin IQ API for matching Texas local/state opportunities"""
    if not GOVWIN_API_KEY:
        print("ℹ️ GOVWIN_API_KEY missing. Skipping GovWin extraction pass.")
        return []

    print("💼 Scanning GovWin IQ for matching Texas procurement leads...")
    govwin_results = []
    headers = {"Authorization": f"Bearer {GOVWIN_API_KEY}", "Content-Type": "application/json"}
    url = "https://api.govwin.com/v1/opportunities/search"
    
    for keyword in TARGET_KEYWORDS:
        payload = {
            "searchString": keyword,
            "states": ["TX"],
            "stages": ["In Planning", "RFI", "RFP Out"]
        }
        try:
            response = requests.post(url, json=payload, headers=headers, timeout=15)
            if response.status_code == 200:
                opportunities = response.json().get("opportunities", [])
                for opp in opportunities:
                    govwin_results.append({
                        "source": "GovWin",
                        "title": opp.get("title"),
                        "agency": opp.get("agencyName"),
                        "value": opp.get("estimatedValue", "N/A"),
                        "link": f"https://iq.govwin.com/neo/opportunity/view/{opp.get('id')}"
                    })
        except Exception as e:
            print(f"⚠️ Error querying GovWin for '{keyword}': {e}")
            
    return govwin_results

def fetch_texas_smartbuy_signals():
    """Queries the ESBD public portal endpoint mockup for specific agency records"""
    print("🛒 Extracting TexasSmartBuy/ESBD active solicitation records...")
    smartbuy_results = []
    url = "https://www.txsmartbuy.com/esbd/search" 
    
    for keyword in TARGET_KEYWORDS:
        params = {"keyword": keyword, "status": "Active"}
        try:
            # Setting up a defensive timeout block
            response = requests.get(url, params=params, timeout=10)
            if response.status_code == 200:
                # Add processing logic here once data structures match target response signatures
                pass
        except Exception as e:
            print(f"⚠️ Error reading TexasSmartBuy parameters: {e}")
            
    return smartbuy_results

def fetch_linkedin_signals():
    """Queries Proxycurl Enrichment APIs for target executive insights and personnel shifts"""
    if not PROXYCURL_API_KEY:
        print("ℹ️ PROXYCURL_API_KEY missing. Skipping LinkedIn employee tracking.")
        return []

    print(f"🕵️‍♂️ Scanning {len(TARGET_PROFILES)} high-value Texas executive and structural profiles...")
    linkedin_insights = []
    headers = {"Authorization": f"Bearer {PROXYCURL_API_KEY}"}
    
    # 1. Main Company Updates & Insights Pass
    for target in TARGET_PROFILES:
        url = f"https://nubela.co/proxycurl/api/v2/linkedin/company?url=https://www.linkedin.com/company/{target['linkedin_id']}"
        try:
            response = requests.get(url, headers=headers, timeout=15)
            if response.status_code == 200:
                data = response.json()
                linkedin_insights.append({
                    "agency": target["agency"],
                    "description": data.get("description", ""),
                    "recent_job_openings": data.get("jobs_description", "None listed"),
                    "follower_count": data.get("follower_count", "N/A")
                })
        except Exception as e:
            print(f"⚠️ Could not pull LinkedIn analytics for {target['agency']}: {str(e)}")
            continue
            
    return linkedin_insights

def track_executive_shifts():
    """Queries Proxycurl company employee lookup endpoints specifically targeting internal role changes"""
    if not PROXYCURL_API_KEY:
        return []
        
    print("👥 Scanning target employee structures for critical organizational shifts (CIOs/Clerks)...")
    detected_shifts = []
    headers = {"Authorization": f"Bearer {PROXYCURL_API_KEY}"}
    url = "https://nubela.co/api/v1/linkedin/company/employees/"
    
    for target in TARGET_PROFILES:
        params = {
            "url": f"https://www.linkedin.com/company/{target['linkedin_id']}",
            "role_search": "Clerk OR CIO OR Information Officer OR IT Director",
            "employment_status": "current"
        }
        try:
            response = requests.get(url, params=params, headers=headers, timeout=15)
            if response.status_code == 200:
                employees = response.json().get("employees", [])
                for emp in employees:
                    title = emp.get("title", "").lower()
                    if any(role in title for role in TARGET_ROLES):
                        detected_shifts.append({
                            "entity": target["agency"],
                            "name": emp.get("profile_name", "Unknown Contact"),
                            "title": emp.get("title", "N/A"),
                            "profile_url": emp.get("linkedin_url", "")
                        })
        except Exception as e:
            print(f"⚠️ Error tracking personnel structure changes for {target['agency']}: {e}")
            
    return detected_shifts

def run_pipeline():
    """Aggregates all procurement and account data engines into an automated delivery payload"""
    print(f"🚀 Initializing OpenText Public Sector Pipeline Engine: {datetime.now().strftime('%Y-%m-%d')}")
    
    dir_data = fetch_texas_dir_contracts()
    govwin_data = fetch_govwin_signals()
    li_data = fetch_linkedin_signals()
    shifts_data = track_executive_shifts()
    
    payload = {
        "execution_date": datetime.now().strftime("%A, %B %d, %Y"),
        "texas_dir_active_contracts": dir_data,
        "govwin_opportunities": govwin_data,
        "linkedin_account_intelligence": li_data,
        "executive_role_shifts": shifts_data
    }
    
    # Format out structural logs for automated routing layers
    print("\n--- BEGIN MARKET PAYLOAD ---")
    print(json.dumps(payload, indent=2))
    print("--- END MARKET PAYLOAD ---\n")
    
    # Format a robust, readable message payload for your Slack channel alerts
    if SLACK_WEBHOOK_URL and not os.environ.get("RUNNING_IN_CLAUDE"):
        slack_summary = f"📊 *Texas Public Sector Intel Report - {payload['execution_date']}*\n"
        slack_summary += f"• *DIR Leads Matched:* {len(dir_data)}\n"
        slack_summary += f"• *GovWin Opportunities Found:* {len(govwin_data)}\n"
        slack_summary += f"• *Key Structural Role Shifts Captured:* {len(shifts_data)}\n\n"
        
        if shifts_data:
            slack_summary += "🔔 *Notable Executive Changes (CIOs/Clerks):*\n"
            for shift in shifts_data[:3]: # Send up to 3 major personnel signals to prevent overflow
                slack_summary += f" - [{shift['entity']}] *{shift['name']}* stepped into: `{shift['title']}`\n"
                
        try:
            requests.post(SLACK_WEBHOOK_URL, json={"text": slack_summary}, timeout=10)
            print("🚀 Successfully streamed comprehensive lead dashboard notification directly into Slack.")
        except Exception as e:
            print(f"❌ Failed to deliver webhook packet to Slack: {e}")

if __name__ == "__main__":
    run_pipeline()
