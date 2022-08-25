source "$DATADIR/modules/utils.sh"

hook_module_add() {
	hook_once_after_config_change "service_start wb-gsm"
}

hook_module_del() {
	systemctl stop wb-gsm || true
}
