# DataHub local notes

Primary path for judges and agents:

```bash
bash scripts/setup-datahub.sh
```

That wraps `datahub docker quickstart` and loads the `showcase-ecommerce` datapack when available.

## Manual equivalents

```bash
pip install acryl-datahub
datahub docker quickstart
datahub init --username datahub --password datahub
datahub datapack load showcase-ecommerce
```

## Endpoints

| Service | URL |
| --- | --- |
| UI | http://localhost:9002 |
| GMS | http://localhost:8080 |

Default UI credentials: `datahub` / `datahub`.

## MCP

```bash
export DATAHUB_GMS_URL=http://localhost:8080
export DATAHUB_GMS_TOKEN=<PAT from UI Settings → Access Tokens>
npx -y @acryldata/mcp-server-datahub
```

## Resource note

Quickstart wants roughly 2 CPUs / 8GB RAM. Cloud agents should start Docker via environment `start`, then run setup only when the task needs a live catalog.
