import os
import json
import time
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait # NEW
from selenium.webdriver.support import expected_conditions as EC # NEW

def run_checkin():
    options = Options()
    options.add_argument("--headless")
    options.set_preference("general.useragent.override", "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0")
    driver = webdriver.Firefox(options=options)
    driver.set_window_size(1920, 1080)

    try:
        # 1. Load Page
        url = "https://game.skport.com/endfield/sign-in?header=0&hg_media=launcher&hg_link_campaign=icon"
        driver.get(url)
        print("Waiting for page load...")
        time.sleep(5) # Shorter wait since we aren't loading the base domain first

        # 2. Login Flow
        try:
            print("Logging in with credentials...")
            email = os.getenv("SKPORT_EMAIL")
            password = os.getenv("SKPORT_PASSWORD")
            
            if email and password:
                # Wait for and click the "Log In" trigger
                login_button_main = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, "//div[contains(text(), 'Please log in first')]/following-sibling::div//div[contains(text(), 'Log In')]"))
                )
                driver.execute_script("arguments[0].click();", login_button_main)
                
                # Fill out the modal
                email_input = WebDriverWait(driver, 10).until(
                    EC.visibility_of_element_located((By.CSS_SELECTOR, "input[type='text']"))
                )
                password_input = driver.find_element(By.CSS_SELECTOR, "input[type='password']")
                
                email_input.send_keys(email)
                password_input.send_keys(password)
                
                # Submit
                login_btn = driver.find_element(By.CSS_SELECTOR, "button[type='submit']")
                driver.execute_script("arguments[0].click();", login_btn)
                
                # Wait for the modal to disappear
                WebDriverWait(driver, 15).until(
                    EC.invisibility_of_element_located((By.XPATH, "//div[contains(text(), 'Please log in first')]"))
                )
                print("✅ Login successful!")
            else:
                print("❌ Missing SKPORT_EMAIL or SKPORT_PASSWORD in GitHub Secrets.")
                return
        except Exception as e:
            print("Login failed or already signed in. Proceeding...")

        # 3. Expand Grid
        try:
            show_all_btn = driver.find_element(By.CSS_SELECTOR, ".sc-fiHwYe")
            driver.execute_script("arguments[0].click();", show_all_btn)
            time.sleep(2)
        except:
            pass

# 4. Claim Logic
        try:
            print("Searching for reward...")
            # 1. Wait for the lottie animation (the glow) to appear
            # We use a shorter wait here to avoid long hangs
            animation = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.ID, "lottie-container"))
            )
            print("✨ Found claimable reward animation!")

            # 2. To be safe, we want to click the container that holds the whole day box.
            # We'll climb up the tree to find the day wrapper (sc-gcnLPh)
            # or simply use JS to click the animation's grandparent.
            target = animation.find_element(By.XPATH, "./ancestor::div[contains(@class, 'sc-gcnLPh')]")
            
            print("Clicking reward container...")
            driver.execute_script("arguments[0].click();", target)
            
            print("✅ Success! Reward claimed.")
            time.sleep(5) # Give it time to register the click

        except Exception as e:
            # If lottie-container isn't found, Day 3 probably already has the "Check" mark.
            print("No claimable animation found. You likely already claimed today's reward.")

    except Exception as e:
        print(f"Error during execution: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    run_checkin()
