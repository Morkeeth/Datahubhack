# Design prompt — the Nullspace demand board

Written in Oscar's own template (`02 Content/design-taste-system.md` Part 3), grounded in
his recorded Visual DNA (Part 1) and named reference products (Part 2). Not improvised.

> **Correction to the first attempt.** `docs/design/board-directions.html` proposed three
> monolithic surfaces — one all-dark, two all-light. Oscar's shipped DNA is neither:
> *"Light page backgrounds. Dark blocks for data/output. The contrast between the two IS
> the design… a light narrative with dark data windows embedded in it."* All three
> directions missed it. This document fixes the brief before any more pixels.

---

## Gate 0 · The brief, said out loud

**The subject, one line.** A board showing assets that agents have asked for and that do
not exist yet.

**The screen's ONE job.** Make a stranger feel the moment a thing nobody had goes from
absent to real — in a 3-minute video, without narration.

**Who operates it.** Nobody. Agents write to it; a human watches. That matters: this is
not a console with controls, it is **a board that is watched**. No buttons in the hero.

**The calm/default state.** Most ghosts sit under threshold, quietly accumulating. The
dramatic 5% is the solidify moment. **Design the waiting, not the payoff** — the payoff
only lands if the waiting reads as patient rather than broken.

**Does a brand system already exist?** No. `nullspace/static/board.html` exists but was
never designed. Greenfield.

**Inspiration Oscar has named.** ⚠️ **NONE YET — this is the open input.** Everything
below is sourced from his recorded taste file, not from something he pointed at tonight.

## The through-line from his own DNA

| His rule | What it forces here |
|---|---|
| Light narrative, dark data windows | The page is light. **Each ghost card is a dark window.** When it goes solid the window *lights up* — the inversion is the animation |
| Numbers are heroes | The demand count is the biggest thing on the page. Mono, large, coloured by meaning |
| Copy as design, no illustrations | The want-phrase in plain English *is* the artwork. No icons, no ghosts-as-cartoons |
| One joke per page, after the serious content, never in the hero | Candidate, in the footer only: *"Nobody asked for this one."* on an empty board |
| One dramatic animation per page | Reserved for ghost → solid. Everything else is 150–300ms ease-out |
| Radius ≤ 8px, no gradients, no glass, no emoji icons | Hard constraints |

---

## The prompt (his template, filled)

```
Build the Nullspace demand board.

REFERENCE — steal these specific elements, named:
  · Linear changelog card: one card per entry, 1px border, NO shadow, tag by area,
    generous vertical rhythm. Our ghost card is that card.
  · Stripe dashboard metric card: large number 28-32px, the supporting label small and
    muted beneath it, no axes, no chartjunk. Our demand count is that number.
  · Warp block-based output: each execution is a discrete, bounded, referenceable block.
    Our dark data window per ghost is that block.
  · Vercel/Geist tokens: gray ramp with zero undertone, blue reserved for interactive
    ONLY, 8px spacing grid, letter-spacing -0.04em on headings, borders at
    rgba(255,255,255,0.08) inside the dark blocks.

PALETTE:
  #fafafa   page (light narrative)
  #0c0c0e   the ghost card (dark data window)
  #e4e4e7   hairline borders on light
  rgba(255,255,255,0.08)  hairline borders inside dark
  #6b6560   muted supporting text
  ACCENT — one, and it must carry meaning, not decoration:
  #0891b2   cyan, for demand accruing (cool = still waiting)
  the solid state does NOT get a second accent colour. It gets INVERTED:
  the card goes from #0c0c0e on #fafafa to #fafafa on #0c0c0e.
  Absence-to-presence is a value flip, not a hue change.

TYPOGRAPHY:
  Body/labels : IBM Plex Sans 300/600
  Data/IDs    : IBM Plex Mono 400/500
  Want-phrase : the one editorial voice — 25-30px, tight tracking, the sentence IS the art
  Max 2 faces. Max 4 sizes. 3x jumps.
  Mono NEVER carries the whole interface (kill-list item).

THE HERO NUMBER:
  The demand count. Biggest thing on the card, mono, #0891b2, ~64px.
  Under it, small caps: "AGENTS ASKED". Under that, their real identities in mono.
  Never a progress bar — a bar implies a task; this is a count of independent minds.

ANIMATION — exactly one dramatic moment:
  ghost -> solid: the dark card inverts to light over 320ms ease-out, and the requester
  names slide up 4px staggered 0.06s. No bounce. No spring. Nothing else on the page moves.

KILL LIST:
  No emojis. No gradients. No glass. No radius above 8px. No pulsing or blinking status
  dots. No amber/green traffic lights. No purple. No Inter, Roboto, Space Grotesk.
  No cream #F4F1EA + serif + terracotta. No progress bars. No fake-precision numbers
  ("run #2,914"). No decoration that carries no data. No centred body text.

THE METAPHOR: [ONE OF THREE BELOW — Oscar rules]
  Not like: an observability console. Not like: a Kanban board. Not like: a crypto dApp.
```

---

## The three metaphors — this is the actual ruling

Each keeps the DNA above (light page, dark data windows, number as hero). They differ in
what the *waiting* feels like, which is the screen's real job.

### M1 · **Darkroom** — latent image becoming a print
Demand is a latent image: already there, not yet visible. Solidifying is *developing*.
The dark card is the exposed negative; the flip to light is the print emerging.
*Why it fits:* "develop" is literally the verb, and absence→presence is a value flip, which
is exactly the DNA's light/dark inversion. **Warmest, most human, least like software.**
*Risk:* the safelight red must stay a ground wash, never a status dot.

### M2 · **The subscription list** — signatures accumulating on a petition
Each agent that asks signs its name. Three signatures and the thing gets made.
*Why it fits:* it makes the requesters the story, which is exactly what the Owners-panel
payoff shot shows. The names are the artwork — pure "copy as design".
*Risk:* can read as a form. Needs the dark window to keep it from feeling like admin.

### M3 · **The arrivals board** — a departure that isn't scheduled yet
Rows of things expected but not present. The flip is a split-flap settling.
*Why it fits:* it is a board that is *watched*, not operated — matching Gate 0 exactly.
*Risk:* split-flap animation is a known charm-trick; it risks reading as decoration, and
it is the least differentiated of the three.

**My read:** **M1 Darkroom.** It is the only one where the metaphor and the DNA are the
same gesture — a value inversion — so the design does not have to carry two ideas at once.
M2 is the safest and would still be good. M3 I would not build.

---

## What is still missing, and only Oscar can supply it

Gate 0 asks for **real inspiration Oscar names or pastes**. Nothing above came from him
tonight — it is all reconstructed from his taste file. **A URL, a screenshot, a product he
already loves, or a flat "M1, go" all unblock this.** Without it, the next build is still
sourced taste rather than his taste.

Gate 0.5 (mood imagery) cannot run in this session — there is no image-generation tool
available here. If the look matters more than the clock, that gate is worth doing in a
session that has one.
