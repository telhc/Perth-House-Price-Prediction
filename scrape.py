from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException

from collections import defaultdict
import numpy as np
import re
import time
import pandas as pd
import sys
import os

pd.set_option('display.max_columns', None)

CHROME_DRIVER_PATH = "chromedriver.exe"
BIN_LOC = "C:\Program Files\BraveSoftware\Brave-Browser\Application\\brave.exe"
HREF_PATH = "href/"
CSV_PATH = "data/"

def generate_driver():    
    options = Options()
    options.binary_location = BIN_LOC

    driver = webdriver.Chrome(options=options, executable_path=CHROME_DRIVER_PATH)

    return driver


def wait_for_elem_by_id(driver, id):
    try:
        element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, id))
        )
        return element
    except:
        driver.quit()


def wait_for_elem_by_xpath(driver, xpath):
    try:
        element = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, xpath))
        )
        return element
    except:
        driver.quit()


def find_max_page(driver):
    from selenium.common.exceptions import NoSuchElementException
    last_page = 1

    home = driver.current_url

    try:
        next_page = driver.find_element_by_link_text("Next >>")
        next_page_url = next_page.get_attribute("href")

        # get redirected to the last page
        driver.get(next_page_url.replace("p=", "p=1000000000"))

        # find last page number
        last_pages = wait_for_elem_by_xpath(driver, "/html/body/center/table/tbody/tr")
        last_page = int(last_pages.text.split()[-1])

    except NoSuchElementException:
        pass

    # go back to starting point
    driver.get(home)

    return last_page


def get_all_links(driver, suburb, timeout_delay=120, progress=True):
    from selenium.common.exceptions import NoSuchElementException

    hrefs = []

    last_page = find_max_page(driver)
    cur_page = 0

    while True:
        cur_page += 1
        if progress:
            sys.stdout.write("{} / {}".format(cur_page, last_page))
            sys.stdout.flush()


        try:
            # wait for page to load everything, then get page links
            # mainT = wait_for_elem_by_id(driver, "mainT")
            # don't wait (faster)
            main_t = driver.find_element_by_id("mainT")

            links = main_t.find_element_by_class_name("addr").find_elements_by_xpath("//span[@class='addr']/a")

            for link in links:
                hrefs.append(link.get_attribute("href"))

            next_page = driver.find_element_by_link_text("Next >>")
            next_page_url = next_page.get_attribute("href")
            driver.get(next_page_url)

        except NoSuchElementException:
            if cur_page < last_page:
                # load error
                wait("retrying in ", timeout_delay)

                driver.refresh()

                cur_page -= 1
            else:
                # reached the last page
                return hrefs

        sys.stdout.write('\b' * (len(str(cur_page)) + len(str(last_page)) + 3))
        sys.stdout.flush()


def append_hrefs_to_file(hrefs, PATH):
    with open(PATH, "a") as file:
        for href in hrefs:
            file.write(href)
            file.write('\n')


def write_hrefs_to_file(hrefs, PATH):
    with open(PATH, "w") as file:
        for href in hrefs:
            file.write(href)
            file.write('\n')


def read_href_file(PATH):
    with open(PATH, "r") as file:
        hrefs = file.read().split('\n')
    try:
        if hrefs[-1] == '':
            return hrefs[:-1]
    except IndexError:
        return hrefs


def return_none():
    return None


def wait(msg, wait_time):
    print()
    sys.stdout.write(msg)
    while wait_time != 0:
        sys.stdout.write(str(wait_time))
        time.sleep(1)
        sys.stdout.write("\b" * len(str(wait_time)))
        wait_time -= 1
    print()

def parse_info_text(infotext):
    texts = infotext.split('\n')    

    dd = defaultdict(return_none())

    for line in texts:
        try:
            if re.match(r"^\d( \d)?( \d)?", line):
                key = "Other"
                val = line
            else:
                key, val = re.findall(r"\n?([A-Za-z]+\s?[A-Za-z]+):?\s?\$?(.*)", line)[0]

            # todo remove v comment
            # if val != None:
            dd[key.replace(' ', '_')] = val

        except IndexError:
            print("error matching {} in".format(line))
            print(texts)

    return dd

