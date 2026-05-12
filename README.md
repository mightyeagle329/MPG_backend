# Marketing Package Generator - Backend (V1 Milestone 1)

Canva integration proof: generate a flyer PDF for a single listing from a Brand Template.

## Setup

1. Create a virtual environment and install dependencies:

```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2. Copy `.env.example` to `.env` and fill in your Canva credentials:

```bash
cp .env.example .env
```

Required values:
- `CANVA_CLIENT_ID` - from canva.com/developers
- `CANVA_CLIENT_SECRET` - from canva.com/developers
- `CANVA_REDIRECT_URI` - must match what is registered in the Canva integration (default: `http://127.0.0.1:7000/oauth/callback`)
- `CANVA_TEMPLATE_5K` and `CANVA_TEMPLATE_10K` - Brand Template IDs for each incentive tier

3. In the Canva integration settings, register the redirect URI exactly as `http://127.0.0.1:7000/oauth/callback`.

4. Make sure the Brand Templates have a **data field named `address`** for the property address text.

## Run

```bash
uvicorn app.main:app --reload --host 127.0.0.1 --port 7000
```

## Usage

1. Open http://127.0.0.1:7000/ in a browser.
2. Click **Connect to Canva** to authorize. After approval, the token is saved in `.canva_token.json`.
3. Generate a flyer:

```bash
curl -X POST http://127.0.0.1:7000/flyer \
  -H "Content-Type: application/json" \
  -d '{"address": "123 Main St, Atlanta, GA", "tier": "5k"}'
```

Response includes the generated `design_id` and a list of `pdf_urls` to download the flyer.

## Structure

```
backend/
├── app/
│   ├── main.py              # FastAPI app, OAuth + flyer endpoints
│   ├── config.py            # Settings from .env
│   ├── canva/
│   │   ├── oauth.py         # OAuth flow + token storage
│   │   └── client.py        # Autofill + Export API client
│   └── flyer/
│       └── service.py       # Flyer generation orchestration
├── requirements.txt
├── .env.example
└── .gitignore
```

## Notes

- Tokens are stored in `.canva_token.json` for development. For production we will move this to a secure store.
- The Canva client is wrapped behind a small interface, so we can swap to an HTML-to-PDF fallback later if needed without changing the rest of the app.
