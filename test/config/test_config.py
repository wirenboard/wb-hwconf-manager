from config import make_modules_list, to_confed, from_confed
import json

MODULES_DIR = "./test/config/modules"
OLD_CONFIG_PATH = "./test/config/old_config.conf"
NEW_CONFIG_PATH = "./test/config/new_config.conf"
BOARD_CONF_PATH = "./test/config/system.conf"
CONFED_JSON_PATH = "./test/config/confed.json"


def test_make_modules_list():
    with open(CONFED_JSON_PATH, "r", encoding="utf-8") as config_file:
        confed_json = json.load(config_file)
    assert confed_json["modules"] == make_modules_list(MODULES_DIR)


def test_to_confed_from_old_config():
    with open(CONFED_JSON_PATH, "r", encoding="utf-8") as config_file:
        confed_json = json.load(config_file)
    assert confed_json == to_confed(OLD_CONFIG_PATH, BOARD_CONF_PATH, MODULES_DIR)


def test_to_confed_from_new_config():
    with open(CONFED_JSON_PATH, "r", encoding="utf-8") as config_file:
        confed_json = json.load(config_file)
    assert confed_json == to_confed(NEW_CONFIG_PATH, BOARD_CONF_PATH, MODULES_DIR)


def test_from_confed():
    with open(CONFED_JSON_PATH, "r", encoding="utf-8") as confed_file:
        confed_str = confed_file.read()
    with open(NEW_CONFIG_PATH, "r", encoding="utf-8") as config_file:
        new_config = json.load(config_file)
    assert new_config == from_confed(confed_str, BOARD_CONF_PATH)
