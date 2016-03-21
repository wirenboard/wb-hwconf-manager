source "$DATADIR/modules/utils.sh"

hook_module_add() {
	hook_once_after_config_change "service_restart_delete_retained wb-homa-adc '/devices/wb-adc/#'"
}

hook_module_del() {
	hook_once_after_config_change "service_restart_delete_retained wb-homa-adc '/devices/wb-adc/#'"
}