def parse_info(info_text, addr_text, suburb):
    # parses one property info into df obj

    infotext = info_text.replace('| Building', '\nBuilding')
    infotext = infotext.replace(';', '\nTransport:')
    # print(infotext)

    # gets a list of every ('key_feature', 'description')
    #todo redo infotext by line
    # parsed_info = re.findall(r"\n?([\w]+\s?[\w]+):?\s?\$?(.*)", infotext)
    # parsed_info = [list((feature.replace(' ', '_'), desc)) for feature, desc in parsed_info]
    parsed_info = parse_info_text(infotext)

    # print(parsed_info)
    # print(len(parsed_info), infotext.count("\n")+1)

    dd = defaultdict(return_none(), parsed_info)

    new_dd = defaultdict(return_none())

    cols_to_drop = []

    for col, val in dd.items():
        if re.match(r"Last_Sold|Sold|Rent", col):
            match = re.findall(r"([0-9,]*)(?:pw)? in (.*\d)", val)
            new_dd[col+"_Price"] = int(match[0][0].replace(',', ''))
            new_dd[col+"_Date"] = match[0][1]
            cols_to_drop.append(col)
        elif re.match(r"List|List_over", col):
            if ", " in val:
                price, days_on_market = val.split(", ")
                new_dd["List_days_on_market"] = int(re.search(r"(\d+)", days_on_market).group(0))
            else:
                price = val

            if " - " in price:
                list_lower, list_upper = [int(i.replace(',', '')) for i in re.findall(r"([0-9,]+)", price)]
                list_price = (list_lower + list_upper) / 2
                new_dd["List_upper"] = list_upper
                new_dd["List_lower"] = list_lower
            else:
                list_price = int(re.search(r"([0-9,]+)", price).group(0).replace(',', ''))
            new_dd["List"] = list_price

            if re.match(r"List_over", col):
                cols_to_drop.append(col)
        elif re.match(r"([0-9,]*) sqm.*", val):
            val = re.match(r"([0-9,]+) (?:sqm.*)", val).groups()[0].replace(',', '').replace(' ', '')
            new_dd[col] = int(val)
        elif val.strip() == "[Measure]":
            new_dd[col] = np.nan
        elif re.match(r"([\d]+)_Days", col):
            new_dd["On_Market"] = re.search("(\d+)", col).groups()[0]
            cols_to_drop.append(col)
        elif re.search(r"\d \d( \d)?", val) or re.match(
                r"(Other|Retail|Business|Leisure|Commercial|Studio|Semi|Duplex|Townhouse|House|Apartment|Unit)", col):
            property_type = re.match(r"([A-Za-z]+)_?([0-9]*)", col).groups()[0]
            new_dd["Property_Type"] = property_type
            try:
                rooms = re.search(r"\d( \d)?( \d)?", val)[0].split()
                if len(rooms) >= 1:
                    new_dd["Bedrooms"] = rooms[0]
                if len(rooms) >= 2:
                    new_dd["Bathrooms"] = rooms[1]
                if len(rooms) >= 3:
                    new_dd["Cars"] = rooms[2]
            except TypeError:
                pass
            cols_to_drop.append(col)
        else:
            val = val.strip()
            new_dd[col] = val

    dd.update(new_dd)

    dd["Address"] = re.match(r"(.*), {}$".format(suburb.split(',')[0]), addr_text).groups()[0]
    dd["Suburb"] = suburb

    df = pd.DataFrame.from_dict([dd])

    df = df.drop(cols_to_drop, axis=1)

    return df


def save_suburb_records(driver, suburb, read_href_txt=False, page_delay=2, timeout_delay=120):
    if read_href_txt:
        print("{}{}.txt exists, reading from it...".format(HREF_PATH, suburb))
        hrefs = read_href_file("{}{}.txt".format(HREF_PATH, suburb))
    else:
        print("making new {}.txt in {}".format(suburb, HREF_PATH))
        hrefs = get_suburb_hrefs(driver, suburb, save_hrefs=True)

    suburb_records = get_suburb_listings(driver, hrefs, suburb, progress=True, page_delay=page_delay, timeout_delay=timeout_delay)

    suburb_records.to_csv("{}{}.csv".format(CSV_PATH, suburb))

    return suburb_records


def get_suburb_hrefs(driver, suburb, save_hrefs=True):
    # fetch all results for the target suburb
    search = driver.find_element_by_id("q")
    search.send_keys(suburb)
    search.send_keys(Keys.RETURN)

    # get links in all pages
    hrefs = get_all_links(driver, suburb)
    print(hrefs)
    print(len(hrefs))
    if save_hrefs:
        write_hrefs_to_file(hrefs, "{}{}.txt".format(HREF_PATH, suburb))

    return hrefs


def get_suburb_listings(driver, hrefs, suburb, progress=True, page_delay=2, timeout_delay=120):
    suburb_df = pd.DataFrame()

    p = 1

    for href in hrefs[p - 1:]:
        sys.stdout.write("{} / {}".format(p, len(hrefs)))
        sys.stdout.flush()

        success = False

        while not success:
            try:
                driver.get(href)

                # todo catch html error 503
                addr = driver.find_element_by_xpath(
                    "//table[@id='mainT']/tbody/tr/td/div/table[1]/tbody/tr/td/table/tbody/tr[1]/td/span[@class='addr']")
                info = driver.find_element_by_xpath(
                    "//table[@id='mainT']/tbody/tr/td/div/table[1]/tbody/tr/td/table/tbody/tr[2]")

                success = True
                break
            except NoSuchElementException:
                wait("retrying in ", timeout_delay)

        # schools = driver.find_element_by_xpath("//table[@id='mainT']/tbody/tr/td/div/table[3]")
        # print("Schools" in schools.text)

        suburb_df = pd.concat([suburb_df, parse_info(info.text, addr.text, suburb)])

        time.sleep(2)

        sys.stdout.write('\b' * (len(str(p)) + len(str(len(hrefs))) + 3))
        sys.stdout.flush()

        p += 1

    return suburb_df.reset_index()


def main():
    URL = "http://house.speakingsame.com"
    PAGE_DELAY = 2
    TIMEOUT_DELAY = 120

    driver = generate_driver()

    # done: "Northbridge, WA", "Nedlands, WA", "Crawley, WA", "East Perth, WA", "West Perth, WA", "Perth, WA", "Doubleview, WA", "Innaloo, WA"

    SUBURBS = ["Northbridge, WA", "Nedlands, WA", "Crawley, WA", "East Perth, WA", "West Perth, WA", "Perth, WA"]

    for suburb in SUBURBS:
        driver.get(URL)

        print("SUBURB: {}".format(suburb))

        # todo tidy
        if os.path.exists("{}{}.csv".format(CSV_PATH, suburb)):
            prompt = input("{}{}.csv exists, are you sure you want to gather this "
                           "suburb's records and overwrite it? (Y/n)".format(CSV_PATH, suburb))
            if prompt.lower() != 'y':
                continue

        READ_FROM_HREF = os.path.exists("{}{}.txt".format(HREF_PATH, suburb))

        df = save_suburb_records(driver, suburb, READ_FROM_HREF, PAGE_DELAY, TIMEOUT_DELAY)

    driver.quit()

if __name__ == '__main__':
    main()

