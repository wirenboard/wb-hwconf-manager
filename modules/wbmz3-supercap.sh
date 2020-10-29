source "$DATADIR/modules/wbmz-supercap-common.sh"

hook_module_add() {
	wb_gpio_add "SUPERCAP_PRESENT" $GPIO_PIN1_SCL input active-low
	wb_gpio_add "SUPERCAP_DISCHARGING"  $GPIO_PIN2_SDA input active-low
	hook_once_after_config_change "service_restart_delete_retained wb-homa-gpio /devices/wb-gpio/#"
}
