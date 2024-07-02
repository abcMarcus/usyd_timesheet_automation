from typing import Callable
import selenium
import time
import sys
import csv
import os
from functools import partial

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.common.keys import Keys

##########################################################

# A few lazy consts we're going to need later
nano_sleep = 0.5
micro_sleep = 1.5
small_sleep = 3
sleep = 5
big_sleep = 15

find_element = lambda driver, xpath: driver.find_element("xpath", xpath)
click_element = lambda driver, xpath: driver.find_element("xpath", xpath).click()
text_element = lambda driver, xpath, text: driver.find_element("xpath", xpath).send_keys(text)
file_element = lambda driver, xpath, filepath: driver.find_element("xpath", xpath).send_keys(filepath)
wait = lambda x: time.sleep(x)


##########################################################
# Load entries from csv
##########################################################

csv_file = ''
raw_data = None

# Time to get a file:
if len(sys.argv) < 2:
    print("Please provide a path to a properly formatted csv file containing your timesheet data.")
    file_names = [input()]
else:
    file_names = sys.argv[1:]

raw_data = []
for file_name in file_names:
    if not os.path.exists(file_name):
        print("Cannot find file: " + file_name)
        exit(-1)

    with open(file_name, 'r', encoding='utf-8') as f:
        raw_data += f.readlines()

raw_data = list(filter(str.strip, raw_data))

##########################################################
# Helper functions
##########################################################
# Try and wait for clicking
def try_and_wait(func: Callable, tries: int = 5, wait_time: float = 0.1) -> WebElement:
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

##########################################################
# Figure out which driver we're using
##########################################################

# I'm only testing this on Firefox myself
try:
    driver = webdriver.Firefox()
except:
    try:
        driver = webdriver.Chrome()
    except:
        print("No Driver found, please use a recent version of either Firefox or Chrome")
        exit()


##########################################################
# Login
##########################################################

initial_url = 'https://uosp.ascenderpay.com/uosp-wss/faces/landing/SAMLLanding.jspx'
driver.get(initial_url)


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
                     tries=5, wait_time=micro_sleep).click()

# Switch to the popped up frame
try_and_wait(partial(driver.switch_to.default_content), tries=5, wait_time=micro_sleep)
try_and_wait(partial(driver.switch_to.frame, 2), tries=5, wait_time=micro_sleep)
try_and_wait(partial(driver.switch_to.frame, 1), tries=5, wait_time=micro_sleep)

# Click Add new Timesheet
try_and_wait(partial(click_element, driver, "/html/body/p[2]/a"), tries=5, wait_time=micro_sleep)

start_date = min(
    [line.split(',')[0] for line in raw_data],
    key=lambda s: (lambda d: (int(d[2]), int(d[1]), int(d[0])))(s.split("/"))
)

# Start Date
try_and_wait(partial(text_element, driver, '//*[@id="P_START_DATE"]', start_date), tries=5, wait_time=micro_sleep)
try_and_wait(partial(text_element, driver, '//*[@id="P_START_DATE"]', Keys.ENTER), tries=5, wait_time=micro_sleep)

##########################################################
# Fill in the timesheet
##########################################################

# Hack for some reason during testing it cannot find table
# entries if we do not reload the frame
try_and_wait(partial(driver.switch_to.default_content), tries=5, wait_time=micro_sleep)
try_and_wait(partial(driver.switch_to.frame, 2), tries=5, wait_time=micro_sleep)
try_and_wait(partial(driver.switch_to.frame, 1), tries=5, wait_time=micro_sleep)

