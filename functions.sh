#!/bin/bash
DATADIR="/usr/share/wb-hwconf-manager"
CONFIG_STATE="/var/lib/wirenboard/hardware.state"

# Set this to any non-empty value to get some debug messages
DEBUG=""

# Set this to any non-empty value to redirect all non-debug output to syslog
SYSLOG=""
SYSLOG_TAG="wb-hwconf-manager"

VERBOSE="yes"
2>/dev/null . /lib/lsb/init-functions

. /usr/lib/wb-utils/wb_env.sh
wb_source "of"

MODULES="$DATADIR/modules"
SLOTS="$DATADIR/slots"

CONFIGFS="/sys/kernel/config"
OVERLAYS="$CONFIGFS/device-tree/overlays"

# List of hooks that is to be run when config changes is done
HOOKS_AFTER_CONFIG_CHANGE=()

debug() { :; }
if [[ -n "$DEBUG" ]]; then
	unset debug
	debug() {
		>&2 echo -e "[${FUNCNAME[2]}]$([[ -n "$SLOT" || -n "$MODULE" ]] && echo " $SLOT:$MODULE"): $*"
	}
fi

die() {
	debug "ERROR: $*"
	if [[ -n "$SYSLOG" ]]; then
		logger -p user.err -t "$SYSLOG_TAG" "$*"
	else
		log_failure_msg "$*"
	fi
	[[ $? == 0 ]] && return 1 || return $?
}

log() {
	if [[ -n "$SYSLOG" ]]; then
		logger -p user.info -t "$SYSLOG_TAG" "$*"
	else
		log_action_msg "$*"
	fi
}

# Use this to safely capture all unwanted data on stdout/stderr and
# redirect to syslog if needed.
# TODO?: ability to put stdout and stderr to different places
# (or just stop with NIH and look for some mainstream and time-proven utils lib)
catch_output() {
	if [[ -n "$SYSLOG" ]]; then
		2>&1 "$@" | logger -p user.info -t "$SYSLOG_TAG"
	else 
		"$@"
	fi	
}

# Join array to string
# Args:
# - delimiter
# - rest args are the array items
# Example: `join , 1 2 3` == "1,2,3"
join() {
	local IFS="$1"
	shift
	echo "$*"
}

################################################################################
# JSON handling functions
#
# It's expected that $JSON variable will contain the name of json file 
# that is to be processed
################################################################################

# Runs jq with given arguments and replaces the original file with result
# Example: json_edit '.foo = 123'
json_edit() {
	[[ -e "$JSON" ]] || {
		die "JSON file '$JSON' not found"
		return 1
	}

	local tmp=`mktemp`
	sed 's#//.*##' "$JSON" |	# there are // comments, strip them out
	jq "$@" > "$tmp"
	local ret=$?
	[[ "$ret" == 0 ]] && cat "$tmp" > "$JSON"
	rm "$tmp"
	return $ret
}

# Find item in array.
# Example: json_array_find '.slots' '.id == "foo"'
json_array_find() {
	[[ -e "$JSON" ]] || {
		die "JSON file '$JSON' not found"
		return 1
	}

	jq -e "${1}[] | select($2)" "$JSON"
}

# Append items to array
# Example: json_array_append '.slots' '{id: "foo", type: "bar", name: "baz"}'
json_array_append() {
	local array=$1
	shift
	json_edit "${array} = [${array}[], $(join ", " "$@")]"
}

# Delete matching array items
# Example: json_array_delete '.slots' '.id == "foo"'
json_array_delete() {
	json_edit "${1} = (${1} | map(select(($2) | not)))"
}

# Update matching array items
# Example: json_array_update '.slots' '.id == "foo"' '.module = "bar"'
#	this will set .module to "bar" for array items having .id == "foo"
json_array_update() {
	json_edit "${1} = (${1} | map(if ($2) then ($3) else . end))"
}

################################################################################
# Config handling functions
#
# It's expected that $CONFIG variable contains file name of the config.
################################################################################

# Return list of slots with associated module for each slot, if any.
# Each line of the output has form "slot module", module can be empty.
config_parse() {
	local SLOT MODULE OPTIONS
	jq -r '.slots[] | @text "\(.id) \(if (.module | length) > 0 then .module + " " + (.options | @text) else "" end)"' "$CONFIG" |
	while read SLOT MODULE OPTIONS; do
		[[ -n "$MODULE" ]] && SLOT+=" $MODULE $(md5sum <<< "$OPTIONS" | cut -f1 -d' ')"
		echo "$SLOT"
	done
}

