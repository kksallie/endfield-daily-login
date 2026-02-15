import os
import json
import time
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By

def run_checkin():
    options = Options()
    options.add_argument("--headless")
    driver = webdriver.Firefox(options=options)

    try:
        # 1. Open the domain to set the context for cookies
        driver.get("https://game.skport.com")
        
        # 2. Inject cookies from environment variable
        cookies_raw = os.getenv("SKPORT_COOKIES")
        if not cookies_raw:
            print("Error: SKPORT_COOKIES secret not found.")
            return

        cookies = json.loads(cookies_raw)
        for cookie in cookies:
            # Selenium doesn't like 'sameSite' in some formats; clean it if needed
            if 'sameSite' in cookie:
                if cookie['sameSite'] not in ["Strict", "Lax", "None"]:
                    del cookie['sameSite']
            driver.add_cookie(cookie)

        # 3. Go to the Sign-in page
        driver.get("https://game.skport.com/endfield/sign-in")
        time.sleep(5) # Wait for page JS to load

        # 4. Logic to find and click the active sign-in button
        items = driver.find_elements(By.CLASS_NAME, "sc-nuIvE")
        for item in items:
            # 1. Check if this day is already completed
            if item.find_elements(By.ID, "completed-overlay"):
                continue
                
            # 2. Check for the 'lottie-container' (the claimable animation)
            # This is the unique marker you just found in the HTML!
            if item.find_elements(By.ID, "lottie-container"):
                day_label = item.find_element(By.CLASS_NAME, "sc-guPfGz")
                print(f"Verified {day_label.text} is ready to claim. Clicking...")
                
                # Click the icon container
                target = item.find_element(By.CLASS_NAME, "sc-dltKUw")
                target.click()
                print("Claim action sent.")
                return # Exit successfully
            
        print("No claimable day (lottie-container) found. Reset likely hasn't happened yet.")

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    run_checkin()
