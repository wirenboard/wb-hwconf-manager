# wb-hwconf-manager
Provides infrastructure for hardware re-configuration via Device Tree overlays

# Customization
Для кастомизации модулей можно использовать файл `/usr/share/wb-hwconf-manager/vendor-modules.json`. Структура файла:
```
{
    "mod-foo": "vendor_description"
}
```
Где `mod-foo` - имя dtso-файла модуля без расширения, а `vendor_description` - кастомизированное описание модуля. Для веб-интерфейса кастомизированные модули помещаются наверх списка.
