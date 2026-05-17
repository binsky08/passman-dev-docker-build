# A docker based development environment for passman

Based on ubuntu images, this repository provides Nextcloud installations with mariadb-server and php7 or php8.

Brings support to run `grunt` / `grunt build` at /var/www/html/apps/passman/ to generate js and css files

User: admin

Password: admin

Pull images from: [https://hub.docker.com/r/binsky/passman-dev](https://hub.docker.com/r/binsky/passman-dev)

Repository: [https://github.com/binsky08/passman-dev-docker-build](https://github.com/binsky08/passman-dev-docker-build)


## Available development versions

| Nextcloud version | Base image | PHP version | Image:Tag |
|-------------------|--------------|------------|-------------|
| 33 | ubuntu:24.04 | 8.4 | binsky/passman-dev:nc33_php8.4 |
| 32 | ubuntu:24.04 | 8.4 | binsky/passman-dev:nc32_php8.4 |
| 31 | ubuntu:24.04 | 8.4 | binsky/passman-dev:nc31_php8.4 |
| 31 | ubuntu:22.04 | 8.3 | binsky/passman-dev:nc31_php8.3 |
| 30 | ubuntu:22.04 | 8.3 | binsky/passman-dev:nc30_php8.3 |
| 29 | ubuntu:22.04 | 8.3 | binsky/passman-dev:nc29_php8.3 |
| 28 | ubuntu:22.04 | 8.3 | binsky/passman-dev:nc28_php8.3 |
| 28 | ubuntu:22.04 | 8.2 | binsky/passman-dev:nc28_php8.2 |
| 27 | ubuntu:22.04 | 8.2 | binsky/passman-dev:nc27_php8.2 |
| 27 | ubuntu:22.04 | 8.1 | binsky/passman-dev:nc27_php8.1 |
| 26 | ubuntu:22.04 | 8.1 | binsky/passman-dev:nc26_php8.1 |
| 25 | ubuntu:22.04 | 8.1 | binsky/passman-dev:nc25_php8.1 |
| 25 | ubuntu:22.04 | 8.0 | binsky/passman-dev:nc25_php8.0 |
| 24 | ubuntu:20.04 | 8.0 | binsky/passman-dev:nc24_php8.0 |
| 24 | ubuntu:20.04 | 7.4 | binsky/passman-dev:nc24_php7.4 |
| 23 | ubuntu:20.04 | 8.0 | binsky/passman-dev:nc23_php8.0 |
| 23 | ubuntu:20.04 | 7.4 | binsky/passman-dev:nc23_php7.4 |
| 22 | ubuntu:20.04 | 8.0 | binsky/passman-dev:nc22_php8 |
| 22 | ubuntu:20.04 | 7.4 | binsky/passman-dev:nc22_php7.4 |
| 21 | ubuntu:20.04 | 8.0 | binsky/passman-dev:nc21_php8 |
| 21 | ubuntu:20.04 | 7.4 | binsky/passman-dev:nc21 |
| 20 | ubuntu:20.04 | 7.4 | binsky/passman-dev:nc20 |

## Available demo versions

| Nextcloud version | Base image | PHP version | Image:Tag |
|-------------------|--------------|------------|-------------|
| 33 | ubuntu:24.04 | 8.4 | binsky/passman-demo:nc33_php8.4 |


## Getting started

```bash
mkdir ~/passman-dev-docker
cd ~/passman-dev-docker
openssl req -newkey rsa:2048 -nodes -keyout key.pem -x509 -days 365 -out certificate.pem

# edit and add the following line to the run command, to directly mount the passman repository folder as local docker volume mount
# -v /home/myuser/dev/passman:/var/www/html/apps/passman \

docker run -d -p 8080:80 -p 8443:443 \
    -v ~/passman-dev-docker/certificate.pem:/etc/ssl/private/cert.pem \
    -v ~/passman-dev-docker/key.pem:/etc/ssl/private/privkey.pem \
    -v ~/passman-dev-docker/certificate.pem:/etc/ssl/private/fullchain.pem \
    --name passman-dev-latest \
    binsky/passman-dev:latest

docker logs -f passman-dev-latest
docker exec -it passman-dev-latest /bin/bash

cd /var/www/html/apps/passman/
# here is the passman repository located
```

Open instance in browser: [https://localhost:8443](https://localhost:8443)


## Mount to local filesystem

- copy your ssh public key to /root/.ssh/authorized_keys
- type `ip a` in the container to get its ip address
- try to login

(Hint: the complete nextcloud folder will be mounted to enable IDE's autocompletion)

```
mkdir ~/passman-dev-docker/passman-nc-complete
sshfs root@172.17.0.3:/var/www/html ~/passman-dev-docker/passman-nc-complete -o idmap=user -o uid=1000 -o gid=1000

# unmount with
fusermount -u ~/passman-dev-docker/passman-nc-complete
```

## CI (GitHub Actions → Docker Hub)

Workflow: `.github/workflows/build-push.yml`. On push to `main` or `master`, it builds and pushes only the image contexts affected by the commit (each top-level directory that contains a `Dockerfile`). Changes under `entrypoint.sh`, `ci/`, or `.github/` trigger a full rebuild of every context. Pull requests run the same Docker builds with push disabled (single-arch **amd64** only so images can be loaded locally).

Pushes to Docker Hub publish **multi-architecture tags** (**`linux/amd64`** and **`linux/arm64`**) as one **manifest list** per public tag (`nc33_php8.4`, `latest`, etc.): native **amd64** builds on `ubuntu-latest` and **arm64** builds on GitHub’s **`ubuntu-24.04-arm`** hosts (same idea as a dedicated ARM runner on GitLab—no QEMU). CI first pushes per-arch tags (`…:-amd64`, `…:-arm64`), then runs **`docker buildx imagetools create`** so the unsuffixed tags point at both architectures.

Pull requests still build **amd64** only (validate Dockerfiles; no manifest job).

Repository secrets: **DOCKERHUB_USERNAME** and **DOCKERHUB_TOKEN**.

Manual runs: **Actions → Build and push container images → Run workflow**. **rebuild all** runs every context; leave it off to rebuild only images touched since the previous commit (`HEAD~1`…`HEAD`).

Config: `ci/registry.json` sets the Docker Hub namespace, repository names (`passman-dev` / `passman-demo`), and which context receives the rolling tag **`latest`** on `passman-dev` (`dev_latest_context`). Demo images are built automatically for any Dockerfile that defines a `demo` build stage (`FROM … AS demo`).

Adding a new variant: create a new directory with a `Dockerfile` (and optional `build.sh` for local use); CI picks it up without editing the workflow.
