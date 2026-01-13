source "$DATADIR/modules/utils.sh"

hook_module_init() {
	sysfs_gpio_export $GPIO_RTS
	sysfs_gpio_direction $GPIO_RTS out

	local term_mode="$(config_module_option ".terminatorsMode")"
	if [ "$term_mode" = "disabled" ]
	then
		echo "terminators are disabled"
		sysfs_gpio_set $GPIO_RTS 0
	else
		echo "terminators are enabled"
		sysfs_gpio_set $GPIO_RTS 1
	fi
}

hook_module_deinit() {
	sysfs_gpio_direction $GPIO_RTS in
	sysfs_gpio_unexport $GPIO_RTS
}
