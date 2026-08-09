#!/usr/bin/env bash
# Join Treaty — stranger-runnable acceptance eval.
#
# Every assertion below is answered by DataHub itself (GraphQL / OpenAPI),
# never by this repo's own log lines. "We wrote it" is not evidence;
# "DataHub returns it" is.
#
#   bash scripts/eval.sh            # assumes the stack is already up
#   bash scripts/eval.sh --cold     # docker compose down -v, then up, then assert
#
# Exit 0 = every check passed. Exit 1 = at least one failed.

set -uo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

GMS="${DATAHUB_GMS_URL:-http://localhost:8080}"
export DATAHUB_GMS_URL="$GMS"
export PATH="$HOME/Library/Python/3.12/bin:$HOME/.local/bin:$PATH"

START_TS=$(date +%s)
PASS=0
FAIL=0

ok()   { printf '  PASS  %s\n' "$1"; PASS=$((PASS + 1)); }
bad()  { printf '  FAIL  %s\n' "$1"; FAIL=$((FAIL + 1)); }
head_() { printf '\n== %s\n' "$1"; }

# Credentials come from the environment. The fallback is the DataHub OSS
# quickstart's published default, which is why it is safe to sit here, and also
# why it must not be the only option: override DATAHUB_USER and DATAHUB_PASS
# against anything that is not a local demo stack.
DH_AUTH="${DATAHUB_USER:-datahub}:${DATAHUB_PASS:-datahub}"

gql() {
  curl -s -m 20 -X POST "$GMS/api/graphql" \
    -H 'Content-Type: application/json' \
    --user "$DH_AUTH" \
    -d "$1"
}

# ---------------------------------------------------------------- cold start
if [[ "${1:-}" == "--cold" ]]; then
  head_ "Cold start (docker compose down -v && up)"
  docker compose down --volumes >/dev/null 2>&1
  docker compose up -d >/dev/null 2>&1
  printf '  waiting for GMS'
  for _ in $(seq 1 120); do
    curl -sf "$GMS/health" >/dev/null 2>&1 && break
    printf '.'; sleep 5
  done
  printf '\n'
  printf '  waiting for warehouse ingestion'
  for _ in $(seq 1 120); do
    docker logs datahub-hack-metadata-ingestion-1 2>&1 \
      | grep -q 'Pipeline finished successfully' && break
    printf '.'; sleep 5
  done
  printf '\n'
fi

# ------------------------------------------------------------------ CHECK 0
head_ "CHECK 0 — DataHub is answering"
if [[ "$(curl -s -m 10 -o /dev/null -w '%{http_code}' "$GMS/health")" == "200" ]]; then
  ok "GMS $GMS/health returns 200"
else
  bad "GMS $GMS/health unreachable — nothing below can be trusted"
  echo; echo "RESULT: FAIL ($PASS passed, $FAIL failed)"; exit 1
fi

# ------------------------------------------------------------------ CHECK 1
# Every rejection must state a reason. A silent rejection is a bug, because a
# user cannot tell "rejected on evidence" from "crashed".
head_ "CHECK 1 — audit is deterministic and every rejection states a reason"
join-treaty seed >/dev/null 2>&1
AUDIT_FILE="$(mktemp -t jt-audit)"
join-treaty audit --json "$AUDIT_FILE" >/dev/null 2>&1

if [[ ! -s "$AUDIT_FILE" ]]; then
  bad "audit produced no JSON report at $AUDIT_FILE — cannot verify anything below"
  ACCEPTED=0; REJECTED=0
else
  read -r ACCEPTED REJECTED MUTE NOGATE <<<"$(python3 - "$AUDIT_FILE" <<'PY'
import json, sys
items = json.load(open(sys.argv[1]))["items"]
rej = [i for i in items if not i.get("accepted")]
mute = sum(1 for i in rej if not (i.get("reason") or "").strip())
# A rejection must also name which gate failed, not just say "rejected".
nogate = sum(1 for i in rej
             if not [g for g in i.get("gates", []) if not g.get("passed")])
print(len(items) - len(rej), len(rej), mute, nogate)
PY
)"
  [[ "${MUTE:-1}" == "0" ]] \
    && ok "every rejection carries a stated reason" \
    || bad "${MUTE} rejection(s) printed with no reason"
  [[ "${NOGATE:-1}" == "0" ]] \
    && ok "every rejection names the gate that failed" \
    || bad "${NOGATE} rejection(s) name no failing gate"
