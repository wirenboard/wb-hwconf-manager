source "$DATADIR/modules/utils.sh"

hook_module_init() {
    DEBUG=true wb-gsm on
}

hook_module_deinit() {
    DEBUG=true wb-gsm off
}
