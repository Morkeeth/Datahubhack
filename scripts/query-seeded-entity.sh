#!/usr/bin/env bash
# Query live DataHub GraphQL for an entity ingested from the seeded warehouse.
set -euo pipefail

GMS_URL="${DATAHUB_GMS_URL:-http://localhost:8080}"
DATASET_URN="${DATASET_URN:-urn:li:dataset:(urn:li:dataPlatform:postgres,local-warehouse.warehouse.ecommerce.customers,DEV)}"

read -r -d '' QUERY <<'GRAPHQL' || true
query SeededWarehouseEntity($urn: String!) {
  dataset(urn: $urn) {
    urn
    name
    platform {
      name
    }
    schemaMetadata {
      fields {
        fieldPath
        nativeDataType
      }
    }
  }
}
GRAPHQL

payload="$(
  QUERY="$QUERY" DATASET_URN="$DATASET_URN" python3 - <<'PY'
import json
import os

print(
    json.dumps(
        {
            "query": os.environ["QUERY"],
            "variables": {"urn": os.environ["DATASET_URN"]},
        }
    )
)
PY
)"

curl --fail --silent --show-error \
  --request POST \
  --header "Content-Type: application/json" \
  --data "$payload" \
  "${GMS_URL}/api/graphql" |
  python3 -m json.tool
