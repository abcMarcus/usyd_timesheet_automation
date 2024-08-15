import importlib.util

if importlib.util.find_spec("selenium") is None:
    print("Please install selenium using 'pip install selenium'")
    exit(-1)

import os
import re
import sys
import time
from typing import Callable
from datetime import datetime, timedelta
from functools import partial

from selenium import webdriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.common.keys import Keys

##########################################################

# A few lazy consts we're going to need later
NANO_SLEEP = 0.1
MICRO_SLEEP = 1.5
SMALL_SLEEP = 3
SLEEP = 5
BIG_SLEEP = 15

TIMESHEET_WEEK_INTERVAL = 2

XPATH = "xpath"
FOLDER_DIR = os.path.dirname(__file__)
USE_PREVIOUS_TIMESHEETS_FLAG = "-p"

PREVIOUS_TIMESHEETS_DIR = os.path.join(FOLDER_DIR, "csvs")
FILENAME_DELIMITER = "-"

TIMESHEET_FILENAME_FORMAT = "%Y-%m-%d"
DATE_COLUMN_FORMAT = "%d/%m/%Y"
UNIT_CODE_RE = re.compile(r"[A-Za-z]{4}\d{4}")

INITIAL_URL = "https://uosp.ascenderpay.com/uosp-wss/faces/landing/SAMLLanding.jspx"

find_element = lambda driver, xpath: driver.find_element(XPATH, xpath)
click_element = lambda driver, xpath: driver.find_element(XPATH, xpath).click()
text_element = lambda driver, xpath, text: driver.find_element(XPATH, xpath).send_keys(text)
file_element = lambda driver, xpath, filepath: driver.find_element(XPATH, xpath).send_keys(filepath)
wait = time.sleep

##########################################################
# Helper functions
##########################################################
# Try and wait for clicking

def try_and_wait(func: Callable, tries: int = 5, wait_time: float = NANO_SLEEP) -> WebElement:
    """
    Try and wait call for webdriver function calls.

    Args:
        func: Callable      -> The callable webdriver function to fetch an element. Non null.
        tries: int          -> The number of tries to attempt driver calls. Must be >= 0
        wait_time: float    -> The wait time between each call. Must be >= 0.
    Returns:
        Webelement          : The webelement fetched
    """
    if func is None or tries <= 0 or wait_time <= 0:
        raise ValueError("Invalid arguments! Function must be non-null and tries/wait time cannot be <= 0.")

    # Keep decrementing tries until we hit the function
    while tries > 0:
        print(f"Trying driver call. Number of tries left: {tries}")
        try:
            return func()
        except:
            print("Current driver call failed. Retrying...")
        tries -= 1
        wait(wait_time)

    # If web element is None then return
    raise ValueError("WebElement not found!")

def get_previous_week_csv_files() -> list[str]:
    """
    Get the names of the CSV file(s) used in the previous week.

    Format of files is <unit code>-YYYY-MM-DD
    """
    now = datetime.now()
    days_subtracted = (now.weekday() % 7) + TIMESHEET_WEEK_INTERVAL * 7
    monday = now - timedelta(days=days_subtracted)
    filenames = []

    for filename in os.listdir(PREVIOUS_TIMESHEETS_DIR):
        filename_parts = filename.rsplit('.')[0].split(FILENAME_DELIMITER, 1)
        if len(filename_parts) == 2:
            unit_code, date = filename_parts

            print("UC", unit_code, "DATE", date)
            if UNIT_CODE_RE.match(unit_code) and date == monday.strftime(TIMESHEET_FILENAME_FORMAT):
                filename = os.path.join(PREVIOUS_TIMESHEETS_DIR, filename)
                filenames.append(filename)

    return filenames

def create_csv_files(previous_week_files: list[str]) -> list[str]:
    new_filenames = []
    for filename in previous_week_files:
        unit_code, date = filename.split('.', 1)[0].split(FILENAME_DELIMITER, 1)
        days_added = timedelta(days=TIMESHEET_WEEK_INTERVAL * 7)
        date_this_week = datetime.strptime(date, TIMESHEET_FILENAME_FORMAT) + days_added

        new_filename = f"{unit_code}{FILENAME_DELIMITER}{date_this_week.strftime(TIMESHEET_FILENAME_FORMAT)}.csv"
        new_filenames.append(new_filename)
        if os.path.isfile(new_filename):
            continue

        with open(filename) as csv_file, open(new_filename, "w") as new_csv_file:
            for line in csv_file:
                date, *other_columns = line.split(',')
                date_this_week = datetime.strptime(date, DATE_COLUMN_FORMAT) + days_added

                new_csv_file.write(date_this_week.strftime(DATE_COLUMN_FORMAT) + ',')
                new_csv_file.write(','.join(other_columns))

    return new_filenames

##########################################################
# Load entries from csv
##########################################################

