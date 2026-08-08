# RULING 001 — product scope (answering HANDOFF 001)

- **From:** Claude (Opus 5), terminal session, 2026-08-08 ~22:4x Paris
- **Answers:** `docs/collab/handoffs/001-product-scope-ruling.md`
- **Status of this document:** a recommendation for Oscar to accept or reject. **Oscar rules. I do not.**

---

## 0. The fact the handoff does not contain

HANDOFF 001 was written before tonight's session. During it, Oscar looked at the
running build — the `join-treaty serve` view and the live receipts in DataHub at
`localhost:9002` — and ruled:

> **"its a feature, not ambitious enough"**

That is a **third** rejection, and materially different from the first two: the
earlier two were reactions to a description. This one is a reaction to the
**working software**, on his screen, after it was verified. It cannot be answered
by making the same thing more honest.

**Consequence for the option set: A, B and C are all Join Treaty variants.** They
differ in how much is written and how well it renders. None of them changes the
property Oscar rejected — that the output is an enrichment of a catalog entry. So
the question the handoff asks ("A/B/C/D?") cannot be answered as posed. The option
set is incomplete.

I am not overruling the build agent's analysis. Within its option set, **B is the
correct recommendation** and the reasoning is sound — real ingested query history
kills the faked-evidence objection, and routing a second write through Ownership
genuinely fixes the UI-invisibility problem. If Oscar reinstates Join Treaty, build
B. That judgement stands.

---

## 1–4. Direct answers to the four questions

**1. Confirm or overrule the concept.**
**Overruled — by Oscar, not by me.** Join Treaty is not the flagship. Its
*machinery* is not discarded (see §3).

**2. Pick the scope: A/B/C/D.**
**None as written.** I am tabling an **Option E** and recommending it. If Option E
is rejected, my ranking of the original set is **B > A > C > D**, unchanged from the
build agent's.

**3. Agree the non-negotiables?**
**Agreed, all five, and they survive the scope change unaltered** — real ingested
evidence rather than self-seeded, realistic volume, native read-after-write proof,
honest hedged language, one review surface. These are the strongest part of the
handoff. Whatever gets built, it is held to these. Add a sixth, below.

**4. The Nullspace question.**
**Wordmark-only. There is no platform framing I would endorse**, and two independent
analyses agreeing on that is enough. Separately, I tested Nullspace end to end
tonight — the first time it has ever been observed running — and three of its
README's headline claims are false as built: `schemaMetadata` is `null` (no schema),
lineage is 0 upstream / 0 downstream (no lineage), and `pr_url` is a `file://`
reference to a local branch in a repo with **no remote**, so the "genuinely
mergeable dbt PR" does not exist and cannot. **D is dead on evidence, not on taste.**

---

## 2. Option E — the tabled option

> **A catalog is documentation about a live system. Documentation rots. Nobody
> re-checks it. Probe every claim in the catalog against the warehouse it describes
> and give each one a verdict: upheld, contradicted, or unverifiable — each carrying
> the probe that produced it.**

Working name: **Half-Life**.

**Why it answers the actual objection.** Join Treaty writes one more true thing into
the catalog. Option E puts a verdict on **everything already in it**. That is a
category rather than an enrichment, and it scales across the whole graph instead of
across three relationships.

**Why it is defensible as a product, not a feature.** No catalog vendor can
credibly audit itself — the catalog's correctness *is* the product, so the auditor
cannot live inside it. That is a structural position, not a head start. It is also
distinct from data observability (Monte Carlo, Anomalo): those watch **the data**;
this watches **the claims about the data**. A table can be perfectly healthy and its
description a two-year-old lie.

**Why it is feasible in the time.** Join Treaty's spine is proven and transfers
whole: evidence gathering → named gates → native write-back → read-after-write →
idempotency. Verified tonight at 13/13 on `scripts/eval.sh` (which also fails
correctly, exit 1, when GMS is unreachable). What is new is the claim-probe layer.

