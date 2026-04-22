import io
import json
from pathlib import Path

import config as config_module
from config import from_confed, make_modules_list, to_combined_config, to_confed

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


def test_get_compatible_boards_list(monkeypatch, tmp_path):
    device_tree = tmp_path / "device-tree"
    device_tree.mkdir()
    (device_tree / "compatible").write_text("wirenboard,wirenboard-85x\x00other-board\x00", encoding="utf-8")

    monkeypatch.setattr(config_module.os, "readlink", lambda path: str(device_tree))

    assert config_module.get_compatible_boards_list() == [
        "wirenboard,wirenboard-85x",
        "other-board",
        "",
    ]


def test_get_board_config_path(monkeypatch):
    monkeypatch.setattr(config_module, "get_compatible_boards_list", lambda: ["wirenboard,wirenboard-85x"])
    assert config_module.get_board_config_path().endswith("/boards/wb85x.conf")

    monkeypatch.setattr(config_module, "get_compatible_boards_list", lambda: ["unknown-board"])
    assert config_module.get_board_config_path().endswith("/boards/default.conf")


def test_extract_config_skips_slots_without_slot_id():
    combined_config = {"slots": [{"id": "slot-without-id", "module": "wbe2-ao-10v-2", "options": {}}]}
    board_slots = {
        "slots": [
            {
                "id": "slot-without-id",
                "compatible": ["wbe2"],
                "module": "",
                "options": {},
            }
        ]
    }

    assert not config_module.extract_config(combined_config, board_slots, [])


def test_to_combined_config():
    result = to_combined_config(
        json.dumps({"mod1": {"module": "wbe2-ao-10v-2", "options": {}}}),
        BOARD_CONF_PATH,
        MODULES_DIR,
        "",
    )

    slot = next(slot for slot in result["slots"] if slot["id"] == "wb72-mod1")
    assert slot["module"] == "wbe2-ao-10v-2"


def test_main_to_confed(monkeypatch, capsys):
    monkeypatch.setattr(config_module.sys, "argv", ["config.py", "--to-confed"])
    monkeypatch.setattr(config_module, "get_board_config_path", lambda: BOARD_CONF_PATH)
    monkeypatch.setattr(config_module, "to_confed", lambda *args: {"ok": True})

    config_module.main()

    assert json.loads(capsys.readouterr().out) == {"ok": True}


def test_main_from_confed(monkeypatch, capsys):
    monkeypatch.setattr(config_module.sys, "argv", ["config.py", "--from-confed"])
    monkeypatch.setattr(config_module.sys, "stdin", io.StringIO("{}"))
    monkeypatch.setattr(config_module, "get_board_config_path", lambda: BOARD_CONF_PATH)
    monkeypatch.setattr(config_module, "from_confed", lambda *args: {"ok": True})

    config_module.main()

    assert json.loads(capsys.readouterr().out) == {"ok": True}


def test_main_to_combined_config(monkeypatch, capsys):
    monkeypatch.setattr(config_module.sys, "argv", ["config.py", "--to-combined-config"])
    monkeypatch.setattr(config_module.sys, "stdin", io.StringIO("{}"))
    monkeypatch.setattr(config_module, "get_board_config_path", lambda: BOARD_CONF_PATH)
    monkeypatch.setattr(config_module, "to_combined_config", lambda *args: {"ok": True})

    config_module.main()

    assert json.loads(capsys.readouterr().out) == {"ok": True}


def test_main_prints_usage(monkeypatch, capsys):
    monkeypatch.setattr(config_module.sys, "argv", ["config.py"])

    config_module.main()

    assert "usage:" in capsys.readouterr().out


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
    config_path.write_text(
        json.dumps({"mod4": {"module": "wbe2-hdmi", "options": {"url": "http://"}}}),
        encoding="utf-8",
    )

    monkeypatch.setattr(config_module.hdmi, "get_hdmi_modes", lambda: [{"value": "auto"}])
    monkeypatch.setattr(config_module.hdmi, "get_monitor_info", lambda: "Panel")

    result = to_confed(str(config_path), WB85_BOARD_PATH, MODULES_DIR_REAL, "")
    slot = next(slot for slot in result["slots"] if slot.get("module") == "wbe2-hdmi")
    assert slot["options"]["url"] == "http://"
    assert slot["options"]["monitor_info"] == "Panel"


def test_to_confed_without_hdmi_does_not_add_modes(tmp_path):
    """Ensure available_hdmi_modes key absent when module missing."""
    config_path = tmp_path / "no-hdmi.json"
    config_path.write_text(
        json.dumps({"mod1": {"module": "wbe2-ao-10v-2", "options": {}}}),
        encoding="utf-8",
    )

    result = to_confed(str(config_path), WB85_BOARD_PATH, MODULES_DIR_REAL, "")
    assert "available_hdmi_modes" not in result
