# Passman Docker images (dev & demo)

This repository builds and publishes **Docker images** for the [Passman](https://github.com/nextcloud/passman) Nextcloud app. Each image is a ready-to-run **Nextcloud** stack (Apache, MariaDB, PHP) with Passman pre-installed and configured (with the latest Passman version during image build time).

Two image families serve different goals:

| Image family | Docker Hub | Purpose |
|--------------|------------|---------|
| **Development** (`passman-dev`) | [binsky/passman-dev](https://hub.docker.com/r/binsky/passman-dev) | Local hacking: mount your Passman checkout, run `grunt`, use SSH/`sshfs`, try many Nextcloud/PHP versions. |
| **Demo** (`passman-demo`) | [binsky/passman-demo](https://hub.docker.com/r/binsky/passman-demo) | Pre-baked, production-like instances (e.g. public demo hosts) without dev tooling. |

**Default login** (all images): user `admin`, password `admin`.

**Rolling tag (only for dev images):** `binsky/passman-dev:latest` tracks the newest supported dev stack (see `ci/registry.json`).

**Source:** [github.com/binsky08/passman-dev-docker-build](https://github.com/binsky08/passman-dev-docker-build)

---

## Development vs demo images

### Development (`binsky/passman-dev`)

Use these when you work on Passman itself:

- **Passman source** is cloned at build time; you typically **bind-mount** your local repo to `/var/www/html/apps/passman`.
- **Node/npm + grunt** are available (on newer stacks) so you can build frontend assets inside the container.
- **SSH** is enabled so you can `ssh` in or mount the whole Nextcloud tree with **sshfs** (IDE autocompletion).
- Several **Nextcloud + PHP** stacks are available; older recipes live in `archived/` (see [Published image tags](#published-image-tags)).

Older directories use a **single-stage** Dockerfile (one image = dev). Newer stacks (e.g. `nc33_php8.4`) use a **multi-stage** Dockerfile: stage `demo` is the runtime base; stage `dev` adds npm/grunt on top.

### Demo (`binsky/passman-demo`)

Use these for **hosted demos** or any setup where you only need a running instance:

- Same Nextcloud + Passman + DB **baked in at build time** (no bind-mount workflow).
- **No** dev extras (no grunt toolchain on top of the demo stage).
- Built from the **`demo`** stage of multi-stage Dockerfiles. Contexts without a `demo` stage do not publish a demo image.

Demo images (as well as dev images) can honor `DEMO_EXTERNAL_FQDN` at runtime (see `entrypoint.sh`) to automatically add an extra trusted domain. This will also set `overwriteprotocol=https` to prevent SCP issues, since a custom demo is usually served via https.

---

## Published image tags

Tags match the **directory name**: `nc<nextcloud>_php<version>` (e.g. `nc33_php8.4`). On Docker Hub, public tags are **multi-arch** (`linux/amd64` + `linux/arm64`); see [CI](#ci-github-actions--docker-hub).

### Built by CI today

Only top-level directories with a `Dockerfile` are built (not `archived/`):

| NC | Ubuntu | PHP | Development | Demo |
|----|--------|-----|-------------|------|
| 35 | 26.04 | 8.5 | `binsky/passman-dev:nc35_php8.5` | `binsky/passman-demo:nc35_php8.5` |
| 35 | 26.04 | 8.4 | `binsky/passman-dev:nc35_php8.4` | `binsky/passman-demo:nc35_php8.4` |
| 34 | 26.04 | 8.5 | `binsky/passman-dev:nc34_php8.5` | `binsky/passman-demo:nc34_php8.5` |
| 33 | 24.04 | 8.4 | `binsky/passman-dev:nc33_php8.4` | `binsky/passman-demo:nc33_php8.4` |
| 32 | 24.04 | 8.4 | `binsky/passman-dev:nc32_php8.4` | — (single-stage Dockerfile, dev only) |

Rolling dev tag: **`binsky/passman-dev:latest`** → same as `nc35_php8.5` (set in `ci/registry.json` → `dev_latest_context`).

### Older stacks

Dockerfiles for Nextcloud 20–31 (various PHP versions) live under **`archived/`** for reference and manual rebuilds. They are **not** part of the CI matrix unless moved back to the repository root. Many corresponding tags may still exist on [Docker Hub](https://hub.docker.com/r/binsky/passman-dev/tags) from earlier releases.

---

## Repository layout

```
passman-dev-docker-build/
├── entrypoint.sh
├── nc34_php8.5/              # multi-stage (demo + dev)
├── nc33_php8.4/              # multi-stage (demo + dev)
├── nc32_php8.4/              # single-stage (dev)
├── archived/                 # legacy Dockerfiles (not built by CI)
├── ci/
│   ├── registry.json
│   └── generate_matrix.py
└── .github/workflows/build-push.yml
```

**Add a new variant:** create a top-level `ncXX_phpY.Z/` with a `Dockerfile` (and optional `build.sh` for local use). CI picks it up automatically. Set `dev_latest_context` in `ci/registry.json` if it should own `passman-dev:latest`.

---

## Quick start (development)

Create TLS files once (self-signed is fine for localhost):

```bash
mkdir -p ~/passman-dev-docker && cd ~/passman-dev-docker
openssl req -newkey rsa:2048 -nodes -keyout key.pem -x509 -days 365 -out certificate.pem
```

Run the latest dev image (or pick a specific tag from the table above). Optionally add  
`-v /path/to/passman:/var/www/html/apps/passman` to use your local Passman clone.

```bash
docker run -d -p 8080:80 -p 8443:443 \
  -v ~/passman-dev-docker/certificate.pem:/etc/ssl/private/cert.pem \
  -v ~/passman-dev-docker/key.pem:/etc/ssl/private/privkey.pem \
  -v ~/passman-dev-docker/certificate.pem:/etc/ssl/private/fullchain.pem \
  --name passman-dev \
  binsky/passman-dev:latest

docker logs -f passman-dev
docker exec -it passman-dev bash
```

Open **https://localhost:8443** (HTTP also on port 8080).

Inside the container, Passman lives at `/var/www/html/apps/passman/` — run `grunt` / `grunt build` there on stacks that include the dev tooling.

### Mount Nextcloud via SSH (optional)

For full-tree IDE support:

1. Add your SSH public key to `/root/.ssh/authorized_keys` in the container.
2. Get the container IP: `docker exec passman-dev ip -4 addr show`.
3. On the host:

```bash
mkdir -p ~/passman-dev-docker/passman-nc-complete
sshfs root@<container-ip>:/var/www/html ~/passman-dev-docker/passman-nc-complete \
  -o idmap=user -o uid=1000 -o gid=1000

# unmount:
fusermount -u ~/passman-dev-docker/passman-nc-complete
```

## CI (GitHub Actions → Docker Hub)

Workflow file: [`.github/workflows/build-push.yml`](.github/workflows/build-push.yml)

### When it runs

| Event | Builds | Pushes to Docker Hub |
|-------|--------|----------------------|
| Push to `main` / `master` | Affected contexts only (see below) | Yes |
| Pull request | Same path logic | No (amd64 build only, smoke-test Dockerfiles) |
| Manual **workflow_dispatch** | All contexts if **rebuild all**; else changes since `HEAD~1` | Yes |

### What gets built

- **Matrix** is generated by [`ci/generate_matrix.py`](ci/generate_matrix.py) from every top-level directory that contains a `Dockerfile`.
- **Incremental builds:** only contexts with file changes under their directory are rebuilt.
- **Full rebuild** only when **`entrypoint.sh`** changes (shared by every image).
- Changing **`ci/registry.json`** rebuilds only the context named in **`dev_latest_context`** (to refresh the `passman-dev:latest` tag), not every stack.
- Changes to other **`ci/`** or **`.github/`** files do not trigger image builds; use manual **workflow_dispatch → rebuild all** if you need a full republish after pipeline edits.
- Per context:
  - **`passman-dev`** — always (final stage, or `dev` stage when multi-stage).
  - **`passman-demo`** — only if the Dockerfile has `FROM … AS demo`.
- Tags and Hub repo names come from [`ci/registry.json`](ci/registry.json) (`dev_latest_context` → `passman-dev:latest`).

### Multi-architecture (no QEMU)

On push, three job types run:

1. **`build-amd64`** — `ubuntu-latest`, `linux/amd64`, pushes `…:<tag>-amd64`
2. **`build-arm64`** — `ubuntu-24.04-arm`, `linux/arm64`, pushes `…:<tag>-arm64`
3. **`merge-manifests`** — `docker buildx imagetools create` so public tags (`nc33_php8.4`, `latest`, …) are **manifest lists** for amd64 + arm64

`docker pull binsky/passman-dev:latest` then works on both Intel/AMD and ARM64 Macs/servers.

**Private repositories:** GitHub’s free `ubuntu-24.04-arm` runners may be unavailable; point `build-arm64` at a self-hosted ARM runner label in the workflow.

### Secrets (repository settings)

| Secret | Purpose |
|--------|---------|
| `DOCKERHUB_USERNAME` | Docker Hub login |
| `DOCKERHUB_TOKEN` | Access token (recommended, not account password) |

### Local builds

Each context may ship a `build.sh` that copies `entrypoint.sh` and runs `docker build` (see `nc34_php8.5/build.sh` for dev + demo targets). CI does not use `build.sh`; it invokes Buildx directly with the same contexts.
