#!/bin/bash

# SIGTERM-handler
term_handler() {
    service apache2 stop

    if [ -f /etc/init.d/mariadb ]; then
        service mariadb stop
    else
        service mysql stop
    fi

    exit 0
}

set -x

service ssh start

if [ -f /etc/init.d/mariadb ]; then
    service mariadb start
else
    service mysql start
fi

# Demo images bake config_is_read_only. Drop it only for this startup so the
# trusted-domain update below can write config.php, then lock again before Apache.
if [ "${PASSMAN_IMAGE_FLAVOR:-}" = "demo" ]; then
    /usr/local/bin/demo-config.sh unlock || exit 1
fi

sudo -u www-data php /var/www/html/occ app:disable ${NC_ENABLE_APP_ID:-passman}
sudo -u www-data php /var/www/html/occ app:enable ${NC_ENABLE_APP_ID:-passman}

if [ "$DEMO_EXTERNAL_FQDN" != "" ]; then
    sudo -u www-data php /var/www/html/occ config:system:set trusted_domains 5 --value=$DEMO_EXTERNAL_FQDN
    # force https usage/redirects for the demo when providing a custom fqdn (as as simple fix for the demo SCP issue)
    sudo -u www-data php /var/www/html/occ config:system:set overwriteprotocol --value=https
fi

if [ "${PASSMAN_IMAGE_FLAVOR:-}" = "demo" ]; then
    sudo -u www-data php /var/www/html/occ config:system:set config_is_read_only --type=boolean --value=true || exit 1
fi

if [ ! -f /etc/ssl/private/cert.pem ] || [ ! -f /etc/ssl/private/privkey.pem ]; then
    cp /etc/ssl/private/ssl-cert-snakeoil.key /etc/ssl/private/privkey.pem
    cp /etc/ssl/certs/ssl-cert-snakeoil.pem /etc/ssl/private/cert.pem
    cp /etc/ssl/certs/ssl-cert-snakeoil.pem /etc/ssl/private/fullchain.pem
fi

service apache2 start

trap 'kill ${!}; term_handler' SIGTERM

# wait forever
while true
do
    if [ -f /var/www/html/data/nextcloud.log ]; then
        tail -f /var/www/html/data/nextcloud.log & wait ${!}
    fi
    
    if [ -f /var/www/html/data-autotest/nextcloud.log ]; then
        tail -f /var/www/html/data-autotest/nextcloud.log & wait ${!}
    fi
done
