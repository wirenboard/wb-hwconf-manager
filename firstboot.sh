#!/bin/bash
CONFFILE=/var/lib/wb-hwconf-manager/system.conf

[[ -s $CONFFILE ]] && exit 0

. /usr/lib/wb-hwconf-manager/functions.sh

is_live_system && {
    CONFFILE_DIST=`get_dist_conffile`
    cat "$CONFFILE_DIST" > $CONFFILE
}
