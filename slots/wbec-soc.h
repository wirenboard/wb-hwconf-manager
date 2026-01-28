#ifndef __WBEC_SOC_H
#define __WBEC_SOC_H

#define SLOT_GPIO_ONE_ARG
#define __gpio_pin __arg1
#define SLOT_GPIO_PORT_ALIAS(x) &wbec_gpio
#define SLOT_GPIO_SPEC(x) SLOT_GPIO_PIN(x)

#endif
