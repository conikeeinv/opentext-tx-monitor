import os
import sys
import json
import requests
from datetime import datetime

print("🔄 SCRIPT START: Python interpreter has successfully initialized fetch_signals.py")

# Ingest Environment Variables Safely
PROXYCURL_API_KEY = os.environ.get("PROXYCURL_API_KEY", "").strip()
SLACK_WEBHOOK_URL = os.environ.get("SLACK_WEBHOOK_URL", "").strip()

print(f"🔑 Environment Check -> Proxycurl Key Present: {bool(PROXYCURL_API_KEY)}, Slack Webhook Present: {bool(SLACK_WEBHOOK_URL)}")

TARGET_KEYWORDS = [
    "opentext", "document management", "ecm", "records management", 
    "information governance", "digital transformation", "cloud storage"
]

TARGET_ROLES = [
    "cio", "chief information officer", "city clerk", "county clerk", 
    "procurement director", "it director", "purchasing agent"
]

TARGET_PROFILES = [
    {"agency": "Texas Department of Transportation (TxDOT)", "linkedin_id": "texas-department-of-transportation"},
    {"agency": "Texas Health and Human Services (HHS)", "linkedin_id": "texas-health-and-human-services"},
    {"agency": "Texas Department of Insurance (TDI)", "linkedin_id": "texas-department-of-insurance"},
    {"agency": "Texas DIR", "linkedin_id": "texas-department-of-information-resources"},
    {"agency": "Texas Department of Public Safety (DPS)", "linkedin_id": "texas-department-of-public-safety"},
    {"agency": "Texas Department of Licensing and Regulation (TDLR)", "linkedin_id": "tdlr"},
    {"agency": "Texas Department of Agriculture (TDA)", "linkedin_id": "texas-department-of-agriculture"},
    {"agency": "Harris County", "linkedin_id": "harris-county"},
    {"agency": "Travis County", "linkedin_id": "travis-county"},
    {"agency": "Dallas County", "linkedin_id": "dallas-county-government"},
    {"agency": "Bexar County", "linkedin_id": "bexar-county-information-technology"},
    {"agency": "City of Houston", "linkedin_id": "city-of-houston"},
    {"agency": "City of Austin", "linkedin_id": "city-of-austin"},
    {"agency": "City of Frisco", "linkedin_id": "city-of-frisco-government"}
]

def fetch_texas_dir_contracts():
    print("📡 Step 1: Querying Texas DIR Portal...")
    url = "https://data.texas.gov/resource/vipt-h4ye.json?$limit=10&$order=last_updated DESC"
    try:
        response = requests.get(url, timeout=15)
        print(f"📡 DIR Portal Response Status: {response.status_code}")
        if response.status_code == 200:
            contracts = response.json()
            compiled_contracts = []
            for item in contracts:
                desc = item.get("rfo_description", "N/A")
                if any(kw in desc.lower() for kw in TARGET_KEYWORDS):
                    compiled_contracts.append({
                        "rfo_description": desc,
                        "vendor": item.get("primary_vendor_name", "N/A"),
                        "contract_id": item.get("contract_number", "N/A")
                    })
            return compiled_contracts
        return []
    except Exception as e:
        print(f"❌ DIR Portal Error: {str(e)}")
        return []

def fetch_linkedin_signals():
    print("🕵️‍♂️ Step 2: Querying Proxycurl Company Profiles...")
    if not PROXYCURL_API_KEY:
        print("ℹ️ Skipping LinkedIn Profile pass (No Key).")
        return []

    linkedin_insights = []
    headers = {"Authorization": f"Bearer {PROXYCURL_API_KEY}"}
    
    # Let's test just the first 2 accounts to see if it works without hitting a timeout block
    for target in TARGET_PROFILES[:2]:
        print(f"🔍 Testing Profile: {target['agency']}")
        url = f"https://nubela.co/proxycurl/api/v2/linkedin/company?url=https://www.linkedin.com/company/{target['linkedin_id']}"
        try:
            response = requests.get(url, headers=headers, timeout=15)
            print(f"   Status for {target['agency']}: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                linkedin_insights.append({
                    "agency": target["agency"],
                    "description": data.get("description", ""),
                    "recent_job_openings": data.get("jobs_description", "None listed"),
                    "follower_count": data.get("follower_count", "N/A")
                })
        except Exception as e:
            print(f"⚠️ Profile Error for {target['agency']}: {str(e)}")
            continue
            
    return linkedin_insights

def track_executive_shifts():
    print("👥 Step 3: Querying Proxycurl Employee Structures...")
    if not PROXYCURL_API_KEY:
        return []
        
    detected_shifts = []
    headers = {"Authorization": f"Bearer {PROXYCURL_API_KEY}"}
    # Notice the updated domain format matching the standard API endpoint patterns
    url = "https://nubela.co/proxycurl/api/v1/linkedin/company/employees/"
    
    # Test just the first profile to verify the API structural clearance
    for target in TARGET_PROFILES[:1]:
        print(f"🔍 Testing Employee Search for: {target['agency']}")
        params = {
            "url": f"https://www.linkedin.com/company/{target['linkedin_id']}",
            "role_search": "Clerk OR CIO OR Information Officer OR IT Director",
            "employment_status": "current"
        }
        try:
            response = requests.get(url, params=params, headers=headers, timeout=15)
            print(f"   Employee Search Status: {response.status_code}")
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
            print(f"⚠️ Employee Search Error for {target['agency']}: {e}")
            
    return detected_shifts

def run_pipeline():
    print("🚀 Execution starting...")
    dir_data = fetch_texas_dir_contracts()
    li_data = fetch_linkedin_signals()
    shifts_data = track_executive_shifts()
    
    payload = {
        "execution_date": datetime.now().strftime("%A, %B %d, %Y"),
        "texas_dir_active_contracts": dir_data,
        "linkedin_account_intelligence": li_data,
        "executive_role_shifts": shifts_data
    }
    
    print("\n--- BEGIN MARKET PAYLOAD ---")
    print(json.dumps(payload, indent=2))
    print("--- END MARKET PAYLOAD ---\n")

if __name__ == "__main__":
    run_pipeline()
