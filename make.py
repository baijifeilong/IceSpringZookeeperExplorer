import pathlib
import shutil

import PyInstaller.__main__
import py7zr

name = "IceSpringZookeeperExplorer"

excluded_files = """
Qt5DataVisualization.dll
Qt5Pdf.dll
Qt5Quick.dll
Qt5VirtualKeyboard.dll
d3dcompiler_47.dll
libGLESv2.dll
opengl32sw.dll
""".strip().splitlines()

print("Building...")
if pathlib.Path("dist").exists():
    print("Folder dist exists, removing...")
    shutil.rmtree("dist")

if pathlib.Path(f"{name}.7z").exists():
    print("Target archive exists, removing...")
    pathlib.Path(f"{name}.7z").unlink()

print("Packing...")
PyInstaller.__main__.run([
    "main.py",
    "--noconsole",
    "--noupx",
    "--name",
    name
])

print("Cleaning...")
for file in pathlib.Path("dist").glob("*/*"):
    if file.name in excluded_files:
        print(f"Removing {file.name}")
        file.unlink()

print("Compressing...")
zf = py7zr.SevenZipFile(f"{name}.7z", "w")
zf.writeall(f"dist/{name}")
