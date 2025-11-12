import json
from pathlib import Path

import config as config_module
from config import from_confed, make_modules_list, to_confed

MODULES_DIR = "./test/config/modules"
OLD_CONFIG_PATH = "./test/config/old_config.conf"
NEW_CONFIG_PATH = "./test/config/new_config.conf"
BOARD_CONF_PATH = "./test/config/system.conf"
CONFED_JSON_PATH = "./test/config/confed.json"
VENDOR_CONFED_JSON_PATH = "./test/config/vendor-confed.json"
VENDOR_CONFIG_PATH = "./test/config/vendor-modules.json"
REPO_ROOT = Path(__file__).resolve().parents[2]
WB85_BOARD_PATH = str(REPO_ROOT / "boards" / "wb85x.conf")
MODULES_DIR_REAL = str(REPO_ROOT / "modules")


def test_make_modules_list():
    with open(CONFED_JSON_PATH, "r", encoding="utf-8") as config_file:
        confed_json = json.load(config_file)
    assert confed_json["modules"] == make_modules_list(MODULES_DIR, "")


def test_to_confed_from_old_config():
    config_paths = [
        OLD_CONFIG_PATH,
        "./test/config/old_config_unsupported_modules.conf",
        "./test/config/old_config_unsupported_slots.conf",
    ]
    with open(CONFED_JSON_PATH, "r", encoding="utf-8") as config_file:
        confed_json = json.load(config_file)
    for config_path in config_paths:
        assert confed_json == to_confed(config_path, BOARD_CONF_PATH, MODULES_DIR, "")


def test_to_confed_from_new_config():
    config_paths = [
        NEW_CONFIG_PATH,
        "./test/config/new_config_unsupported_modules.conf",
        "./test/config/new_config_unsupported_slots.conf",
    ]
    with open(CONFED_JSON_PATH, "r", encoding="utf-8") as config_file:
        confed_json = json.load(config_file)
    for config_path in config_paths:
        assert confed_json == to_confed(config_path, BOARD_CONF_PATH, MODULES_DIR, "")


def test_from_confed():
    with open(CONFED_JSON_PATH, "r", encoding="utf-8") as confed_file:
        confed_str = confed_file.read()
    with open(NEW_CONFIG_PATH, "r", encoding="utf-8") as config_file:
        new_config = json.load(config_file)
    assert new_config == from_confed(confed_str, BOARD_CONF_PATH, MODULES_DIR, "")


def test_make_vendor_modules_list():
    with open(VENDOR_CONFED_JSON_PATH, "r", encoding="utf-8") as config_file:
        confed_json = json.load(config_file)
    assert confed_json["modules"] == make_modules_list(MODULES_DIR, VENDOR_CONFIG_PATH)


def test_to_confed_adds_monitor_info(monkeypatch, tmp_path):
    """Ensure HDMI slots include monitor info and available modes when present."""
    config_path = tmp_path / "hdmi-config.json"
    config_path.write_text(json.dumps({"mod4": {"module": "wbe2-hdmi", "options": {}}}), encoding="utf-8")

    monkeypatch.setattr(config_module.hdmi, "get_hdmi_modes", lambda: [{"value": "auto"}])
    monkeypatch.setattr(config_module.hdmi, "get_monitor_info", lambda: "Test Monitor (max: 4k)")

    result = to_confed(str(config_path), WB85_BOARD_PATH, MODULES_DIR_REAL, "")

    assert result["available_hdmi_modes"][0]["value"] == "auto"
    slot = next(slot for slot in result["slots"] if slot.get("module") == "wbe2-hdmi")
    assert slot["options"]["monitor_info"] == "Test Monitor (max: 4k)"


def test_to_confed_preserves_existing_options(monkeypatch, tmp_path):
    """Existing options should remain while monitor info is appended."""
    config_path = tmp_path / "hdmi-config.json"
    config_path.write_text(json.dumps({"mod4": {"module": "wbe2-hdmi", "options": {"url": "http://"}}}), encoding="utf-8")

    monkeypatch.setattr(config_module.hdmi, "get_hdmi_modes", lambda: [{"value": "auto"}])
    monkeypatch.setattr(config_module.hdmi, "get_monitor_info", lambda: "Panel")

    result = to_confed(str(config_path), WB85_BOARD_PATH, MODULES_DIR_REAL, "")
    slot = next(slot for slot in result["slots"] if slot.get("module") == "wbe2-hdmi")
    assert slot["options"]["url"] == "http://"
    assert slot["options"]["monitor_info"] == "Panel"


def test_to_confed_without_hdmi_does_not_add_modes(tmp_path):
    """Ensure available_hdmi_modes key absent when module missing."""
    config_path = tmp_path / "no-hdmi.json"
    config_path.write_text(json.dumps({"mod1": {"module": "wbe2-ao-10v-2", "options": {}}}), encoding="utf-8")

    result = to_confed(str(config_path), WB85_BOARD_PATH, MODULES_DIR_REAL, "")
    assert "available_hdmi_modes" not in result
