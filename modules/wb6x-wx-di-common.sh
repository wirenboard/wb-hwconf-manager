source "$DATADIR/modules/utils.sh"

hook_module_add() {
	wb_gpio_add "W${SLOT_NUM}_IN" $GPIO_DATA input active-low
	hook_once_after_config_change "service_restart_delete_retained wb-homa-gpio /devices/wb-gpio/#"
}

hook_module_del() {
	wb_gpio_del $GPIO_DATA
	hook_once_after_config_change "service_restart_delete_retained wb-homa-gpio /devices/wb-gpio/#"
}

hook_module_deinit() {
	echo $GPIO_DATA > /sys/class/gpio/unexport 2>/dev/null || true
}
