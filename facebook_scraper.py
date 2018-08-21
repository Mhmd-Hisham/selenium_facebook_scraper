#!/user/bin/python3
# -*- coding: utf-8 -*-
"""
    Selenium Facebook Scraper.
    author: Mhmd-Hisham  (gtihub)
    author: AdhamGhoname (github)
    
    Licensed under the GNU General Public License Version 3 (GNU GPL v3)
        available at: http://www.gnu.org/licenses/gpl-3.0.txt

"""

import sys
import time
import json, csv, re
import argparse, getpass

from bs4 import BeautifulSoup

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
    parser.add_argument("-b", "--headless", help="Set headless mode, run firefox in the background.", action="store_true", default=False, dest="headless")
    parser.add_argument("-t", "--timeout", help="Time to wait for elements on webpages before giving up. (30)", type=int, default=30, dest="timeout")
    parser.add_argument("-j", "--json", help="Export data in JSON format. (default)", default=True, action="store_true", dest="json")
    parser.add_argument("-c", "--csv", help="Export data in CSV format.", default=False, action="store_true", dest="csv")
    parser.add_argument("-s", "--html", help="Export the source html page.", default=False, action="store_true", dest="html")
    parser.add_argument("-i", "--import-html", help="Import data from facebook htmlpage.", default=None, dest="htmlpage")
    parser.add_argument("-l", "--login-data", help="Read login data from file.", default=None, dest="loginfile")
    return parser.parse_args()

def check_page_loaded(driver):
    """Check whether the page is loaded or not. """
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

