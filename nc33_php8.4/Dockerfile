# Nextcloud - passman - custom dev container
# since externally shipped apps have to be installed manually (see https://docs.nextcloud.com/server/latest/developer_manual/getting_started/devenv.html), these apps will be extra included:
# - nextcloud/viewer (usually a default core app; will be added to prevent getting flushed with errors during runtime)
# - https://github.com/nextcloud/notifications (usually a default core app; will be added since passman kinda depends on it)

FROM ubuntu:24.04 AS base

ENV SETUP_NEXTCLOUD_VERSION=stable33
ENV SETUP_NEXTCLOUD_VIEWER_BRANCH=stable33
ENV SETUP_NEXTCLOUD_NOTIFICATIONS_BRANCH=stable33
ENV SETUP_PHP_VERSION=php8.4
ENV SETUP_PHPUNIT_VERSION=12
ENV SETUP_PASSMAN_BRANCH=master
ENV SETUP_PASSMAN_REPO=https://github.com/nextcloud/passman

RUN /bin/bash -c "export DEBIAN_FRONTEND=noninteractive" && \
        /bin/bash -c "debconf-set-selections <<< 'tzdata    tzdata/Zones/Europe select  Madrid'" && \
        /bin/bash -c "echo \"Europe/Zurich\" > /etc/timezone " && \
        /bin/bash -c "ln -fs /usr/share/zoneinfo/`cat /etc/timezone` /etc/localtime" && \
        /bin/bash -c "debconf-set-selections <<< 'mariadb-server mysql-server/root_password password PASS'" && \
        /bin/bash -c "debconf-set-selections <<< 'mariadb-server mysql-server/root_password_again password PASS'" && \
        apt update && \
        apt install -y \
        apache2 \
        git \
        curl \
        mariadb-server \
        software-properties-common \
        wget \
        openssh-server \
        sudo

RUN /bin/bash -c "export DEBIAN_FRONTEND=noninteractive" && add-apt-repository -y ppa:ondrej/php
        
RUN /bin/bash -c "export DEBIAN_FRONTEND=noninteractive" && \
        apt install -y \
        libapache2-mod-${SETUP_PHP_VERSION} \
        ${SETUP_PHP_VERSION} \
        ${SETUP_PHP_VERSION}-mysql \
        ${SETUP_PHP_VERSION}-curl \
        ${SETUP_PHP_VERSION}-gd \
        ${SETUP_PHP_VERSION}-mbstring \
        ${SETUP_PHP_VERSION}-xml \
        ${SETUP_PHP_VERSION}-zip \
        ${SETUP_PHP_VERSION}-intl \
        ${SETUP_PHP_VERSION}-bcmath \
        ${SETUP_PHP_VERSION}-gmp \
        ${SETUP_PHP_VERSION}-imagick

RUN a2enmod ssl
RUN ln -s /etc/apache2/sites-available/default-ssl.conf /etc/apache2/sites-enabled
RUN git clone -b $SETUP_PASSMAN_BRANCH $SETUP_PASSMAN_REPO /var/www/passman
ADD https://raw.githubusercontent.com/nextcloud/travis_ci/master/before_install.sh /var/www/passman

RUN /bin/bash -c "export DEBIAN_FRONTEND=noninteractive" && \
        wget -O /usr/local/bin/phpunit https://phar.phpunit.de/phpunit-${SETUP_PHPUNIT_VERSION}.phar && \
        wget -O /usr/local/bin/composer https://getcomposer.org/download/latest-stable/composer.phar && \
        chmod +x /usr/local/bin/phpunit /usr/local/bin/composer

RUN mkdir /srv/nctemp && chown -R www-data:www-data /srv/nctemp


FROM base AS build

RUN service mariadb restart && \
    mysql -uroot -pPASS -e "SET PASSWORD = PASSWORD('');" && \
    sed  -i '0,/.*SSLCertificateChainFile.*/s/.*SSLCertificateChainFile.*/SSLCertificateChainFile \/etc\/ssl\/private\/fullchain.pem/' /etc/apache2/sites-enabled/default-ssl.conf && \
    sed -i '0,/.*ssl-cert-snakeoil.pem.*/s/.*ssl-cert-snakeoil.pem.*/SSLCertificateFile \/etc\/ssl\/private\/cert.pem/' /etc/apache2/sites-enabled/default-ssl.conf && \
    sed -i '0,/.*SSLCertificateKeyFile.*/s/.*SSLCertificateKeyFile.*/SSLCertificateKeyFile \/etc\/ssl\/private\/privkey.pem/' /etc/apache2/sites-enabled/default-ssl.conf && \
    echo "echo hhvm" > /bin/phpenv && chmod +x /bin/phpenv && \
    cd /var/www/passman && \
    chmod +x before_install.sh && \
    sleep 1 && \
    /bin/bash -c "./before_install.sh passman $SETUP_NEXTCLOUD_VERSION mysql; exit 0" && \
    rm /var/www/server/apps/passman/before_install.sh && \
    git clone --depth 1 -b $SETUP_NEXTCLOUD_VIEWER_BRANCH https://github.com/nextcloud/viewer.git /var/www/server/apps/viewer && \
    git clone --depth 1 -b $SETUP_NEXTCLOUD_NOTIFICATIONS_BRANCH https://github.com/nextcloud/notifications.git /var/www/server/apps/notifications && \
    mv /var/www/server/* /var/www/html/ && \
    rm -r /var/www/server && \
    chown -R www-data:www-data /var/www

RUN service mariadb restart && \
    cd /var/www/html/ && \
    chmod +x occ && \
    sed -i 's/\/var\/www\/server/\/var\/www\/html/g' /var/www/html/config/config.php && \
    ./occ check && \
    ./occ status && \
    ./occ app:list && \
    ./occ upgrade && \
    ./occ config:system:set defaultapp --value=passman && \
    ./occ config:system:set appstoreenabled --value=false && \
    ./occ config:system:set log_type --value=file && \
    ./occ config:system:set loglevel --value=1 && \
    ./occ config:system:set tempdirectory --value=/srv/nctemp && \
    ./occ config:system:set trusted_domains 2 --value=172.17.0.2 && \
    ./occ config:system:set trusted_domains 3 --value=10.0.2.2 && \
    ./occ config:system:set trusted_domains 4 --value=demo.passman.cc && \
    chown -R www-data:www-data /var/www


FROM base AS demo

COPY --from=build /var/www/html /var/www/html
COPY --from=build /var/lib/mysql /var/lib/mysql

EXPOSE 80
EXPOSE 443

COPY entrypoint.sh /
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
CMD []


FROM demo AS dev

RUN /bin/bash -c "export DEBIAN_FRONTEND=noninteractive" && \
        apt -y update && \
        apt install -y \
        npm 

RUN npm install -g sass grunt-cli
RUN cd /var/www/html/apps/passman && \
        npm install && \
        chown -R www-data:www-data /var/www/html/apps/passman

