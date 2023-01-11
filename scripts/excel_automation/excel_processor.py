# ----------------------------------------------------------------------------------------------------------------------
# - Package Imports -
# ----------------------------------------------------------------------------------------------------------------------
# General Packages
from __future__ import annotations
import pathlib
import pandas as pd

# Athena Packages

# Local Imports
from excel_automation.models import CustomModel, OriginalItem, ModelType

# ----------------------------------------------------------------------------------------------------------------------
# - Support Code -
# ----------------------------------------------------------------------------------------------------------------------
EXCEL_HEADERS:list[str] = [
    "Verbose Name",
    "Type",
    "Minecraft Item",
    "Parent",
    "Textures",
    "Custom Model Data",
    "Location",
    "Link to BBMODEL",
    "Link to JSON",
    "Link to texture folder",
    "Give Command",
]

# ----------------------------------------------------------------------------------------------------------------------
# - Code -
# ----------------------------------------------------------------------------------------------------------------------
def process_excel(excel_file:pathlib.Path) -> dict[OriginalItem,list[CustomModel]]:
    # Create some basic objects we'll need
    data:dict[OriginalItem,list[CustomModel]] = {}
    assigned_custom_model_data:list[int] = []

    # Read the Excel file
    #   and process the data
    excel_data:pd.DataFrame = pd.read_excel(excel_file)

    # Check if the headers are still as expected, else the data might get corrupted
    if set(cols:=excel_data.columns) != set(EXCEL_HEADERS):
        raise TypeError(f"Excel file does not satisfy the correct order of columns:\n{EXCEL_HEADERS}\nvs\n{cols}")

    for (
        verbose_name, model_type, minecraft_item, parent, textures_string, cmd, location,
        link_to_bbmodel, link_to_json, link_to_texture_folder, _, *_
    ) in pd.read_excel(excel_file).values:

        # Check the custom_model_data and cast to an int,
        #   because the json output has to use an int as well
        custom_model_data = int(cmd)
        if custom_model_data in assigned_custom_model_data:
            raise ValueError(f"Duplicate custom_model_data id found of: {custom_model_data}")

        # Makes sure the parent item is present in the data dict
        #   Without this, we'd have to have a couple more if checks, while now dict handles it
        original_item = OriginalItem(
            minecraft_item=minecraft_item,
            parent=parent,
            textures_string=textures_string,
        )
        data.setdefault(original_item, [])

        # Create model and store
        custom_model:CustomModel = CustomModel(
            verbose_name= verbose_name,
            type=ModelType(model_type),
            custom_model_data=custom_model_data,
            location=location,
            link_to_bbmodel=pathlib.Path(link_to_bbmodel.replace('../', '')) if isinstance(link_to_bbmodel, str) else None,
            link_to_json=pathlib.Path(link_to_json.replace('../', '')),
            link_to_texture_folder=pathlib.Path(link_to_texture_folder.replace('../', '')),
        )
        data[original_item].append(custom_model)

    return data
