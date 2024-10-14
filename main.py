import time
import os

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
import requests
import winreg as reg
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Proxy information
proxy_host = os.getenv("PROXY_HOST")
proxy_port = os.getenv("PROXY_PORT")
proxy_username = os.getenv("PROXY_USERNAME")
proxy_password = os.getenv("PROXY_PASSWORD")

# Path for proxy extension (create a temporary folder to store extension files)
extension_folder = os.path.join(os.getcwd(), "proxy_extension")
if not os.path.exists(extension_folder):
    os.makedirs(extension_folder)

# File manifest.json
manifest_content = '''
{
  "version": "1.0.0",
  "manifest_version": 2,
  "name": "Proxy Extension",
  "permissions": [
    "proxy",
    "tabs",
    "unlimitedStorage",
    "storage",
    "<all_urls>",
    "webRequest",
    "webRequestBlocking"
  ],
  "background": {
    "scripts": ["background.js"]
  },
  "minimum_chrome_version": "76.0.0"
}
'''

# File background.js
background_js_content = f'''
var config = {{
    mode: "fixed_servers",
    rules: {{
        singleProxy: {{
            scheme: "http",
            host: "{proxy_host}",
            port: parseInt({proxy_port})
        }},
        bypassList: ["localhost", "127.0.0.1"]
    }}
}};

chrome.proxy.settings.set(
    {{value: config, scope: "regular"}},
    function() {{}}
);

chrome.webRequest.onAuthRequired.addListener(
    function(details) {{
        var authCredentials = {{
            username: "{proxy_username}" if "{proxy_username}" else "",
            password: "{proxy_password}" if "{proxy_password}" else ""
        }};
        return {{
            authCredentials: authCredentials
        }};
    }},
    {{urls: ["<all_urls>"]}},
    ['blocking']
);
'''

# Save manifest.json file
with open(os.path.join(extension_folder, "manifest.json"), "w") as f:
    f.write(manifest_content)

# Save background.js file
with open(os.path.join(extension_folder, "background.js"), "w") as f:
    f.write(background_js_content)

# Setup Chrome options
chrome_options = Options()

# Load extension from the newly created folder
# chrome_options.add_argument(f"--load-extension={extension_folder}")

# Disable bot detection via WebDriver
chrome_options.add_experimental_option('excludeSwitches', ['enable-automation'])
chrome_options.add_experimental_option('useAutomationExtension', False)
# Disable location detection
chrome_options.add_argument("--use-fake-ui-for-media-stream")

''' add spoof location according to proxy IP using IP geolocation 
https://ipinfo.io/(ip_proxy)/json
'''
def get_location(ip):
    url = f"https://ipinfo.io/{ip}/json"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        print(data)
        return data['loc']
    return None

# Set location
    
# Disable headless mode and automation detection
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-blink-features=AutomationControlled')

# Initialize WebDriver with proxy extension
service = Service()
driver = webdriver.Chrome(service=service, options=chrome_options)

# Disable bot detection via JavaScript
driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

# Open pixelscan.net for testing
# get active IP 
driver.get("https://api4.ipify.org/")
# 
ip = driver.find_element(By.TAG_NAME, "body").text
location = get_location(ip)
print(f'your IP {ip}')
latitude, longitude = location.split(",")

# Set location using Chrome DevTools Protocol (CDP)
def set_location(latitude, longitude):
    # Define the registry path for location settings
    registry_path = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Location And Sensors\Location"
    
    try:
        # Open the registry key with write access
        with reg.OpenKey(reg.HKEY_CURRENT_USER, registry_path, 0, reg.KEY_SET_VALUE) as key:
            # Set the latitude and longitude values (as strings)
            reg.SetValueEx(key, "Latitude", 0, reg.REG_SZ, str(latitude))
            reg.SetValueEx(key, "Longitude", 0, reg.REG_SZ, str(longitude))
            print(f"Default location set to Latitude: {latitude}, Longitude: {longitude}")
    except Exception as e:
        print(f"Failed to set location: {e}")

# Set location
set_location(latitude, longitude)

driver.refresh()
# Open pixelscan.net for testing
driver.get("https://pixelscan.net/")

# Wait a few seconds to ensure the page is fully loaded
time.sleep(30)

# Take a screenshot to ensure detection results
driver.save_screenshot("pixelscan_test.png")

# Close browser
driver.quit()

# Clean up extension files after completion
try:
    os.remove(os.path.join(extension_folder, "manifest.json"))
    os.remove(os.path.join(extension_folder, "background.js"))
    os.rmdir(extension_folder)
except Exception as e:
    print(f"Error deleting extension files: {e}")
