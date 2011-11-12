

from cx_Freeze import setup, Executable

copyDependentFiles=True
silent = True
includes = ["lxml", "lxml._elementpath", "lxml.etree", "pyreadline", "pyreadline.release", "gzip"]
excludes = ["tcl", "tk", "tkinter"]
setup(
    name = "The Mole",
    version = "0.3",
    description = "The Mole: Digging up your data",
    options = {
        "build_exe": {
            "includes": includes,                          
            "excludes": excludes
            }
        },
    executables = [Executable("mole.py")]
)