csv_file = ''
raw_data = None
use_previous_week_timesheets = len(sys.argv) > 1 and USE_PREVIOUS_TIMESHEETS_FLAG in sys.argv

# Time to get a file:
if use_previous_week_timesheets:
    old_filenames = get_previous_week_csv_files()
    if not old_filenames:
        print("No CSV files found.")
        exit(1)
    filenames = create_csv_files(old_filenames)
elif len(sys.argv) < 2:
    print("Please provide a path to a properly formatted CSV file containing your timesheet data.")
    filenames = [input()]
else:
    filenames = sys.argv[1:]

raw_data = []
for filename in filenames:
    if not os.path.exists(filename):
        print("Cannot find file:", filename)
        exit(-1)

    raw_data.extend(line.rstrip() for line in open(filename) if line.strip())


##########################################################
# Figure out which driver we're using
##########################################################

# I'm only testing this on Firefox myself
try:
    driver = webdriver.Chrome()
except:
    try:
        driver = webdriver.Firefox()
    except:
        print("No Driver found, please use a recent version of either Firefox or Chrome")
        exit()


##########################################################
# Login
##########################################################

driver.get(INITIAL_URL)

print("Please Login")
print("Once you have Logged in, and website loaded")
input("Press Enter (in the terminal) to Continue")


##########################################################
# Get a new timesheet
##########################################################
# Switch to the academic timesheet frame
driver.switch_to.frame("P1_IFRAME")

# Access the academic time sheet from the main menu
# NOTE: You may need to change this to Professional Timesheet (may possibly break)
try_and_wait(partial(driver.find_element, "xpath", '''//span[@title='Academic/Sessional Timesheet']'''),
                     tries=5, wait_time=MICRO_SLEEP).click()

# Switch to the popped up frame
try_and_wait(partial(driver.switch_to.default_content), tries=5, wait_time=MICRO_SLEEP)
try_and_wait(partial(driver.switch_to.frame, 2), tries=5, wait_time=MICRO_SLEEP)
try_and_wait(partial(driver.switch_to.frame, 1), tries=5, wait_time=MICRO_SLEEP)

# Click Add new Timesheet
try_and_wait(partial(click_element, driver, "/html/body/p[2]/a"), tries=5, wait_time=MICRO_SLEEP)

start_date = min(
    [line.split(',')[0] for line in raw_data],
    key=lambda s: (lambda d: (int(d[2]), int(d[1]), int(d[0])))(s.split("/"))
)

# Start Date
try_and_wait(partial(text_element, driver, '//*[@id="P_START_DATE"]', start_date), tries=5, wait_time=MICRO_SLEEP)
try_and_wait(partial(text_element, driver, '//*[@id="P_START_DATE"]', Keys.ENTER), tries=5, wait_time=MICRO_SLEEP)

##########################################################
# Fill in the timesheet
##########################################################

# Hack for some reason during testing it cannot find table
# entries if we do not reload the frame
try_and_wait(partial(driver.switch_to.default_content), tries=5, wait_time=MICRO_SLEEP)
try_and_wait(partial(driver.switch_to.frame, 2), tries=5, wait_time=MICRO_SLEEP)
try_and_wait(partial(driver.switch_to.frame, 1), tries=5, wait_time=MICRO_SLEEP)

# Get the right number of rows
n_rows = len(raw_data)
if n_rows > 20:
    for _ in range(n_rows - 20):
        try_and_wait(partial(click_element, driver, "/html/body/form/p[3]/input[3]"), tries=5, wait_time=MICRO_SLEEP)

