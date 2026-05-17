import os
import sys
import json
import requests
from datetime import datetime

# Ingest Environment Variables Safely
PROXYCURL_API_KEY = os.environ.get("PROXYCURL_API_KEY", "").strip()
SLACK_WEBHOOK_URL = os.environ.get("SLACK_WEBHOOK_URL", "").strip()

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

def fetch_texas_smartbuy_signals():
    """Queries the ESBD public portal endpoint mockup for specific agency records"""
    print("🛒 Extracting TexasSmartBuy/ESBD active solicitation records...")
