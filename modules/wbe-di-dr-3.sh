source "$DATADIR/modules/utils.sh"

hook_module_add() {
	wb_gpio_add "MOD${SLOT_NUM}_IN1" $GPIO_SDA input
	wb_gpio_add "MOD${SLOT_NUM}_IN2" $GPIO_SCL input
	wb_gpio_add "MOD${SLOT_NUM}_IN3" $GPIO_CS input
}

hook_module_del() {
	wb_gpio_del $GPIO_SDA
	wb_gpio_del $GPIO_SCL
	wb_gpio_del $GPIO_CS
}

hook_once_after_config_change "service wb-homa-gpio restart"
