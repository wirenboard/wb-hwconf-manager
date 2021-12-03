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


#include "wb-extio-common.h"
