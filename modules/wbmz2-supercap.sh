source "$DATADIR/modules/utils.sh"

hook_module_add() {
	echo "gpio pin1_scl  $GPIO_PIN1_SCL "
	echo "gpio pin2_sda  $GPIO_PIN2_SDA "
	wb_gpio_add "SUPERCAP_PRESENT" $GPIO_PIN1_SCL input active-low
	wb_gpio_add "SUPERCAP_DISCHARGING"  $GPIO_PIN2_SDA input active-high
	hook_once_after_config_change "service_restart_delete_retained wb-homa-gpio /devices/wb-gpio/#"
}

hook_module_del() {
	wb_gpio_del $GPIO_PIN1_SCL
	wb_gpio_del $GPIO_PIN2_SDA
	hook_once_after_config_change "service_restart_delete_retained wb-homa-gpio /devices/wb-gpio/#"
}

hook_module_deinit() {
    echo $GPIO_PIN1_SCL > /sys/class/gpio/unexport 2>/dev/null || true
    echo $GPIO_PIN2_SDA > /sys/class/gpio/unexport 2>/dev/null || true
}
