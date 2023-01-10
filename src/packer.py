# ----------------------------------------------------------------------------------------------------------------------
# - Package Imports -
# ----------------------------------------------------------------------------------------------------------------------
# General Packages
from __future__ import annotations
import os
import pathlib
import zipfile

# Athena Packages

# Local Imports

# ----------------------------------------------------------------------------------------------------------------------
# - Code -
# ----------------------------------------------------------------------------------------------------------------------
def packer(original_folder:pathlib.Path, output_file:pathlib.Path, *, excluded_filetypes:list[str]|tuple[str,...]=None, overwrite:bool=False):
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


if __name__ == '__main__':
    version = (0,0,0)

    packer(
        original_folder=pathlib.Path("texturepack/"),
        output_file=pathlib.Path(f"output/blockgame_{'.'.join(str(v) for v in version)}.zip"),
        excluded_filetypes=(".bbmodel",),
        overwrite=True
    )