**Why it is fair to prior work.** It extends Helicon's R13 (document vs live
system), which is already shipped with real tests — and the rules explicitly reward
*"existing contributions extended for the hackathon."*

---

## 3. The strongest case AGAINST Option E

Stated plainly, because I proposed it and that is a reason to discount me, not trust me:

1. **It trades a verified build for an unverified one with ~46 hours left.** A/B
   start from 13/13 passing. E starts from a spine plus new code. Rule 7 of the
   project's own laws is *"a shipped B beats an unshipped A."* That rule points at B.
2. **The payoff is a number I cannot promise.** The demo warehouse will not rot on
   its own, so the catalog has to be seeded with realistic wrongness. If that seeding
   is not disclosed prominently, it is a worse version of the exact faked-evidence
   tell the build agent is trying to remove. **This is the single biggest risk.**
3. **`docs/final-ranking.md` lists Notary and EPISTEME in catalog-truth already.**
   The rot-vs-live-system angle is narrower than their "trust the graph" claims, but
   the room is not empty and I have not re-probed the public field tonight.
4. **Oscar has not said yes to it.** He asked what the product vision was; he has not
   ruled. Treating E as decided would repeat the exact failure that produced the
   correction earlier in this session.

---

## 4. Ruling on the build agent's offer to start now

The offer: begin **Option A** (replace seeded queries with real ingested query
history) as "lowest-regret work, valuable under any of A/B."

**Recommendation: do not start it yet.** The claim "valuable under any option" is
true only inside the Join Treaty option set. Under Option E the mined-join pipeline
is not the product, so that work is not a floor — it is a sunk day. **Its
low-regret property depends on an assumption Oscar has already rejected once
tonight.**

**One exception, genuinely option-independent:** the stranger-path fix. Following
`scripts/install-deps.sh` and then the README **fails at the first command** —
`join-treaty` installs to `~/Library/Python/3.12/bin`, which is not on `PATH`, and
`datahub` is reported not found. Observed tonight on a clean run. That breaks the
"repo with clear setup instructions" route to submission requirement 2 and is worth
fixing under every option, including E. **Start there.**

---

## 5. The sixth non-negotiable

Add to the list in HANDOFF 001:

> **6. Any headline number is disclosed at its source.** If a figure comes from a
> seeded catalog, the README and the video say so in the same breath as the number.
> Nullspace's README is the cautionary case: it claims schema, lineage and a
> mergeable PR, and the running system produces none of the three.

---

## 6. Submission state — unglamorous and currently decisive

Independent of scope, these are open and cannot be bought late:

| Requirement | State |
|---|---|
| Public repo, Apache-2.0 licence | ✅ fixed 2026-08-08 (`43bfa03`); GitHub previously reported **no licence at all** |
| Demo video < 3 min, public | 🔴 not started |
| Text description | 🔴 not started |
| Project URL judges can test | ⚠️ legal via repo + setup, but the setup path is broken (§4) |
| OSS contribution bonus | 🔴 zero — one of six judged dimensions, currently unscored |

**Two of six judged dimensions are at zero.** Whatever scope wins, that is where the
cheapest points are.

---

## 7. Footnote for the build agent — a doc that contradicts the running system

`AGENTS.md:64` describes setting `features.containerd-snapshotter: false` in
`daemon.json`. **No such file is tracked by git or present on disk** (`git ls-files
-- daemon.json` → no output). Either the file was never committed or the guidance is
stale; as written it cannot be followed. Flagging, not fixing — it is your file.

Also observed tonight, for your environment notes: `docker compose` was **not
installed** on this machine at all (colima, no plugin), and lima's port-forwarder
has been stale since 19 Jul — GMS answered 200 inside the container while refusing
connections on the host. Both are host-side, neither is a defect in this repo, and
both cost about an hour before anything could be tested.

---

## What I need from Oscar — one question

**Option E, or reinstate Join Treaty as B?**

Accept or reject in one line. Everything downstream is already sequenced.
