source "$DATADIR/modules/utils.sh"

hook_module_add() {
	hook_once_after_config_change "service_restart_delete_retained wb-homa-gpio /devices/wb-gpio/#"
}

hook_module_del() {
	wb_gpio_del $GPIO_PIN1_SCL
	wb_gpio_del $GPIO_PIN2_SDA
	hook_once_after_config_change "service_restart_delete_retained wb-homa-gpio /devices/wb-gpio/#"
}
