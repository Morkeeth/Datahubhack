# APPLY — Oscar's 5-minute runbook for RFC #19022

Oscar is recording; this is the exact apply after the take. Everything below runs against
the fork that already holds the RFC branch. The polished body lives in this package at
`docs/oss/datahub-rfc-19022/19022-demand-side-metadata.md`.

## Prereqs (once)

- `gh auth status` shows you (Oscar) logged in with a token that can push to the fork and
  edit PR #19022. If not: `gh auth login`.
- You have the polished file from this repo. Easiest: keep this repo checked out somewhere
  and reference the absolute path in the copy step below.

## The apply

```bash
# 1. Go to the fork that holds the RFC branch
cd ~/path/to/Morkeeth/datahub

# 2. Be on the RFC branch and fresh
git checkout rfc/demand-side-metadata
git pull --ff-only

# 3. Rename the placeholder RFC to its PR number (skip if already 19022-*.md)
git mv docs/rfcs/active/000-demand-side-metadata.md docs/rfcs/active/19022-demand-side-metadata.md 2>/dev/null || true

# 4. Copy the polished body over the (now renamed) file.
#    Replace <NULLSPACE_REPO> with wherever you have this nullspace repo checked out.
cp <NULLSPACE_REPO>/docs/oss/datahub-rfc-19022/19022-demand-side-metadata.md \
   docs/rfcs/active/19022-demand-side-metadata.md

# 5. Retitle the PR
gh pr edit 19022 --repo datahub-project/datahub \
  --title "docs(rfc): RFC for demand-side metadata — a first-class record of assets that do not exist yet"

# 6. Commit and push
git add -A
git commit -m "docs(rfc): harden demand-side metadata RFC for #19022"
git push

# 7. (optional) Open the discussion issue and paste DISCUSSION-ISSUE.md if you decide to
#    split discussion out of the PR thread. Not required for the judged artifact.
```

## Verify before you stop recording

- `gh pr view 19022 --repo datahub-project/datahub` shows the new title and your commit.
- The file at `docs/rfcs/active/19022-demand-side-metadata.md` opens on GitHub and the
  header line 2 reads `- RFC PR: https://github.com/datahub-project/datahub/pull/19022`.
- The Basic example imports `MetadataChangeProposalWrapper` and the requester carries
  `source="query-log"` and `requestId=...`.

## If `git mv` says the file is already `19022-*.md`

It has already been renamed (that is the current state on the branch). Skip step 3 and just
copy the polished body over the existing `docs/rfcs/active/19022-demand-side-metadata.md`.

## Rollback

Nothing here is destructive beyond a single commit. `git reset --hard origin/rfc/demand-side-metadata`
before pushing, or revert the commit after, restores the prior state.
