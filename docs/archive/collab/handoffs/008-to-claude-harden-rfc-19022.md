# HANDOFF 008 → Claude — harden DataHub RFC #19022

- **From:** Cursor Lane A · 2026-08-09 ~23:05 UTC
- **To:** Lane B (Claude) — OSS / submission surface
- **Branch (nullspace kit):** `cursor/datahub-hack-setup-4c9d` @ `4cc3f3f`
- **Upstream PR:** https://github.com/datahub-project/datahub/pull/19022
- **Fork branch:** `Morkeeth/datahub` · `rfc/demand-side-metadata`

Oscar is recording / just recorded. The OSS cherry is this RFC. **Do not open a
connector PR.** Multi-model consensus: harden #19022 only.

---

## Status

| Item | State |
|---|---|
| RFC PR open | ✅ OPEN, labeled `docs` / `community-contribution` / `needs-review` |
| PR title | ❌ still `RFC: …` — fails **Validate PR title** (`docs(rfc):` required) |
| markdown_format_check | ❌ red (prettier italics `*` → `_`) |
| Mergeable bot | ❌ fails with title |
| cubic review | 10 findings posted (advisory) — kit addresses them |
| Cursor push to `Morkeeth/datahub` | ❌ `push: false` — needs Oscar/Claude write token |

---

## What Cursor already packaged (do not redo from scratch)

Everything is in **`docs/oss/datahub-rfc-19022/`** on nullspace:

| File | Use |
|---|---|
| `STRATEGY.md` | Decision: RFC only tonight; connector later |
| `19022-demand-side-metadata.md` | Polished RFC body — copy onto the fork |
| `APPLY.md` | Exact 5-minute apply runbook |
| `REVIEWER-RESPONSE.md` | Paste as a comment on #19022 |
| `DEVPOST-BLURB.md` | Paste into Devpost / SUBMISSION |

Also pointed from `docs/submission/SUBMISSION.md` § OSS.

---

## Your job (mechanical)

1. Authenticate `gh` as someone who can **push** `Morkeeth/datahub` and **edit** #19022.
2. Follow `docs/oss/datahub-rfc-19022/APPLY.md` literally:
   - checkout `rfc/demand-side-metadata`
   - copy polished body → `docs/rfcs/active/19022-demand-side-metadata.md`
   - retitle PR:
     ```
     docs(rfc): RFC for demand-side metadata — a first-class record of assets that do not exist yet
     ```
   - commit + push
3. Paste `REVIEWER-RESPONSE.md` as a top-level comment on #19022.
4. Verify green:
   ```bash
   gh pr checks 19022 --repo datahub-project/datahub
   ```
   Expect: Validate PR title ✓ · markdown_format_check ✓ · Mergeable not failing on title.
5. Optionally open a discussion issue (3 questions only: entity vs aspect, mutation
   semantics, privacy/`recordedBy`) and link it in the RFC header — not required.

---

## Done when

- [ ] `gh pr view 19022` shows the `docs(rfc):` title
- [ ] File on the PR is `docs/rfcs/active/19022-demand-side-metadata.md` with
      `RFC PR: https://github.com/datahub-project/datahub/pull/19022` in the header
- [ ] CI title + markdown checks green
- [ ] Reviewer-response comment posted
- [ ] STATE updated: OSS handoff closed

---

## Do not

- Open `NullspaceDemandSource` / any `metadata-ingestion` PR tonight
- Force-push unrelated history on the datahub fork
- Claim the RFC is merged — it is **open**, which is the honest judged claim
- Change Nullspace product code for this handoff

---

## Why this shape

The RFC argues *against* Nullspace’s dataset squat and for a real `demand` entity.
That honesty is the contribution. A rushed connector would re-ship the squat and
contradict the RFC. Full reasoning: `docs/oss/datahub-rfc-19022/STRATEGY.md`.
