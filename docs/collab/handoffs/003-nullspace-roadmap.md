# HANDOFF 003 — NULLSPACE: full roadmap and build brief

- **From:** Claude (Opus 5) · 2026-08-08 ~23:2x Paris
- **To:** Cursor cloud build agent
- **Ruled by:** Oscar, 2026-08-08 — *"lets commit to nullspace… its the best one we have"*
- **Supersedes:** HANDOFF 002 (Half-Life) entirely. Also closes D5 (A/B/C/D) — see RULING 002.
- **Deadline:** Mon 10 Aug 2026, 17:00 EDT / **23:00 Paris — ~46h from this file**

---

## 1. What we are building

> **Nullspace — demand-side metadata. A catalog entry for data that does not exist yet.**

Consumer agents search DataHub for an asset that isn't there. Instead of each one
failing silently in its own context, every miss materialises or increments a
**ghost**: a real DataHub dataset URN under platform `nullspace`, tagged `ghost`,
carrying a demand counter and edges back to every requesting agent. When demand
crosses threshold, a **builder agent** claims the ghost, writes a real dbt model,
**opens a real PR**, and on merge the ghost **goes solid** — real schema, real
lineage, and provenance pointing back at the agents that asked for it.

**Why this and not Join Treaty:** Join Treaty writes one more true thing into a
catalog. Nullspace inverts what a catalog *is* — an inventory of things that exist
becomes a place where things that don't exist can be *demanded*. The name and the
idea are one object, which is law 1.

**Why the originality score that killed it does not stand:** see RULING 002. The
"public-entry scan" behind `docs/final-ranking.md`'s competitive table cannot have
happened — the Devpost gallery is unpublished. Nullspace was scored 8/30 on
originality against rivals nobody has ever seen.

---

## 2. Ground truth — measured tonight, not recalled

I ran Nullspace end to end against a live DataHub (GMS v1.7.0, ingestion
*"Pipeline finished successfully"*, 52 events). **This is the first time it has ever
been observed running.** Results:

### Works, verified in the graph
- ghost materialises as a **real DataHub dataset**, returned by search
- `nullspace.demand = 3`, all three requesters recorded
- full resolution history (miss / miss / miss / claim / solidify) with timestamps
- `solid` tag applied and returned by GraphQL
- a **real dbt model committed to a real git branch** (`7aa7763`)
- 3/3 unit tests pass

### The README claims three things the running system does not produce
| README says | DataHub actually returns |
|---|---|
| "goes solid: **real schema**" | `schemaMetadata: **null**` |
| "real **lineage**" | **0 upstream, 0 downstream** |
| "a genuinely **mergeable dbt PR**" | `pr_url` is `file:///…#branch`; `dbt_project` **has no remote** — no PR exists or can |

**This gap is the entire build.** Close those three and Nullspace is what it says it
is. Everything else is polish.

### Also missing (Join Treaty has all four — port, don't rebuild)
`app/join_treaty/` is at **13/13** on `scripts/eval.sh`, which was verified both
ways (passes live, exits 1 when GMS is down). It has what Nullspace lacks:
**read-after-write proof · idempotency · named gates that state their reason ·
receipts**. Port that spine.

---

## 3. Roadmap

### Phase 0 — unblock (≈1h, do first, blocks nothing else)
- Nullspace source currently lives **only** on `park/nullspace-2026-08-08` (commit
  `747eb1b`). Bring it onto the working line.
- `dbt_project/` carries a **nested `.git`** — it will land as a broken gitlink under
  `git add -A`. Stage explicitly, always. Backup exists and is verified:
  `~/backups/git-bundles/datahubhack-dbt_project-2026-08-08.bundle`.
- Fix the stranger path (§6). It breaks submission requirement 2 on its own.

### Phase 1 — make the three false claims true (**critical path**)
| Lane | Owns | Done when |
|---|---|---|
| **L1 schema** | `nullspace/builder.py`, `nullspace/emit.py` | DataHub returns `schemaMetadata` with the model's real fields on the solid asset |
| **L2 lineage** | `nullspace/emit.py` | DataHub returns **≥1 upstream** from the solid asset to the warehouse tables the dbt model reads |
| **L3 real PR** | `nullspace/builder.py` | `pr_url` is an `https://` GitHub URL and `gh pr view` reports it **OPEN** |

**L3 needs a decision from Oscar (§7): `dbt_project` has no remote.** Until it does,
"opens a real PR" cannot be true. This is the single hardest dependency in the build
and it is not technical.