# Return module that is associated with given slot.
# Args:
# - slot id
config_slot_module() {
	jq -r ".slots[] | select(.id == \"$1\") | .module" "$CONFIG"
}

# Add new slot to the config
# Args:
# - slot id (e.g. wb5-mod1)
# - slot type (e.g. wb5-mod)
# - slot description (arbitrary string)
config_slot_add() {
	local SLOT=$1
	local JSON=$CONFIG

	slot_get_filename >/dev/null || return 1

	json_array_find ".slots" ".id == \"$SLOT\"" >/dev/null && {
		die "Slot $SLOT already present in config"
		return 100
	}
	
	log "Adding slot $SLOT"
	json_array_append ".slots" \
		"{id: \"$1\", type: \"$2\", name: \"$3\", module: \"\"}"
}

# Delete given slot from the config
# Args:
# - slot id
config_slot_del() {
	local SLOT=$1
	local JSON=$CONFIG

	json_array_find >/dev/null ".slots" ".id == \"$SLOT\"" || {
		die "Slot $SLOT not present in config"
		return 100
	}
	
	local m=$(config_slot_module "$SLOT")
	[[ -n "$m" ]] && {
		die "Slot $SLOT is used by module $m, remove it first"
		return 101
	}

	log "Deleting slot $SLOT"
	json_array_delete ".slots" ".id == \"$SLOT\""
}

config_module_option() {
	jq -r ".slots[] | select(.id == \"$SLOT\") | .options$1" "$CONFIG"
}

config_module_options_hash() {
	config_module_option "" | md5sum | cut -f1 -d' '
}

################################################################################
# Slot/module manipulation functions
#
# By convention, global variables $SLOT and $MODULE are used to specify current
# slot and module, but some functions supports overriding them with arguments
################################################################################

# Get full path of the slot definition file
# Args:
# - slot id
slot_get_filename() {
	local slot=${1:-$SLOT}
	[[ -z "$slot" ]] && {
		die "SLOT is unset"
		return 1
	}

	slot="$SLOTS/${slot}.def"
	[[ -f "$slot" ]] || {
		die "Slot definition file ${slot} not found"
		return 1
	}

	echo "$slot"
}

# Get full path of the module definition file
# Args:
# - module id
module_get_filename() {
	local mod=${1:-$MODULE}
	[[ -z "$mod" ]] && {
		die "MODULE is unset"
		return 1
	}
	local ext=${2:-dtso}

	mod="$MODULES/${mod}.${ext}"
	[[ -f "$mod" ]] || {
		die "Module definition file ${mod} not found"
		return 1
	}

	echo "$mod"
}

# Get slot-specific shell variables definitions. Output supposed to be eval'd
# Example: eval "`slot_get_vars $SLOT`" - will set some local variables.
# Args:
# - slot id (optional, $SLOT env will be used if not specified)
slot_get_vars() {
	SLOT=${SLOT:-$1} slot_preprocess -DFROM_SHELL <<<"" | sed 's/#.*//; /^$/d'
}

