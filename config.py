#!/usr/bin/env python3

import argparse
import glob
import json
import logging
import os
import re
import sys
from pathlib import Path
from typing import List

MODULES_DIR = "/usr/share/wb-hwconf-manager/modules"
CONFIG_PATH = "/etc/wb-hardware.conf"
VENDOR_CONFIG_PATH = "/usr/share/wb-hwconf-manager/vendor-modules.json"


def get_compatible_boards_list() -> List[str]:
    """
    Returns a list of compatible board identifiers from the device tree.

    Returns:
        List[str]: A list of compatible board names (strings).
    """
    root_node = os.readlink("/proc/device-tree")
    with open(root_node + "/compatible", "r", encoding="utf-8") as file:
        return file.read().split("\x00")


def get_board_config_path() -> str:
    """
    Determines the board configuration file path based on the detected hardware.

    Returns:
        str: Path to the appropriate board configuration file.
    """
    boards = [
        ("wirenboard,wirenboard-85xm", "wb85xm"),
        ("wirenboard,wirenboard-85x", "wb85x"),
        ("wirenboard,wirenboard-84x", "wb84x"),
        ("wirenboard,wirenboard-74x", "wb74x"),
        ("wirenboard,wirenboard-731", "wb72x-73x"),
        ("wirenboard,wirenboard-730", "wb730"),
        ("wirenboard,wirenboard-73x", "wb72x-73x"),
        ("wirenboard,wirenboard-72x", "wb72x-73x"),
        ("wirenboard,wirenboard-720", "wb72x-73x"),
        ("contactless,imx6ul-wirenboard670", "wb67"),
        ("contactless,imx6ul-wirenboard61", "wb61"),
        ("contactless,imx6ul-wirenboard60", "wb60"),
    ]
    config_format = "/usr/share/wb-hwconf-manager/boards/{}.conf"
    compatible_boards = get_compatible_boards_list()
    for compatible, conf in boards:
        if compatible in compatible_boards:
            return config_format.format(conf)
    return config_format.format("default")


# board config structure
# {
#     "slots": [
#         {
#             "slot_id": "mod1",
#             "id": "wb67-mod1",
#             "compatible": ["wbe2", "wbe3-reduced"],
#             "name": "Internal slot 1",
#             "module": "",
#             "options": {}
#         },
#         ...,
#         {
#               "slot_id": "extio1",
#               "id": "wb6-extio1",
#               "compatible": ["wb5-extio"],
#               "name": "External I/O module 1",
#               "module": "",
#               "options": {}
#         },
#         ...
#     ]
# }

# config structure
# {
#     "mod1": {
#         "module": "MODULE_NAME1",
#         "options": {}
#     },
#     ...,
#     "extio1": {
#         "module": "MODULE_NAME2",
#         "options": {
#             "param": "value"
#         }
#     },
#     ...
# }


# combined config structure
# {
#     "slots": [
#         {
#             "slot_id": "mod1",
#             "id": "wb67-mod1",
#             "compatible": ["wbe2", "wbe3-reduced"],
#             "name": "Internal slot 1",
#             "module": "MODULE_NAME1",
#             "options": {}
#         },
#         ...,
#         {
#             "slot_id": "extio1",
#             "id": "wb6-extio1",
#             "compatible": ["wb5-extio"],
#             "name": "External I/O module 1",
#             "module": "MODULE_NAME2",
#             "options": {
#                 "param": "value"
#             }
#         },
#         ...
#     ]
# }


def merge_config_and_slots(config: dict, board_slots: dict) -> dict:
    """
    Merges user-defined configuration with board slot definitions.

    Args:
        config (dict): The user-defined configuration.
        board_slots (dict): The board slot definitions.

    Returns:
        dict: Combined configuration with modules and options set.
    """
    merged_config_slots = []
    for slot in board_slots["slots"]:
        slot_config = config.get(slot["slot_id"])
        if slot_config:
            slot["module"] = slot_config["module"]
            slot["options"] = slot_config["options"]
            merged_config_slots.append(slot["slot_id"])
        del slot["slot_id"]
    for slot_id in config.keys():
        if slot_id not in merged_config_slots:
            logging.warning("Slot %s is not supported by board", slot_id)
    return board_slots


def has_unsupported_module(combined_slot: dict, modules_by_id: dict) -> bool:
    """
    Checks whether a module is unsupported in a given slot.

    Args:
        combined_slot (dict): The slot configuration including module.
        modules_by_id (dict): Mapping of module IDs to compatible slots.

    Returns:
        bool: True if the module is unsupported in the slot, False otherwise.
    """
    module = combined_slot.get("module")
    if module:
        return set(combined_slot.get("compatible", [])).isdisjoint(modules_by_id.get(module, set()))
    return False