### Phase 2 — proof (runs behind Phase 1, same day)
| Lane | Owns | Done when |
|---|---|---|
| **L4 read-after-write + idempotency** | `nullspace/client.py` | every write verified by reading it back; a 4th miss does **not** create a second ghost |
| **L5 eval** | `scripts/eval-nullspace.sh` | the checks in §5 pass on a cold stack, and the script is proven able to **fail** |

### Phase 3 — the reveal (Sunday morning)
| Lane | Owns | Done when |
|---|---|---|
| **L6 board** | `nullspace/board.py`, `nullspace/static/board.html` | ghost → solid is legible on film in one continuous shot, no narration needed |

### Phase 4 — submission (**not optional; start Sunday at the latest**)
| Lane | Owns | Done when |
|---|---|---|
| **L7 video + description** | `docs/submission/` | ≤3-min video public on YouTube; text description written |
| **L8 OSS contribution** | upstream `datahub-project/datahub` | one real PR — connector, skill, RFC, or docs |

**Two of the six judged dimensions — Submission Quality and OSS Bonus — are at
zero right now.** They are the cheapest points available and they cannot be bought
late. If Phase 1 slips, Phase 4 still ships.

---

## 4. Non-negotiables

1. **No claim in the README that the running system does not produce.** This is the
   exact defect found tonight and it is now the project's first rule.
2. **DataHub is the witness.** "We wrote it" is not evidence; "DataHub returns it on
   read-back" is.
3. **Every abstention states its reason.** A miss that produces no ghost, a claim
   that is refused, a rejection — each prints why. Silence is not a verdict.
4. **Demo data is disclosed at the point of the claim**, in the README and the video.
5. **One review surface.** The board, not three dashboards.
6. **Never `git add -A`** in this repo — the nested `dbt_project/.git` guarantees a
   broken gitlink.

---

## 5. The eval — write it before the code

`scripts/eval-nullspace.sh`, stranger-runnable, DataHub as witness:

- **cold stack:** three consumer misses produce **exactly one** ghost, which DataHub
  returns on read-back with `demand=3`
- **convergence:** a 4th miss for the same phrase increments, and does **not** create
  a second ghost
- **solidify:** DataHub returns `schemaMetadata` with ≥1 field **and** ≥1 upstream
  lineage edge on the solid asset
- **the PR is real:** `pr_url` matches `^https://github.com/` and `gh pr view`
  returns state OPEN
- **provenance survives:** the solid asset still names all three original requesters
- **stranger clock:** miss → solid reached in **under 3 minutes** from the README
- **the eval can fail:** prove it red before trusting it green

---

## 6. Known defects (observed 2026-08-08, not guessed)

- **Stranger path breaks at command 1.** `scripts/install-deps.sh` installs the CLI
  to `~/Library/Python/3.12/bin`, not on `PATH`, and prints `datahub: command not
  found` twice. Anyone following the README fails immediately.
- **`AGENTS.md:64` documents a `daemon.json` that does not exist** — not tracked by
  git, not on disk (`git ls-files -- daemon.json` → no output). Commit it or delete
  the guidance; as written it cannot be followed.
- **Host-side, not repo defects, for your notes:** `docker compose` was not installed
  on the operator's machine (colima, no plugin), and lima's port-forwarder had been
  stale since 19 Jul — GMS answered 200 inside the container while refusing host
  connections. Together ~1h before anything could be tested. The compose substrate
  itself came up clean once both were fixed.

---

## 7. Blocked on Oscar — one decision

**`dbt_project` needs a GitHub remote, or "opens a real PR" stays false.**
Recommended: a small **public** repo (e.g. `Morkeeth/nullspace-dbt`) that the builder
agent opens PRs against, so a judge can click the PR link and see it open. Requires
Oscar to create it or approve its creation. **Until then L3 cannot complete, and the
README must not claim a PR.**

---

## 8. Already safe

| Artifact | State |
|---|---|
| `43bfa03` | Apache-2.0 LICENSE **pushed to main** — GitHub previously reported *no licence at all* |
| `747eb1b` | Nullspace tree parked on `park/nullspace-2026-08-08`, staged explicitly |
| `…/datahubhack-dbt_project-2026-08-08.bundle` | `git bundle verify` → *"records a complete history"* |
| `af761f4` | `scripts/eval.sh` — 13/13 live, exit 1 when GMS down; the model for L5 |
