import argparse
import getpass
import json
import platform
import subprocess
import sys
from pathlib import Path

import httpx

# Ensure proper stdout encoding on Windows
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

DEFAULT_KEY_FILE = Path(__file__).parent / "service_key.json"


def load_service_key(key_path: Path) -> dict:
    if not key_path.exists():
        print(f"\n❌ Error: Service key file not found at: {key_path}")
        print("💡 Hint: Download your service key from SAP BTP Cockpit and save it as 'service_key.json',")
        print("   or copy 'service_key.example.json' and fill in your credentials.\n")
        sys.exit(1)
    try:
        with open(key_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as exc:
        print(f"❌ Error reading JSON file '{key_path}': {exc}")
        sys.exit(1)


def get_credentials(cli_user: str | None, cli_pass: str | None) -> tuple[str, str]:
    user = cli_user or input("Enter SAP BTP User (email / username): ").strip()
    password = cli_pass or getpass.getpass("Enter SAP BTP Password: ").strip()
    if not user or not password:
        print("❌ Username and password cannot be empty.")
        sys.exit(1)
    return user, password


def copy_to_clipboard(text: str):
    system = platform.system()
    try:
        if system == "Windows":
            subprocess.run(["clip"], input=text, text=True, check=True)
        elif system == "Darwin":  # macOS
            subprocess.run(["pbcopy"], input=text, text=True, check=True)
        else:  # Linux
            try:
                subprocess.run(["wl-copy"], input=text, text=True, check=True)
            except Exception:
                subprocess.run(["xclip", "-selection", "clipboard"], input=text, text=True, check=True)
        print("📋 Bearer token copied to your clipboard!")
    except Exception as e:
        print(f"⚠️ Note: Could not automatically copy to clipboard ({e}). You can copy the token from token.json.")


def main():
    parser = argparse.ArgumentParser(
        description="Authenticate to SAP BTP ABAP Cloud and generate OAuth 2.0 Bearer tokens."
    )
    parser.add_argument("--key", default=str(DEFAULT_KEY_FILE), help="Path to service_key.json (default: ./service_key.json)")
    parser.add_argument("--user", default=None, help="SAP BTP Username or Email")
    parser.add_argument("--password", default=None, help="SAP BTP Password")
    args = parser.parse_args()

    # 1. Load Service Key
    key_file = Path(args.key)
    print(f"\n📂 Reading service key from: {key_file}")
    key_data = load_service_key(key_file)

    uaa_section = key_data.get("uaa", {})
    uaa_url = uaa_section.get("url")
    client_id = uaa_section.get("clientid")
    client_secret = uaa_section.get("clientsecret")
    abap_base_url = key_data.get("url") or key_data.get("endpoints", {}).get("abap")

    if not (uaa_url and client_id and client_secret and abap_base_url):
        print("❌ Invalid service key: missing required fields (uaa.url, uaa.clientid, uaa.clientsecret, url).")
        sys.exit(1)

    # 2. Get User & Password
    sap_user, sap_password = get_credentials(args.user, args.password)

    # 3. Request OAuth Token from XSUAA
    token_url = f"{uaa_url}/oauth/token"
    print(f"\n🔑 Requesting OAuth Bearer token from: {token_url} ...")

    token_payload = {
        "grant_type": "password",
        "username": sap_user,
        "password": sap_password,
        "client_id": client_id,
        "client_secret": client_secret,
    }

    headers = {
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept": "application/json",
    }

    with httpx.Client(timeout=25.0) as client:
        try:
            token_resp = client.post(token_url, data=token_payload, headers=headers)
        except Exception as exc:
            print(f"❌ Failed to reach authentication server: {exc}")
            sys.exit(1)

        if token_resp.status_code != 200:
            print(f"\n❌ Authentication Failed (HTTP {token_resp.status_code}):")
            try:
                print(json.dumps(token_resp.json(), indent=2))
            except Exception:
                print(token_resp.text)
            print("\nPlease verify your SAP username and password.")
            sys.exit(1)

        token_data = token_resp.json()
        access_token = token_data.get("access_token")
        if not access_token:
            print("❌ No access_token found in server response.")
            sys.exit(1)

        token_type = token_data.get("token_type", "Bearer")
        expires_in = token_data.get("expires_in", 43200)
        bearer_header = f"Bearer {access_token}"

        print(f"\n✅ Authentication successful!")
        print(f"   - Token Type      : {token_type}")
        print(f"   - Valid Duration  : {expires_in} seconds (~{round(expires_in / 3600, 1)} hours)")
        print(f"   - Token Preview   : {access_token[:30]}...")

        # Copy to clipboard
        copy_to_clipboard(bearer_header)

        # Cache locally in token.json (ignored by git)
        token_info_path = Path(__file__).parent / "token.json"
        with open(token_info_path, "w", encoding="utf-8") as tf:
            json.dump({
                "access_token": access_token,
                "token_type": token_type,
                "expires_in": expires_in,
                "authorization_header": bearer_header,
                "abap_base_url": abap_base_url
            }, tf, indent=2)
        print(f"💾 Saved token details to: {token_info_path}")

        # 4. Verification: Test ABAP OData Catalog Service
        catalog_path = key_data.get("catalogs", {}).get("abap", {}).get("path", "/sap/opu/odata/IWFND/CATALOGSERVICE;v=2")
        odata_endpoint = f"{abap_base_url}{catalog_path}/ServiceCollection"
        odata_params = {
            "$top": "5",
            "$format": "json",
        }

        print(f"\n📡 Testing connection against ABAP Catalog Service...")
        print(f"   URL: {odata_endpoint}")

        abap_headers = {
            "Authorization": bearer_header,
            "Accept": "application/json",
        }

        try:
            odata_resp = client.get(odata_endpoint, params=odata_params, headers=abap_headers)
        except Exception as exc:
            print(f"⚠️ Could not reach ABAP endpoint: {exc}")
            return

        print(f"\n--- [ ABAP OData Response - HTTP {odata_resp.status_code} ] ---")
        if odata_resp.status_code == 200:
            print("✅ Successfully verified connection to SAP BTP ABAP System!\n")
            odata_json = odata_resp.json()
            results = odata_json.get("d", {}).get("results", [])

            if results:
                print(f"Sample Published Services ({len(results)} found):")
                for idx, svc in enumerate(results, 1):
                    svc_id = svc.get("ID", "N/A")
                    desc = svc.get("Description", "No description")
                    print(f"  {idx}. ID: {svc_id}")
                    print(f"     Description: {desc}")
                    print("-" * 50)
        else:
            print(f"⚠️ ABAP System returned HTTP {odata_resp.status_code}:")
            print(odata_resp.text[:400])


if __name__ == "__main__":
    main()
