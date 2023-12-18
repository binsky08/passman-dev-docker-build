# A docker based development environment for passman

Based on ubuntu images, this repository provides Nextcloud installations with mariadb-server and php7 or php8.

Brings support to run `grunt` / `grunt build` at /var/www/html/apps/passman/ to generate js and css files

User: admin

Password: admin

Pull images from: [https://hub.docker.com/r/binsky/passman-dev](https://hub.docker.com/r/binsky/passman-dev)

Repository: [https://github.com/binsky08/passman-dev-docker-build](https://github.com/binsky08/passman-dev-docker-build)


## Available versions

| Nextcloud version | Base image | PHP version | Image:Tag |
|-------------------|--------------|------------|-------------|
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


## Getting started

```bash
mkdir ~/passman-dev-docker
cd ~/passman-dev-docker
openssl req -newkey rsa:2048 -nodes -keyout key.pem -x509 -days 365 -out certificate.pem

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
