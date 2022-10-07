source "$DATADIR/modules/utils.sh"

local CONFIG_SERIAL=${CONFIG_SERIAL:-/etc/wb-mqtt-serial.conf}

hook_module_init() {
	sysfs_gpio_export $GPIO_RTS
	sysfs_gpio_direction $GPIO_RTS out

	sysfs_gpio_set $GPIO_RTS 0  # setting lora module to working mode
}

hook_module_deinit() {
	sysfs_gpio_direction $GPIO_RTS in
	sysfs_gpio_unexport $GPIO_RTS
}

hook_module_add() {  # lora chip supports only 9600-8-N-1 settings
	local JSON=$CONFIG_SERIAL
	json_array_update ".ports" ".path == \"/dev/ttyMOD${SLOT_NUM}\"" ".enabled = true |
		.stop_bits = 1 |
		.baud_rate = 9600 |
		.parity = \"N\" |
		.data_bits = 8 |
		.response_timeout_ms = 8000"  # to prevent red-coloring of devices in webui
}

hook_module_del() {  # restoring default settings (9600-8-N-2; disabled; default response_timeout_ms)
	local JSON=$CONFIG_SERIAL
	json_array_update ".ports" ".path == \"/dev/ttyMOD${SLOT_NUM}\"" ".enabled = false |
		.stop_bits = 2 |
		.baud_rate = 9600 |
		.parity = \"N\" |
		.data_bits = 8 |
		.devices = []"
	json_edit "del(.ports[] | select(.path == \"/dev/ttyMOD${SLOT_NUM}\") | .response_timeout_ms)"

    hook_once_after_config_change "service_restart wb-mqtt-serial"
}
