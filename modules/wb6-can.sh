source "$DATADIR/modules/utils.sh"

hook_module_init() {
	sysfs_gpio_export $GPIO_CAN_OFF
	sysfs_gpio_set $GPIO_CAN_OFF 0
	
	sysfs_gpio_export $GPIO_RS485_RTS
	sysfs_gpio_set $GPIO_RS485_RTS 0
}

hook_module_deinit() {
	sysfs_gpio_direction $GPIO_CAN_OFF in
	sysfs_gpio_unexport $GPIO_CAN_OFF

	sysfs_gpio_direction $GPIO_RS485_RTS in
	sysfs_gpio_unexport $GPIO_RS485_RTS
}
