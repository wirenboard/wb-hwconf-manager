source "$DATADIR/modules/utils.sh"

hook_module_add() {
	sysfs_gpio_export $GPIO_CAN_EN
	sysfs_gpio_set $GPIO_CAN_EN 1

	sysfs_gpio_export $GPIO_RS485_FS

	local bias_mode="$(config_module_option ".mode")"
	if [ "$bias_mode" = "enabled" ]
	then
		echo "failsafe bias enabled"
		sysfs_gpio_set $GPIO_RS485_FS 0
	else
		echo "failsafe bias enabled"
		sysfs_gpio_direction $GPIO_RS485_FS in
	fi

	echo "++++ failsafe gpio is: $GPIO_RS485_FS"
}

hook_module_del() {
	sysfs_gpio_direction $GPIO_CAN_EN in
	sysfs_gpio_unexport $GPIO_CAN_EN

	sysfs_gpio_direction $GPIO_RS485_FS in
	sysfs_gpio_unexport $GPIO_RS485_FS
}