# Night build plan — Join Treaty MVP

Date: 2026-08-07 (overnight build for morning evaluation)

Scope contract: `docs/build-brief.md` + `docs/final-ranking.md` "Scope lock".
This plan does not reopen ideation. It builds the five locked must-have
capabilities on top of the concept-neutral substrate (`compose.yaml`).

## What Join Treaty does

Mine the equality joins teams repeat in DataHub's query history, verify each
one against schema and column profiles, and write it back as a native DataHub
`ERModelRelationship` — the join graph that lineage never captures.

## Substrate reuse (already live)

`docker compose up` starts DataHub OSS + a seeded Postgres warehouse and
profiles it into DataHub. That gives **real** dataset entities, schemas, and
column profiles for `ecommerce.{customers,orders,order_items,products}` plus a
view. The profiles carry real uniqueness signal:

| Field | uniqueProportion | Role |
| --- | --- | --- |
| `customers.customer_id` | 1.0 | unique key (destination / "one") |
| `orders.customer_id` | 0.67 | duplicated FK (source / "many") |
| `orders.order_id` | 1.0 | unique key |
| `order_items.order_id` | 0.75 | duplicated FK |
| `products.product_id` | 1.0 | unique key |
| `order_items.product_id` | 0.75 | duplicated FK |

So three genuine `N:1` join treaties are derivable from real evidence, and we
can seed weak/negative queries to prove the abstain path.

## Architecture

Deterministic Python 3 pipeline (no LLM verdict), typed run model.

- `app/join_treaty/datahub.py` — DataHub client: read `SchemaMetadata`,
  `DatasetProfile` (timeseries), enumerate + read `Query` entities; emit MCPs;
  read-after-write.
- `app/join_treaty/seed.py` — emit **real** `Query` entities (QueryProperties +
  QuerySubjects) with SQL that joins the warehouse tables. Strong joins repeat
  ≥3 times; two negatives exercise the threshold and type gates.
- `app/join_treaty/parser.py` — SQLGlot extraction of **single-column explicit
  equality** join predicates with alias→dataset resolution. Composite/implicit
  joins are ignored by design.
- `app/join_treaty/discover.py` — aggregate evidence by canonical join across
  distinct Query URNs; require ≥3 independent occurrences.
- `app/join_treaty/validate.py` — field existence + type-bucket compatibility;
  profile-based cardinality inference; **abstain** when evidence is not
  positive.
- `app/join_treaty/apply.py` — write native `ERModelRelationshipKey` +
  `ERModelRelationshipProperties` (field mapping, cardinality, evidence), PATCH
  a compact treaty receipt onto both datasets, then **read both back**.
- `app/join_treaty/web.py` — minimal FastAPI view on `:3000`.
- CLI: `join-treaty seed | audit | apply | serve | demo`.

## Deterministic decision rules

1. Evidence: same canonical single-column equality join in ≥ 3 distinct Query
   URNs.
2. Fields: both columns exist in their dataset schemas and share a normalized
   type bucket (integer/numeric/string/temporal/boolean).
3. Cardinality from profiles: unique side (`uniqueProportion == 1.0`) is the
   "one"; a duplicated side is the "many" → `N_ONE`. Both unique → `ONE_ONE`.
   Neither unique → **abstain** (reject; no referential-integrity claim).
4. Language is "observed join treaty", never "verified foreign key".

## Demo path (< 3 min, morning evaluation)

1. `docker compose up` (already validated) → DataHub + seeded warehouse.
2. `join-treaty seed` → real Query entities appear in DataHub.
3. `join-treaty audit` → prints candidates, supporting query URNs, gate
   results, and the rejected negatives.
4. `join-treaty apply --candidate <id> --yes` → native ER relationship +
   receipts on both datasets + read-after-write proof; writes
   `examples/join-treaty-receipt.json`.
5. Re-run `apply` → idempotent (`0 new relationships`).
6. `join-treaty serve` → open `:3000` for the evidence/relationship view and
   the deep link to the DataHub Properties receipt.

## Morning evaluation checklist

- [ ] `pytest app/tests` green (deterministic parser/validate/discover).
- [ ] `join-treaty audit` shows 3 accepted `N:1` treaties + 2 rejected negatives
      with reasons.
- [ ] A native `ERModelRelationship` exists in DataHub (read-after-write) with
      field mapping, cardinality, evidence count, run id.
- [ ] Both datasets show the `join_treaty:*` receipt in DataHub Properties.
- [ ] Re-running apply reports idempotent (0 new).
- [ ] `examples/join-treaty-receipt.json` present and matches the live write.
- [ ] Web view on `:3000` renders candidates, evidence, gates, and links.

## Honest platform gap

DataHub OSS V2 UI does not yet render `ERModelRelationship` entities. The
relationship is canonical storage (proven by read-after-write); the native UI
proof is the PATCHed dataset receipt in the Properties tab, plus the app view.
