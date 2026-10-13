import json
import httpx

data = json.load(open("token.json", encoding="utf-8"))
token = data["access_token"]
base_url = data["abap_base_url"]
url = f"{base_url}/sap/opu/odata/sap/ZOD_SB_PRODUCT/Products?$format=json"

# Test 1: Exactly 'Bearer <token>'
r1 = httpx.get(url, headers={"Authorization": f"Bearer {token}"})
print(f"1. Valid 'Bearer <token>' -> Status: {r1.status_code}")

# Test 2: Double Bearer 'Bearer Bearer <token>'
r2 = httpx.get(url, headers={"Authorization": f"Bearer Bearer {token}"})
print(f"2. Double 'Bearer Bearer <token>' -> Status: {r2.status_code}, Title: {'Anmeldung fehlgeschlagen' if 'Anmeldung fehlgeschlagen' in r2.text else 'Other'}")

# Test 3: Raw token without 'Bearer ' -> 'Authorization: <token>'
r3 = httpx.get(url, headers={"Authorization": token})
print(f"3. Raw '<token>' without Bearer -> Status: {r3.status_code}, Title: {'Anmeldung fehlgeschlagen' if 'Anmeldung fehlgeschlagen' in r3.text else 'Other'}")

# Test 4: Basic Auth (e.g. if credentials defaulted to basic)
r4 = httpx.get(url, auth=("wrong_user", "wrong_pass"))
print(f"4. Invalid Basic Auth -> Status: {r4.status_code}, Title: {'Anmeldung fehlgeschlagen' if 'Anmeldung fehlgeschlagen' in r4.text else 'Other'}")