def remove_unsupported_modules(combined_config: dict, modules: List[dict]) -> None:
    """
    Removes unsupported modules from a combined configuration.

    Args:
        combined_config (dict): The combined configuration object (with slots).
        modules (List[dict]): List of all available module descriptions.
    """
    modules_by_id = {module["id"]: set(module.get("compatible_slots", [])) for module in modules}
    for slot in combined_config["slots"]:
        if has_unsupported_module(slot, modules_by_id):
            logging.warning("Module %s is not supported by slot %s", slot.get("module"), slot.get("id"))
            slot["module"] = ""
            slot["options"] = {}


def make_combined_config(config: dict, board_slots: dict, modules: List[dict]) -> dict:
    """
    Creates a combined configuration by merging slots and removing unsupported modules.

    Args:
        config (dict): User-defined configuration or combined config.
        board_slots (dict): Board slot definitions.
        modules (List[dict]): Available modules with compatibility info.

    Returns:
        dict: Final combined configuration with valid modules.
    """
    # Config has slots property, it is an old combined config format,
    # convert it to normal config format
    if "slots" in config:
        return merge_config_and_slots(extract_config(config, board_slots, modules), board_slots)

    combined_config = merge_config_and_slots(config, board_slots)
    remove_unsupported_modules(combined_config, modules)
    return combined_config


def module_configs_are_different(slot1: dict, slot2: dict) -> bool:
    """
    Compares two slot configurations to determine if they differ.

    Args:
        slot1 (dict): First slot configuration.
        slot2 (dict): Second slot configuration.

    Returns:
        bool: True if configurations differ, False otherwise.
    """
    return slot1.get("module") != slot2.get("module") or slot1.get("options") != slot2.get("options")


def extract_config(combined_config: dict, board_slots: dict, modules: List[dict]) -> dict:
    """
    Extracts a simple hardware config from a combined config structure.

    Args:
        combined_config (dict): Combined slot configuration.
        board_slots (dict): Board slot definitions.
        modules (List[dict]): List of module info with compatibility data.

    Returns:
        dict: Simplified config structure keyed by slot_id.
    """
    config = {}
    id_to_slots_id = {slot["id"]: slot for slot in board_slots["slots"]}
    modules_by_id = {module["id"]: set(module.get("compatible_slots", [])) for module in modules}

    for config_slot in combined_config["slots"]:
        board_slot = id_to_slots_id.get(config_slot["id"])
        if board_slot is None:
            logging.warning("Slot %s is not supported by board", config_slot["id"])
            continue
        slot_id = board_slot.get("slot_id")
        if slot_id is None:
            continue
        if module_configs_are_different(board_slot, config_slot):
            if has_unsupported_module(config_slot, modules_by_id):
                logging.warning(
                    "Module %s is not supported by slot %s", config_slot.get("module"), config_slot.get("id")
                )
            else:
                config[slot_id] = {
                    "module": config_slot["module"],
                    "options": config_slot["options"],
                }
    return config


def to_confed(config_path: str, board_slots_path: str, modules_dir: str, vendor_config_path: str) -> dict:
    """
    Converts the current hardware configuration to a format compatible with wb-mqtt-confed.

    Args:
        config_path (str): Path to the hardware configuration file.
        board_slots_path (str): Path to the board slot definitions.
        modules_dir (str): Directory containing module .dtso files.
        vendor_config_path (str): Path to vendor module descriptions.

    Returns:
        dict: Configuration formatted for wb-mqtt-confed.
    """
    with open(config_path, "r", encoding="utf-8") as config_file:
        config = json.load(config_file)
    modules = make_modules_list(modules_dir, vendor_config_path)
    with open(board_slots_path, "r", encoding="utf-8") as board_slots_file:
        board_slots = json.load(board_slots_file)

    available_hdmi_modes = []
    hdmi_modes_path = "/sys/class/drm/card0-HDMI-A-1/modes"
    if os.path.exists(hdmi_modes_path):
        try:
            with open("/sys/class/drm/card0-HDMI-A-1/modes", "r", encoding="utf-8") as f:
                progressive_modes = set()
                interlaced_modes = set()

                for line in f:
                    mode = line.strip()
                    if not mode:
                        continue
                    if mode.endswith("i"):
                        interlaced_modes.add(mode)
                    else:
                        progressive_modes.add(mode)

                # удаляем interlaced, если есть прогрессив с такой же базой:
                filtered_interlaced = {m for m in interlaced_modes if m[:-1] not in progressive_modes}

                all_modes = progressive_modes.union(filtered_interlaced)

                def sort_key(res):
                    try:
                        res_clean = res.replace("i", "")
                        w, h = map(int, res_clean.split("x"))
                        return (w, h)
                    except:
                        return (float("inf"), float("inf"))

                sorted_modes = sorted(all_modes, key=sort_key)

                for mode in sorted_modes:
                    available_hdmi_modes.append({"value": mode, "title": mode})
        except:
            pass

    config = make_combined_config(config, board_slots, modules)

    config["available_hdmi_modes"] = available_hdmi_modes
    config["modules"] = modules
    return config