"""
NOTE for the table layout of each row:
td[1] : copy              :
td[2] : delete
td[3] : empty space
td[4] : date               : P_WORK_DATE
td[5] : day of the week
td[6] : Unit of study       : P_UNIT_OF_STUDY
td[7] : Paycode             : P_PAYCODE
td[8] : Unit                : P_UNITS
td[9] : empty space
td[10]: required on site    : P_REQ_LOC_TICK
td[11]: start time          : P_START_TIME
td[12]: responsibilty code  : P_GL_OVERRIDE
td[13]: project code        : P_GL_ACCOUNT
td[14]: analysis code       : P_GL_SUB_ACCOUNT
td[15]: topic               : P_TOPIC
td[16]: topic details       : P_TOPIC_DETAILS
td[17]: empty space
td[18]: special leave       : P_SPEC_LV_TICK
td[19]: empty space
"""
# Enter Data
for i, entry in enumerate(raw_data):
    entry = entry.split(',')
    print("Entering: ", entry)

    # Date
    element = try_and_wait(partial(driver.find_element, "xpath", f'''//*[@id="TSEntry"]/tr[{i + 1}]/td[4]'''), tries=5, wait_time=MICRO_SLEEP)
    field = try_and_wait(partial(element.find_element,"xpath", './*[@id="P_WORK_DATE"]'), tries=5, wait_time=MICRO_SLEEP)
    field.send_keys(entry[0])

    # Unit of Study
    element = try_and_wait(partial(driver.find_element, "xpath", '/html/body/form/table/tbody/tr[{}]/td[6]'.format(i + 1)),
                           tries=5, wait_time=MICRO_SLEEP)
    field = try_and_wait(partial(element.find_element, "xpath", './*[@id="P_UNIT_OF_STUDY"]'),
                         tries=5, wait_time=MICRO_SLEEP)
    field.send_keys(entry[1])

    # Paycode
    element = try_and_wait(partial(driver.find_element, "xpath", '/html/body/form/table/tbody/tr[{}]/td[7]'.format(i + 1)),
                           tries=5, wait_time=MICRO_SLEEP)
    field = try_and_wait(partial(element.find_element, "xpath", './*[@id="P_PAYCODE"]'),
                         tries=5, wait_time=MICRO_SLEEP)
    field.send_keys(entry[2])

    # Units
    element = try_and_wait(partial(driver.find_element, "xpath", '/html/body/form/table/tbody/tr[{}]/td[8]'.format(i + 1)),
                           tries=5, wait_time=MICRO_SLEEP)
    field = try_and_wait(partial(element.find_element, "xpath", './*[@id="P_UNITS"]'),
                         tries=5, wait_time=MICRO_SLEEP)
    field.send_keys(entry[3])

    # Start time
    element = try_and_wait(partial(driver.find_element, "xpath", '/html/body/form/table/tbody/tr[{}]/td[11]'.format(i + 1)),
                           tries=5, wait_time=MICRO_SLEEP)
    field = try_and_wait(partial(element.find_element, "xpath", './*[@id="P_START_TIME"]'),
                         tries=5, wait_time=MICRO_SLEEP)
    field.send_keys(entry[4])


    if len(entry) > 5:
        # reqired on site
        element = try_and_wait(partial(driver.find_element,"xpath",
                '/html/body/form/table/tbody/tr[{}]/td[10]'.format(i + 1)), tries=5, wait_time=MICRO_SLEEP)
        field = try_and_wait(partial(element.find_element, "xpath",'./*[@id="P_REQ_LOC_TICK"]'), tries=5, wait_time=MICRO_SLEEP)

        if (field.is_selected() != (entry[5] == "T")):
            field.click()

    if len(entry) > 6 and len(entry[6]):
        # Responsibility code
        element = try_and_wait(partial(driver.find_element,"xpath",
        '/html/body/form/table/tbody/tr[{}]/td[12]'.format(i + 1)), tries=5, wait_time=MICRO_SLEEP)
        field = try_and_wait(partial(element.find_element, "xpath",'./*[@id="P_GL_OVERRIDE"]'), tries=5, wait_time=MICRO_SLEEP)
        field.send_keys(entry[6])

    if len(entry) > 7 and len(entry[7]):
        # project code
        element = try_and_wait(partial(driver.find_element,"xpath",
        '/html/body/form/table/tbody/tr[{}]/td[13]'.format(i + 1)), tries=5, wait_time=MICRO_SLEEP)
        field = try_and_wait(partial(element.find_element, "xpath",'./*[@id="P_GL_ACCOUNT"]'), tries=5, wait_time=MICRO_SLEEP)
        field.send_keys(entry[7])

    if len(entry) > 8 and len(entry[8]):
        # Analysis Code
        element = try_and_wait(partial(driver.find_element,"xpath",
        '/html/body/form/table/tbody/tr[{}]/td[14]'.format(i + 1)), tries=5, wait_time=MICRO_SLEEP)
        field = try_and_wait(partial(element.find_element, "xpath",'./*[@id="P_GL_SUB_ACCOUNT"]'), tries=5, wait_time=MICRO_SLEEP)
        field.send_keys(entry[8])

    if len(entry) > 9 and len(entry[9]):
        # Topic
        element = try_and_wait(partial(driver.find_element,"xpath",
        '/html/body/form/table/tbody/tr[{}]/td[15]'.format(i + 1)), tries=5, wait_time=MICRO_SLEEP)
        field = try_and_wait(partial(element.find_element, "xpath",'./*[@id="P_TOPIC"]'), tries=5, wait_time=MICRO_SLEEP)
        field.send_keys(entry[9])

    if len(entry) > 10 and len(entry[10]):
        # Topic detail
        element = try_and_wait(partial(driver.find_element,"xpath",
        '/html/body/form/table/tbody/tr[{}]/td[16]'.format(i + 1)), tries=5, wait_time=MICRO_SLEEP)
        field = try_and_wait(partial(element.find_element, "xpath",'./*[@id="P_TOPIC_DETAILS"]'), tries=5, wait_time=MICRO_SLEEP)
        field.send_keys(entry[10])


# You get to enter the approver and press the button
print("READY TO LODGE!")
print("Don't forget to select your timesheet approver")
input("Press enter to finish")

