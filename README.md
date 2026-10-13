# SAP BTP ABAP Cloud — Token Mint & OData Tool

A lightweight, cross-platform Python CLI utility to authenticate against **SAP BTP ABAP Cloud (XSUAA OAuth 2.0)**, generate Bearer tokens, automatically copy credentials to your clipboard, and test OData V2 / V4 CRUD operations.

---

## Features

- 🔑 **OAuth 2.0 Bearer Token Minting**: Requests access tokens directly from SAP XSUAA using the Password Grant flow.
- 📋 **Cross-Platform Clipboard Copy**: Automatically copies `Bearer <token>` to your clipboard on **Windows** (`clip`), **macOS** (`pbcopy`), and **Linux** (`wl-copy` / `xclip`).
- 📡 **Live System Verification**: Automatically probes the ABAP Catalog service (`/sap/opu/odata/IWFND/CATALOGSERVICE;v=2`) to verify network and credentials.
- 💾 **Local Token Caching**: Saves token info to `token.json` for easy reuse across tools, Postman, FastAPI apps, or AI / MCP connectors.
- 🛠️ **OData V4 CRUD Example**: Complete script (`test_crud.py`) demonstrating CSRF token fetching, entity creation (POST), reading (GET), updating (PATCH), and deletion (DELETE).
- 🔒 **Security First**: Real credentials (`service_key.json`, `token.json`, `.env`) are pre-configured in `.gitignore`.

---

## Project Structure

```text
├── get_sap_token.py          # Main CLI script to authenticate and copy Bearer token
├── test_crud.py              # Ready-to-run OData V4 CRUD example (with CSRF handling)
├── service_key.example.json  # Template showing the required BTP Service Key JSON structure
├── requirements.txt          # Python dependencies (httpx, fastapi, uvicorn)
├── .gitignore                # Protects your sensitive service keys and tokens
└── README.md                 # Documentation
```

---

## Prerequisites

1. **Python 3.10+** installed.
2. An active **SAP BTP ABAP Environment** (Trial or Enterprise / Steampunk).
3. A **Service Key** downloaded from your SAP BTP Cockpit.

---

## Setup & Installation

### 1. Clone the repository
```bash
git clone https://github.com/<your-username>/sap-btp-token-tool.git
cd sap-btp-token-tool
```

### 2. Create and activate a virtual environment

**On Windows (PowerShell):**
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

**On macOS / Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

---

## How to Get Your SAP BTP Service Key

1. Log in to the [SAP BTP Cockpit](https://cockpit.hanatrial.ondemand.com/).
2. Navigate to your **Subaccount** → **Instances and Subscriptions** → **Instances**.
3. Locate your **ABAP Trial / ABAP System** instance.
4. Click the **`...`** (Actions) button next to the instance → **Service Keys** → **Create Service Key**.
5. Give it a name, click **Create**, then click **View** / **Download**.
6. Save the downloaded file as **`service_key.json`** in the root directory of this project.

*(See `service_key.example.json` for the expected schema).*

---

## Usage

### 1. Minting a Bearer Token

Run the script:

```bash
python get_sap_token.py
```

When prompted:
1. Enter your **SAP BTP Username or Email** (e.g., your Universal ID email).
2. Enter your **SAP BTP Password** *(input is masked for security)*.

#### What happens:
1. Authenticates against your SAP XSUAA tenant (`/oauth/token`).
2. Copies `Bearer <token>` directly to your operating system's clipboard.
3. Saves token metadata to `token.json` (valid for ~12 hours).
4. Verifies live connection to your ABAP instance by fetching sample published services.

#### Optional CLI arguments:
```bash
# Pass custom service key path or arguments:
python get_sap_token.py --key /path/to/my_key.json --user my_email@example.com
```

---

### 2. Testing OData CRUD Operations

Once your token is generated, run `test_crud.py` to test live OData V4 operations:

```bash
python test_crud.py
```

This script:
1. Reads `token.json` for Bearer credentials.
2. Automatically performs an `x-csrf-token: fetch` request.
3. **READ (GET)**: Lists all existing records.
4. **CREATE (POST)**: Creates a new sample record.
5. **UPDATE (PATCH)**: Updates the record status.
6. **DELETE (DELETE)**: Cleans up the test record.

---

### 3. Using in Connectors, Postman, or MCP Nodes

- **Postman / REST Clients**:
  - Add Header: `Authorization`
  - Value: Paste from clipboard (`Bearer eyJ...`)
- **MCP / AI Agent Connectors (e.g. SAP OData Multi-URL MCP)**:
  - Auth Method: `Authorization header / Bearer`
  - Base URL: Your system URL (from `token.json` or `service_key.json`)
  - Token Field: Paste from clipboard (`Bearer eyJ...` or raw `access_token` from `token.json`).

---

## Security

> [!IMPORTANT]
> **Never commit your actual credentials!**  
> `service_key.json` contains your client secret, and `token.json` contains active JWT access tokens. Both files are listed in `.gitignore` by default. Always verify git status before pushing.

---

## License

MIT License. Free to use, modify, and distribute.
