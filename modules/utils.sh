eval "`slot_get_vars $SLOT`"
local SLOT_TYPE=${SLOT%%[0-9]}
local SLOT_NUM=${SLOT#$SLOT_TYPE}

CONFIG_GPIO=${CONFIG_GPIO:-/etc/wb-homa-gpio.conf}

# Waits until given path become available, with timeout
# Args:
# - path
# - timeout (seconds). if not given - 5 sec.
wait_for_path() {
	local i
	local path=$1
	local timeout=${2:-5}
	for ((i=0; i<timeout*2; i++)); do
		[[ -e "$path" ]] && return 0
		sleep 0.5
	done
	return 1
}

# Add GPIO to the wb-homa-gpio driver config
# Args:
# - gpio name (for mqtt)
# - gpio number (as in /sys/class/gpio)
# - direction - "input" or "output"
# - polarity - "active-high" or "active-low" (inverted)
# These 4 args can be repeated multiple times to add many gpios at once
wb_gpio_add() {
	local JSON=$CONFIG_GPIO
	local items=()
	while [[ $# -ge 3 ]]; do
		[[ -n "$1" && -n "$2" && -n "$3" && -n "$4" ]] || {
			die "Bad arguments"
			return 1
		}
		local inverted="false"
		[[ "$4" == "active-low" ]] && {
			inverted="true"
		}
		wb_gpio_del $2
		items+=( "{name: \"$1\", gpio: $2, direction: \"$3\", inverted: $inverted}" )
		shift 4
	done

	json_array_append ".channels" "${items[@]}"
}

# Remove GPIO from the wb-homa-gpio driver config
# Args:
# - gpio number (as in /sys/class/gpio)
wb_gpio_del() {
	local JSON=$CONFIG_GPIO
	json_array_delete ".channels" \
		". as \$chan | ([$(join ', ' "$@")] | map(. == \$chan.gpio) | any)"
}

# Get maximum number of slot with given prefix that is present in config
# Args:
# - slot id prefix
wb_max_slot_num() {
	jq '
		[ .slots[].id | select(startswith("'$1'")) ] |
		map(ltrimstr("'$1'") | tonumber) |
		max
	' "$CONFIG"
}
# Get i2c device number by name
# Args:
# - i2c device name
i2c_bus_num() {
	local bus_name="$1"
	[[ -z "$bus_name" ]] && return 1
	grep -l "^${bus_name}$" /sys/bus/i2c/devices/i2c-*/name |  grep -Po '(?<=i2c-)(\d+)'
}

slot_i2c_bus_num() {
	local bus_name=$(sed -rn "s/.*(mod[0-9]+)$/\1_i2c@0/p" <<< "$SLOT")
	[[ -z "$bus_name" ]] && return 1
	grep -l "^${bus_name}$" /sys/bus/i2c/devices/i2c-*/name |  grep -Po '(?<=i2c-)(\d+)'
}

slot_i2c_bus_sysfs() {
	local num=$(slot_i2c_bus_num)
	[[ -z "$num" ]] && return 1
	echo "/sys/bus/i2c/devices/i2c-${num}"
}

slot_i2c_dev_sysfs() {
	local bus=$(slot_i2c_bus_num)
	[[ -z "$bus" ]] && return 1
	printf "/sys/bus/i2c/devices/%d-%0.4x" ${bus} 0x${1}
}

# Restarts given service if $NO_RESTART_SERVICE is not set.
# Args:
# - service name (from /etc/init.d/)
service_restart() {
	[[ -z "$NO_RESTART_SERVICE" ]] && service "$1" restart
}

# Restarts given service if $NO_RESTART_SERVICE is not set,
# and also deletes retained MQTT messages with supplied topic pattern.
# Args
# - service name (from /etc/init.d/)
# - MQTT topic to delete
service_restart_delete_retained() {
	[[ -z "$NO_RESTART_SERVICE" ]] && {
		service "$1" stop
		mqtt-delete-retained "$2"
		service "$1" start
	}
}

SYSFS_GPIO="/sys/class/gpio"

# Exports GPIO to sysfs
# Args
# - GPIO number
sysfs_gpio_export() {
	[[ -e "${SYSFS_GPIO}/gpio$1" ]] && return 0
	echo "$1" > "${SYSFS_GPIO}/export"
}

# Unexports GPIO from sysfs
# Args
# - GPIO number
sysfs_gpio_unexport() {
	[[ -e "${SYSFS_GPIO}/gpio$1" ]] || return 0
	echo "$1" > "${SYSFS_GPIO}/unexport"
}

# Set GPIO direction
# Args
# - GPIO number
# - Direction, "in" or "out"
sysfs_gpio_direction() {
	[[ "$2" == "in" || "$2" == "out" ]] || return 1
	echo "${2}" > "${SYSFS_GPIO}/gpio${1}/direction"
}

# Set GPIO state
# Args
# - GPIO number
# - Value (0/1)
sysfs_gpio_set() {
	sysfs_gpio_direction "$1" "out"
	echo "$2" > "${SYSFS_GPIO}/gpio${1}/value"
}
