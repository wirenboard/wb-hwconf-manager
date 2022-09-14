source "$DATADIR/modules/utils.sh"

hook_module_add() {
	hook_once_after_config_change "service_restart wb-gsm"
}

hook_module_del() {
	[[ -z "$NO_RESTART_SERVICE" ]] && {
		systemctl stop wb-gsm || true
	}
}