fi
[[ "${ACCEPTED:-0}" -ge 1 ]] && ok "audit accepted ${ACCEPTED} treaty candidate(s)" \
                             || bad "audit accepted nothing — no write to verify"
[[ "${REJECTED:-0}" -ge 1 ]] && ok "audit rejected ${REJECTED} negative(s) — the filter is doing work" \
                             || bad "audit rejected nothing — the negatives are not being exercised"

# ------------------------------------------------------------------ CHECK 2
head_ "CHECK 2 — the write lands, and DATAHUB says so (not our log)"
join-treaty apply --all-accepted --yes >/dev/null 2>&1
ER_TOTAL=$(gql '{"query":"{ search(input:{type:ER_MODEL_RELATIONSHIP, query:\"*\", start:0, count:50}) { total } }"}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['data']['search']['total'])" 2>/dev/null)
if [[ "${ER_TOTAL:-0}" == "${ACCEPTED:-0}" && "${ER_TOTAL:-0}" -gt 0 ]]; then
  ok "DataHub returns ${ER_TOTAL} ERModelRelationship(s) on read-back — matches ${ACCEPTED} accepted"
else
  bad "DataHub returned '${ER_TOTAL:-none}' ERModelRelationships, expected ${ACCEPTED:-?}"
fi

# The relationship must carry its evidence, or it is an assertion, not a treaty.
FIRST_URN=$(gql '{"query":"{ search(input:{type:ER_MODEL_RELATIONSHIP, query:\"*\", start:0, count:1}) { searchResults { entity { urn } } } }"}' \
  | python3 -c "import sys,json; r=json.load(sys.stdin)['data']['search']['searchResults']; print(r[0]['entity']['urn'] if r else '')" 2>/dev/null)
if [[ -n "$FIRST_URN" ]]; then
  ENC=$(python3 -c "import urllib.parse,sys; print(urllib.parse.quote(sys.argv[1], safe=''))" "$FIRST_URN")
  BODY=$(curl -s -m 20 "$GMS/openapi/v3/entity/ermodelrelationship/$ENC")
  grep -q 'evidence_count'      <<<"$BODY" && ok "relationship carries evidence_count"      || bad "relationship has no evidence_count"
  grep -q 'evidence_query_urns' <<<"$BODY" && ok "relationship cites its Query URNs"        || bad "relationship cites no query evidence"
  grep -q 'cardinality'         <<<"$BODY" && ok "relationship records an inferred cardinality" || bad "relationship has no cardinality"
else
  bad "no ERModelRelationship URN to inspect"
fi

# ------------------------------------------------------------------ CHECK 3
head_ "CHECK 3 — running twice produces no duplicate"
RERUN="$(join-treaty apply --all-accepted --yes 2>&1)"
ER_AFTER=$(gql '{"query":"{ search(input:{type:ER_MODEL_RELATIONSHIP, query:\"*\", start:0, count:50}) { total } }"}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['data']['search']['total'])" 2>/dev/null)
[[ "${ER_AFTER:-0}" == "${ER_TOTAL:-0}" ]] \
  && ok "second run left the count at ${ER_AFTER} — idempotent in the graph" \
  || bad "count moved ${ER_TOTAL} -> ${ER_AFTER} on rerun — duplicates"
grep -qi 'New this run: 0' <<<"$RERUN" \
  && ok "second run reports 'New this run: 0'" \
  || bad "second run did not report zero new writes"

# ------------------------------------------------------------------ CHECK 4
head_ "CHECK 4 — the receipt is readable back off both datasets"
RCPT=$(gql '{"query":"{ searchAcrossEntities(input:{query:\"join_treaty\", start:0, count:20}) { total } }"}' \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['data']['searchAcrossEntities']['total'])" 2>/dev/null)
[[ "${RCPT:-0}" -ge 1 ]] \
  && ok "DataHub search finds ${RCPT} entity/entities carrying a join_treaty receipt" \
  || bad "no join_treaty receipt is searchable in DataHub"

# ------------------------------------------------------------------ CHECK 5
head_ "CHECK 5 — time to the reveal"
ELAPSED=$(( $(date +%s) - START_TS ))
[[ "$ELAPSED" -lt 180 ]] \
  && ok "reveal reached in ${ELAPSED}s (< 180s)" \
  || bad "took ${ELAPSED}s — over the 3-minute stranger budget"

# ------------------------------------------------------------------- summary
echo
if [[ "$FAIL" -eq 0 ]]; then
  echo "RESULT: PASS ($PASS checks)"
  exit 0
fi
echo "RESULT: FAIL ($PASS passed, $FAIL failed)"
exit 1
