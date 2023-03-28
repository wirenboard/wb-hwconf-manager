source "$DATADIR/modules/utils.sh"

hide_modem_connections() {
	[[ -f "/usr/lib/wb-nm-helper/wb-hide-connection" ]] && {
		for conn_id in wb-gsm-sim1 wb-gsm-sim2; do
			/usr/lib/wb-nm-helper/wb-hide-connection $conn_id "$1"
		done
	}
}

hook_module_add() {
	hide_modem_connections ""
	hook_once_after_config_change "service_restart wb-gsm"
}

hook_module_del() {
	hide_modem_connections "true"
	[[ -z "$NO_RESTART_SERVICE" ]] && {
		systemctl stop wb-gsm || true
	}
}
