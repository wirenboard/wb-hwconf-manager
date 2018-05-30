#ifndef UTILS_H
#define UTILS_H

#include "strutils.h"

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
#define SLOT_PINMUX(x, func) __cat4(__cat(SOC_TYPE, _PAD_), __pin_attr(x, pad), __, func)
#define SLOT_PINMUX_GPIO(x) SLOT_PINMUX(x, __cat4(GPIO_, __pin_attr(x, gpio_port), _, __pin_attr(x, gpio_pin)))
#define SLOT_GPIO_PORT(x) __pin_attr(x, gpio_port)
#define SLOT_GPIO_PORT_ALIAS(x) __cat(&gpio, __pin_attr(x, gpio_port))
#define SLOT_GPIO_PIN(x) __pin_attr(x, gpio_pin)
#define SLOT_GPIO(x) SLOT_GPIO_PORT_ALIAS(x) SLOT_GPIO_PIN(x) 0
#define SLOT_DT_ALIAS(x) __cat3(SLOT_ALIAS, _, x)

#ifdef FROM_SHELL

#ifndef GPIO_PORT_PIN_TO_NUM
#define GPIO_PORT_PIN_TO_NUM(port, pin) $((port * 32 + pin))
#endif

#ifdef SLOT_ALL_PINS
#define SLOT_FOR_PIN(x) local GPIO_##x=GPIO_PORT_PIN_TO_NUM(SLOT_GPIO_PORT(x), SLOT_GPIO_PIN(x));
SLOT_ALL_PINS
#undef SLOT_FOR_PIN
#endif

local QUOTE(SLOT_ALIAS)=EXPAND_AND_QUOTE(SLOT_ALIAS);
#endif

#include "irq.h"

#endif /* UTILS_H */
