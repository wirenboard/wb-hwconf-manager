source "$DATADIR/modules/utils.sh"

local CONFIG_SERIAL=${CONFIG_SERIAL:-/etc/wb-mqtt-serial.conf}

hook_module_init() {
	sysfs_gpio_export $GPIO_RTS
	sysfs_gpio_direction $GPIO_RTS out

	sysfs_gpio_set $GPIO_RTS 0
}

hook_module_deinit() {
	sysfs_gpio_direction $GPIO_RTS in
	sysfs_gpio_unexport $GPIO_RTS
}

hook_module_add() {
	local JSON=$CONFIG_SERIAL
	json_array_update ".ports" ".path == \"/dev/ttyMOD${SLOT_NUM}\"" ".enabled = true |
		.stop_bits = 1 |
		.baud_rate = 9600 |
		.parity = \"N\" |
		.data_bits = 8"
}

hook_module_del() {
	local JSON=$CONFIG_SERIAL
	json_array_update ".ports" ".path == \"/dev/ttyMOD${SLOT_NUM}\"" ".enabled = false |
		.stop_bits = 2 |
		.baud_rate = 9600 |
		.parity = \"N\" |
		.data_bits = 8 |
		.devices = []"
}