# Preprocess stdin, applying per slot-specific definitions with C preprocessor.
slot_preprocess() {
	local slot=`slot_get_filename` || return 1

	cat "$slot" - |
	sed -r 's/#((\w+-)+cells)/__\1/' |
	tcc -x assembler-with-cpp \
		-Ulinux \
		-nostdinc \
		-I "$SLOTS" -I "$MODULES" "$@" -E - |
	perl -ne '
		next if m/^\s*(# |$)/;
		s/__COUNTER__/$n++/ge;
		s/__((\w+-)+cells)/#$1/g;
		print;'
}

# Feeds input through dtc compiler to produce dtb
dts_compile() {
	cat - | dtc -I dts -O dtb -@ -
}

# Adds valid dts header to stdin
dts_add_header() {
	echo '/dts-v1/; /plugin/;'
	cat -
}

# Preprocess module DTSO with slot definition to get DTBO suitable for feeding
# it to the kernel
dtbo_build() {
	local mod=`module_get_filename` || return 1

	cat "$mod" |
	dts_add_header |
	slot_preprocess |
	dts_compile
}

# Check if DTBO is compatible with the device.
# Args:
# - dtbo file
dtbo_check_compatible() {
	local dtbo_compat=`fdtget "$1" / compatible 2>/dev/null`
	[[ -z "$dtbo_compat" || "$dtbo_compat" == "unknown" ]] && return 0
	for compat in `tr < /proc/device-tree/compatible  '\000' '\n'`; do
		[[ "$dtbo_compat" == "$compat" ]] && return 0
	done
	return 1
}

# Run module hook, if it is defined.
# Possible hooks:
#	init
#		After DTBO loading (e.g. to initialize hardware on boot)
#	deinit
#		Before DTBO unloading (FIXME: unloading is not implemented)
#	add
#		After module was linked with some slot, runs only once
#		when config is changed. Can be used to reconfigure some other
#		services which is using the module.
#	del
#		After module was unlinked from its slot. See above.
# Args:
# - hook name (init/deinit/add/remove)
module_run_hook() {
	local func=hook_module_${1}
	local file="$MODULES/${MODULE}.sh"

	module_get_filename >/dev/null || return 1

	[[ -e "$file" ]] || {
		debug "No hooks script file"
		return 0
	}

	unset $func
	source $file
	local t=`type -t $func`
	[[ -n "$t" && "$t" == function ]] || {
		debug "Hook function $func is not defined"
		return 0
	}

	debug "Running $1 hook"
	$func
	local ret=$?
	unset $func
	return $ret
}

# Add hook to the list of hooks that is runned after config change.
# Each distinct hook is added only once even if added multiple times.
# Args:
# - bash command that should be run
hook_once_after_config_change() {
	local h
	for h in "${HOOKS_AFTER_CONFIG_CHANGE[@]}"; do
		[[ "$h" == "$1" ]] && return 0
	done
	HOOKS_AFTER_CONFIG_CHANGE+=("$1")
}

# Get configfs path for given slot/module
# Args (optional):
# - slot
# - module
overlay_path() {
	echo "$OVERLAYS/${SLOT:-$1}:${MODULE:-2}"
}

# Initialize module plugged to the slot.
# This builds DTBO, loads it into the kernel, and runs module hook 'init'
# Args:
# - slot
# - module
module_init() {
	local SLOT=$1
	local MODULE=$2

	local t=`echo "$OVERLAYS/$SLOT:"*`
	[[ -d "$t" ]] && {
		local m="${t#$OVERLAYS/$SLOT:}"
		local st="$(cat "$t/status")"
		case "$st" in
			"applied")
				[[ "$m" != "$MODULE" ]] && {
					die "Slot $SLOT is used by $m module"
					return 1
				}
				log_action_msg "Module $SLOT:$MODULE already initialized"
				return 0
				;;
			*)
				log_warning_msg "Overlay ${t#$OVERLAYS/} have status '$st', try to remove"
				rmdir "$t"
				;;
		esac
	}
	t=`echo "$OVERLAYS/$SLOT:"*`
	[[ -d "$t" ]] && {
		die "Overlays conflict on slot $SLOT"
		return 1
	}

	log_action_msg "Initializing $SLOT:$MODULE"

	local dtbo=`mktemp`
	dtbo_build > "$dtbo" || {
		rm "$dtbo"
		die "Device Tree overlay building failed"
		return 1
	}
	dtbo_check_compatible "$dtbo" || {
		rm "$dtbo"
		die "Device Tree overlay is incompatible with this device"
		return 1
	}

	debug "Loading DTBO"
	local overlay=`overlay_path $SLOT $MODULE`
	mkdir "$overlay" &&
	cat "$dtbo" > "$overlay/dtbo"

	local OVERLAY_LOADING_CHECK_COUNT=5
	local i
	for ((i=0; i<$OVERLAY_LOADING_CHECK_COUNT; i++)); do
		log_action_cont_msg
		[[ $(cat "$overlay/status") == "applied" ]] && break
		sleep 1
	done
	[[ $i == $OVERLAY_LOADING_CHECK_COUNT ]] && {
		rm "$dtbo"
		die "Device Tree overlay loading failed"
		return 1
	}
	rm "$dtbo"

	module_run_hook init
}


# Formatы overy name from DTS basename and hash of its contents
# Args:
# - path to DTS file
dts_get_overlay_name() {
	local dts_fname=$1
	# overlay name is constructed from basename and hash
	local dts_hash=$(md5sum ${dts_fname} | cut -d ' ' -f 1)

	echo "${dts_fname}-${dts_hash}"
}

