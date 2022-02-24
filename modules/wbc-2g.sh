source "$DATADIR/modules/utils.sh"

hook_module_init() {
	udevadm control --reload-rules && udevadm trigger  # /dev/ttyGSM symlink
}
