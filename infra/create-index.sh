#!/bin/bash
# create-index.sh — create Elastic index for hybrid RAG search

# === CONFIG ===
CLOUD_ID="<YOUR_ELASTIC_CLOUD_ID>"
API_KEY="<YOUR_ELASTIC_API_KEY>"
INDEX_NAME="searchsphere_docs"

# === EXECUTION ===
echo "Creating Elastic index: $INDEX_NAME ..."
curl -X PUT "https://$CLOUD_ID/api/as/v1/engines/$INDEX_NAME" \
     -H "Authorization: ApiKey $API_KEY" \
     -H 'Content-Type: application/json' \
     -d @elastic-mappings.json

echo "✅ Index created successfully!"
