source "$DATADIR/modules/utils.sh"

hook_module_add() {
	wb_gpio_add "MOD${SLOT_NUM}_OUT1" $GPIO_CS output active-high
	hook_once_after_config_change "service_restart_delete_retained wb-homa-gpio /devices/wb-gpio/#"
}

hook_module_del() {
	wb_gpio_del $GPIO_CS
	hook_once_after_config_change "service_restart_delete_retained wb-homa-gpio /devices/wb-gpio/#"
}
