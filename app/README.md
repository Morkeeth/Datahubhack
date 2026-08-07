# Join Treaty

Mine repeated equality joins from DataHub query history, verify them against
schema and column profiles, and persist each as a native DataHub
`ERModelRelationship` with a receipt on both datasets.

This package is the implementation of the locked hackathon concept. See the
repository root `README.md` for the one-command substrate and the full demo
path, and `docs/build-brief.md` for the scope contract.

```bash
# from a running `docker compose up` substrate:
join-treaty seed          # emit real Query entities into DataHub
join-treaty audit         # discover + validate candidates (deterministic)
join-treaty apply --candidate <id> --yes
join-treaty serve         # web view on :3000
```
