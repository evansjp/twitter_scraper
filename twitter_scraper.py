import base64
import hashlib
import io
import os
import psycopg2
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from selenium.common.exceptions import NoSuchElementException, TimeoutException, StaleElementReferenceException
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

DB_NAME='prydwen_analytica_api_production'
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

def get_all_users(cursor):
    """Fetch all user_ids from the database."""
    cursor.execute("SELECT DISTINCT user_id FROM Accounts;")
    return [row[0] for row in cursor.fetchall()]

def get_accounts_to_scrape(cursor, user_id):
    """Fetch the accounts to scrape for a specific user_id from the database."""
    cursor.execute("SELECT account FROM Accounts WHERE user_id = %s;", (user_id,))
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

def save_post(account_id, timestamp, content, image_data, hash_value):
    """Uploads the post along with the image to the Rails API."""

    # Define the API endpoint
    url = 'http://localhost:3000/api/v1/posts'
    
    # Prepare the files payload. Send the image as a file (multipart/form-data).
    files = {'post[image]': ('screenshot.png', image_data, 'image/png')}
    
    # Prepare the data payload for the post (account ID, timestamp, content, etc.)
    data = {
        'post[account_id]': int(account_id),
        'post[timestamp]': timestamp,
        'post[content]': content,
        'post[post_hash]': hash_value
    }

    headers = {
        'X-Api-Key': '6217ef56a56e1fda195656a0391ce252be87ac8f3aa0e571'
    }

    # Make a POST request to the API
    response = requests.post(url, files=files, data=data, headers=headers)

    # Print the response from the server for debugging
    if response.status_code == 201:
        # print(f"Post with hash {hash_value} successfully uploaded.")
        pass
    else:
        print(f"Failed to upload post with hash {hash_value}. Status code: {response.status_code}")
        print(response.json())


# def upload_post(account_id, timestamp, content, image_data, hash_value):
#     url = 'http://localhost:4000/api/v1/posts'
    
#     files = {'post[image]': ('screenshot.png', image_data, 'image/png')}

#     # files = {
#     #     'post[image]': image_file
#     # }
    
#     data = {
#         'post[account_id]': account_id,
#         'post[timestamp]': timestamp,
#         'post[content]': content,
#         'post[hash]': hash_value,
#     }

#     response = requests.post(url, files=files, data=data, headers={})
#     print(response.json())

def twitter_login(driver, username, email, password, retries=10):
    for attempt in range(retries):
        try:
            
            # Open Twitter login page
            driver.get('https://twitter.com/login')
            time.sleep(5)  # Wait for the page to load

            # Enter the username
            username_input_xpath = '/html/body/div/div/div/div[1]/div[2]/div/div/div/div/div/div[2]/div[2]/div/div/div[2]/div[2]/div/div/div/div[4]/label/div/div[2]/div/input'
            username_input = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, username_input_xpath))
            )
            username_input.send_keys(username)

            # Click the "Next" button
            next_button_xpath = '/html/body/div/div/div/div[1]/div[2]/div/div/div/div/div/div[2]/div[2]/div/div/div[2]/div[2]/div/div/div/button[2]'
            next_button = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, next_button_xpath))
            )
            next_button.click()
            time.sleep(5)  # Wait for the password field to load

            # Check if the email field appears
            try:
                email_input_xpath = '/html/body/div/div/div/div[1]/div[2]/div/div/div/div/div/div[2]/div[2]/div/div/div[2]/div[2]/div[1]/div/div[2]/label/div/div[2]/div/input'
                email_input = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, email_input_xpath))
                )
                email_input.send_keys(email)

                # Click the "Next" button after entering the email
                email_next_button_xpath = '/html/body/div/div/div/div[1]/div[2]/div/div/div/div/div/div[2]/div[2]/div/div/div[2]/div[2]/div[2]/div/div/div/button'
                email_next_button = WebDriverWait(driver, 10).until(
                    EC.presence_of_element_located((By.XPATH, email_next_button_xpath))
                )
                email_next_button.click()
                time.sleep(5)  # Wait for the password field to load
            except TimeoutException:
                # No email field, continue with the password
                pass

            # Enter the password
            password_input_xpath = '/html/body/div/div/div/div[1]/div[2]/div/div/div/div/div/div[2]/div[2]/div/div/div[2]/div[2]/div[1]/div/div/div[3]/div/label/div/div[2]/div[1]/input'
            password_input = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, password_input_xpath))
            )
            password_input.send_keys(password)

            # Click the "Log In" button
            login_button_xpath = '/html/body/div/div/div/div[1]/div[2]/div/div/div/div/div/div[2]/div[2]/div/div/div[2]/div[2]/div[2]/div/div[1]/div/div/button'
            login_button = WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.XPATH, login_button_xpath))
            )
            login_button.click()

            time.sleep(5)  # Wait for the home page to load after logging in

            # If login succeeds, break out of the loop
            # print("Login successful.")
            break

        except (NoSuchElementException, TimeoutException) as e:
            print(f"Error during login attempt {attempt + 1}: {str(e)}")
            if attempt == retries - 1:
                print("Max retries reached. Login failed.")
            else:
                time.sleep(5)  # Wait a bit before retrying




