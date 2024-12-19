#Final version
from selenium import webdriver
from selenium.webdriver.common.by import By
import time
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
import pandas as pd
from sqlalchemy import create_engine
import mysql.connector
import MySQLdb.connections


#Establishing connection to MySQL
try:
    db_connection = mysql.connector.connect(
        host='127.0.0.1',
        user='root',
        password='Kumar123$'
    )
    print("Database connection established.")
    db_cursor = db_connection.cursor()
    db_cursor.execute("CREATE DATABASE IF NOT EXISTS redbus")
    db_cursor.execute("USE redbus")
    db_cursor.execute("DROP TABLE IF EXISTS bus_routes")
    db_cursor.execute("CREATE TABLE IF NOT EXISTS bus_routes ("
                       "id INT AUTO_INCREMENT PRIMARY KEY, "
                       "state VARCHAR(50), "
                       "route_name TEXT, "
                       "route_link TEXT, "
                       "bus_name TEXT, "
                       "bus_type TEXT, "
                       "departure_time TIME, "
                       "duration TEXT, "
                       "arrival_time TIME, "
                       "rating FLOAT, "
                       "price DECIMAL(10, 2), "
                       "seats_available INT)")

          
    db_connection.commit()
    print("Database setup complete.")
except mysql.connector.Error as e:
    print(f"Error connecting to database: {e}")
    exit()

#SQLAlchemy Engine for easier database operations
engine = create_engine("mysql+pymysql://root:Kumar123$@127.0.0.1/redbus")


driver = webdriver.Chrome()
actions = ActionChains(driver)



# List of states and their corresponding transport URLs
states = ['APSRTC', 'TSRTC', 'Kerala', 'SBSTC', 'West bengal', 'Bihar', 'HRTC', 'RSRTC', 'PEPSU','Assam']
transport_urls = [
    'https://www.redbus.in/online-booking/apsrtc/?utm_source=rtchometile',
    'https://www.redbus.in/online-booking/tsrtc/?utm_source=rtchometile',
    'https://www.redbus.in/online-booking/ksrtc-kerala/?utm_source=rtchometile',
    'https://www.redbus.in/online-booking/south-bengal-state-transport-corporation-sbstc/?utm_source=rtchometile',
    'https://www.redbus.in/online-booking/west-bengal-transport-corporation?utm_source=rtchometile',
    'https://www.redbus.in/online-booking/bihar-state-road-transport-corporation-bsrtc/?utm_source=rtchometile',
    'https://www.redbus.in/online-booking/hrtc/?utm_source=rtchometile',
    'https://www.redbus.in/online-booking/rsrtc/?utm_source=rtchometile',
    'https://www.redbus.in/online-booking/pepsu/?utm_source=rtchometile',
    'https://www.redbus.in/online-booking/astc/?utm_source=rtchometile',     
]


def is_at_end_of_page(driver):
    # JavaScript to load all the details by scrolling to the end of the page 
    scroll_position = driver.execute_script("return window.scrollY;")
    page_height = driver.execute_script("return document.documentElement.scrollHeight;")
    viewport_height = driver.execute_script("return window.innerHeight;")

    # Check if we've reached the bottom of the page
    return scroll_position + viewport_height >= page_height


# Looping the state transport links
for state, url in zip(states, transport_urls):
    driver.get(url)
    time.sleep(2)  # Wait for the page to load


    # Empty dictionary and list to store the data
    routes = []
    route_links = []

    bus_details = {
        'state': [], 'route_name': [], 'route_link': [], 'bus_name': [], 'bus_type': [],
        'departure_time': [], 'duration': [], 'arrival_time': [], 'rating': [], 'price': [], 
        'seats_available': []
    }



    no_of_pages = driver.find_elements(By.CLASS_NAME, 'DC_117_pageTabs ')

    # Navigating to the page numbers in the bus routes page
    try:
        no_of_pages = len(driver.find_elements(By.CLASS_NAME, 'DC_117_pageTabs '))
    except Exception:
        no_of_pages = 1  # Default to 1 if pagination is not found

    for page_num in range(1, no_of_pages + 1):
        # Navigate to each page
        page_button = driver.find_element(By.XPATH, f"//*[@id='root']/div/div[4]/div[12]/div[text()='{page_num}']")
        actions.move_to_element(page_button).click().perform()
        


        # Extract route names and links
        routes_on_page = driver.find_elements(By.CLASS_NAME,"route")
        for route in routes_on_page:
            routes.append(route.text)
            route_links.append(route.get_attribute('href'))
        

    for route_name, route_link in zip(routes, route_links):
        driver.get(route_link)
        time.sleep(5)


        buttons = driver.find_elements(By.XPATH, "//*[@class='button']")

        # Clicking the view buses button 
        for button in reversed(buttons):
            try:
                driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", button)
                time.sleep(3)
                button.click()
                time.sleep(3)  # Allow content to load after clicking
            except Exception as e:
                print(f"Error clicking button: {e}")
   
        
   
        while not is_at_end_of_page(driver):
            # Scroll down by sending PAGE_DOWN
            driver.find_element('tag name', 'body').send_keys(Keys.PAGE_DOWN)  


        # Extract bus details
        bus_rows = driver.find_elements(By.XPATH, "//*[@class='row-sec clearfix']")

        for row in bus_rows:
            bus_details['state'].append(state)
            bus_details['route_name'].append(route_name)
            bus_details['route_link'].append(route_link)
            bus_details['bus_name'].append(row.find_element(By.CSS_SELECTOR, "div[class='travels lh-24 f-bold d-color']").text)
            bus_details['bus_type'].append(row.find_element(By.CSS_SELECTOR, "div[class='bus-type f-12 m-top-16 l-color evBus']").text)
            bus_details['departure_time'].append(row.find_element(By.CSS_SELECTOR, "div[class='dp-time f-19 d-color f-bold']").text)
            bus_details['duration'].append(row.find_element(By.CSS_SELECTOR,"div[class='dur l-color lh-24']").text)
            bus_details['arrival_time'].append(row.find_element(By.CSS_SELECTOR, "div[class='bp-time f-19 d-color disp-Inline']").text)            
            bus_details['price'].append(row.find_element(By.XPATH, ".//div[contains(@class, 'fare d-block')]//span").text.strip())
            bus_details['seats_available'].append(int(row.find_element(By.XPATH, ".//div[1]/div[7]/div[1]").text.split(' ')[0]))

            # Star rating add 0, if star rating not available in few cases
            
            try:
                bus_details['rating'].append(float(row.find_element(By.XPATH, ".//div[5]/div[1]/div/span").text))
            except Exception as e:
                bus_details['rating'].append(0.0)  # Default to 0 if no rating is found
                print(f"Rating not found for row: {row}. Defaulting to 0. Error: {e}")
                                          
            
    df = pd.DataFrame(bus_details)
    df.to_sql('bus_routes', engine, if_exists='append', index=False)
    df.to_csv(f"{state}_routes.csv", index=False)
    print(f"Data for {state} saved successfully.")


print("Data extraction and storage completed.")
driver.quit()