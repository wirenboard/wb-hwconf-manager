source "$DATADIR/modules/utils.sh"

hook_module_add() {
	bus_num=$(readlink -f /dev/i2c-mod${SLOT_NUM} | sed -r 's/^\/dev\/i2c-//')
	mkdir -p /var/lib/wb-mqtt-tlv493/conf.d/
	echo "{'bus_num': $bus_num}" > /var/lib/wb-mqtt-tlv493/conf.d/wb-mqtt-tlv493.conf
	systemctl restart wb-mqtt-tlv493 || true
}

hook_module_del() {
	rm /var/lib/wb-mqtt-tlv493/conf.d/wb-mqtt-tlv493.conf || true
	systemctl restart wb-mqtt-tlv493 || true
}
