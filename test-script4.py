import time

from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

options = Options()
options.headless = True  # Run browser without GUI

driver = webdriver.Chrome(options=options)  # Requires chromedriver installed and in PATH
driver.get("https://gamebanana.com/mods?search=pizza+tower")

time.sleep(5)  # Wait for JS to load content

html = driver.page_source
driver.quit()

soup = BeautifulSoup(html, "html.parser")

# Find mod items - you’ll need to inspect the live page for correct selectors
mods = soup.select("selector_for_mod_items")

for mod in mods:
    title = mod.select_one("selector_for_mod_title").get_text(strip=True)
    link = mod.select_one("selector_for_mod_link")['href']
    print(title, link)
