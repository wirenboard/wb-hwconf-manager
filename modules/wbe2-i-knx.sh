source "$DATADIR/modules/utils.sh"

hook_module_init() {
	if [[ -e /dev/ttyKNX ]]; then
		ln -s /dev/ttyMOD${SLOT_NUM} /dev/ttyKNX${SLOT_NUM}
	else
		ln -s /dev/ttyMOD${SLOT_NUM} /dev/ttyKNX
	fi
}

hook_module_deinit() {
	if [[ -e /dev/ttyKNX${SLOT_NUM} ]]; then
		rm -f /dev/ttyKNX${SLOT_NUM}
	else
		rm -f /dev/ttyKNX
	fi
}
