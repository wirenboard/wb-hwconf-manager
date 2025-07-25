#!/bin/bash
source "$DATADIR/modules/utils.sh"

hook_module_add() {
	local XORG_CONFIG_PATH="/etc/X11/xorg.conf.d/10-monitor.conf"
	local URL_CONFIG_PATH="/root/url"

	# Извлечение параметров через jq
	local mode="$(config_module_option ".mode")"
	local rotate="$(config_module_option ".rotate")"
	local url="$(config_module_option ".url")"

	# Преобразуем rotate в формат X11 (допустимые значения: normal, left, right, inverted)
	case "$rotate" in
		90) xrotate="right" ;;
		180) xrotate="inverted" ;;
		270) xrotate="left" ;;
		*) xrotate="normal" ;;
	esac

	# Генерация xorg.conf.d/10-monitor.conf
	mkdir -p "$(dirname "$XORG_CONFIG_PATH")"
	{
		echo 'Section "Monitor"'
		echo '    Identifier "HDMI-1"'
		if [[ "$mode" != "auto" && -n "$mode" ]]; then
			echo "    Option \"PreferredMode\" \"$mode\""
		fi
		echo "    Option \"Rotate\" \"$xrotate\""
		echo 'EndSection'
	} > "$XORG_CONFIG_PATH"

	if [[ -n "$url" ]]; then
		echo "$url" > "$URL_CONFIG_PATH"
	else
		rm "$URL_CONFIG_PATH"
	fi

	# Обновляем xrandr настройки или запускаем xinit
	if pgrep -x xinit > /dev/null; then
		echo "Xinit is running. Applying xrandr settings..."
		export DISPLAY=:0

		cmd=(xrandr --output HDMI-1)

		if [[ "$mode" != "auto" && -n "$mode" ]]; then
			cmd+=("--mode" "$mode")
		fi

		cmd+=("--rotate" "$xrotate")

		# Выполнить команду
		"${cmd[@]}"

	else
		systemctl start xinit.service
	fi

}

hook_module_init() {
	systemctl enable xinit.service
	systemctl start xinit.service
}

hook_module_deinit() {
	systemctl stop xinit.service
	systemctl disable xinit.service
}
