source "$DATADIR/modules/utils.sh"

hook_module_add() {
    hook_once_after_config_change "service_restart_delete_retained wb-mqtt-gpio /devices/wb-gpio/#"
}

hook_module_del() {
	stop_service_and_schedule_restart "wb-mqtt-gpio" "/devices/wb-gpio/#"
    wb_gpio_del ${!DO2_GPIO_K1}
    wb_gpio_del ${!DO2_GPIO_K2}
}
