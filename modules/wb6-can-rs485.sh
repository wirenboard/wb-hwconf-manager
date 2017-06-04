source "$DATADIR/modules/utils.sh"

hook_module_init() {
	sysfs_gpio_export $GPIO_CAN_OFF
	sysfs_gpio_set $GPIO_CAN_OFF 1
}

hook_module_deinit() {
	sysfs_gpio_direction $GPIO_CAN_OFF in
	sysfs_gpio_unexport $GPIO_CAN_OFF
}
