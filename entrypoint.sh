#!/bin/bash

# SIGTERM-handler
term_handler() {
  service apache2 stop
  service mysql stop
  exit 0
}

set -x

service ssh start
service mysql start
service apache2 start

sudo -u www-data php /var/www/html/occ app:disable passman
sudo -u www-data php /var/www/html/occ app:enable passman

trap 'kill ${!}; term_handler' SIGTERM

# wait forever
while true
do
    tail -f /var/www/html/data/nextcloud.log & wait ${!}
done
