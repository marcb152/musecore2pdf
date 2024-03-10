from selenium import webdriver
from selenium.webdriver.common.by import By

from svglib.svglib import svg2rlg
from reportlab.graphics import renderPDF
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.utils import ImageReader
from PyPDF2 import PdfMerger

import requests
import time
import tempfile
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service

from configparser import ConfigParser
import tkinter as tk
from tkinter.messagebox import showwarning, showerror

from configparser import ConfigParser

class Extraction:
    def __init__(self, root: tk.Tk = None, status: tk.StringVar = None, progress_bar_var: tk.IntVar = None) -> None:
        self.root = root
        self.status = status
        self.progress_bar_var = progress_bar_var
        self.kill_ = False

        # default file path
        self.file_path = "render.pdf"

        config = ConfigParser()
        config.read("config.conf")

        self.driver_path = config.get("general", "driver_path")
        self.binary_location = config.get("general", "binary_location")

    def kill(self):
        self.kill_ = True


    def name_to_filename(self, name):
        """Convert a name to a valid filename"""
        avoid = ["\\", "/", ":", "*", "?", "\"", "<", ">", "|"]
        for char in avoid:
            name = name.replace(char, "")
        return name
    
    def progress_set_status(self, status, value):
        if self.status is not None:
            self.status.set(status)
        else:
            print(f"[INFO] {status}")
        if self.progress_bar_var is not None:
            self.progress_bar_var.set(value)
        
    def extract(self, url, render_path, is_directory=False):
        # open the browser
        if self.driver_path is not None and self.driver_path != "":
            service = Service(executable_path=self.driver_path)

        options = webdriver.ChromeOptions()
        if self.binary_location is not None and self.binary_location != "":
            options.binary_location = self.binary_location

        options = webdriver.ChromeOptions()
        options.add_argument("--incognito")
        options.add_argument("window-size=1920,1080")
        options.add_argument("--headless")
        options.add_argument("--disable-gpu")
        options.add_argument("--disable-extensions")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")

        if self.driver_path is not None and self.driver_path != "":
            browser = webdriver.Chrome(options=options, service=service)
        else:
            browser = webdriver.Chrome(options=options)

        self.progress_set_status("Opening the browser", 10)

        browser.get(url)
        
        self.progress_set_status("Waiting for the page to load", 20)

        # remove the cookie banner
        try:
            self.progress_set_status("Removing the cookie banner", 25)

            browser.find_element(By.CLASS_NAME, "css-1ucyjdz").click()
        except:
            pass

        # get the title of the score and convert it to a valid filename
        title = browser.find_element(By.CLASS_NAME, "nFRPI").text
        title = self.name_to_filename(title) + ".pdf"

        # get the number of pages
        scroll_widget = WebDriverWait(browser, 10).until(EC.presence_of_element_located((By.ID, "jmuse-scroller-component")))
        pages = browser.find_elements(By.CLASS_NAME, "EEnGW")
        nb_pages = len(pages)

        ratio = 70/nb_pages
        png = False

        # get the temporary dir to save the svg files
        temp_dir = tempfile.mkdtemp()

        browser.execute_script(f"arguments[0].scrollTop += {15};", scroll_widget)
        for i in range(nb_pages):

            self.progress_set_status(f"Downloading the page {i+1}/{nb_pages}", 20 + int(ratio*(i+1)))

            # wait for the image to load
            img = None
            while img == None:
                time.sleep(0.5)
                img = pages[i].find_element(By.TAG_NAME, "img").get_attribute("src")

                if self.kill_ == True:
                    browser.close()
                    return

            if ".svg" in img:
                r = requests.get(img)
                open(fr"{temp_dir}\page{i}.svg","w", encoding='utf-8').write(r.text)

                # Convert the svg file to pdf
                drawing = svg2rlg(fr"{temp_dir}\page{i}.svg")
                renderPDF.drawToFile(drawing,fr"{temp_dir}\page{i}.pdf")

            elif ".png" in img:
                if not png:
                    png = True
                    showwarning("Warning", "The score contains png images, the quality of the pdf may be affected")

                r = requests.get(img)
                open(fr"{temp_dir}\page{i}.png","wb").write(r.content)

                c = canvas.Canvas(fr"{temp_dir}\page{i}.pdf", pagesize=A4)
                img_ = ImageReader(fr"{temp_dir}\page{i}.png")
                c.drawImage(img_, 0, 0, A4[0], A4[1])
                c.save()

            else:
                showerror("Error", "The score contains unsupported images")
                browser.close()
                return

            # get the height of the page
            taille = pages[i].get_attribute("style")
            taille = taille.replace("width: ", "")
            taille = taille.replace("height: ", "")
            taille = taille.replace("px;", "")
            taille = taille.split(" ")
            height = int(taille[0])
            height = int(float(taille[1]))
            
            # scroll down to load the next page
            browser.execute_script(f"arguments[0].scrollTop += {height+15};", scroll_widget)
            time.sleep(0.5)
            browser.execute_script(f"arguments[0].scrollTop += {-20};", scroll_widget)
            time.sleep(0.5) 
            browser.execute_script(f"arguments[0].scrollTop += {20};", scroll_widget)

        browser.close()

        # merge the pdf files
        merger = PdfMerger()

        for i in range(nb_pages):
            merger.append(fr"{temp_dir}\page{i}.pdf")

        self.progress_set_status("Merging the pdf files", 95)

        if is_directory:
            render_path = render_path + "\\" + title

        self.file_path = render_path

        merger.write(render_path)
        merger.close()     

        self.progress_set_status("Done", 100)
