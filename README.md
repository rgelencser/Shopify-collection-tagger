# Shopify Collection Tagger

Automatically syncs Shopify collection memberships as product tags.
Runs nightly via GitHub Actions.

## What it does

- Fetches all collections from the Shopify store
- For each product, adds tags matching the collections it belongs to
- Removes stale collection tags if a product is removed from a collection
- Preserves all non-collection tags (e.g. `new-arrival`, `metallic`)

## Files

- `sync_tags.py` — main sync script
- `auth.py` — one-time OAuth flow to generate a local access token
- `.github/workflows/sync_tags.yml` — GitHub Actions workflow (runs daily at 2am UTC)
- `.env` — local environment variables (never committed)
- `.shopify_token` — local access token (never committed)

## Setup

### Local

1. Install dependencies:
  pip install requests python-dotenv


2. Create a `.env` file:
   SHOPIFY_SHOP=your-store.myshopify.com
   SHOPIFY_CLIENT_ID=your_client_id
   SHOPIFY_CLIENT_SECRET=your_client_secret


3. Run the OAuth flow once to generate a token:
   python auth.py


4. Run the sync:
   python sync_tags.py


### GitHub Actions

Add the following secrets to your repository
(**Settings → Secrets and variables → Actions**):

| Secret | Value |
|---|---|
| `SHOPIFY_SHOP` | `your-store.myshopify.com` |
| `SHOPIFY_CLIENT_ID` | Your app's client ID |
| `SHOPIFY_CLIENT_SECRET` | Your app's client secret |
| `SHOPIFY_TOKEN` | Contents of your `.shopify_token` file |

The workflow runs automatically every night at 2am UTC.
It can also be triggered manually from the Actions tab.

## Security

- Never commit `.env` or `.shopify_token` — both are in `.gitignore`
- Rotate your client secret on dev.shopify.com if it is ever exposed
- All secrets are stored as encrypted GitHub Actions secrets

## Notes

- Collection titles are used as tag values exactly as they appear in Shopify
- If a tag name matches a collection title, it will be managed by this script
- The script handles pagination and works with any number of collections or products
