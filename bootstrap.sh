#!/bin/sh

VAGRANT_ROOT="/vagrant"

setup_pkg() {
    mkdir -p /usr/local/etc/pkg/repos
    cp -f $VAGRANT_ROOT/FreeBSD.conf /usr/local/etc/pkg/repos/FreeBSD.conf
    pkg upgrade -yf
}

setup_poudriere() {
    mkdir -p /var/cache/ccache/poudriere
    pkg install -y poudriere ccache dialog4ports
    cp -f $VAGRANT_ROOT/poudriere.conf /usr/local/etc/poudriere.conf
}

setup_portshaker() {
    pkg install -y portshaker
}

setup_nginx() {
    pkg install -y nginx
    cp -f $VAGRANT_ROOT/nginx.conf /usr/local/etc/nginx/nginx.conf
    service nginx enable
    service nginx start
}

setup_ports() {
    pkg install -y tmux rsync
    cp $VAGRANT_ROOT/ports /usr/local/bin/ports
    chmod 0755 /usr/local/bin/ports
}

setup_pkg
setup_poudriere
setup_nginx
setup_ports
