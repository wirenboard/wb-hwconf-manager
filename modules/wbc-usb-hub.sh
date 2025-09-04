source "$DATADIR/modules/utils.sh"

GPIO_USB_POWER=$(gpioinfo "GSM ON" 2>/dev/null | awk '{print $2}') || GPIO_USB_POWER=132

hook_module_init() {
    systemctl stop wb-gsm || true

    sysfs_gpio_export $GPIO_USB_POWER
    sysfs_gpio_set $GPIO_USB_POWER 1
}

hook_module_deinit() {
    sysfs_gpio_unexport $GPIO_USB_POWER
}
