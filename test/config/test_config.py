import json

from config import from_confed, make_modules_list, to_confed

MODULES_DIR = "./test/config/modules"
OLD_CONFIG_PATH = "./test/config/old_config.conf"
NEW_CONFIG_PATH = "./test/config/new_config.conf"
BOARD_CONF_PATH = "./test/config/system.conf"
CONFED_JSON_PATH = "./test/config/confed.json"
VENDOR_CONFIG_PATH = "./test/vendor-modules.json"


def test_make_modules_list():
    with open(CONFED_JSON_PATH, "r", encoding="utf-8") as config_file:
        confed_json = json.load(config_file)
    assert confed_json["modules"] == make_modules_list(MODULES_DIR, VENDOR_CONFIG_PATH)


def test_to_confed_from_old_config():
    config_paths = [
        OLD_CONFIG_PATH,
        "./test/config/old_config_unsupported_modules.conf",
        "./test/config/old_config_unsupported_slots.conf",
    ]
    with open(CONFED_JSON_PATH, "r", encoding="utf-8") as config_file:
        confed_json = json.load(config_file)
    for config_path in config_paths:
        assert confed_json == to_confed(config_path, BOARD_CONF_PATH, MODULES_DIR, VENDOR_CONFIG_PATH)


def test_to_confed_from_new_config():
    config_paths = [
        NEW_CONFIG_PATH,
        "./test/config/new_config_unsupported_modules.conf",
        "./test/config/new_config_unsupported_slots.conf",
    ]
    with open(CONFED_JSON_PATH, "r", encoding="utf-8") as config_file:
        confed_json = json.load(config_file)
    for config_path in config_paths:
        assert confed_json == to_confed(config_path, BOARD_CONF_PATH, MODULES_DIR, VENDOR_CONFIG_PATH)


def test_from_confed():
    with open(CONFED_JSON_PATH, "r", encoding="utf-8") as confed_file:
        confed_str = confed_file.read()
    with open(NEW_CONFIG_PATH, "r", encoding="utf-8") as config_file:
        new_config = json.load(config_file)
    assert new_config == from_confed(confed_str, BOARD_CONF_PATH, MODULES_DIR, VENDOR_CONFIG_PATH)
