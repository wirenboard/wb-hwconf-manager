#define __gpio_pin __arg1

#define SLOT_GPIO_PORT_ALIAS(x) &wbec_gpio
#define SLOT_GPIO_SPEC(x) SLOT_GPIO_PIN(x)

#define WBE_INPUT(name, pin, index) \
    __cat4(MOD, MOD_SLOT_NUM, _, name) {\
        io-gpios = <SLOT_GPIO(pin)>;\
        input;\
        sort-order = <__cat(MOD_SLOT_NUM, index)>;\
    }

#define WBE_OUTPUT_HIGH(name, pin, index) \
    __cat4(MOD, MOD_SLOT_NUM, _, name) {\
        io-gpios = <SLOT_GPIO(pin)>;\
        sort-order = <__cat(MOD_SLOT_NUM, index)>;\
    }
