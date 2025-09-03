#!/bin/bash
source "$DATADIR/modules/utils.sh"

hook_module_add() {
	local XORG_CONFIG_PATH="/etc/X11/xorg.conf.d/10-monitor.conf"
	local URL_CONFIG_PATH="/root/url"

	# Извлечение параметров через jq
	local mode="$(config_module_option ".mode")"
	local rotate="$(config_module_option ".rotate")"
	local url="$(config_module_option ".url")"

	# Разбираем режим: может быть "WxH-Rate|EDID" / "WxH-Rate|CVT" / "WxH-Rate" / "WxH"
	local res=""
	local rate=""
	local variant=""
	local modeline_name=""
	local modeline_def=""
	if [[ -n "$mode" && "$mode" != "auto" ]]; then
		# отделяем вариант, если указан через суффикс после |
		if [[ "$mode" == *"|"* ]]; then
			variant="${mode##*|}"
			variant_base="${variant%%:*}"
			variant_extra="${variant#*:}"
			[[ "$variant" == "$variant_base" ]] && variant_extra=""
			mode="${mode%%|*}"
		fi
		if [[ "$mode" == *-* ]]; then
			res="${mode%%-*}"
			rate="${mode##*-}"
		else
			res="$mode"
		fi
	fi

	# Получаем Modeline через hdmi.py (EDID -> встроенный CVT) и запоминаем индекс нужного режима
	if [[ -n "$res" && -n "$rate" ]]; then
		local w="${res%x*}"
		local h="${res#*x}"
		# Найти индекс нужного режима из списка hdmi.py (один режим на строку)
		local idx
		if [[ "$variant" == "CVT" ]]; then
			idx=$( /usr/lib/wb-hwconf-manager/hdmi.py 2>/dev/null | awk -F ' - ' -v target="${w}x${h}-${rate} (VESA CVT)" '$2==target {print $1; exit}' )
		elif [[ "$variant" == "EDID" ]]; then
			idx=$( /usr/lib/wb-hwconf-manager/hdmi.py 2>/dev/null | awk -F ' - ' -v t1="${w}x${h}-${rate} (From display, EDID)" -v t2="${w}x${h}-${rate}" '($2==t1 || $2==t2){print $1; exit}' )
		else
			idx=$( /usr/lib/wb-hwconf-manager/hdmi.py 2>/dev/null | awk -F ' - ' -v target="${w}x${h}-${rate}" '{t=$2; sub(/ \(.+\)$/,"",t); if(t==target){print $1; exit}}' )
		fi
		# Сгенерировать моделайн для записи в Xorg
		if [[ -n "$idx" ]]; then
			modeline_def=$(/usr/lib/wb-hwconf-manager/hdmi.py "$idx" 2>/dev/null)
		fi

		# Имя режима — первый токен (с кавычками) из modeline_def
		if [[ -n "$modeline_def" ]]; then
			modeline_name=$(sed -E 's/^"([^"]+)".*$/\1/' <<< "$modeline_def")
			# Если имя не нормализовано — принудительно нормализуем
			if [[ "$modeline_name" != "${w}x${h}-${rate}" ]]; then
				local norm_name="${w}x${h}-${rate}"
				modeline_def=$(sed -E "s/^\"[^\"]+\"/\"${norm_name}\"/" <<< "$modeline_def")
				modeline_name="$norm_name"
			fi
		fi
	fi

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
		# Если удалось сформировать Modeline — добавим её и сделаем предпочтительной
		if [[ -n "$modeline_def" && -n "$modeline_name" ]]; then
			echo "    Modeline $modeline_def"
			echo "    Option \"PreferredMode\" \"$modeline_name\""
		elif [[ -n "$res" ]]; then
			# Резервный случай: хотя бы зафиксируем желаемое разрешение
			echo "    Option \"PreferredMode\" \"$res\""
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
		export DISPLAY=:0.0

		# Если нашли индекс — применим режим номером (hdmi.py сам добавит режим при необходимости)
		if [[ -n "$idx" ]]; then
			/usr/lib/wb-hwconf-manager/hdmi.py "$idx" >/dev/null 2>&1 || true
		else
			# Резерв: применим через xrandr по разрешению/частоте
			cmd=(xrandr --output HDMI-1)
			if [[ -n "$res" ]]; then
				cmd+=("--mode" "$res")
				[[ -n "$rate" ]] && cmd+=("--rate" "$rate")
			fi
			"${cmd[@]}" || true
		fi

		# Повернуть экран
		xrandr --output HDMI-1 --rotate "$xrotate" || true

	else
		systemctl start xinit.service
	fi

}

hook_module_init() {
	systemctl enable xinit.service
	systemctl start xinit.service &
}

hook_module_deinit() {
	systemctl stop xinit.service &
	systemctl disable xinit.service
}
