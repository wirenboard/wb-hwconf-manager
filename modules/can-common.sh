is_errwb730001_check_and_warn() {
    local compat=`tr < /proc/device-tree/compatible  '\000' '\n' | head -n1`
    if [[ "$compat" = "wirenboard,wirenboard-730" ]]; then
        echo "ERROR: CAN bus on RS-485-2 is disabled because of ERRWB730001 error"
        echo "ERROR: See https://wirenboard.com/wiki/WB_7:_Errata for details"
        return 0;
    fi
    return 1
}
