# ----------------------------------------------------------------------------------------------------------------------
# - Package Imports -
# ----------------------------------------------------------------------------------------------------------------------
# General Packages
from __future__ import annotations
import json
import os
import pathlib
import zipfile

# Athena Packages

# Local Imports
from excel_automation.models import CustomModel, OriginalItem, ModelType
from excel_automation.excel_processor import process_excel

# ----------------------------------------------------------------------------------------------------------------------
# - Support Stuff -
# ----------------------------------------------------------------------------------------------------------------------
EXCEL_HEADERS:list[str] = [
    "original_item",
    "parent",
    "textures",
    "custom_model_data",
    "location",
    "internal_name",
    "link_to_bbmodel",
    "link_to_texture",
    "command",          # Auto generated and only useful in-game
]
SETTINGS_PATH = pathlib.Path("scripts/builder/settings.json")

# ----------------------------------------------------------------------------------------------------------------------
# - Functionality -
# ----------------------------------------------------------------------------------------------------------------------
def pack_cleaner(original_folder:pathlib.Path) -> None:
    # Clean the old json models from the pack
    models_path:pathlib.Path = original_folder.joinpath("assets/minecraft/models/item/")
    for file in models_path.iterdir():
        if file.is_file() and file.name.endswith(".json"):
            file.unlink()

def create_json_files(original_folder:pathlib.Path, data:dict[OriginalItem,list[CustomModel]]):
    for original_item, custom_models in data.items():

        path = original_folder.joinpath(
            f"assets/minecraft/models/{original_item.minecraft_item.split(':')[-1]}.json"
        )

        with open(path, "w+") as file:
            file.write(json.dumps(
                {
                    "parent": original_item.parent,
                    "textures": original_item.textures,
                    "overrides": [model.output_predicate() for model in custom_models]
                },
                indent=2
            ))

def pack_assembler(original_folder:pathlib.Path, output_files:list[pathlib.Path], *, excluded_filetypes:list[str]|tuple[str,...]=None):
    if excluded_filetypes is None:
        excluded_filetypes = []

    # check if the zipfile is already present
    #   Overwrites if allowed
    for output_file in output_files:
        # The zip file always has to be closed, so use with
        with zipfile.ZipFile(output_file, "w", zipfile.ZIP_DEFLATED) as zip_file:
            for root, folders, files in os.walk(original_folder):
                for file in filter(
                    # Uses a simple filter function to exclude those files which are excluded
                    lambda f: not f.endswith(tuple(excluded_filetypes)),
                    files
                ):
                    # Writes to zip
                    #   arcname is used to define a new file_path to put the file under. We stripped the base folder out of this
                    zip_file.write(
                        filename = (full_path := os.path.join(root, file)),
                        arcname = pathlib.Path(*pathlib.Path(full_path).parts[1:])
                    )

# ----------------------------------------------------------------------------------------------------------------------
# - Code -
# ----------------------------------------------------------------------------------------------------------------------
def main():
    if not SETTINGS_PATH.exists():
        raise FileNotFoundError(SETTINGS_PATH)

    with open(SETTINGS_PATH, "r") as file:
        settings = json.load(file)

    # Cleans the pack
    pack_cleaner(
        original_folder=pathlib.Path(settings["original_folder"])
    )

    # Extract the Excel data
    excel_data:dict[OriginalItem,list[CustomModel]] = process_excel(
        excel_file=pathlib.Path("data/custom_models.xlsx")
    )

    # Processes the data and creates the correct json files
    create_json_files(
        original_folder=pathlib.Path(settings["original_folder"]),
        data=excel_data
    )

    # Pack the completed
    version_str = '.'.join(str(v) for v in settings["version"])
    pack_assembler(
        original_folder=pathlib.Path(settings["original_folder"]),
        output_files=[
            pathlib.Path(file.format(version_str=version_str))
            for file in settings["output_files"]
        ],
        excluded_filetypes=settings["excluded_files"]
    )

if __name__ == '__main__':
    main()