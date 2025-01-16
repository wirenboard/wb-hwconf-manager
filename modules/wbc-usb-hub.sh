source "$DATADIR/modules/utils.sh"

GPIO_USB_POWER=132

hook_module_init() {
    systemctl stop wb-gsm || true

	sysfs_gpio_export $GPIO_USB_POWER
	sysfs_gpio_direction $GPIO_USB_POWER out
    sysfs_gpio_set $GPIO_USB_POWER 1
}

hook_module_deinit() {
	sysfs_gpio_direction $GPIO_USB_POWER in
	sysfs_gpio_unexport $GPIO_USB_POWER
}
