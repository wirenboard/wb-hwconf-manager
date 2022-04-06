#ifndef UTILS_H
#define UTILS_H

#include "strutils.h"

#include "gpio.h"

#ifdef FROM_SHELL
local QUOTE(SLOT_ALIAS)=EXPAND_AND_QUOTE(SLOT_ALIAS);
#endif

/*
 * SLOT_DT_ALIAS(foo) -> mod<n>_foo
 *	use to reference on per-slot peripherials (i2c, spi, uart)
*/
#define SLOT_DT_ALIAS(x) __cat3(SLOT_ALIAS, _, x)
#define SLOT_GPIO(x) SLOT_GPIO_PORT_ALIAS(x) SLOT_GPIO_SPEC(x) GPIO_ACTIVE_HIGH
#define SLOT_GPIO_LOW(x) SLOT_GPIO_PORT_ALIAS(x) SLOT_GPIO_SPEC(x) GPIO_ACTIVE_LOW


#include "irq.h"

#endif /* UTILS_H */
