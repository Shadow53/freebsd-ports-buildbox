#! /bin/sh

VAGRANT_ROOT="/vagrant"

setup_pkg() {
    mkdir -p /usr/local/etc/pkg/repos
    cp -f $VAGRANT_ROOT/FreeBSD.conf /usr/local/etc/pkg/repos/FreeBSD.conf
    pkg upgrade -y
}

setup_poudriere() {
    mkdir -p /var/cache/ccache/poudriere
    pkg install -y poudriere ccache
    cp -f $VAGRANT_ROOT/poudriere.conf /usr/local/etc/poudriere.conf
}

setup_portshaker() {
    pkg install -y portshaker
}

setup_nginx() {
    pkg install -y nginx
    cp -f $VAGRANT_ROOT/nginx-logs.conf /usr/local/etc/nginx/conf.d/nginx.conf
    service nginx enable
    service nginx start
}

setup_pkg
setup_poudriere
setup_nginx
