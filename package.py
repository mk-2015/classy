import configparser
import datetime
import shutil
from pathlib import Path
import subprocess

pkg = "classy"
package_dir = Path("package")
venv_dir = Path(".venv")

if package_dir.exists():
    shutil.rmtree(package_dir)

shutil.rmtree(venv_dir)
subprocess.run(["python", "-m", "venv", ".venv"], check=True)
subprocess.run(["source", ".venv/bin/activate"], check=True)
subprocess.run(["python", "-m", "pip", "build"], check=True)
subprocess.run(["python", "-m", "pip", "-r", "requirements.txt"], check=True)
subprocess.run(["python", "-m", "build"], check=True)

package_dir.mkdir(parents=True, exist_ok=True)
if Path("dist").exists():
    shutil.copytree("dist", package_dir / "dist")

metadata_folder = next(Path().glob(f"*{pkg}*.egg-info"), None) or next(Path("src").glob(f"*{pkg}*.egg-info"), None)
if metadata_folder and metadata_folder.exists():
    shutil.copytree(metadata_folder, package_dir / metadata_folder.name)

info_file = package_dir / ".info.r"
current_time = datetime.datetime.now().strftime("%Y/%m:%d %H:%M:%S")
info_file.write_text(f"Time: {current_time}\nPackage: {pkg}\n")

config = configparser.ConfigParser()
config["CONFIG"] = {"IsPackage": "TRUE"}
with open(package_dir / ".gitinfo.r.ini", "w") as configfile:
    config.write(configfile)

subprocess.run(["deactivate"], check=True)