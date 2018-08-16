#!/user/bin/python3
# -*- coding: utf-8 -*-
#
# TODO:-
#     1- restrict connections to be https only.
#     2-
#
#

import time
import sys, os
import json, csv, re
import argparse, getpass

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def opt_parser():
    """Parse command-line options."""
    # verbose, headless, json, csv, html, htmlpage, loginfile
    parser = argparse.ArgumentParser(description='Use Selenium & firefox to automate facebook login and scrape data.')
    parser.add_argument("-v", "--verbose", help="Increase verbosity level.", action="store_true", default=False, dest="verbose")
    parser.add_argument("--headless", help="Open firefox in headless mode", action="store_true", default=False, dest="headless")
    parser.add_argument("--json", help="Export data in JSON format. (default)", default=True, action="store_true", dest="json")
    parser.add_argument("--csv", help="Export data in CSV format.", default=False, action="store_true", dest="csv")
    parser.add_argument("--html", help="Export data in HTML format.", default=False, action="store_true", dest="html")
    parser.add_argument("--import-html", help="Import data from facebook htmlpage.", default=None, dest="htmlpage")
    parser.add_argument("--login-data", help="Read login data from file.", default=None, dest="loginfile")

    return parser.parse_args()

def check_page_loaded(driver):
    try:
        existing = False
        a = []
        a = driver.find_elements_by_class_name("uiHeaderTitle")
        for x in a:
            if (x.get_attribute('innerHTML') == "More About You"):
                existing = True
        return existing
    except:
        return False
def sec_to_hms(sec):
    h = sec / 3600
    sec %= 3600
    m = sec / 60
    sec %= 60
    return '%02d:%02d:%02d' % (h, m, sec)
def export_as_csv(names, ids):
    filename = 'facebook_friends from %s.csv'%time.strftime("%Y-%m-%d %H-%M-%S")

    with open(filename, mode='w+', encoding='utf-8') as ffile:
        writer = csv.writer(ffile, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        writer.writerow(['Name', 'Facebook profile id'])

        for i in range(len(ids)):
            writer.writerow([names[i], ids[i]])

    return filename
def export_as_html(htmlpage):
    filename = 'facebook_friends from %s.html'%time.strftime("%Y-%m-%d %H-%M-%S")

    with open(filename, "w+", encoding="utf-8") as htmlfile:
        htmlfile.write(htmlpage)

    return filename
def export_as_json(names, ids):
    filename = 'facebook_friends from %s.json'%time.strftime("%Y-%m-%d %H-%M-%S")

    data = dict()
    data["number of friends"] = len(ids)
    data["friends"] = dict(zip(ids, names))

    with open(filename, "w+", encoding='utf-8') as jsonfile:
        json.dump(data, jsonfile, indent=4)

    return filename
def import_from_htmlfile(path_to_htmlfile):
    with open(path_to_htmlfile, "r", encoding="utf-8") as htmlfile:
        htmlpage = htmlfile.read()

    return htmlpage
def get_login_data():
    user = input("Email: ")
    password = ""

    while (not password):
        password = getpass.getpass("Enter password: ")
        confirm = getpass.getpass("Confirm password: ")
        if (password == confirm):
            break
        print("Passwords didn't match!")
        password = ""

    return user, password
def get_login_data_from_file(filename):
    with open(filename, "r", encoding="utf-8") as login_file:
        user = login_file.readlines(1)
        password = login_file.readlines(1)

    return user, password

def automate(driver, user, password, timeout=30, verbose=False):
    """ Used to Automate user interaction and return html source page."""
    wait = WebDriverWait(driver, timeout)
    driver.get("https://www.facebook.com")

    elem = wait.until(EC.presence_of_element_located((By.ID, "email")))
    elem.send_keys(user)
    elem =  wait.until(EC.presence_of_element_located((By.ID, "pass")))
    elem.send_keys(password)
    elem.send_keys(Keys.RETURN)
    wait.until(EC.element_to_be_clickable((By.XPATH, "/html/body/div[1]/div[2]/div/div[1]/div/div/div/div[2]/div[1]/div[1]/div/a")))#.click()
    driver.get("https://www.facebook.com/profile.php")
    while (driver.current_url == "https://www.facebook.com/profile.php"):
    	time.sleep(0.2)

    driver.get((driver.current_url[0:-2] if "#_" == driver.current_url[-2:] else driver.current_url) + "/friends")

    while True:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        if check_page_loaded(driver):
            break

    return driver.page_source

def start(options):
    """Start the program and handle options"""
    if options.verbose:
        s = time.time()
        print("Loading html page... ", end="", flush=True)

    if options.loginfile:
        try:
            user, password = get_login_data_from_file(options.loginfile)
        except Exception as Error:
            print(Error)
            if 'y' in input("Do you want to get login data from stdout?(y/n) ").lower():
                user, password = get_login_data()
            else:
                sys.exit(0)
    else:
        user, password = get_login_data()

    firefox_options = Options()
    firefox_options.set_headless(headless=options.headless)

    ffprofile = webdriver.FirefoxProfile()
    ffprofile.set_preference("dom.webnotifications.enabled", False)
    driver = webdriver.Firefox(firefox_profile=ffprofile, firefox_options=firefox_options)

    htmlpage = automate(driver, user, password, verbose=options.verbose)

    driver.quit()

    if options.verbose:
        print("Done!.. (%s)\n"%sec_to_hms(time.time()-s))

    return htmlpage

def main():
    # verbose, headless, json, csv, html, htmlpage, loginfile
    options = opt_parser()

    if options.htmlpage:
        try:
            htmlpage = import_from_htmlfile(options.htmlpage)
        except Exception as error:
            print(error)
            if y in input("Do you want to scrape data online?(y/n) ").lower():
                htmlpage = start(options)
            else:
                return 0
    else:
        htmlpage = start(options)

    if options.verbose:
        print("Processing data... ")

    ids = re.findall('friend_list_item.+?data-profileid="(.+?)"', htmlpage)
    names = re.findall('friend_list_item.+?aria-label="(.+?)"', htmlpage)

    if options.verbose:
        print("%s friends found!"%len(ids))

    if options.json:
        print("Exporting data as json file... ", end="", flush=True)
        filename = export_as_json(names, ids)
        print("Done. File: '%s'"%filename)

    if options.csv:
        print("Exporting data as csv file... ", end="", flush=True)
        filename = export_as_csv(names, ids)
        print("Done. File: '%s'"%filename)

    if options.html:
        print("Exporting data as html file... ", end="", flush=True)
        filename = export_as_html(htmlpage)
        print("Done. File: '%s'"%filename)

    for i in range(len(ids)):
       print(names[i], ":", ids[i])

if __name__ == "__main__":
    try:
        main()

    except KeyboardInterrupt:
        print("Keyboard Interruption! exitting... ")

    sys.exit(0)
