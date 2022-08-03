source "$DATADIR/modules/utils.sh"
source "$DATADIR/modules/can-common.sh"

hook_module_init() {
	is_errwb730001_check_and_warn && return 0

	sysfs_gpio_export $GPIO_RS485_FS
	sysfs_gpio_direction $GPIO_RS485_FS out
	sysfs_gpio_direction $GPIO_RS485_FS 0

	sysfs_gpio_export $GPIO_CAN_EN
	sysfs_gpio_direction $GPIO_CAN_EN out
	sysfs_gpio_set $GPIO_CAN_EN 1

	sysfs_gpio_export $GPIO_RS485_RTS
	sysfs_gpio_direction $GPIO_RS485_RTS out
	sysfs_gpio_set $GPIO_RS485_RTS 0

	sysfs_gpio_export $GPIO_RS485_TERM
	sysfs_gpio_direction $GPIO_RS485_TERM out

	local term_mode="$(config_module_option ".terminatorsMode")"
	if [ "$term_mode" = "disabled" ]
	then
		echo "terminators are disabled"
		sysfs_gpio_set $GPIO_RS485_TERM 0
	else
		echo "terminators are enabled"
		sysfs_gpio_set $GPIO_RS485_TERM 1
	fi
}

hook_module_deinit() {
	is_errwb730001_check_and_warn && return 0

	sysfs_gpio_direction $GPIO_CAN_EN in
	sysfs_gpio_unexport $GPIO_CAN_EN

	sysfs_gpio_direction $GPIO_RS485_FS in
	sysfs_gpio_unexport $GPIO_RS485_FS

	sysfs_gpio_direction $GPIO_RS485_RTS in
	sysfs_gpio_unexport $GPIO_RS485_RTS

	sysfs_gpio_direction $GPIO_RS485_TERM in
	sysfs_gpio_unexport $GPIO_RS485_TERM
}