def from_confed(
    confed_config_str: str, board_slots_path: str, modules_dir: str, vendor_config_path: str
) -> dict:
    """
    Converts a wb-mqtt-confed-style JSON config back to the simplified hardware config.

    Args:
        confed_config_str (str): Confed JSON string from stdin.
        board_slots_path (str): Path to board slot definitions.
        modules_dir (str): Directory containing module .dtso files.
        vendor_config_path (str): Path to vendor module descriptions.

    Returns:
        dict: Simplified configuration.
    """
    confed_config = json.loads(confed_config_str)
    modules = make_modules_list(modules_dir, vendor_config_path)
    with open(board_slots_path, "r", encoding="utf-8") as board_slots_file:
        board_slots = json.load(board_slots_file)
    return extract_config(confed_config, board_slots, modules)

def to_combined_config(
    config_str: str, board_slots_path: str, modules_dir: str, vendor_config_path: str
) -> dict:
    """
    Converts a simplified config JSON string to a full combined configuration.

    Args:
        config_str (str): JSON string of the simplified config.
        board_slots_path (str): Path to board slot definitions.
        modules_dir (str): Directory containing module .dtso files.
        vendor_config_path (str): Path to vendor module descriptions.

    Returns:
        dict: Combined slot-based configuration.
    """
    config = json.loads(config_str)
    modules = make_modules_list(modules_dir, vendor_config_path)
    with open(board_slots_path, "r", encoding="utf-8") as board_slots_file:
        board_slots = json.load(board_slots_file)
    return make_combined_config(config, board_slots, modules)


# Build list of json description of all modules in form
# {
# 	"id": "mod-foo",
# 	"description": "Foo Module",
# 	"compatible_slots": ["bar", "baz"]
# }
# Vendor config looks like
# {
# 	"mod-foo":"vendor_description"
# }
def make_modules_list(modules_dir: str, vendor_config_path: str) -> List[dict]:
    """
    Builds a list of available modules from .dtso files and vendor descriptions.

    Args:
        modules_dir (str): Directory with .dtso files describing modules.
        vendor_config_path (str): Path to vendor descriptions JSON.

    Returns:
        List[dict]: List of module definitions with ID, description, and compatible slots.
    """
    modules = []
    compatible_slots_pattern = re.compile(r"compatible-slots\s*=\s*\"(.*)\";")
    description_pattern = re.compile(r"description\s*=\s*\"(.*)\";")
    for dtso_filename in glob.glob(modules_dir + "/*.dtso"):
        with open(dtso_filename, "r", encoding="utf-8") as file:
            module = {"id": Path(dtso_filename).stem}
            for line in file:
                description = description_pattern.search(line)
                if description:
                    module["description"] = description.group(1)
                else:
                    compatible_slots = compatible_slots_pattern.search(line)
                    if compatible_slots:
                        module["compatible_slots"] = [compatible_slots.group(1)]
                if module.get("compatible_slots") and module.get("description"):
                    modules.append(module)
                    break

    modules.sort(key=lambda item: item["id"])
    if not os.path.exists(vendor_config_path):
        return modules

    with open(vendor_config_path, "r", encoding="utf-8") as vendor_config_file:
        vendor_config = json.load(vendor_config_file)
        vendor_modules = []
        wb_modules = []
        for module in modules:
            if module["id"] in vendor_config:
                module["description"] = vendor_config[module["id"]]
                vendor_modules.append(module)
            else:
                wb_modules.append(module)

        return vendor_modules + wb_modules


def main(args=None):
    parser = argparse.ArgumentParser(description="Config generator/updater for wb-hwconf-manager")
    parser.add_argument(
        "-j",
        "--to-confed",
        help="make JSON for wb-mqtt-confed from /etc/wb-hardware.conf",
        action="store_true",
    )
    parser.add_argument(
        "-J",
        "--from-confed",
        help="make /etc/wb-hardware.conf from wb-mqtt-confed output",
        action="store_true",
    )
    parser.add_argument(
        "-o",
        "--to-combined-config",
        help="convert stdin to combined configuration file",
        action="store_true",
    )
    args = parser.parse_args()

    logging.basicConfig(format="%(levelname)s: %(message)s")

    if args.to_confed:
        print(json.dumps(to_confed(CONFIG_PATH, get_board_config_path(), MODULES_DIR, VENDOR_CONFIG_PATH)))
        return

    if args.from_confed:
        print(
            json.dumps(
                from_confed(sys.stdin.read(), get_board_config_path(), MODULES_DIR, VENDOR_CONFIG_PATH),
                indent=4,
            )
        )
        return

    if args.to_combined_config:
        print(
            json.dumps(
                to_combined_config(
                    sys.stdin.read(), get_board_config_path(), MODULES_DIR, VENDOR_CONFIG_PATH
                ),
                indent=4,
            )
        )
        return

    parser.print_usage()


if __name__ == "__main__":
    main()
