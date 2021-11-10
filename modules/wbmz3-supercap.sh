source "$DATADIR/modules/wbmz-supercap-common.sh"

hook_module_add() {
	hook_once_after_config_change "service_restart_delete_retained wb-homa-gpio /devices/wb-gpio/#"
}
