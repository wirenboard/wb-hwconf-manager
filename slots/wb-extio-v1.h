#include "strutils.h"
#define SLOT_ALIAS __cat(extio, EXTIO_SLOT_NUM)

/* utils.h has to be included after SLOT_ALIAS is defined */
#include "utils.h"

/* Fields: ADDRESS_IN (hex), ADDRESS_OUT (hex), ADDRESS_DAC (hex), GPIO_BASE_8, GPIO_BASE_40 */
#define SLOT1 ( 27,	20, 31, 160,	256 )
#define SLOT2 ( 26,	21, 33,	168,	296 )
#define SLOT3 ( 25,	22, 43, 176,	336 )
#define SLOT4 ( 23,	24, 52, 184,	376 )
#define SLOT5 ( 27,	20, 31, 192,	416 )
#define SLOT6 ( 26,	21, 33, 200,	456 )
#define SLOT7 ( 25,	22, 43, 208,	496 )
#define SLOT8 ( 23,	24, 52, 216,	536 )

#define SLOT_DEF __cat(SLOT, EXTIO_SLOT_NUM)

#define SLOT_I2C_ADDRESS_IN		__pass(__arg1 SLOT_DEF)
#define SLOT_I2C_ADDRESS_OUT	__pass(__arg2 SLOT_DEF)
#define SLOT_I2C_ADDRESS_DAC	__pass(__arg3 SLOT_DEF)
#define SLOT_GPIO_BASE_8		__pass(__arg4 SLOT_DEF)
#define SLOT_GPIO_BASE_40		__pass(__arg5 SLOT_DEF)

/* order for EXTIO_INPUT and EXTIO_OUTPUT_HIGH
   must be two digit number, 1 must be 01, 2 - 02 etc.
   The macros concatenates EXTIO_SLOT_NUM and supplied order.
   Resulting sort order for extio pins starts from 100.
*/
#define EXTIO_INPUT(name, pin, order) \
    __cat4(EXT, EXTIO_SLOT_NUM, _, name) {\
        io-gpios = <&SLOT_DT_ALIAS(WBIO_NAME) pin GPIO_ACTIVE_HIGH>;\
        input;\
        sort-order = <__cat(EXTIO_SLOT_NUM, order)>;\
    }

#define EXTIO_OUTPUT_HIGH(name, pin, order) \
    __cat4(EXT, EXTIO_SLOT_NUM, _, name) {\
        io-gpios = <&SLOT_DT_ALIAS(WBIO_NAME) pin GPIO_ACTIVE_HIGH>;\
        output-high;\
        sort-order = <__cat(EXTIO_SLOT_NUM, order)>;\
    }

#ifdef FROM_SHELL
local GPIO_BASE_8=SLOT_GPIO_BASE_8
local GPIO_BASE_40=SLOT_GPIO_BASE_40
#endif
