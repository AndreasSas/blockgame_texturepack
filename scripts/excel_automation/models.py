# ----------------------------------------------------------------------------------------------------------------------
# - Package Imports -
# ----------------------------------------------------------------------------------------------------------------------
# General Packages
from __future__ import annotations

import pathlib
from dataclasses import dataclass, InitVar, field
import json
import enum

# Athena Packages

# Local Imports

# ----------------------------------------------------------------------------------------------------------------------
# - Enums -
# ----------------------------------------------------------------------------------------------------------------------
class ModelType(enum.StrEnum):
    model = enum.auto()
    item = enum.auto()

# ----------------------------------------------------------------------------------------------------------------------
# - Code -
# ----------------------------------------------------------------------------------------------------------------------
@dataclass(slots=True)
class CustomModel:
    verbose_name:str
    type:ModelType

    custom_model_data:int
    location:str

    link_to_bbmodel:pathlib.Path|None = None
    link_to_json:pathlib.Path|None = None
    link_to_texture_folder:pathlib.Path|None = None

    def __post_init__(self):
        # Validate the filepaths
        for path in (self.link_to_bbmodel, self.link_to_json, self.link_to_texture_folder):
            if path is not None and not path.exists():
                raise FileNotFoundError(path)

    def output_predicate(self) -> dict:
        return {"predicate": {"custom_model_data":self.custom_model_data}, "model": self.location}

# ----------------------------------------------------------------------------------------------------------------------
@dataclass(slots=True)
class OriginalItem:
    minecraft_item:str
    parent:str
    textures:dict = field(init=False)

    # init args
    textures_string:InitVar[str]

    def __post_init__(self,textures_string:str):
        self.textures = json.loads(textures_string.replace("'",'"'))

    def __hash__(self):
        # hash on the original item name,
        #   all other values should be the same
        return hash(self.minecraft_item)