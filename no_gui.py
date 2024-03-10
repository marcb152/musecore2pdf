from configparser import ConfigParser
from extraction import Extraction

# load the configuration
config = ConfigParser()
config.read("config.conf")

url = config.get("main.py", "url")
render_path = config.get("main.py", "render_path")
file_name = config.get("main.py", "file_name")

if ".pdf" not in file_name:
    file_name += ".pdf"

# extract the PDF from the URL
extraction = Extraction()
extraction.extract(url, render_path+file_name)