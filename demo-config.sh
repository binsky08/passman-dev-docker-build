#!/bin/bash
# Demo-only Nextcloud lockdown. The dev stage runs `restore`.
# CI and build.sh copy this file into the image build context.

set -euo pipefail

# Enough for a password-manager demo, small enough that the public instance
# is not useful as a file host. Chunk size caps a single upload request.
DEMO_USER_QUOTA="100 MB"
DEMO_CHUNK_BYTES=10485760

# Dropped again by restore, except appstoreenabled (already off on dev images).
SYSTEM_KEYS=(
    knowledgebaseenabled
    updatechecker
    integrity.check.scheduled
    check_for_working_wellknown_setup
    appstoreenabled
    sharing.enable_share_mail
    files_external_allow_create_new_local
    upgrade.disable-web
    bulkupload.enabled
    files.chunked_upload.max_size
    config_is_read_only
)

occ() {
    sudo -u www-data -- php /var/www/html/occ "$@"
}

start_db() {
    if [ -f /etc/init.d/mariadb ]; then
        service mariadb start
    else
        service mysql start
    fi
}

stop_db() {
    if [ -f /etc/init.d/mariadb ]; then
        service mariadb stop
    else
        service mysql stop
    fi
}

each_user() {
    local uid
    local found=0
    local listing
    listing="$(occ user:list)"
    while IFS= read -r uid; do
        [ -n "$uid" ] || continue
        found=1
        "$@" "$uid"
    done < <(printf '%s\n' "$listing" | sed -n 's/^[[:space:]]*-[[:space:]]*\([^:]*\):.*/\1/p')
    if [ "$found" -ne 1 ]; then
        echo "demo-config: no Nextcloud users found" >&2
        exit 1
    fi
}

set_bool() {
    occ config:system:set "$1" --type=boolean --value="$2"
}

unlock_config() {
    php <<'PHP'
<?php
$file = '/var/www/html/config/config.php';
$src = file_get_contents($file);
if ($src === false) {
    fwrite(STDERR, "demo-config: cannot read config.php\n");
    exit(1);
}
$count = 0;
$updated = preg_replace(
    '/([\'"]config_is_read_only[\'"]\s*=>\s*)true\b/',
    '$1false',
    $src,
    1,
    $count
);
if ($count > 0 && is_string($updated)) {
    if (file_put_contents($file, $updated) === false) {
        fwrite(STDERR, "demo-config: cannot write config.php\n");
        exit(1);
    }
    chown($file, 'www-data');
    chgrp($file, 'www-data');
}
PHP
}

harden() {
    start_db
    set_bool knowledgebaseenabled false
    set_bool updatechecker false
    set_bool integrity.check.scheduled false
    set_bool check_for_working_wellknown_setup false
    set_bool appstoreenabled false
    set_bool sharing.enable_share_mail false
    set_bool files_external_allow_create_new_local false
    set_bool upgrade.disable-web true
    set_bool bulkupload.enabled false
    occ config:system:set files.chunked_upload.max_size --type=integer --value="$DEMO_CHUNK_BYTES"
    occ config:app:set files_sharing shareapi_enabled --value=no
    occ config:app:set files default_quota --value="$DEMO_USER_QUOTA"
    each_user apply_user_quota
    set_bool config_is_read_only true
    stop_db
}

apply_user_quota() {
    occ user:setting "$1" files quota "$DEMO_USER_QUOTA"
}

restore() {
    start_db
    unlock_config
    local key
    for key in "${SYSTEM_KEYS[@]}"; do
        if [ "$key" = "appstoreenabled" ]; then
            continue
        fi
        occ config:system:delete "$key"
    done
    occ config:app:set files_sharing shareapi_enabled --value=yes
    occ config:app:delete files default_quota
    each_user clear_user_quota
    stop_db
}

clear_user_quota() {
    occ user:setting "$1" files quota none
}

case "${1:-}" in
    harden) harden ;;
    restore) restore ;;
    unlock) unlock_config ;;
    *)
        echo "usage: demo-config.sh harden|restore|unlock" >&2
        exit 1
        ;;
esac
