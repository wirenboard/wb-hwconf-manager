#!/usr/bin/env python3

import json
import glob
import re
import argparse
import sys
from pathlib import Path

MODULES_DIR = "/usr/share/wb-hwconf-manager/modules"
SLOTS_PATH = "/var/lib/wb-hwconf-manager/system.conf"
CONFIG_PATH = "/etc/wb-hardware.conf"

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


def to_combined_config(config_str: str, board_slots_path: str):
    config = json.loads(config_str)
    # Config has slots property, it is actually old config format, pass as is
    if "slots" in config:
        return config

    with open(board_slots_path, "r", encoding="utf-8") as board_slots_file:
        board_slots = json.load(board_slots_file)

    for slot in board_slots["slots"]:
        slot_config = config.get(slot["slot_id"])
        if slot_config:
            slot["module"] = slot_config["module"]
            slot["options"] = slot_config["options"]
        del slot["slot_id"]
    return board_slots


def to_confed(config_path: str, board_slots_path: str, modules_dir: str):
    with open(config_path, "r", encoding="utf-8") as config_file:
        config = to_combined_config(config_file.read(), board_slots_path)
        config["modules"] = make_modules_list(modules_dir)
        return config


def from_confed(confed_config_str: str, board_slots_path: str):
    confed_config = json.loads(confed_config_str)
    with open(board_slots_path, "r", encoding="utf-8") as board_slots_file:
        board_slots = json.load(board_slots_file)

    id_to_slots_id = {slot["id"]: slot for slot in board_slots["slots"]}

    new_config = {}

    for config_slot in confed_config["slots"]:
        board_slot = id_to_slots_id.get(config_slot["id"])
        if board_slot is None:
            continue
        slot_id = board_slot.get("slot_id")
        if slot_id is not None and (
            board_slot.get("module") != config_slot.get("module", "")
            or board_slot.get("options") != config_slot.get("options", {})
        ):
            new_config[slot_id] = {
                "module": config_slot["module"],
                "options": config_slot["options"],
            }

    return new_config


# Build json description of all modules in form
# {
# 	"id": "mod-foo",
# 	"description": "Foo Module",
# 	"compatible_slots": ["bar", "baz"]
# }
# and put it to "modules" array
def make_modules_list(modules_dir: str):
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
    modules = sorted(modules, key=lambda item: item["id"])
    return modules


def main(args=None):
    parser = argparse.ArgumentParser(
        description="Config generator/updater for wb-hwconf-manager"
    )
    parser.add_argument(
        "-j",
        "--to-json",
        help="make JSON for wb-mqtt-confed from /etc/wb-hardware.conf",
        action="store_true",
    )
    parser.add_argument(
        "-J",
        "--from-json",
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

    if args.to_json:
        print(json.dumps(to_confed(CONFIG_PATH, SLOTS_PATH, MODULES_DIR)))
        return

    if args.from_json:
        print(json.dumps(from_confed(sys.stdin.read(), SLOTS_PATH), indent=4))
        return

    if args.to_combined_config:
        print(json.dumps(to_combined_config(sys.stdin.read(), SLOTS_PATH), indent=4))
        return

    parser.print_usage()


if __name__ == "__main__":
    main()
