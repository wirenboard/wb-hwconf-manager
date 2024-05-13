#ifndef __DTS_R40_PINFUNC_H
#define __DTS_R40_PINFUNC_H

#define SOC_TYPE R40

#include "allwinner-soc.h"

#endif

// ao-10v-2 driver needs vdd-regulator phandle
// TODO: define, when wb7 migrates to 6.8 kernel
#ifndef SLOT_VDD_SUPPLY
#define SLOT_VDD_SUPPLY
#endif
