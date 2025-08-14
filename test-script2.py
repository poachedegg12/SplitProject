from pybanana.api import PyBanana

# Create the Gamebanana API interface
api = PyBanana()

# Replace this with the actual mod ID
mod_id = 398632  # Example: https://gamebanana.com/mods/398632

# Fetch mod details


ini_id = 605787
if ini_id:
    try:
        mod = api.get_mod_profile(ini_id)  # Example mod ID
        if mod:
            print(f"Mod: {mod.name}")
            print(f"Author: {mod.submitter.name}")
            print(f"Description: {mod.text}")
            print(f"Embeddables: {mod.thumbnail_url}")
    except Exception as e:
        print(f"Failed to handle mod ID: {e}")

import requests

mod_id = 605787
url = f"https://gamebanana.com/mods/{mod_id}?json=1"
response = requests.get(url)
print(response.status_code)
print(response.text)
# Raise error if bad response

mod_data = response.json()

thumbnail_url = mod_data.get("_sThumbnailUrl")
mod_name = mod_data.get("_sName")
author_name = mod_data.get("_aSubmitter", {}).get("_sName")
description_html = mod_data.get("_sText", "")

print("Mod Name:", mod_name)
print("Author:", author_name)
print("Thumbnail URL:", thumbnail_url)
print("Description (HTML):", description_html)
