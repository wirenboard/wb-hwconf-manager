#define WBE_INPUT(name, pin, index) \
    __cat4(MOD, MOD_SLOT_NUM, _, name) {\
        io-gpios = <SLOT_GPIO(pin)>;\
        input;\
        sort-order = <__cat(MOD_SLOT_NUM, index)>;\
        gpio-xlate-type = SLOT_GPIO_XLATE_TYPE(pin); \
        gpio-pins-per-bank = <SLOT_GPIO_PINS_PER_BANK(pin)>; \
    }

#define WBE_OUTPUT_HIGH(name, pin, index) \
    __cat4(MOD, MOD_SLOT_NUM, _, name) {\
        io-gpios = <SLOT_GPIO(pin)>;\
        sort-order = <__cat(MOD_SLOT_NUM, index)>;\
        gpio-xlate-type = SLOT_GPIO_XLATE_TYPE(pin); \
        gpio-pins-per-bank = <SLOT_GPIO_PINS_PER_BANK(pin)>; \
    }
