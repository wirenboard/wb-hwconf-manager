#ifndef __DTS_IMX6UL_SOC_H
#define __DTS_IMX6UL_SOC_H

#define SOC_TYPE MX6UL

// GPIO ports in DT counts from 1, and in sysfs GPIO interface from 0
#define GPIO_PORT_PIN_TO_NUM(port, pin) $(((port-1) * 32 + pin))

#include "imx-common.h"
#include "imx6ul-pinfunc.h"
#endif

// ao-10v-2 driver needs vdd-regulator phandle
// TODO: define, when wb6 migrates to 6.8 kernel
#ifndef SLOT_VDD_SUPPLY
#define SLOT_VDD_SUPPLY
#endif
