source "$DATADIR/modules/utils.sh"

service_name="wb-mqtt-tlv493"

hook_module_init() {
	systemctl is-active wb-hwconf-manager && systemctl stop $service_name || true
	bus_num=$(readlink -f /dev/i2c-mod${SLOT_NUM} | sed -r 's/^\/dev\/i2c-//')
	mkdir -p "/var/lib/${service_name}/conf.d/"
	echo "{'bus_num': $bus_num}" > "/var/lib/${service_name}/conf.d/wb-mqtt-tlv493.conf"
	systemctl is-active wb-hwconf-manager && systemctl restart $service_name || true
}

hook_module_deinit() {
	systemctl is-active wb-hwconf-manager && systemctl stop $service_name || true
	rm /var/lib/wb-mqtt-tlv493/conf.d/wb-mqtt-tlv493.conf || true
	systemctl is-active wb-hwconf-manager && systemctl restart $service_name || true
}
