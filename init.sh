#!/bin/bash

. /usr/lib/wb-hwconf-manager/functions.sh

NO_RESTART_SERVICE="yes" wb-hwconf-helper config-apply

grep "$CONFIGFS" /proc/mounts >/dev/null 2>&1 || {
	echo "$CONFIGFS not mounted, skipping modules initialization"
	return 1
}

CONFIG="/etc/wb-hardware.conf"
OLD_CONFIG=`mktemp`
cat "$CONFIG" | /usr/lib/wb-hwconf-manager/config.py -o > "$OLD_CONFIG" || {
	rm "$OLD_CONFIG"
	exit 1
}
CONFIG="$OLD_CONFIG"

cat "$CONFIG_STATE" | while read SLOT MODULE OPTIONS_HASH; do
	[[ -z "$SLOT" || -z "$MODULE" ]] && continue
	module_init "$SLOT" "$MODULE"
done

rm "$OLD_CONFIG"
