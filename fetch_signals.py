import os
import sys
import json
import requests
from datetime import datetime

# Ingest Environment Variables Safely
PROXYCURL_API_KEY = os.environ.get("PROXYCURL_API_KEY", "").strip()
SLACK_WEBHOOK_URL = os.environ.get("SLACK_WEBHOOK_URL", "").strip()

# Target Texas Agency Tickers / Profiles to Watch
TARGET_PROFILES = [
    {"agency": "Texas Department of Transportation (TxDOT)", "linkedin_id": "texas-department-of-transportation"},
    {"agency": "Texas Health and Human Services (HHS)", "linkedin_id": "texas-health-and-human-services"},
    {"agency": "Texas Department of Insurance (TDI)", "linkedin_id": "texas-department-of-insurance"},
    {"agency": "Texas DIR", "linkedin_id": "texas-department-of-information-resources"}
]

def fetch_texas_dir_contracts():
    """Queries Texas Open Data Portal (Socrata API) for live Cooperative Technology Contracts"""
    print("📡 Fetching live Texas DIR Cooperative Contracts...")
    # Dataset ID vipt-h4ye tracks live active DIR tech agreements
    url = "https://data.texas.gov/resource/vipt-h4ye.json?$limit=5&$order=last_updated DESC"
    
    try:
        response = requests.get(url, timeout=15)
        if response.status_code == 200:
            contracts = response.json()
            compiled_contracts = []
            for item in contracts:
                compiled_contracts.append({
                    "rfo_description": item.get("rfo_description", "N/A"),
                    "vendor": item.get("primary_vendor_name", "N/A"),
                    "contract_id": item.get("contract_number", "N/A")
                })
            return compiled_contracts
        print(f"⚠️ DIR Portal responded with status code: {response.status_code}")
        return []
    except Exception as e:
        print(f"❌ Failed to fetch DIR open dataset: {str(e)}")
        return []

def fetch_linkedin_signals():
    """Queries Enrichment API for target executive insights and keyword activities"""
    if not PROXYCURL_API_KEY:
        print("ℹ️ PROXYCURL_API_KEY missing. Skipping LinkedIn structural scraping pass.")
        return []

    print(f"🕵️‍♂️ Scanning {len(TARGET_PROFILES)} high-value Texas public sector accounts...")
    linkedin_insights = []
    
    headers = {"Authorization": f"Bearer {PROXYCURL_API_KEY}"}
    
    for target in TARGET_PROFILES:
        # Proxycurl company profile endpoint extracts employee counts, job postings, and structural pivots
        url = f"https://nubela.co/proxycurl/api/v2/linkedin/company?url=https://www.linkedin.com/company/{target['linkedin_id']}"
        try:
            response = requests.get(url, headers=headers, timeout=15)
            if response.status_code == 200:
                data = response.json()
                linkedin_insights.append({
                    "agency": target["agency"],
                    "description": data.get("description", ""),
                    "recent_job_openings": data.get("jobs_description", "None listed"),
                    "company_size_growth": data.get("follower_count", "N/A")
                })
        except Exception as e:
            print(f"⚠️ Could not pull LinkedIn analytics for {target['agency']}: {str(e)}")
            continue
            
    return linkedin_insights

def run_pipeline():
    """Aggregates payloads to output clean schema context to stdout for Claude Routines"""
    print(f"🚀 Initializing OpenText Public Sector Pipeline Engine: {datetime.now().strftime('%Y-%m-%d')}")
    
    dir_data = fetch_texas_dir_contracts()
    li_data = fetch_linkedin_signals()
    
    payload = {
        "execution_date": datetime.now().strftime("%A, %B %d, %Y"),
        "texas_dir_active_contracts": dir_data,
        "linkedin_account_intelligence": li_data
    }
    
    # We output a formatted JSON block to the terminal log. 
    # Claude Routines catch this stdout output block instantly to process reasoning.
    print("\n--- BEGIN MARKET PAYLOAD ---")
    print(json.dumps(payload, indent=2))
    print("--- END MARKET PAYLOAD ---\n")
    
    # Optional: If you want to bypass Claude Routines interface and log directly via webhook
    if SLACK_WEBHOOK_URL and not os.environ.get("RUNNING_IN_CLAUDE"):
        try:
            requests.post(SLACK_WEBHOOK_URL, json={"text": f"✅ Market Intelligence extraction complete. Captured {len(dir_data)} DIR lines and {len(li_data)} LinkedIn tracks."})
        except Exception:
            pass

if __name__ == "__main__":
    run_pipeline()
