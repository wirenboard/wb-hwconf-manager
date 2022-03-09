source "$DATADIR/modules/utils.sh"

hook_module_add() {
	jq '.enable = true' /etc/wbmz2-battery.conf | sponge /etc/wbmz2-battery.conf
	hook_once_after_config_change "service_restart_delete_retained wb-rules /devices/wbmz2-battery/#"
}

hook_module_del() {
	jq '.enable = false' /etc/wbmz2-battery.conf | sponge /etc/wbmz2-battery.conf
	hook_once_after_config_change "service_restart_delete_retained wb-rules /devices/wbmz2-battery/#"
}

hook_module_init() {
	local bus=$(i2c_bus_num "wbmz2_i2c_0")
	[[ -z "$bus" ]] && return 1
	jq '.bus = '$bus /etc/wbmz2-battery.conf | sponge /etc/wbmz2-battery.conf
	local bias_mode="$(config_module_option ".resetButon")"
	if [ "$bias_mode" = "disabled" ]
	then
		jq '.resetButon = false' /etc/wbmz2-battery.conf | sponge /etc/wbmz2-battery.conf
	else
		jq '.resetButon = true' /etc/wbmz2-battery.conf | sponge /etc/wbmz2-battery.conf
	fi
}
