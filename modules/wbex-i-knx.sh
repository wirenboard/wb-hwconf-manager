source "$DATADIR/modules/utils.sh"

hook_module_init() {
	ln -s /dev/ttyMOD${SLOT_NUM} /dev/ttyKNX${SLOT_NUM}
	if [[ ! -e /dev/ttyKNX ]]; then
		ln -s /dev/ttyMOD${SLOT_NUM} /dev/ttyKNX	
	fi	
}

hook_module_deinit() {
	rm -f /dev/ttyKNX${SLOT_NUM}
	if [[ $(readlink /dev/ttyKNX) == "/dev/ttyMOD${SLOT_NUM}" ]]; then
		rm -f /dev/ttyKNX	
	fi
}
