#undef __gpio_pin
#define __gpio_pin __arg1

#undef SLOT_GPIO_PORT_ALIAS
#define SLOT_GPIO_PORT_ALIAS(x) &wbec_gpio
#undef SLOT_GPIO_SPEC
#define SLOT_GPIO_SPEC(x) SLOT_GPIO_PIN(x)

#undef WBE_INPUT
#define WBE_INPUT(name, pin, index) \
    __cat4(MOD, MOD_SLOT_NUM, _, name) {\
        io-gpios = <SLOT_GPIO(pin)>;\
        input;\
        sort-order = <__cat(MOD_SLOT_NUM, index)>;\
    }

#undef WBE_OUTPUT_HIGH
#define WBE_OUTPUT_HIGH(name, pin, index) \
    __cat4(MOD, MOD_SLOT_NUM, _, name) {\
        io-gpios = <SLOT_GPIO(pin)>;\
        sort-order = <__cat(MOD_SLOT_NUM, index)>;\
    }

#ifdef FROM_SHELL
#ifdef SLOT_ALL_PINS
#undef SLOT_FOR_PIN
#define SLOT_FOR_PIN(x) local GPIO_##x=SLOT_GPIO_PIN(x);
SLOT_ALL_PINS
#undef SLOT_FOR_PIN
#endif
#endif
