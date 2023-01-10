# ----------------------------------------------------------------------------------------------------------------------
# - Package Imports -
# ----------------------------------------------------------------------------------------------------------------------
# General Packages
from __future__ import annotations
import dataclasses
import json
import os
import pandas as pd
import pathlib
import zipfile

# Athena Packages

# Local Imports

# ----------------------------------------------------------------------------------------------------------------------
# - Support Stuff -
# ----------------------------------------------------------------------------------------------------------------------
EXCEL_HEADERS:list[str] = [
    "original_item", "custom_model_data", "location", "internal_name", "link_to_bbmodel", "link_to_texture", "command"
]
SETTINGS_PATH = pathlib.Path("scripts/builder/settings.json")

@dataclasses.dataclass(slots=True)
class CustomModel:
    custom_model_data:int
    location:str
    original_item:str

    def output_overrides(self) -> dict:
        return {"predicate": {"custom_model_data":self.custom_model_data}, "model": self.location}

# ----------------------------------------------------------------------------------------------------------------------
# - Functionality -
# ----------------------------------------------------------------------------------------------------------------------
def pack_cleaner(original_folder:pathlib.Path) -> None:
    # Clean the old json models from the pack
    models_path:pathlib.Path = original_folder.joinpath("assets/minecraft/models/item/")
    for file in models_path.iterdir():
        if file.is_file() and file.name.endswith(".json"):
            file.unlink()

def process_excel(excel_file:pathlib.Path) -> dict[str,list[CustomModel]]:
    # Create some basic objects we'll need
    data:dict[str,list[CustomModel]] = {}
    assigned_custom_model_data:list[int] = []

    # Read the Excel file
    #   and process the data
    excel_data:pd.DataFrame = pd.read_excel(excel_file)

    if set(cols:=excel_data.columns) != set(EXCEL_HEADERS):
        raise TypeError(f"Excel file does not satisfy the correct order of columns:\n{EXCEL_HEADERS}\nvs\n{cols}")

    for original_item, cmd, location, *_ in pd.read_excel(excel_file).values:
        # Check the custom_model_data and cast to an int,
        #   because the json output has to use an int as well
        custom_model_data = int(cmd)
        if custom_model_data in assigned_custom_model_data:
            raise ValueError(f"Duplicate custom_model_data id found of: {custom_model_data}")

        # Makes sure the parent item is present in the data dict
        #   Without this, we'd have to have a couple more if checks, while now dict handles it
        data.setdefault(original_item, [])

        # Create model and store
        data[original_item].append(CustomModel(
            custom_model_data=custom_model_data,
            location=location,
            original_item=original_item
        ))

    return data

def create_json_files(original_folder:pathlib.Path, data:dict[str,list[CustomModel]]):
    for original_item, custom_models in data.items():
        with open(original_folder.joinpath(f"assets/minecraft/models/{original_item.split(':')[-1]}.json"), "w+") as file:
            file.write(json.dumps(
                {
                    "parent": f"item/generated",
                    "textures": {"layer0":original_item},
                    "overrides": [model.output_overrides() for model in custom_models]
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
                    #   arcname is used to define a new path to put the file under. We stripped the base folder out of this
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
    excel_data:dict[str,list[CustomModel]] = process_excel(
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