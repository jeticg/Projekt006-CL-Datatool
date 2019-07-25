import os


def getPTPath(moduleName):
    if os.path.expandvars("$NATLANG_MODEL") == "$NATLANG_MODEL":
        nlPath = os.path.expanduser("~/.natlang") + moduleName
    else:
        nlPath = os.path.expandvars("$NATLANG_MODEL") + moduleName
    return nlPath