def scroll_and_collect(driver, account_id, cursor, max_tweets=5):
    tweets_data = []
    last_height = driver.execute_script("return document.body.scrollHeight")
    scraped_hashes = set()
    
    # Find the section where the tweets are located
    tweets_section_xpath = '//section[starts-with(@aria-labelledby, "accessible-list-")]'
    try:
        tweets_section = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, tweets_section_xpath))
        )
    except TimeoutException:
        print("Could not find the tweets section.")
        return tweets_data

    previous_tweet_count = 0  # Track the number of tweets loaded in the previous scroll
    scroll_attempts = 0  # Track the number of scrolls made without finding new tweets
    max_scroll_attempts = 3  # Allow a maximum number of scrolls without new content before giving up

    while len(tweets_data) < max_tweets:
        # After each scroll, re-fetch the tweet divs to avoid stale element reference errors
        tweet_divs = tweets_section.find_elements(By.XPATH, './/article[@data-testid="tweet"]')

        # Break if no new tweets are found after scrolling multiple times
        if len(tweet_divs) == previous_tweet_count:
            scroll_attempts += 1
            if scroll_attempts >= max_scroll_attempts:
                print("No new tweets found after scrolling. Exiting...")
                break
        else:
            scroll_attempts = 0  # Reset the counter if new tweets are found

        # print(f"Found {len(tweet_divs)} tweets on this scroll.")

        # Process only new tweets loaded after the last scroll
        for tweet_div in tweet_divs[previous_tweet_count:]:
            try:
                # Scroll the tweet into view if it's not fully visible
                tweet_top_position = tweet_div.location['y']
                tweet_bottom_position = tweet_top_position + tweet_div.size['height']
                window_height = driver.execute_script("return window.innerHeight")

                if tweet_top_position < 0 or tweet_bottom_position > window_height:
                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", tweet_div)
                    time.sleep(2)  # Wait a moment for the tweet to scroll and settle

                # Extract tweet content and hash
                content = extract_tweet_text(tweet_div)
                tweet_hash = hash_tweet_content(content)

                # Check if this tweet has already been scraped in this session
                if tweet_hash in scraped_hashes:
                    # print(f"Tweet with hash {tweet_hash} already processed in this session. Skipping...")
                    continue

                # Check if the tweet with this hash already exists in the database
                cursor.execute("SELECT 1 FROM Posts WHERE post_hash = %s LIMIT 1;", (tweet_hash,))
                if cursor.fetchone():
                    # print(f"Tweet with hash {tweet_hash} already exists. Skipping...")
                    continue

                # If the tweet is new, capture the screenshot & time of tweet
                screenshot = tweet_div.screenshot_as_png
                timestamp = tweet_div.find_element(By.XPATH, './/time').get_attribute('datetime')

                # print(f"Tweet {len(tweets_data) + 1}: {content}")

                tweets_data.append({
                    'account_id': account_id,
                    'timestamp': timestamp,
                    'content': content,
                    'image': screenshot,
                    'hash': tweet_hash,
                })

                # Add this tweet's hash to the set to avoid processing it again in this session
                scraped_hashes.add(tweet_hash)

                if len(tweets_data) >= max_tweets:
                    break

            except NoSuchElementException:
                continue

            except StaleElementReferenceException:
                # print("Encountered a stale element reference. Refetching tweets...")
                break  # Refetch tweets in the next loop iteration

        previous_tweet_count = len(tweet_divs)  # Update the tweet count after processing new tweets

        # Scroll down to load more tweets
        driver.execute_script("window.scrollBy(0, window.innerHeight);")
        time.sleep(4)  # Increase the wait time to ensure new tweets are loaded
        
        # Check if new tweets are loaded
        new_height = driver.execute_script("return document.body.scrollHeight")
        if new_height == last_height:
            # print("Reached the end of the page or no new tweets loaded.")
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
    # chrome_options.add_argument('--headless')  # Uncomment for headless mode
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-gpu')

    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=chrome_options)

    try:
        # Connect to the database
        conn = get_db_connection()
        cursor = conn.cursor()

        scraper_encryption_key = '2c2e24fa373b10a1e8a64a90ff3d53c55c553581f8bfa9b181f55ad0304609ca'

        # Get all users
        user_ids = get_all_users(cursor)

        # Iterate through each user
        for user_id in user_ids:

            # Get scraper credentials for this user
            username, email, password = get_scraper_credentials(cursor, scraper_encryption_key, user_id)

            if not username or not password:
                print(f"Skipping user_id {user_id}, missing credentials.")
                continue

            # Get accounts to scrape for this user
            accounts_to_scrape = get_accounts_to_scrape(cursor, user_id)

            if not accounts_to_scrape:
                print(f"No accounts to scrape for user_id {user_id}")
                continue

            # Log into Twitter for this user
            twitter_login(driver, username, email, password)

            # Process all accounts for this user
            for account in accounts_to_scrape:
                print(f"Processing account: {account} for user_id {user_id}")
                
                # Visit the Twitter account page
                driver.get(f'https://twitter.com/{account}')
                time.sleep(5)  # Adjust this to wait for the page to load

                # Fetch the account ID from the database
                cursor.execute("SELECT id FROM Accounts WHERE account = %s AND user_id = %s LIMIT 1;", (account, user_id))
                account_id = cursor.fetchone()[0]

                # Collect tweets for the current account
                tweets = scroll_and_collect(driver, account_id, cursor, max_tweets=10)

                # Save the tweets to the database
                for tweet in tweets:
                    save_post(tweet['account_id'], tweet['timestamp'], tweet['content'], tweet['image'], tweet['hash'])

                # Commit after saving posts for each account
                conn.commit()

    except Exception as e:
        print(f'An error occurred: {e}')
    finally:
        driver.quit()
        conn.close()

if __name__ == '__main__':
    main()
