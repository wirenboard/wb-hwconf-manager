#ifndef __ALLWINNER_SOC_H
#define __ALLWINNER_SOC_H

/* Pattern-matching accessors for pins declarations */
#define __gpio_bank __arg1
#define __gpio_pin __arg2
#define __pin_attr(x, attr) __pass(__##attr __cat3(SLOT, _, x))


/* Helper macros that substitutes actual pins values depending on used slot
 * e.g. if SLOT == wb5-mod1 it will expand to pins regarding to MOD1 connector
 * Supposed to be used to avoid DTS duplication for modules fitting more than
 * one slot.
 *
 * SLOT_GPIO_PORT_ALIAS(FOO) -> &pio
 * SLOT_GPIO_PIN(FOO) -> <GPIO pin number>
 *	use to get GPIO pin number
 * SLOT_GPIO(FOO) -> &gpio<port> <pin>
 *	use in peripheral device nodes, e.g. gpios = <SLOT_GPIO(FOO)>
 */

#define SLOT_GPIO_BANK(x) __pin_attr(x, gpio_bank)

#define SLOT_GPIO_PORT_ALIAS(x) &pio
#define SLOT_GPIO_XLATE_TYPE(x) "bank_pin"
#define SLOT_GPIO_PINS_PER_BANK(x) 32

#define SLOT_GPIO_PIN(x) __pin_attr(x, gpio_pin)

#define SLOT_GPIO_SPEC(x) SLOT_GPIO_BANK(x) SLOT_GPIO_PIN(x)


#define GPIO_PORT_PIN_TO_NUM(bank, pin) $((bank * 32 + pin))

#include "strutils.h"

#ifdef FROM_SHELL


#ifdef SLOT_ALL_PINS
#define SLOT_FOR_PIN(x) local GPIO_##x=GPIO_PORT_PIN_TO_NUM(SLOT_GPIO_BANK(x), SLOT_GPIO_PIN(x));
SLOT_ALL_PINS
#undef SLOT_FOR_PIN
#endif

#endif

#endif
