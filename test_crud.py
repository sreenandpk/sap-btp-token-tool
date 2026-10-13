"""
Example: Perform CRUD operations on SAP BTP ABAP Cloud OData V4 services using Python.
Requires: Run `python get_sap_token.py` first to generate `token.json`.
"""

import json
import sys
from pathlib import Path
import httpx

# Ensure proper stdout encoding on Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

TOKEN_FILE = Path(__file__).parent / "token.json"

if not TOKEN_FILE.exists():
    print("[!] Error: token.json not found! Please run `python get_sap_token.py` first.")
    sys.exit(1)

with open(TOKEN_FILE, "r", encoding="utf-8") as f:
    token_data = json.load(f)

access_token = token_data["access_token"]
base_url = token_data["abap_base_url"]

# Example Customer Service URL (OData V4)
service_url = f"{base_url}/sap/opu/odata4/sap/zui_cust_demo_o4/srvd/sap/zui_cust_demo/0001/"
entity_set = "ZI_CUST_DEMO"


def main():
    print(f"\n[*] Connecting to SAP OData V4 Service:")
    print(f"    {service_url}{entity_set}\n")

    with httpx.Client(timeout=20.0) as client:
        # 1. Fetch CSRF token (required for POST, PATCH, DELETE)
        auth_headers = {"Authorization": f"Bearer {access_token}"}
        csrf_resp = client.get(
            service_url,
            headers={**auth_headers, "x-csrf-token": "fetch"}
        )
        csrf_token = csrf_resp.headers.get("x-csrf-token")
        cookies = csrf_resp.cookies
        print(f"[+] CSRF Token retrieved: {csrf_token}")

        mutation_headers = {
            **auth_headers,
            "x-csrf-token": csrf_token,
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

        # 2. READ (GET all customers)
        print("\n--- 1. READ (GET) ---")
        get_resp = client.get(f"{service_url}{entity_set}", headers=auth_headers)
        if get_resp.status_code == 200:
            customers = get_resp.json().get("value", [])
            print(f"Found {len(customers)} customers:")
            for c in customers:
                print(f"  * ID: {c.get('CustomerId')} | Name: {c.get('CustomerName')} | Status: {c.get('Status')} | Email: {c.get('Email')}")
        else:
            print(f"GET failed: HTTP {get_resp.status_code} - {get_resp.text}")

        # 3. CREATE (POST a new customer)
        test_id = "C999"
        print(f"\n--- 2. CREATE (POST customer '{test_id}') ---")
        payload = {
            "CustomerId": test_id,
            "CustomerName": "Demo Partner Corp",
            "Email": "demo@partner.com",
            "Status": "Pending"
        }
        post_resp = client.post(
            f"{service_url}{entity_set}",
            json=payload,
            headers=mutation_headers,
            cookies=cookies
        )
        print(f"POST Status: HTTP {post_resp.status_code}")
        if post_resp.status_code in (200, 201):
            print(f"[OK] Successfully created customer '{test_id}'")
        else:
            print(f"POST note: {post_resp.text[:300]}")

        # 4. UPDATE (PATCH status to 'Active')
        print(f"\n--- 3. UPDATE (PATCH customer '{test_id}') ---")
        patch_resp = client.patch(
            f"{service_url}{entity_set}(CustomerId='{test_id}')",
            json={"Status": "Active"},
            headers=mutation_headers,
            cookies=cookies
        )
        print(f"PATCH Status: HTTP {patch_resp.status_code}")
        if patch_resp.status_code in (200, 204):
            print(f"[OK] Successfully updated customer '{test_id}' Status -> 'Active'")

        # 5. DELETE (Clean up test record)
        print(f"\n--- 4. DELETE (DELETE customer '{test_id}') ---")
        del_resp = client.delete(
            f"{service_url}{entity_set}(CustomerId='{test_id}')",
            headers=mutation_headers,
            cookies=cookies
        )
        print(f"DELETE Status: HTTP {del_resp.status_code}")
        if del_resp.status_code in (200, 204):
            print(f"[OK] Successfully deleted test customer '{test_id}'")


if __name__ == "__main__":
    main()