def export_as_csv(names, ids, filename):
    """Export friends list in CSV format. """
    with open(filename, mode='w+', encoding='utf-8') as ffile:
        writer = csv.writer(ffile, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        writer.writerow(['Name', 'Facebook profile id'])

        for i in range(len(ids)):
            writer.writerow([ids[i], names[i][0], names[i][1]])

    return filename

def export_as_html(htmlpage, filename):
    """Export the source html page."""
    with open(filename, "w+", encoding="utf-8") as htmlfile:
        htmlfile.write(htmlpage)

    return filename

def export_as_json(names, ids, filename):
    """Export friends list in JSON format. """
    data = dict()
    data["number of friends"] = len(ids)
    data["friends"] = dict(zip(ids, names))

    with open(filename, "w+", encoding='utf-8') as jsonfile:
        json.dump(data, jsonfile, indent=4)

    return filename

def import_from_htmlfile(path_to_htmlfile):
    """Import friend list from htmlfile downloaded from a web browser. """
    with open(path_to_htmlfile, "r", encoding="utf-8") as htmlfile:
        htmlpage = htmlfile.read()

    return htmlpage

def get_login_data():
    """ Get login data from stdin. """
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
    if verbose:
        print("GET https://www.facebook.com")
    driver.get("https://www.facebook.com")

    elem = wait.until(EC.presence_of_element_located((By.ID, "email")))
    if verbose:
        print("Entering email.. ")
    elem.send_keys(user)
    
    elem =  wait.until(EC.presence_of_element_located((By.ID, "pass")))
    if verbose:
        print("Entering password.. ")
        print("Hitting enter.. ")
    elem.send_keys(password)
    elem.send_keys(Keys.RETURN)
    if verbose:
        print("Waiting for elements to load. timeout=%s"%timeout)

    wait.until(EC.element_to_be_clickable((By.XPATH, "/html/body/div[1]/div[2]/div/div[1]/div/div/div/div[2]/div[1]/div[1]/div/a")))#.click()
    if verbose:
        print("GET https://www.facebook.com/profile.php")
    driver.get("https://www.facebook.com/profile.php")

    while (driver.current_url == "https://www.facebook.com/profile.php"):
    	time.sleep(0.2)

    url = (driver.current_url[0:-2] if "#_" == driver.current_url[-2:] else driver.current_url) + "/friends"
    if verbose:
        print("GET", url)

    driver.get(url)
    if verbose:
        print("Scroling down.. ")

    while True:
        driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
        if check_page_loaded(driver):
            break

    return driver.page_source

def start(options):
    """Start the program and handle options"""

    if options.loginfile:
        try:
            user, password = get_login_data_from_file(options.loginfile)
        except Exception as Error:
            print(Error)
            if input("Do you want to get login data from stdout?(y/n) ").lower()[0] == 'y':
                user, password = get_login_data()
            else:
                sys.exit(0)
    else:
        user, password = get_login_data()

    if options.verbose:
        s = time.time()
        print("Downloading the html page... ")

    firefox_options = Options()
    firefox_options.set_headless(headless=options.headless)

    ffprofile = webdriver.FirefoxProfile()
    ffprofile.set_preference("dom.webnotifications.enabled", False)
    driver = webdriver.Firefox(firefox_profile=ffprofile, firefox_options=firefox_options)

    htmlpage = automate(driver, user, password, verbose=options.verbose, timeout=options.timeout)

    driver.quit()

    if options.verbose:
        print("Done downloading!.. (%s)\n"%sec_to_hms(time.time()-s))

    return htmlpage

def process(htmlpage):
    """Process using regex expressions only. This function should be removed soon."""
    ids = re.findall('friend_list_item.+?data-profileid="(.+?)"', htmlpage)
    names = re.findall('friend_list_item.+?aria-label="(.+?)"', htmlpage)

    return names, ids

def process(htmlpage):
    """Process using BeautifulSoup and regex expressions."""
    friend_list_items = BeautifulSoup(htmlpage, "html.parser").find_all("li", class_="_698")
    names = []
    ids = []
    
    for item in friend_list_items:
    	try:
    		if (item.find_all("a")[2].text[0].isdigit()):
    			continue
    		names.append((item.find_all("a")[2].text, 0))
    		ids.append(re.findall("www.facebook.com\/(.+?)[&]?[a]?[m]?[p]?[;]?[\?]?fref=pb", item.find_all("a")[2].attrs['href'])[0].replace("profile.php?id=",""))
    	except:
    		names.append((item.find_all("a")[1].text, 1))
    		try:
    			ids.append(item.find_all("a")[0].attrs['data-profileid'])
    		except:
    			continue
    
    return names, ids

def main():
    # verbose, headless, json, csv, html, htmlpage, loginfile, timeout
    options = opt_parser()

    if options.htmlpage:
        try:
            htmlpage = import_from_htmlfile(options.htmlpage)
        except Exception as error:
            print(error)
            if input("Do you want to scrape data online?(y/n) ").lower()[0] == 'y':
                htmlpage = start(options)
            else:
                return 0
    else:
        htmlpage = start(options)

    if options.verbose:
        print("Processing data... ")

    names, ids = process(htmlpage)
    filename = 'facebook friends from %s'%time.strftime("%Y-%m-%d %H-%M-%S")

    if (len(names) != len(ids)):
        print("Error!..")
        print("This message shouldn't be displayed! Please send us your html file.")
        print("Please file an issue in our repository on github so we can fix this bug.")
        print("Github repository: https://github.com/Mhmd-Hisham/selenium_facebook_scraper.git")
        if options.html == False:
            if input("Do you want to export the html page and send it manually?(y/n) ").lower()[0] == 'y':
                options.html = True
                print("Thank you for your support. ")

    print("%s friends found!"%len(ids))

    if options.json:
        print("Exporting data as json file... ", end="", flush=True)
        export_as_json(names, ids, filename + ".json")
        print("Done. File: '%s'"%filename + ".json")

    if options.csv:
        print("Exporting data as csv file... ", end="", flush=True)
        export_as_csv(names, ids, filename + ".csv")
        print("Done. File: '%s'"%filename + ".csv")

    if options.html:
        print("Exporting source html page... ", end="", flush=True)
        export_as_html(htmlpage, filename + ".html")
        print("Done. File: '%s'"%filename + ".html")

    if input("Print data to stdout?(y/n) ").lower()[0] == 'y':
        for i in range(len(ids)):
           print(names[i][0],"[Deactivated]" if names[i][1] else '', ":", ids[i])

if __name__ == "__main__":
    try:
        main()

    except KeyboardInterrupt:
        print("Keyboard Interruption! exitting... ")

    sys.exit(0)
