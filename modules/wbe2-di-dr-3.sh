source "$DATADIR/modules/utils.sh"

hook_module_add() {
	wb_gpio_add "MOD${SLOT_NUM}_IN1" $GPIO_TX input active-high
	wb_gpio_add "MOD${SLOT_NUM}_IN2" $GPIO_RX input active-high
	wb_gpio_add "MOD${SLOT_NUM}_IN3" $GPIO_RTS input active-high
	hook_once_after_config_change "service_restart_delete_retained wb-homa-gpio /devices/wb-gpio/#"
}

hook_module_del() {
	wb_gpio_del $GPIO_TX
	wb_gpio_del $GPIO_RX
	wb_gpio_del $GPIO_RTS
	hook_once_after_config_change "service_restart_delete_retained wb-homa-gpio /devices/wb-gpio/#"
}

hook_module_deinit() {
    echo $GPIO_TX > /sys/class/gpio/unexport 2>/dev/null || true
    echo $GPIO_RX > /sys/class/gpio/unexport 2>/dev/null || true
    echo $GPIO_RTS > /sys/class/gpio/unexport 2>/dev/null || true
}
