source "$DATADIR/modules/utils.sh"

hook_module_init() {
	bus_num=$(readlink -f /dev/i2c-mod${SLOT_NUM} | sed -r 's/^\/dev\/i2c-//')
	echo "{'bus_num': $bus_num}" > /var/lib/wb-mqtt-tlv493/conf.d/wb-mqtt-tlv493.conf
	systemctl restart wb-mqtt-tlv493 || true
}

hook_module_deinit() {
	rm /var/lib/wb-mqtt-tlv493/conf.d/wb-mqtt-tlv493.conf
	systemctl restart wb-mqtt-tlv493 || true
}
