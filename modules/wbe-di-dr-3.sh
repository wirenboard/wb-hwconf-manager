source "$DATADIR/modules/utils.sh"

hook_module_add() {
	wb_gpio_add "MOD${SLOT_NUM}_IN1" $GPIO_SDA input active-high
	wb_gpio_add "MOD${SLOT_NUM}_IN2" $GPIO_SCL input active-high
	wb_gpio_add "MOD${SLOT_NUM}_IN3" $GPIO_CS input active-high
	hook_once_after_config_change "service_restart_delete_retained wb-homa-gpio /devices/wb-gpio/#"
}

hook_module_del() {
	wb_gpio_del $GPIO_SDA
	wb_gpio_del $GPIO_SCL
	wb_gpio_del $GPIO_CS
	hook_once_after_config_change "service_restart_delete_retained wb-homa-gpio /devices/wb-gpio/#"
}
