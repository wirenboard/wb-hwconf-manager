hook_module_add() {
	hook_once_after_config_change "service_restart_delete_retained wb-mqtt-gpio /devices/wb-gpio/#"
}

hook_module_del() {
	# Remove all the added gpios
	systemctl stop wb-mqtt-gpio || true
	wb_gpio_del $(seq $GPIO_BASE $[GPIO_BASE+WBIO_COUNT-1])
	hook_once_after_config_change "service_restart_delete_retained wb-mqtt-gpio /devices/wb-gpio/#"
}
