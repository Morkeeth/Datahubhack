#!/usr/bin/env bash
# Query live DataHub GraphQL for an entity ingested from the seeded warehouse.
set -euo pipefail

GMS_URL="${DATAHUB_GMS_URL:-http://localhost:8080}"

read -r -d '' QUERY <<'GRAPHQL' || true
query SeededWarehouseEntity {
  search(
    input: {
      type: DATASET
      query: "customers"
      start: 0
      count: 10
      filters: [
        {
          field: "platform"
          values: ["urn:li:dataPlatform:postgres"]
          condition: EQUAL
        }
      ]
    }
  ) {
    total
    searchResults {
      entity {
        urn
        ... on Dataset {
          name
          platform {
            name
          }
        }
      }
    }
  }
}
GRAPHQL

payload="$(
  QUERY="$QUERY" python3 - <<'PY'
import json
import os

print(json.dumps({"query": os.environ["QUERY"]}))
PY
)"

curl --fail --silent --show-error \
  --request POST \
  --header "Content-Type: application/json" \
  --data "$payload" \
  "${GMS_URL}/api/graphql" |
  python3 -m json.tool