# Loads DTS overlay without preprocessing
# This builds DTBO and loads it into the kernel
# This subroutine is mainly used for debug purposes
# Args:
# - path to DTS file
dts_load() {
	local dts_fname=$1
	[[ ! -f ${dts_fname} ]] && {
		die "DTS file not found"
		return 1
	}


	local overlay_name=`dts_get_overlay_name ${dts_fname}`

	local overlay_path="$OVERLAYS/${overlay_name}"
	[[ -d "${overlay_path}" ]] && {
		local st="$(cat "${overlay_path}/status")"
		case "$st" in
			"applied")
				log_action_msg "DTS file is already applied"
				return 0
				;;
			*)
				log_warning_msg "Overlay ${overlay_path#$OVERLAYS/} have status '$st', trying to remove"
				rmdir "${overlay_path}"
				;;
		esac
	}

	log_action_msg "Loading ${dts_fname}"

	local dtbo=`mktemp`

	cat "${dts_fname}" |
	dts_add_header |
	dts_compile > "$dtbo" || {
		rm "$dtbo"
		die "Device Tree overlay building failed"
		return 1
	}
	dtbo_check_compatible "$dtbo" || {
		rm "$dtbo"
		die "Device Tree overlay is incompatible with this device"
		return 1
	}

	debug "Loading DTBO"
	mkdir "${overlay_path}" &&
	cat "$dtbo" > "${overlay_path}/dtbo"

	local i
	for ((i=0; i<5; i++)); do
		log_action_cont_msg
		[[ $(cat "${overlay_path}/status") == "applied" ]] && break
		sleep 1
	done
	[[ $i == 3 ]] && {
		rm "$dtbo"
		die "Device Tree overlay loading failed"
		return 1
	}
	rm "$dtbo"
}

# Unloads previously loaded DTS overlay
# Args:
# - path to DTS file
dts_unload() {
	local dts_fname=$1
	[[ ! -f ${dts_fname} ]] && {
		die "DTS file not found"
		return 1
	}

	log_action_msg "Unloading ${dts_fname}"

	local overlay_name=`dts_get_overlay_name ${dts_fname}`

	local overlay_path="$OVERLAYS/${overlay_name}"
	[[ ! -d "${overlay_path}" ]] && {
		die "DTS is not loaded"
		return 1
	}

	debug "Unloading DTS"
	rmdir ${overlay_path}
}

# Deinitialize any module plugged to given slot.
# This runs module hook 'deinit' and unloads DTBO.
# Args:
# - slot
module_deinit() {
	local SLOT=$1

	local t=`echo "$OVERLAYS/$SLOT:"*`
	[[ -e "$t" ]] || {
		log_warning_msg "Slot $SLOT is not in use"
		return 0
	}

	local MODULE="${t##$OVERLAYS/$SLOT:}"

	log_action_msg "Deinitializing $SLOT:$MODULE"

	module_run_hook deinit || return $?

	debug "Unloading DTBO"
	rmdir "$t"
}


is_live_system() {
	if [[ -e /proc/device-tree/compatible ]]; then
		for compat in `tr < /proc/device-tree/compatible  '\000' '\n'`; do
			if [[ "$compat" == wirenboard,* ]] || [[ "$compat" ==  contactless,* ]]; then
				return 0
			fi
		done
	fi
	return 1
}

get_dist_conffile() {
	if of_machine_match "wirenboard,wirenboard-731"; then
		BOARD_CONF="wb72x-73x"
	elif of_machine_match "wirenboard,wirenboard-730"; then
		BOARD_CONF="wb730"
	elif of_machine_match "wirenboard,wirenboard-73x"; then
		BOARD_CONF="wb72x-73x"
	elif of_machine_match "wirenboard,wirenboard-72x"; then
		BOARD_CONF="wb72x-73x"
	elif of_machine_match "wirenboard,wirenboard-720"; then
		BOARD_CONF="wb72x-73x"
	elif of_machine_match "contactless,imx6ul-wirenboard670"; then
		BOARD_CONF="wb67"
	elif of_machine_match "contactless,imx6ul-wirenboard61"; then
		BOARD_CONF="wb61"
	elif of_machine_match "contactless,imx6ul-wirenboard60"; then
		BOARD_CONF="wb60"
	else
		BOARD_CONF="default"
	fi

	echo "/usr/share/wb-hwconf-manager/boards/$BOARD_CONF.conf"
}
