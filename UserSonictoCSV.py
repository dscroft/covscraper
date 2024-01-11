from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException, TimeoutException, ElementClickInterceptedException, StaleElementReferenceException
import csv
import time

def wait_for_it(driver, xpath, wait=5):
    return WebDriverWait(driver, wait).until(EC.element_to_be_clickable((By.XPATH, xpath)))

def process(driver, module: str, month: int, year: int):
    driver.get(f"https://webapp.coventry.ac.uk/Sonic/Exams/MarksEntry.aspx?modid={module}&effdate=01%2f{month:02}%2f{year:04}&sessiontype=N&bmode=sab&smode=AllModules&sfaculty=&smodid={module}&ssessiontype=N&seffdate=01%2f{month:02}%2f{year:04}&sgridpage=0")

    previous_second_cell_data = None
    no_new_data = False

    while True and not no_new_data:
        table = wait_for_it(driver, "//table[@class='rgMasterTable']")
        rows = table.find_elements(By.CLASS_NAME, "rgEditRow")

        if rows:
            second_cell_data = rows[0].find_elements(By.TAG_NAME, "td")[1].text

            if second_cell_data != previous_second_cell_data:
                append_to_csv(rows, module, year, month)
                previous_second_cell_data = second_cell_data
            else:
                no_new_data = True  # No new data loaded, must be last page

        # Scroll down
        for i in range(10):
            ActionChains(driver).send_keys(Keys.PAGE_DOWN).perform()
            time.sleep(0.1)

        # Check for the presence of the Next Page button
        try:
            nextPage = driver.find_element(By.XPATH, "//input[@title='Next Page']")
            nextPage.click()
            time.sleep(2)  # Wait a bit for new data to load
        except NoSuchElementException:
            break  # No Next Page button, break the loop

def append_to_csv(rows, module, year, month):
    file_path = f'data_{module}_{year}_{month}.csv'
    existing_data = set()

    # Read existing data from the CSV file
    try:
        with open(file_path, 'r', newline='', encoding='utf-8') as file:
            reader = csv.reader(file)
            for row in reader:
                if row:  # Ensure the row is not empty
                    existing_data.add(tuple(row))
    except FileNotFoundError:
        pass  # If file does not exist, proceed with empty existing_data

    # Append new data, excluding duplicates
    with open(file_path, 'a', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        for row in rows:
            cols = row.find_elements(By.TAG_NAME, "td")
            if cols:
                # Skip the first (empty) column and form a tuple
                row_data = tuple(col.text for col in cols[1:])
                if row_data not in existing_data:  # Check if data is not a duplicate
                    writer.writerow(row_data)
                    existing_data.add(row_data)

if __name__ == "__main__":
    options = webdriver.ChromeOptions()
    options.add_argument("-headless=new")
    driver = webdriver.Chrome(options=options)

    username = "username"  # Replace with your username
    password = "password"  # Replace with your password

    # Open and authenticate
    driver.get(f"https://{username}:{password}@webapp.coventry.ac.uk/Sonic/Exams/MarksEntry.aspx")
    wait_for_it(driver, "//body[@class='coventry']")

    for module in (["4000CMD", "4003CMD"]):  # Replace with actual module code
        for year in range(2023, 2020, -1): # Set year range
            for month in (10, 2, 6): #set months where module was running for the normal attempt
                print(module, year, month)
                process(driver, module, month, year)

    print("Done")
    input()  # Wait for user input before closing
