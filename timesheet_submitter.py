import importlib.util

if importlib.util.find_spec("selenium") is None:
    print("Please install selenium using 'pip install selenium'")
    exit(-1)

from selenium import webdriver
from selenium.common.exceptions import UnexpectedAlertPresentException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.keys import Keys
import sys
import os
import time

MAX_WAIT_TIME = 20

# CSV Column

CSV_COLUMNS = {
    "date": 0,
    "unit_of_study": 1,
    "paycode": 2,
    "units": 3,
    "start_time": 4,
    "required_on_site": 5,
    "responsibility_code": 6,
    "project_code": 7,
    "analysis_code": 8,
    "topic": 9,
    "topic_detail": 10,
}

##########################################################
# Load CSV Entries
##########################################################

file_names = [input()] if len(sys.argv) < 2 else sys.argv[1:]

raw_data = []
for file_name in file_names:
    if not os.path.exists(file_name):
        print(f"Cannot find file: {file_name}")
        exit(-1)

    with open(file_name, "r", encoding="utf-8") as f:
        raw_data += f.readlines()

raw_data = list(filter(str.strip, raw_data))

start_date = min(
    [line.split(",")[CSV_COLUMNS["date"]] for line in raw_data],
    key=lambda s: (lambda d: (int(d[2]), int(d[1]), int(d[0])))(s.split("/")),
)

##########################################################
# moneyy
##########################################################

RATES = {
    "TU2": 11.11,
    "TU4": 11.11,
    "A02": 11.11,
    "M05": 11.11,
    "DE2": 11.11,
}

each = {}
for row in raw_data:
    row = row.split(",")
    paycode = row[CSV_COLUMNS["paycode"]]
    units = float(row[CSV_COLUMNS["units"]])

    if paycode not in RATES:
        print(f"Unknown pay code {paycode}")
        exit(-1)

    each[paycode] = each.get(paycode, 0) + RATES[paycode] * units

print(each)
print(f"Total pay: ${sum(each.values()):.2f}")

# Topics

TOPICS = {
    "ACAD INTGY", "ADMIN", "LECTURE", "MARKING", "MEETING",
    "PRACTICAL", "PREP", "SEMINAR", "TEACHING", "TRAINING",
    "TUTORIAL", "UOSMAT DEV", "WORKSHOP"
}

for row in raw_data:
    row = row.split(",")
    topic = row[CSV_COLUMNS["topic"]]
    if topic and topic not in TOPICS:
        print(f"Unknown topic code {topic}")
        exit(-1)

##########################################################
# Figure out which driver we're using
##########################################################

try:
    driver = webdriver.Firefox()
except:
    try:
        driver = webdriver.Chrome()
    except:
        print("No Driver found, please use a recent version of either Firefox or Chrome")
        exit()


# Helper function to wait for an element
def wait_for_element(xpath, timeout=10):
    for _ in range(5):
        try:
            return WebDriverWait(driver, timeout).until(
                EC.presence_of_element_located((By.XPATH, xpath))
            )
        except UnexpectedAlertPresentException as e:
            print(f"Popup: {e.msg}")
            time.sleep(1)
            print("Retrying...")


##########################################################
# Login
##########################################################

initial_url = "https://uosp.ascenderpay.com/uosp-wss/faces/landing/SAMLLanding.jspx"
driver.get(initial_url)

print("Please Login")
print("Once you have Logged in, and website loaded")
input("Press Enter (in the terminal) to Continue")

##########################################################
# Get a new timesheet
##########################################################

driver.switch_to.frame("P1_IFRAME")
wait_for_element("//span[@title='Academic/Sessional Timesheet']").click()
driver.switch_to.default_content()

WebDriverWait(driver, MAX_WAIT_TIME).until(
    EC.frame_to_be_available_and_switch_to_it(
        (By.CSS_SELECTOR, "#apex_dialog_1 > iframe")
    )
)
WebDriverWait(driver, MAX_WAIT_TIME).until(
    EC.frame_to_be_available_and_switch_to_it("P5_LAUNCHER_IFRAME")
)

wait_for_element("/html/body/p[2]/a").click()
wait_for_element('//*[@id="P_START_DATE"]').send_keys(start_date + Keys.ENTER)

##########################################################
# Fill in the timesheet
##########################################################

add_row = WebDriverWait(driver, MAX_WAIT_TIME).until(
    EC.element_to_be_clickable((By.XPATH, "/html/body/form/p[3]/input[3]"))
)

n_rows = len(raw_data)
if n_rows > 20:
    for _ in range(n_rows - 20):
        driver.execute_script("arguments[0].click();", add_row)

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

for i, entry in enumerate(raw_data, 1):
    entry = entry.split(",")
    print("Entering: ", entry)

    XPATH_MAPPINGS = {
        "date": f'//*[@id="TSEntry"]/tr[{i}]/td[4]//*[@id="P_WORK_DATE"]',
        "unit_of_study": f'/html/body/form/table/tbody/tr[{i}]/td[6]//*[@id="P_UNIT_OF_STUDY"]',
        "paycode": f'/html/body/form/table/tbody/tr[{i}]/td[7]//*[@id="P_PAYCODE"]',
        "units": f'/html/body/form/table/tbody/tr[{i}]/td[8]//*[@id="P_UNITS"]',
        "start_time": f'/html/body/form/table/tbody/tr[{i}]/td[11]//*[@id="P_START_TIME"]',
        "required_on_site": f'/html/body/form/table/tbody/tr[{i}]/td[10]//*[@id="P_REQ_LOC_TICK"]',
        "responsibility_code": f'/html/body/form/table/tbody/tr[{i}]/td[12]//*[@id="P_GL_OVERRIDE"]',
        "project_code": f'/html/body/form/table/tbody/tr[{i}]/td[13]//*[@id="P_GL_ACCOUNT"]',
        "analysis_code": f'/html/body/form/table/tbody/tr[{i}]/td[14]//*[@id="P_GL_SUB_ACCOUNT"]',
        "topic": f'/html/body/form/table/tbody/tr[{i}]/td[15]//*[@id="P_TOPIC"]',
        "topic_detail": f'/html/body/form/table/tbody/tr[{i}]/td[16]//*[@id="P_TOPIC_DETAILS"]',
    }

    for field, index in CSV_COLUMNS.items():
        if len(entry) > index and entry[index]:
            wait_for_element(XPATH_MAPPINGS[field]).send_keys(entry[index])

    if len(entry) > CSV_COLUMNS["required_on_site"]:
        checkbox = wait_for_element(XPATH_MAPPINGS["required_on_site"])
        if checkbox.is_selected() != (entry[CSV_COLUMNS["required_on_site"]] == "T"):
            checkbox.click()

# Fill in approver
wait_for_element('//*[@id="P_APPROVER"]').send_keys("0001016")

print("READY TO LODGE!")
input("Press enter to finish")
