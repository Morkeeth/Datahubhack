# PROMPT — Cursor, Lane A: make the ending real

Paste into a Cursor cloud agent on branch `cursor/datahub-hack-setup-4c9d`.

---

**Objective**
A judge clicks one link in our README and lands on an **OPEN pull request on GitHub
that an agent wrote by itself** — against a dbt repo whose model reads a table that
DataHub shows, on read-back, as the ghost's upstream. Today that link is a `file://`
path and the lineage is empty. Close both. That is the ending of the pitch and right
now the pitch has no ending.

**Context**
- Repo `Morkeeth/nullspace`, branch `cursor/datahub-hack-setup-4c9d` (you are trunk).
- Read first: `docs/collab/handoffs/005-final-38-hours.md`, then `003-nullspace-roadmap.md`,
  then `docs/collab/LANES.md`. You own Lane A only — never edit `nullspace/mcp_server.py`,
  `nullspace/agents/**`, `nullspace/board.py`, `nullspace/static/**`, `docs/submission/**`.
- Live stack is up on Oscar's laptop (`datahub-hack-*`, GMS `:8080`, UI `:9002`).
- **Your last run's `STATE.md` witness table did not survive an independent read-back.**
  Verified 2026-08-09 09:1x Paris: all 7 nullspace ghosts return
  `lineage(UPSTREAM).total = 0`, and `GET /aspects/<urn>?aspect=upstreamLineage`
  returns **404** on every one. The asset whose schema the table quotes has no
  `schemaMetadata` aspect either. Assume nothing in that table is currently true;
  re-earn each row.
- Deadline Mon 10 Aug 23:00 Paris. **Freeze 18:00 Paris.**

**Constraints**
- **A witness row must carry the command that printed it, in the same row.** No row
  survives into `STATE.md` without a reproducible command. This is the rule your last
  run broke.
- Prove lineage on a ghost **created after your fix**, not on a pre-existing one.
  Prove it **twice**: the aspect API returns 200, *and* GraphQL `lineage(UPSTREAM).total ≥ 1`.
- Do **not** add `systemMetadata` to the MCP proposal — that caused a 400 for an hour.
- Never `git add -A`. `dbt_project/` carries a nested `.git` and lands as a broken gitlink.
- No new features. Every temptation in `RULING.md`'s kill list is still dead.
- If a slice is blocked on Oscar, say so in one line and move to the next — do not stall
  the branch waiting.

**Done when — five checks, each one a command**
1. `nullspace reset` exists and wipes demo ghosts; after it,
   search for platform `nullspace` returns **0** assets. Demo starts hollow.
2. A fresh end-to-end run creates one ghost, and on solidify:
   `curl /aspects/<urn>?aspect=upstreamLineage` → **200 with ≥1 upstream**, and GraphQL
   `lineage(UPSTREAM).total ≥ 1`. Both outputs pasted into `STATE.md`.
3. `schemaMetadata` and `ownership` are present on **that same asset** — 3 requester
   Owners, fields = union of the declared contracts.
4. `pr_url` is an `https://github.com/...` URL, `gh pr view <url> --json state` returns
   **OPEN**, and that URL is bound into the ghost's resolution history in DataHub
   (read it back to prove it).
5. Merging that PR flips the ghost to `solid` — observed, not assumed.

**Blocked-on-Oscar (do not guess a workaround)**
- Check 4 needs `Morkeeth/nullspace-dbt` to exist and be public (**D9**). If it does not
  exist when you start, build everything else, leave `pr_url` honestly `file://`, and
  write one line in `STATE.md` naming D9 as the blocker.

**Start by**
Re-run the current demo end to end and paste the four read-backs (schema, ownership,
lineage aspect, lineage GraphQL) into your first message — before writing any code.
Confirm or refute my finding that lineage was never written. If I am wrong, say so
plainly and show the command that proves it.
