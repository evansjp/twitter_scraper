import os
import hashlib
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from datetime import datetime

# Function to read credentials from a file
def get_credentials(filepath='credentials.txt'):
    credentials = {}
    with open(filepath, 'r') as file:
        for line in file:
            if line.strip():  # Ignore empty lines
                key, value = line.strip().split('=', 1)
                credentials[key] = value
    return credentials['username'], credentials['password']

# Function to read accounts to scrape from a file
def get_accounts_to_scrape(filepath='accounts_to_scrape.txt'):
    with open(filepath, 'r') as file:
        accounts = [line.strip() for line in file if line.strip()]
    return accounts

# Function to create the screenshots folder if it doesn't exist
def create_screenshots_folder():
    folder_name = "screenshots"
    if not os.path.exists(folder_name):
        os.makedirs(folder_name)
    return folder_name

# Function to extract tweet text
def extract_tweet_text(tweet_div):
    tweet_text = ""
    tweet_text_elements = tweet_div.find_elements(By.XPATH, './/div[@data-testid="tweetText"]/*')
    
    for element in tweet_text_elements:
        if element.tag_name == 'span':
            tweet_text += element.text
        elif element.tag_name == 'img':
            tweet_text += element.get_attribute('alt')
    
    return tweet_text

# Function to hash tweet content
def hash_tweet_content(tweet_text):
    return hashlib.md5(tweet_text.encode('utf-8')).hexdigest()

def twitter_login(driver, username, password):
    driver.get('https://twitter.com/login')
    time.sleep(5)  # Wait for the page to load

    # Enter the username
    username_input_xpath = '/html/body/div/div/div/div[1]/div[2]/div/div/div/div/div/div[2]/div[2]/div/div/div[2]/div[2]/div/div/div/div[4]/label/div/div[2]/div/input'
    username_input = driver.find_element(By.XPATH, username_input_xpath)
    username_input.send_keys(username)
    
    # Click the "Next" button
    next_button_xpath = '/html/body/div/div/div/div[1]/div[2]/div/div/div/div/div/div[2]/div[2]/div/div/div[2]/div[2]/div/div/div/button[2]'
    next_button = driver.find_element(By.XPATH, next_button_xpath)
    next_button.click()
    time.sleep(2)  # Wait for the password field to load

    # Enter the password
    password_input_xpath = '/html/body/div/div/div/div[1]/div[2]/div/div/div/div/div/div[2]/div[2]/div/div/div[2]/div[2]/div[1]/div/div/div[3]/div/label/div/div[2]/div[1]/input'
    password_input = driver.find_element(By.XPATH, password_input_xpath)
    password_input.send_keys(password)
    
    # Click the "Log In" button
    login_button_xpath = '/html/body/div/div/div/div[1]/div[2]/div/div/div/div/div/div[2]/div[2]/div/div/div[2]/div[2]/div[2]/div/div[1]/div/div/button'
    login_button = driver.find_element(By.XPATH, login_button_xpath)
    login_button.click()
    
    time.sleep(5)  # Wait for the home page to load after logging in

def scroll_and_collect(driver, screenshots_folder, account, max_tweets=5):
    last_height = driver.execute_script("return document.body.scrollHeight")
    
    # Find the section where the tweets are located
    tweets_section_xpath = '//section[starts-with(@aria-labelledby, "accessible-list-")]'
    try:
        tweets_section = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, tweets_section_xpath))
        )
    except TimeoutException:
        print("Could not find the tweets section.")
        return

    screenshot_count = 0

    while screenshot_count < max_tweets:
        tweet_divs = tweets_section.find_elements(By.XPATH, './/article[@data-testid="tweet"]')

        if not tweet_divs:
            print("No tweets found, breaking the loop.")
            break

        print(f"Found {len(tweet_divs)} tweets on this scroll.")

        for index, tweet_div in enumerate(tweet_divs):   
            try:
                # Extract tweet content and hash it
                tweet_text = extract_tweet_text(tweet_div)
                tweet_hash = hash_tweet_content(tweet_text)
                filename = f"{tweet_hash}.png"
                filepath = os.path.join(screenshots_folder, filename)
                
                # Check if the screenshot already exists
                if os.path.exists(filepath):
                    print(f"Screenshot {filename} already exists. Skipping...")
                    continue

                # Scroll the tweet into view if it's not fully visible
                tweet_top_position = tweet_div.location['y']
                tweet_bottom_position = tweet_top_position + tweet_div.size['height']
                window_height = driver.execute_script("return window.innerHeight")

                if tweet_top_position < 0 or tweet_bottom_position > window_height:
                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", tweet_div)
                    time.sleep(1)  # Wait a moment for the tweet to scroll and settle

                # Capture the screenshot
                screenshot = tweet_div.screenshot_as_png
                
                # Save the screenshot
                with open(filepath, 'wb') as f:
                    f.write(screenshot)
                
                print(f"Saved screenshot {filename}")
                screenshot_count += 1
            
            except NoSuchElementException:
                continue

            if screenshot_count >= max_tweets:
                break

        # Scroll down by a smaller amount to load more tweets
        driver.execute_script("window.scrollBy(0, window.innerHeight / 2);")
        time.sleep(2)
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            print("Reached the end of the page.")
            break
        last_height = new_height

def main():
    chrome_options = Options()
    # chrome_options.add_argument('--headless')  # Run in headless mode
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--no-sandbox')

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

    try:
        # Get user inputs from files
        username, password = get_credentials('credentials.txt')
        accounts_to_scrape = get_accounts_to_scrape('accounts_to_scrape.txt')

        # Log into Twitter
        twitter_login(driver, username, password)

        # Create the screenshots folder
        screenshots_folder = create_screenshots_folder()

        for account in accounts_to_scrape:
            driver.get(f'https://twitter.com/{account}')
            time.sleep(5)
            scroll_and_collect(driver, screenshots_folder, account, max_tweets=5)

    except Exception as e:
        print(f'An error occurred: {e}')
    finally:
        driver.quit()

if __name__ == '__main__':
    main()
