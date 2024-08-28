import base64
import hashlib
import io
import os
import psycopg2
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import pandas as pd
from credentials import get_scraper_credentials
from datetime import datetime
import requests
# from PIL import Image

DB_NAME='prydwen_analytica_api_development'
DB_USER='postgres'
DB_PASSWORD = 'Maryann1'
DB_HOST='localhost'

# Your Twitter credentials
# USERNAME = 'PrydwenAI'
# PASSWORD = '!Maryann101'

# Accounts to scrape
ACCOUNTS_TO_SCRAPE = [
    'alexhaobao',
]

def get_db_connection():
    """Establishes a connection to the PostgreSQL database."""
    return psycopg2.connect(
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST
    )

def get_accounts_to_scrape(cursor):
    """Fetch the accounts to scrape from the database."""
    cursor.execute("SELECT account FROM Accounts WHERE user_id = 1;")
    return [row[0] for row in cursor.fetchall()]

# def save_post(cursor, account_id, timestamp, content, encoded_image, hash_value):
#     """Inserts a new post into the Posts table if it doesn't already exist."""
#     cursor.execute("SELECT 1 FROM Posts WHERE hash = %s LIMIT 1;", (hash_value,))
#     if cursor.fetchone():
#         print(f"Post with hash {hash_value} already exists. Skipping...")
#         return False

#     # Insert the post into the database with the encoded image
#     cursor.execute(
#         """
#         INSERT INTO Posts (account_id, timestamp, content, image, hash, created_at, updated_at)
#         VALUES (%s, %s, %s, %s, %s, %s, %s);
#         """,
#         (account_id, timestamp, content, encoded_image, hash_value, datetime.now(), datetime.now())
#     )
#     print(f"Post with hash {hash_value} inserted.")
#     return True

def upload_post(account_id, timestamp, content, image_data, hash_value):
    url = 'http://localhost:4000/api/v1/posts'
    
    files = {'post[image]': ('screenshot.png', image_data, 'image/png')}

    # files = {
    #     'post[image]': image_file
    # }
    
    data = {
        'post[account_id]': account_id,
        'post[timestamp]': timestamp,
        'post[content]': content,
        'post[hash]': hash_value,
    }

    response = requests.post(url, files=files, data=data, headers={})
    print(response.json())

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


def scroll_and_collect(driver, account_id, cursor, max_tweets=5):
    tweets_data = []
    last_height = driver.execute_script("return document.body.scrollHeight")
    
    # Find the section where the tweets are located
    tweets_section_xpath = '//section[starts-with(@aria-labelledby, "accessible-list-")]'
    try:
        tweets_section = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, tweets_section_xpath))
        )
    except TimeoutException:
        print("Could not find the tweets section.")
        return tweets_data

    while len(tweets_data) < max_tweets:
        tweet_divs = tweets_section.find_elements(By.XPATH, './/article[@data-testid="tweet"]')

        if not tweet_divs:
            print("No tweets found, breaking the loop.")
            break

        print(f"Found {len(tweet_divs)} tweets on this scroll.")

        for index, tweet_div in enumerate(tweet_divs):   
            try:
                # Scroll the tweet into view if it's not fully visible
                tweet_top_position = tweet_div.location['y']
                tweet_bottom_position = tweet_top_position + tweet_div.size['height']
                window_height = driver.execute_script("return window.innerHeight")

                if tweet_top_position < 0 or tweet_bottom_position > window_height:
                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", tweet_div)
                    time.sleep(1)  # Wait a moment for the tweet to scroll and settle

                # Extract tweet content and hash
                content = extract_tweet_text(tweet_div)
                tweet_hash = hash_tweet_content(content)

                # Check if the tweet with this hash already exists in the database
                cursor.execute("SELECT 1 FROM Posts WHERE hash = %s LIMIT 1;", (tweet_hash,))
                if cursor.fetchone():
                    print(f"Tweet with hash {tweet_hash} already exists. Skipping...")
                    continue

                # If the tweet is new, capture the screenshot & time of tweet
                screenshot = tweet_div.screenshot_as_png
                timestamp = tweet_div.find_element(By.XPATH, './/time').get_attribute('datetime')
        
                print(f"Tweet {len(tweets_data) + 1}: {content}")

                tweets_data.append({
                    'account_id': account_id,
                    'timestamp': timestamp,
                    'content': content,
                    'image': screenshot,
                    'hash': tweet_hash,
                })
            
            except NoSuchElementException:
                continue

            if len(tweets_data) >= max_tweets:
                break

        # Scroll down by a smaller amount to load more tweets
        driver.execute_script("window.scrollBy(0, window.innerHeight / 2);")
        time.sleep(2)
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            print("Reached the end of the page.")
            break
        last_height = new_height

    return tweets_data

def extract_tweet_text(tweet_div):
    # Initialize an empty string for the tweet text
    tweet_text = ""
    
    # Find all elements within the tweet text div, including text and images
    tweet_text_elements = tweet_div.find_elements(By.XPATH, './/div[@data-testid="tweetText"]/*')
    
    for element in tweet_text_elements:
        if element.tag_name == 'span':
            # If it's a span, add its text content
            tweet_text += element.text
        elif element.tag_name == 'img':
            # If it's an img, add its alt attribute (emoji representation)
            tweet_text += element.get_attribute('alt')
    
    return tweet_text


def hash_tweet_content(tweet_text):
    return hashlib.md5(tweet_text.encode('utf-8')).hexdigest()

def main():
    chrome_options = Options()
    # chrome_options.add_argument('--headless')  # Run in headless mode
    chrome_options.add_argument('--disable-gpu')
    chrome_options.add_argument('--no-sandbox')

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

    try:
        # Connect to the database
        conn = get_db_connection()
        cursor = conn.cursor()

        scraper_encryption_key = '2c2e24fa373b10a1e8a64a90ff3d53c55c553581f8bfa9b181f55ad0304609ca'

        # Get scraper credentials
        username, password = get_scraper_credentials(cursor, scraper_encryption_key)

        print(f'username: {username}\npassword: {password}')

        # Get accounts to scrape
        accounts_to_scrape = get_accounts_to_scrape(cursor)

        # Log into Twitter
        twitter_login(driver, username, password)

        for account in accounts_to_scrape:
            driver.get(f'https://twitter.com/{account}')
            time.sleep(5)

            # Assume account_id is available from the Accounts table
            cursor.execute("SELECT id FROM Accounts WHERE account = %s LIMIT 1;", (account,))
            account_id = cursor.fetchone()[0]

            tweets = scroll_and_collect(driver, account_id, cursor, max_tweets=5)

            for tweet in tweets:
                upload_post(tweet['account_id'], tweet['timestamp'], tweet['content'], tweet['image'], tweet['hash'])

            # Commit after saving posts for each account
            conn.commit()

    except Exception as e:
        print(f'An error occurred: {e}')
    finally:
        driver.quit()

if __name__ == '__main__':
    main()
