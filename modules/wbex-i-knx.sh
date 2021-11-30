source "$DATADIR/modules/utils.sh"

wb_knxd_config_service_active() {
    # this will also fail when wb-knxd-config is not installed / not a service
    systemctl is-active wb-knxd-config.service >/dev/null
}

hook_module_init() {
	ln -s /dev/ttyMOD${SLOT_NUM} /dev/ttyKNX${SLOT_NUM}
	if [[ ! -e /dev/ttyKNX ]]; then
		ln -s /dev/ttyMOD${SLOT_NUM} /dev/ttyKNX	
	fi

	if wb_knxd_config_service_active; then
		systemctl restart wb-knxd-config.service
	fi
}

hook_module_deinit() {
	rm -f /dev/ttyKNX${SLOT_NUM}
	if [[ $(readlink /dev/ttyKNX) == "/dev/ttyMOD${SLOT_NUM}" ]]; then
		rm -f /dev/ttyKNX	
	fi

	if wb_knxd_config_service_active; then
		systemctl restart wb-knxd-config.service
	fi
}
