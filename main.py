from configparser import ConfigParser
from extraction import Extraction

config = ConfigParser()
config.read("config.conf")

url = config.get("general", "url")
render_path = config.get("general", "render_path")
file_name = config.get("general", "file_name")

if ".pdf" not in file_name:
    file_name += ".pdf"

extraction = Extraction()
extraction.extract(url, render_path+file_name)