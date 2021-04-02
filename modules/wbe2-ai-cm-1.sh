source "$DATADIR/modules/utils.sh"

hook_module_init() {
	modprobe ina2xx
}

hook_module_deinit() {
	rmmod ina2xx
}

hook_module_add() {
	jq '.enable = true' /etc/wbe2-ai-cm-1.conf | sponge /etc/wbe2-ai-cm-1.conf
	hook_once_after_config_change "service_restart_delete_retained wb-rules /devices/wbe2-ai-cm-1/#"
}

hook_module_del() {
	jq '.enable = false' /etc/wbe2-ai-cm-1.conf | sponge /etc/wbe2-ai-cm-1.conf
	hook_once_after_config_change "service_restart_delete_retained wb-rules /devices/wbe2-ai-cm-1/#"
}
