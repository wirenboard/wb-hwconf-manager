hook_module_add() {
	hook_once_after_config_change "service_restart_delete_retained wb-mqtt-gpio /devices/wb-gpio/#"
}

hook_module_del() {
	stop_service_and_schedule_restart "wb-mqtt-gpio" "/devices/wb-gpio/#"
	# Remove all the added gpios
	wb_gpio_del $(seq $GPIO_BASE $[GPIO_BASE+WBIO_COUNT-1])
}
