import os
import json
import time
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By

def run_checkin():
    options = Options()
    options.add_argument("--headless")
    # 1. SET A REAL USER AGENT (Prevents bot detection)
    options.set_preference("general.useragent.override", "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0")
    
    driver = webdriver.Firefox(options=options)
    driver.set_window_size(1920, 1080) # Ensure the grid isn't cramped

    try:
        # 2. LOAD DOMAIN
        driver.get("https://game.skport.com")
        time.sleep(2)
        
        # 3. INJECT COOKIES
        cookies_raw = os.getenv("SKPORT_COOKIES")
        if not cookies_raw:
            print("Error: SKPORT_COOKIES secret not found.")
            return

        cookies = json.loads(cookies_raw)
        for cookie in cookies:
            if 'sameSite' in cookie:
                if cookie['sameSite'] not in ["Strict", "Lax", "None"]:
                    del cookie['sameSite']
            driver.add_cookie(cookie)

        # 4. GO TO SIGN-IN PAGE
        driver.get("https://game.skport.com/endfield/sign-in?header=0&hg_media=launcher&hg_link_campaign=icon")
        time.sleep(8) # Wait extra time for the session to "take"

        # DEBUG: Check if we are actually logged in
        if "Log in" in driver.page_source:
            print("WARNING: 'Log in' text detected. Cookies might be invalid or expired.")
            driver.save_screenshot("login_failed.png") 

        # 5. FIND THE REWARD
        items = driver.find_elements(By.CLASS_NAME, "sc-nuIvE")
        for item in items:
            if item.find_elements(By.ID, "completed-overlay"):
                continue
                
            if item.find_elements(By.ID, "lottie-container"):
                day_label = item.find_element(By.CLASS_NAME, "sc-guPfGz")
                print(f"Verified {day_label.text} is ready. Clicking...")
                
                # TARGET THE BUTTON
                target = item.find_element(By.CLASS_NAME, "sc-dltKUw")
                
                # 6. USE JAVASCRIPT CLICK (Bypasses the "Obscured" error)
                driver.execute_script("arguments[0].click();", target)
                
                print("Claim action sent via JavaScript.")
                time.sleep(5)
                return 
            
        print("No claimable day found. It's possible you're already signed in or reset hasn't happened.")

    except Exception as e:
        print(f"An error occurred: {e}")
        driver.save_screenshot("error_state.png") # This helps us see the "obscuring" element
    finally:
        driver.quit()

if __name__ == "__main__":
    run_checkin()
