source "$DATADIR/modules/utils.sh"

hook_module_init() {
	sysfs_gpio_export $GPIO_RS485_FS
	sysfs_gpio_direction $GPIO_RS485_FS out

	local bias_mode="$(config_module_option ".mode")"
	if [ "$bias_mode" = "disabled" ]
	then
		echo "failsafe bias disabled"
		sysfs_gpio_set $GPIO_RS485_FS 0
	else
		echo "failsafe bias enabled"
		sysfs_gpio_set $GPIO_RS485_FS 1
	fi
}

hook_module_deinit() {
	sysfs_gpio_direction $GPIO_RS485_FS in
	sysfs_gpio_unexport $GPIO_RS485_FS
}