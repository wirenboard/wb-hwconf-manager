source "$DATADIR/modules/utils.sh"

hook_module_init() {
	service wb-homa-ism-radio restart || true
}

# here must be deinit hook, but it call before remove overlay. so when we switch to onboard rfm module it will not work until controller reboot
