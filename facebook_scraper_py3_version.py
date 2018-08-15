#!/user/bin/python3
# -*- coding: utf-8 -*-
#
# TODO:-
#     1- restrict connections to be https only.
#     2- use another way to wait for element to load than delays.
#     3- write full command-line interface for it?(if so, suggest options)
#
#

import re
import sys
import csv
import json
import time
import getpass

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.firefox.options import Options

def checkPageLoaded(driver):
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

def automate(driver, user, password):
    """ Used to Automate user interaction and return html source page."""
    driver.get("https://www.facebook.com")

    assert "Facebook" in driver.title
    time.sleep(10)

    elem = driver.find_element_by_id("email")
    elem.send_keys(user)
    elem = driver.find_element_by_id("pass")
    elem.send_keys(password)
    elem.send_keys(Keys.RETURN)
    time.sleep(5)
    driver.find_element_by_xpath("/html/body/div[1]/div[2]/div/div[1]/div/div/div/div[2]/div[1]/div[1]/div/a").click()
    time.sleep(5)
    driver.find_element_by_xpath("/html/body/div[1]/div[3]/div[1]/div/div[2]/div[2]/div[1]/div/div[1]/div/div[3]/div/div[2]/div[2]/ul/li[3]/a").click()
    time.sleep(2.5)

    while True:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        if checkPageLoaded(driver):
            break
            continue

    return driver.page_source

def export_as_csv(names, ids):
    filename = 'facebook_friends from %s.csv'%time.strftime("%Y-%m-%d %H-%M-%S")

    with open(filename, mode='w+', encoding='utf-8') as ffile:
        writer = csv.writer(ffile, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        writer.writerow(['Name', 'Facebook profile id'])

        for i in range(len(ids)):
            writer.writerow(name[i], ids[i])

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
    data["friends"] = dict(zip(names,ids))

    with open(filename, "w+", encoding='utf-8') as jsonfile:
        json.dump(data, jsonfile, indent=4)

    return filename

def main():
    user = input("Email: ")
    password = ""

    while (not password):
        password = getpass.getpass("Enter password: ")
        confirm = getpass.getpass("Confirm password: ")
        if (password == confirm):
            break
        print("Passwords didn't match!")
        password = ""

    options = Options()
    options.set_headless(headless=False)

    ffprofile = webdriver.FirefoxProfile()
    ffprofile.set_preference("dom.webnotifications.enabled", False)

    driver = webdriver.Firefox(firefox_profile=ffprofile, firefox_options=options)

    print("Loading html page... ", end="", flush=True)
    s = time.time()
    htmlpage = automate(driver, user, password)
    print("Done!.. (%s)\nProcessing data... \n"%sec_to_hms(time.time()-s))
    driver.quit()

    ids = re.findall('friend_list_item.+?data-profileid="(.+?)"', htmlpage)
    names = re.findall('friend_list_item.+?aria-label="(.+?)"', htmlpage)
    
    print("%s friends found!"%len(ids))

    print("Exporting data as json file... ", end="", flush=True)
    filename = export_as_json(names, ids)
    print("Done!\nFile: "+filename)

    for i in range(len(ids)):
        print(names[i], ":", ids[i])

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("Keyboard Interruption! exitting...")

    sys.exit(0)
