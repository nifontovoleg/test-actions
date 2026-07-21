# Deployment

Deploy Time Server API with GitHub Actions: build a Docker image → push to GHCR → SSH to the server → pull and run the container.

## Architecture

```text
push to main / workflow_dispatch
        │
        ▼
┌─────────────────────┐
│  Job 1: build-and-  │
│  push               │
│  • docker build     │
│  • push → ghcr.io   │
└─────────┬───────────┘
          │
          ▼
┌─────────────────────┐
│  Job 2: deploy      │
│  • SSH to server    │
│  • docker login     │
│  • pull + run       │
└─────────────────────┘
```

Workflow file: `.github/workflows/deploy.yml`

## Image

| Parameter | Value |
|-----------|-------|
| Registry | `ghcr.io` |
| Name | `ghcr.io/<owner>/<repo>` (lowercase) |
| Tags | `latest`, `<commit-sha>` |
| Container on server | `time-server` |
| Port | `8000` |

Example: `ghcr.io/myuser/actions:latest`

## Server requirements

- Docker installed and available to the SSH user
- Port `8000` open (or a reverse proxy in front)
- Outbound access to `ghcr.io`

## GitHub secrets

Settings → Secrets and variables → Actions:

| Secret | Required | Description |
|--------|----------|-------------|
| `SSH_HOST` | yes | Server IP or hostname |
| `SSH_USER` | yes | SSH username |
| `SSH_PRIVATE_KEY` | yes | Private key (full PEM, including `BEGIN/END`) |
| `SSH_PASSPHRASE` | no | Key passphrase, if the key is encrypted |
| `SSH_PORT` | no | SSH port, default `22` |
| `GHCR_USERNAME` | no* | Not required: deploy pulls with `GITHUB_TOKEN` |
| `GHCR_TOKEN` | no* | Not required: deploy pulls with `GITHUB_TOKEN` |

\* You may keep `GHCR_*` secrets, but the current workflow does not use them.

### Optional GHCR_TOKEN

The workflow uses the built-in `GITHUB_TOKEN` for pull on the server.  
A personal PAT is only needed if you pull the image manually outside Actions.

### SSH key

Put the public key in `~/.ssh/authorized_keys` on the server. Put the private key in `SSH_PRIVATE_KEY`.

## Triggering a deploy

Runs automatically on push to `main`, or manually:

Actions → **Build and Deploy** → **Run workflow**

## What runs on the server

```bash
docker login ghcr.io
docker pull ghcr.io/<owner>/<repo>:latest
docker rm -f time-server || true
# also frees anything bound to port 8000
docker run -d \
  --name time-server \
  --restart unless-stopped \
  -p 8000:8000 \
  ghcr.io/<owner>/<repo>:latest
docker image prune -f
```

## Verify after deploy

```bash
curl http://<SSH_HOST>:8000/health
curl http://<SSH_HOST>:8000/time
curl http://<SSH_HOST>:8000/date
```

On the server:

```bash
docker ps --filter name=time-server
docker logs time-server
```

## Local build (no CI)

```bash
docker build -t time-server-api .
docker run -d --name time-server -p 8000:8000 time-server-api
```

## Troubleshooting

| Problem | Check |
|---------|--------|
| GHCR push fails with 403 | Workflow has `packages: write`; packages are allowed for the repo |
| Pull on server returns 401/403 | Token / login path; package visibility |
| `ssh: overflow reading version string` | That host/port is **not SSH**. Usually wrong `SSH_HOST` or `SSH_PORT` |
| SSH timeout / connection refused | `SSH_HOST`, `SSH_PORT`, firewall, key in `authorized_keys` |
| Port already allocated | `docker ps`, another process on `8000` |
| Container exits immediately | `docker logs time-server` |

### `ssh: overflow reading version string`

The client connected, but the response is not an SSH banner (often HTTP/TLS on ports 80/443/8000).

Check secrets:

| Secret | Should be | Should not be |
|--------|-----------|---------------|
| `SSH_HOST` | `203.0.113.10` or `vps.example.com` | `https://...`, `ssh://...`, URL with a path, Cloudflare/proxy IP of a website |
| `SSH_PORT` | `22` or your custom SSH port (e.g. `2222`) | `8000`, `80`, `443`, empty with spaces/newlines |
| `SSH_USER` | `root` / `ubuntu` / etc. | an email |

Local check:

```bash
ssh -i ./key -p 22 USER@HOST
```

### `unable to authenticate, attempted methods [none publickey]`

Host and port are fine; the server rejected the key.

Check in order:

1. **`SSH_USER`** — the Linux user that owns `~/.ssh/authorized_keys` (often `root` or `ubuntu`, not your GitHub login).
2. **`SSH_PRIVATE_KEY`** — the full **private** key:
   ```text
   -----BEGIN OPENSSH PRIVATE KEY-----
   ...
   -----END OPENSSH PRIVATE KEY-----
   ```
   or `BEGIN RSA PRIVATE KEY`. Not the `.pub` file, no surrounding quotes, no leading spaces on lines.
3. On the server, the matching public key must be in `authorized_keys`:
   ```bash
   mkdir -p ~/.ssh
   chmod 700 ~/.ssh
   echo "ssh-ed25519 AAAA... comment" >> ~/.ssh/authorized_keys
   chmod 600 ~/.ssh/authorized_keys
   ```
4. If the key has a **passphrase**, add secret `SSH_PASSPHRASE` (only if your workflow reads it).
5. Test locally with the same key and user:
   ```bash
   ssh -i ./private_key -p 22 USER@HOST
   ```
   If local login fails, fix the key / `authorized_keys` — not Actions.
