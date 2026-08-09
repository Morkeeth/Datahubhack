# Last comments on the submission package

*Lane A pass, 2026-08-09 ~21:00 UTC — review only. Does not replace your package.*  
Cross-checked against `docs/collab/SUBMISSION-AUDIT.md` and live `nullspace-dbt` PRs.

---

## Overall

The package is strong and submission-shaped. Pitch insight, ladder, and “what we will
not claim” are the right tone. Tagline stack (#1 headline / #2 subtitle / #3 close) is
the right pick. Ship it — with the sync notes below so video, pitch, and README don’t
contradict each other under a rushed judge.

---

## Sync before you hit submit

1. **PR ban in `video-script.md` is stale.** D9 is done; `#1` and `#2` on
   `nullspace-dbt` are both **MERGED**. The rule should be: *ban the phrase only if this
   recording’s `pr_url` is `file://`*. Pitch already cites `#1` — fine; README cites `#2`.
   Pick one for the form (either works; both are the same want).

2. **Checklist still says “blocked on Lane A.”** Owners + schema-on-solid are in the
   loop now. Retest once on a **reset** board; if green, strike the blockers so the
   shoot list doesn’t scare you into skipping those shots.

3. **Pitch vs video on “real dbt model.”** Pitch §“What is actually running” and video
   1:55 both say real dbt. On hosts where Fusion wins, solid is **CTAS** (D33). Either
   record where `dbt run` works, or VO: *“materialises in the warehouse; opens a PR a
   human merges.”* Don’t show a Fusion error in frame.

4. **Walk-the-book is missing from the video.** That’s the best judge beat you have
   (skip churn/NRR → claim pipeline coverage). Pitch already claims “declines out loud.”
   Steal ~20s from 1:55–2:35 for one skip line + claim line, or keep MRR only and soften
   that pitch bullet to “can decline.”

5. **Reset before camera.** Dirty graph (throughput noise, stranded `claimed`) will
   kill the 0:40–1:20 demand climb. Script already says cold clone — treat
   `python3 -m nullspace.cli reset` as non-optional even on a warm laptop.

6. **Public MCP line in the pitch.** “Your own agent can create demand” is true;
   fulfilment via the public endpoint is not (`claim_and_build` disabled when public).
   Don’t imply the judge’s agent finishes the loop on the hosted URL.

7. **Harvest number.** README’s `1,205 → 41` isn’t in this package. If the Devpost
   description pulls README bullets, either commit the corpus or omit the number from
   the pasted text.

---

## What I’d leave alone

- One-liner and insight paragraphs in `pitch.md`
- Taglines #1 / #2 / #3 recommendation
- Video structure (silence → three rooms → DataHub ghost → owners → queries run)
- Honest “human at the merge button” section — keep that; it wins trust

---

## Suggested VO tweak (optional, 1:55)

Was: *“Real dbt model. Ghost → solid.”*  
Safer: *“The builder writes the model, opens the PR, and on merge the ghost goes solid —
owners and lineage land in DataHub.”*

Only say “dbt” on camera if `dbt run` is what you just showed.
