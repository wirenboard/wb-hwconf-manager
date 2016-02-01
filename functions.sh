#!/bin/bash
CONFIG="/etc/wb-hardware.conf"
DATADIR="/usr/share/wb-hwconf-manager"
CONFIG_STATE="/var/lib/wirenboard/hardware.state"

DEBUG=""
SYSLOG=""

VERBOSE="yes"
2>/dev/null . /lib/lsb/init-functions

2>/dev/null . ./debug-env

MODULES="$DATADIR/modules"
SLOTS="$DATADIR/slots"

CONFIGFS="/sys/kernel/config"
OVERLAYS="$CONFIGFS/device-tree/overlays"

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
		logger -p user.err -t "wb-hwconf-manager" "$*"
	else
		log_failure_msg "$*"
	fi
	[[ $? == 0 ]] && return 1 || return $?
}

log() {
	if [[ -n "$SYSLOG" ]]; then
		logger -p user.info -t "wb-hwconf-manager" "$*"
	else
		log_action_msg "$*"
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
	cat "$tmp" > "$JSON"
	rm "$tmp"
	#debug "json_edit\n"
	#>&2 cat "$JSON"
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
################################################################################

config_parse() {
	jq -r '.slots[] | @text "\(.id) \(.module)"' "$CONFIG"
}

config_slot_module() {
	jq -r ".slots[] | select(.id == \"$1\") | .module" "$CONFIG"
}

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

slot_get_vars() {
	SLOT=${SLOT:-$1} slot_preprocess -DFROM_SHELL <<<"" | sed 's/#.*//; /^$/d'
}

slot_preprocess() {
	local slot=`slot_get_filename` || return 1

	cat "$slot" - |
	sed -r 's/#(\w+-cells)/__\1/' |
	tcc \
		-x assembler-with-cpp \
		-Ulinux \
		-nostdinc \
		-I "$SLOTS" -I "$MODULES" "$@" -E - |
	sed -r '/^\s*(# |$)/d; s/__(\w+-cells)/#\1/;'
}

dtbo_build() {
	local mod=`module_get_filename` || return 1

	{
		echo '/dts-v1/ /plugin/;'
		cat "$mod"
	} |
	slot_preprocess |
	dtc -I dts -O dtb -@ -
}

dtbo_check_compatible() {
	local dtbo_compat=`fdtget "$1" / compatible 2>/dev/null`
	[[ -z "$dtbo_compat" || "$dtbo_compat" == "unknown" ]] && return 0
	for compat in `tr < /proc/device-tree/compatible  '\000' '\n'`; do
		[[ "$dtbo_compat" == "$compat" ]] && return 0
	done
	return 1
}

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

	$func
	unset $func
}

overlay_path() {
	echo "$OVERLAYS/$1:$2"
}

module_bind() {
	local SLOT=$1
	local MODULE=$2

	local t=`echo "$OVERLAYS/$SLOT:"*`
	[[ -d "$t" ]] && {
		local st="$(cat "$t/status")"
		case "$st" in
			"applied")
				die "Slot $SLOT is used by ${t#$OVERLAYS/$SLOT:} module"
				return 1
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

	log_action_msg "Binding module $MODULE to slot $SLOT"

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

	local overlay=`overlay_path $SLOT $MODULE`
	mkdir "$overlay" &&
	cat "$dtbo" > "$overlay/dtbo"

	local i
	for ((i=0; i<5; i++)); do
		log_action_cont_msg
		[[ $(cat "$overlay/status") == "applied" ]] && break
		sleep 1
	done
	[[ $i == 3 ]] && {
		rm "$dtbo"
		die "Device Tree overlay loading failed"
		return 1
	}
	rm "$dtbo"

	module_run_hook init
}

module_unbind() {
	local SLOT=$1

	log_action_msg "Unbinding module from slot $SLOT"
	local t=`echo "$OVERLAYS/$SLOT:"*`
	[[ -e "$t" ]] || {
		log_end_msg "Slot $SLOT is not in use"
	}

	module_run_hook deinit
	rmdir "$t"
}


