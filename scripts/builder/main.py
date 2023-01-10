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
    "parent_item", "custom_model_data", "model", "model_location", "internal_name", "link_to_bbmodel", "link_to_texture"
]
SETTINGS_PATH = pathlib.Path("scripts/builder/settings.json")

@dataclasses.dataclass(slots=True)
class CustomModel:
    parent_item:str
    custom_model_data:int
    model:str
    model_location:str

    def output_overrides(self) -> dict:
        return {"predicate": {"custom_model_data":self.custom_model_data}, "model": self.model}

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

    if set(excel_data.columns) != set(EXCEL_HEADERS):
        raise TypeError("Excel file does not satisfy the correct order of columns:")

    for parent_item, cmd, model, model_location, *_ in pd.read_excel(excel_file).values:
        # Check the custom_model_data and cast to an int,
        #   because the json output has to use an int as well
        custom_model_data = int(cmd)
        if custom_model_data in assigned_custom_model_data:
            raise ValueError(f"Duplicate custom_model_data id found of: {custom_model_data}")

        # Makes sure the parent item is present in the data dict
        #   Without this, we'd have to have a couple more if checks, while now dict handles it
        data.setdefault(parent_item, [])

        # Create model and store
        data[parent_item].append(CustomModel(
            parent_item=parent_item,
            custom_model_data=custom_model_data,
            model=model,
            model_location=model_location
        ))

    return data

def create_json_files(original_folder:pathlib.Path, data:dict[str,list[CustomModel]]):
    for parent, custom_models in data.items():
        with open(original_folder.joinpath(f"assets/minecraft/models/{parent}.json"), "w+") as file:
            file.write(json.dumps(
                {"parent": parent, "overrides": [model.output_overrides() for model in custom_models]},
                indent=2
            ))

def pack_assembler(original_folder:pathlib.Path, output_file:pathlib.Path, *, excluded_filetypes:list[str]|tuple[str,...]=None, overwrite:bool=False):
    if excluded_filetypes is None:
        excluded_filetypes = []

    # check if the zipfile is already present
    #   Overwrites if allowed
    if output_file.is_file():
        if not overwrite:
            raise FileExistsError(
                "A zipfile was found at the 'output_file' location." 
                " Overwriting an existing zipfile is not enabled"
            )
        else:
            os.remove(output_file)

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
        output_file=pathlib.Path(settings["output_file".format(version_str=version_str)]),
        excluded_filetypes=settings["excluded_files"],
        overwrite=True
    )

if __name__ == '__main__':
    main()