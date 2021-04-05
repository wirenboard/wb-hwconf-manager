source "$DATADIR/modules/utils.sh"

hook_module_init() {
	modprobe ina2xx
}

hook_module_deinit() {
	rmmod ina2xx
}
