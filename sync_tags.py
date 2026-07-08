import requests
import json
import os

SHOP = os.environ["SHOPIFY_SHOP"]
CLIENT_ID = os.environ["SHOPIFY_CLIENT_ID"]
CLIENT_SECRET = os.environ["SHOPIFY_CLIENT_SECRET"]
API_VERSION = "2024-01"

# --- Load or obtain access token ---
import os
TOKEN_FILE = ".shopify_token"

def get_token():
    if os.path.exists(TOKEN_FILE):
        with open(TOKEN_FILE) as f:
            return f.read().strip()
    raise Exception("No token found. Run auth.py first.")

def graphql(query, variables=None, token=None):
    url = f"https://{SHOP}/admin/api/{API_VERSION}/graphql.json"
    headers = {"X-Shopify-Access-Token": token, "Content-Type": "application/json"}
    r = requests.post(url, json={"query": query, "variables": variables or {}}, headers=headers)
    r.raise_for_status()
    return r.json()

GET_COLLECTIONS = """
query($cursor: String) {
  collections(first: 50, after: $cursor) {
    pageInfo { hasNextPage endCursor }
    edges {
      node { id title }
    }
  }
}
"""

GET_COLLECTION_PRODUCTS = """
query($id: ID!, $cursor: String) {
  collection(id: $id) {
    products(first: 50, after: $cursor) {
      pageInfo { hasNextPage endCursor }
      edges {
        node { id tags }
      }
    }
  }
}
"""

UPDATE_TAGS = """
mutation($id: ID!, $tags: [String!]!) {
  productUpdate(input: {id: $id, tags: $tags}) {
    product { id tags }
    userErrors { field message }
  }
}
"""

def get_all_collections(token):
    collections = []
    cursor = None
    while True:
        data = graphql(GET_COLLECTIONS, {"cursor": cursor}, token)
        edges = data["data"]["collections"]["edges"]
        for e in edges:
            collections.append({"id": e["node"]["id"], "title": e["node"]["title"]})
        page_info = data["data"]["collections"]["pageInfo"]
        if not page_info["hasNextPage"]:
            break
        cursor = page_info["endCursor"]
    return collections

def get_collection_products(collection_id, token):
    products = []
    cursor = None
    while True:
        data = graphql(GET_COLLECTION_PRODUCTS, {"id": collection_id, "cursor": cursor}, token)
        edges = data["data"]["collection"]["products"]["edges"]
        for e in edges:
            products.append({"id": e["node"]["id"], "tags": e["node"]["tags"]})
        page_info = data["data"]["collection"]["products"]["pageInfo"]
        if not page_info["hasNextPage"]:
            break
        cursor = page_info["endCursor"]
    return products

def sync():
    token = get_token()
    print("Fetching all collections...")
    collections = get_all_collections(token)
    print(f"Found {len(collections)} collections.")

    # Build a map: product_id -> set of collection titles it belongs to
    product_collections = {}
    for col in collections:
        print(f"Processing collection: {col['title']}")
        products = get_collection_products(col["id"], token)
        for p in products:
            if p["id"] not in product_collections:
                product_collections[p["id"]] = {"tags": p["tags"], "collections": set()}
            product_collections[p["id"]]["collections"].add(col["title"])

    # All collection titles (for removal logic)
    all_collection_titles = {col["title"] for col in collections}

    print(f"\nSyncing tags for {len(product_collections)} products...")
    for product_id, data in product_collections.items():
        current_tags = set(data["tags"])
        collection_tags = data["collections"]

        # Remove stale collection tags, add current ones
        non_collection_tags = current_tags - all_collection_titles
        new_tags = list(non_collection_tags | collection_tags)

        result = graphql(UPDATE_TAGS, {"id": product_id, "tags": new_tags}, token)
        errors = result["data"]["productUpdate"]["userErrors"]
        if errors:
            print(f"Error on {product_id}: {errors}")
        else:
            print(f"Updated {product_id}: {sorted(new_tags)}")

    print("\nDone!")

if __name__ == "__main__":
    sync()
