#ifndef UTILS_H
#define UTILS_H

/* For somewhat reason, tcc assumes that linux equals 1 */
#undef linux

/* Abusing the preprocessor violently */
#define __cat_internal(a, ...) a ## __VA_ARGS__
#define __cat(a, ...) __cat_internal(a, __VA_ARGS__)
#define __cat3(a, b, ...) __cat(a, __cat(b, __VA_ARGS__))
#define __cat4(a, b, c, ...) __cat(a, __cat3(b, c, __VA_ARGS__))
#define __pass(...) __VA_ARGS__

/* Append '0x' prefix to hex numbers */
#define HEX_PREFIX(x) __cat(0x, x)

#define __arg1(a, ...) a
#define __arg2(a, b, ...) b
#define __arg3(a, b, c, ...) c
#define __arg4(a, b, c, d, ...) d

/* Pattern-matching accessors for pins declarations */
#define __pad __arg1
#define __gpio_port __arg2
#define __gpio_pin __arg3
#define __pin_attr(x, attr) __pass(__##attr __cat3(SLOT, _, x))

/* Helper macros that substitutes actual pins values depending on used slot
 * e.g. if SLOT == wb5-mod1 it will expand to pins regarding to MOD1 connector
 * Supposed to be used to avoid DTS duplication for modules fitting more than
 * one slot.
 *
 * SLOT_PINMUX(FOO, SOME_MUX) -> MX28_PAD_<pad name>__SOME_MUX
 *	use for fine-grained pinmux control, usually not needed
 * SLOT_PINMUX_GPIO(FOO) -> MX28_PAD_<pad name>__GPIO_<port>_<pin>
 *	use to configure pin as GPIO
 * SLOT_GPIO_PORT(FOO) -> <GPIO port number>
 *	use to get GPIO port number
 * SLOT_GPIO_PORT_ALIAS(FOO) -> &gpio<GPIO port number>
 *	use to get GPIO port DT alias (e.g. &gpio3)
 * SLOT_GPIO_PIN(FOO) -> <GPIO pin number>
 *	use to get GPIO pin number
 * SLOT_GPIO(FOO) -> &gpio<port> <pin>
 *	use in periherial device nodes, e.g. gpios = <SLOT_GPIO(FOO)>
 * SLOT_DT_ALIAS(foo) -> mod<n>_foo
 *	use to reference on per-slot peripherials (i2c, spi, uart)
 */
#define SLOT_PINMUX(x, func) __cat4(MX28_PAD_, __pin_attr(x, pad), __, func)
#define SLOT_PINMUX_GPIO(x) SLOT_PINMUX(x, __cat4(GPIO_, __pin_attr(x, gpio_port), _, __pin_attr(x, gpio_pin)))
#define SLOT_GPIO_PORT(x) __pin_attr(x, gpio_port)
#define SLOT_GPIO_PORT_ALIAS(x) __cat(&gpio, __pin_attr(x, gpio_port))
#define SLOT_GPIO_PIN(x) __pin_attr(x, gpio_pin)
#define SLOT_GPIO(x) SLOT_GPIO_PORT_ALIAS(x) SLOT_GPIO_PIN(x) 0
#define SLOT_DT_ALIAS(x) __cat3(SLOT_ALIAS, _, x)

#define QUOTE(str) #str
#define EXPAND_AND_QUOTE(str) QUOTE(str)

#ifdef FROM_SHELL

#ifdef SLOT_ALL_PINS
#define SLOT_FOR_PIN(x) local GPIO_##x=$((SLOT_GPIO_PORT(x) * 32 + SLOT_GPIO_PIN(x)));
SLOT_ALL_PINS
#undef SLOT_FOR_PIN
#endif

local QUOTE(SLOT_ALIAS)=EXPAND_AND_QUOTE(SLOT_ALIAS);
#endif


#endif /* UTILS_H */