# Get the right number of rows
n_rows = len(raw_data)
if n_rows > 20:
    for _ in range(n_rows - 20):
        try_and_wait(partial(click_element, driver, "/html/body/form/p[3]/input[3]"), tries=5, wait_time=micro_sleep)

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
    element = try_and_wait(partial(driver.find_element, "xpath", f'''//*[@id="TSEntry"]/tr[{i + 1}]/td[4]'''), tries=5, wait_time=micro_sleep)
    field = try_and_wait(partial(element.find_element,"xpath", './*[@id="P_WORK_DATE"]'), tries=5, wait_time=micro_sleep)
    field.send_keys(entry[0])

    # Unit of Study
    element = try_and_wait(partial(driver.find_element, "xpath", '/html/body/form/table/tbody/tr[{}]/td[6]'.format(i + 1)),
                           tries=5, wait_time=micro_sleep)
    field = try_and_wait(partial(element.find_element, "xpath", './*[@id="P_UNIT_OF_STUDY"]'),
                         tries=5, wait_time=micro_sleep)
    field.send_keys(entry[1])

    # Paycode
    element = try_and_wait(partial(driver.find_element, "xpath", '/html/body/form/table/tbody/tr[{}]/td[7]'.format(i + 1)),
                           tries=5, wait_time=micro_sleep)
    field = try_and_wait(partial(element.find_element, "xpath", './*[@id="P_PAYCODE"]'),
                         tries=5, wait_time=micro_sleep)
    field.send_keys(entry[2])

    # Units
    element = try_and_wait(partial(driver.find_element, "xpath", '/html/body/form/table/tbody/tr[{}]/td[8]'.format(i + 1)),
                           tries=5, wait_time=micro_sleep)
    field = try_and_wait(partial(element.find_element, "xpath", './*[@id="P_UNITS"]'),
                         tries=5, wait_time=micro_sleep)
    field.send_keys(entry[3])

    # Start time
    element = try_and_wait(partial(driver.find_element, "xpath", '/html/body/form/table/tbody/tr[{}]/td[11]'.format(i + 1)),
                           tries=5, wait_time=micro_sleep)
    field = try_and_wait(partial(element.find_element, "xpath", './*[@id="P_START_TIME"]'),
                         tries=5, wait_time=micro_sleep)
    field.send_keys(entry[4])


    if len(entry) > 5:
        # reqired on site
        element = try_and_wait(partial(driver.find_element,"xpath",
                '/html/body/form/table/tbody/tr[{}]/td[10]'.format(i + 1)), tries=5, wait_time=micro_sleep)
        field = try_and_wait(partial(element.find_element, "xpath",'./*[@id="P_REQ_LOC_TICK"]'), tries=5, wait_time=micro_sleep)

        if (field.is_selected() != (entry[5] == "T")):
            field.click()

    if len(entry) > 6 and len(entry[6]):
        # Responsibility code
        element = try_and_wait(partial(driver.find_element,"xpath",
        '/html/body/form/table/tbody/tr[{}]/td[12]'.format(i + 1)), tries=5, wait_time=micro_sleep)
        field = try_and_wait(partial(element.find_element, "xpath",'./*[@id="P_GL_OVERRIDE"]'), tries=5, wait_time=micro_sleep)
        field.send_keys(entry[6])

    if len(entry) > 7 and len(entry[7]):
        # project code
        element = try_and_wait(partial(driver.find_element,"xpath",
        '/html/body/form/table/tbody/tr[{}]/td[13]'.format(i + 1)), tries=5, wait_time=micro_sleep)
        field = try_and_wait(partial(element.find_element, "xpath",'./*[@id="P_GL_ACCOUNT"]'), tries=5, wait_time=micro_sleep)
        field.send_keys(entry[7])

    if len(entry) > 8 and len(entry[8]):
        # Analysis Code
        element = try_and_wait(partial(driver.find_element,"xpath",
        '/html/body/form/table/tbody/tr[{}]/td[14]'.format(i + 1)), tries=5, wait_time=micro_sleep)
        field = try_and_wait(partial(element.find_element, "xpath",'./*[@id="P_GL_SUB_ACCOUNT"]'), tries=5, wait_time=micro_sleep)
        field.send_keys(entry[8])

    if len(entry) > 9 and len(entry[9]):
        # Topic
        element = try_and_wait(partial(driver.find_element,"xpath",
        '/html/body/form/table/tbody/tr[{}]/td[15]'.format(i + 1)), tries=5, wait_time=micro_sleep)
        field = try_and_wait(partial(element.find_element, "xpath",'./*[@id="P_TOPIC"]'), tries=5, wait_time=micro_sleep)
        field.send_keys(entry[9])

    if len(entry) > 10 and len(entry[10]):
        # Topic detail
        element = try_and_wait(partial(driver.find_element,"xpath",
        '/html/body/form/table/tbody/tr[{}]/td[16]'.format(i + 1)), tries=5, wait_time=micro_sleep)
        field = try_and_wait(partial(element.find_element, "xpath",'./*[@id="P_TOPIC_DETAILS"]'), tries=5, wait_time=micro_sleep)
        field.send_keys(entry[10])


# You get to enter the approver and press the button
print("READY TO LODGE!")
print("Don't forget to select your timesheet approver")
input("Press enter to finish")

