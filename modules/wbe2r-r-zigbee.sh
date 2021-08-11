source "$DATADIR/modules/utils.sh"

hook_module_init() {
	sysfs_gpio_export $GPIO_RTS
	sysfs_gpio_direction $GPIO_RTS out
	sysfs_gpio_set $GPIO_RTS 1
}

