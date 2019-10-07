from bs4 import BeautifulSoup
import json
import hashlib
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
from collections import defaultdict
from datetime import datetime
import os.path 
import re
import logging
import logging.handlers
from pprint import pformat

# create logger with 'this modules name'
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

# create file handler which logs even debug messages
fh = logging.handlers.RotatingFileHandler(__name__+'.log', 
    mode='w', maxBytes=1e7, backupCount=4)
fh.setLevel(logging.DEBUG)
# create console handler with a higher log level
ch = logging.StreamHandler()
ch.setLevel(logging.INFO)

# create a detailed and simple formatter and add it to the handlers
detailed_formatter = logging.Formatter(fmt=
    ("%(asctime)-22s - %(name)-4s - %(levelname)-4s - "
    "%(filename)-5s - %(lineno)-2s - "
    "%(funcName)-5s \n%(message)s")
)
simple_formatter = logging.Formatter('%(name)s: %(levelname)s: %(message)s')

fh.setFormatter(detailed_formatter)
ch.setFormatter(simple_formatter)
# add the handlers to the logger
logger.addHandler(fh)
logger.addHandler(ch)

# root logger - when used as logging.info() for example instead of logger.info()
# logging.basicConfig(level=logging.DEBUG, handlers=[fh, ch])

def print_article_list_summary_details(dic):
    """
    Log some summary details for the dictionary containing article list/information
    """
    mm_datetime_format = "%Y-%m-%dT%H:%M:%S+00:00"
    yearmonth_format = "%Y%m"
    author_counts = defaultdict(int)
    month_counts = defaultdict(int)
    for value in dic.values():
        _datetime = datetime.strptime(value['date'], mm_datetime_format)
        month_counts[_datetime.strftime(yearmonth_format)] += 1
        author_counts[value['author']] += 1

    logger.debug("Author article_info counts")
    logger.debug(pformat(author_counts, indent=2, compact=True))
    logger.info("Month article_info counts")
    logger.info(pformat(month_counts, indent=2, compact=True))


def get_existing_articles_list(fname):
    """
    Load existing articles info list into the memory (so as not to overwrite them)
    """
    if os.path.isfile(fname):
        article_infos = {}
        with open(fname, 'r') as article_list_file:
            article_infos = json.load(article_list_file)
        logger.info("Total Current number of article infos = {}".format(len(article_infos)))
        _first_key = list(article_infos.keys())[0]
        logger.debug("First entry : {}".format(article_infos[_first_key]))
        print_article_list_summary_details(article_infos)
        return article_infos
    else:
        logger.info("Couldnt find any existing article infos")
        return {}


def initialize_webdriver_for_sb(webdriver_executable_path, archives_root_url):
    # Define Chrome options to open the window in maximized mode
    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    # Initialize the Chrome webdriver and open the URL
    driver = webdriver.Chrome(executable_path=webdriver_executable_path, options=options)
    driver.implicitly_wait(1)

    # open the root_url
    driver.get(archives_root_url)
    wait = WebDriverWait(driver, 10)
    # click privacy button and wait til its disappeared
    privacy_button = wait.until(EC.element_to_be_clickable((By.XPATH, '//*[@id="accept-privacy-consent"]/div')))
    privacy_button.click()
    wait.until(EC.invisibility_of_element(privacy_button))
    logger.debug("Initialized webdriver, opened {} and clicked on privacy button".format(archives_root_url))
    return driver


def get_fully_loaded_html_page(month, year, driver, archives_root_url, 
    tries_after_which_to_refresh=3, number_of_failures_after_which_to_skip=7):
    """
    Returns bs4 object of the fully loaded html archive page with all the article links for
    that particular month
    :param: tries_after_which_to_refresh : number of times of unsuccessful 
    tries after which to refresh the webpage
    """
    # go to correct url
    time.sleep(2)
    url = archives_root_url + str(year) + "/" + str(month)
    driver.get(url)
    wait = WebDriverWait(driver, 2)
    fails = 0
    # click load more button as many times as possible 
    # (note that sometimes website just doesnt work which is why the code allows for retries)
    # The sbnation website themselves have limits and sometimes starts returning black pages and saying 'go slow on archives'
    # In that case, the scraper just skips over the months and years which have not been done and writes them to the file
    # page refreshes after every 3 unsuccessfull tries
    time_to_refresh = tries_after_which_to_refresh
    while True:
        if len(driver.find_elements_by_class_name('c-archives-load-more__button')) == 1 and time_to_refresh > 0:
            try:
                time.sleep(2)
                wait.until(EC.element_to_be_clickable((By.CLASS_NAME, 'c-archives-load-more__button')))
                driver.execute_script("document.getElementsByClassName('c-archives-load-more__button')[0].click()")
            except BaseException:
                if fails >= number_of_failures_after_which_to_skip:
                    logger.debug("Reached too many failures for {}-{}, time to parse data".format(year, month))
                    time_to_refresh = 3
                    break
                logger.debug("waited too long for load more button")
                driver.execute_script('window.scrollTo(0, document.body.scrollHeight)')
                time_to_refresh -= 1
        elif time_to_refresh == 0:
            logger.debug("refreshing the page")
            fails += 1
            driver.refresh()
            time_to_refresh = 3
        else:
            logger.debug("Done clicking load more for {}-{}, time to parse data".format(year, month))
            time_to_refresh = 3
            break

    # response = requests.get(root_url, timeout=5)
    bs4_content = BeautifulSoup(driver.page_source, "html.parser")
    #logger.debug("Printing HTML content found for {}-{}".format(year, month))
    #logger.debug(bs4_content.prettify())
    return bs4_content


def add_to_dictionary(existing_article_infos, _date, title, author, address):
    _hash = int(hashlib.sha1((_date+title+author).encode('utf-8')).hexdigest(), 16) % (10 ** 8)
    if _hash not in existing_article_infos:
        existing_article_infos[_hash] = {"date": _date, "title": title, "url": address, "author": author}
        logger.debug("Added article to dictionary")
    else:
        logger.debug("Article already exists in dictionary")
        # print("Hash already exists")
    return existing_article_infos


def extract_links_from_html(bs4_content, existing_article_infos,
        regex_compiled_pattern = re.compile(
            r'\/(?P<year>\d{4})\/(?P<month>\d{1,2})\/(?P<day>\d{1,2})\/'
        )
    ):
    # Load all content into the dictionary by scouring through the html content
    logger.debug("Parsing HTML for extracting article entries")
    for entry in bs4_content.findAll('div', attrs={"class":"c-entry-box--compact__body"}):
        h2 = entry.find('h2', attrs={"class": 'c-entry-box--compact__title'})
        a = h2.find('a')
        title = a.text
        address = a['href']
        byline_div = entry.find('div', attrs={"class":"c-byline"})
        logger.debug("found an article entry with title : {}".format(title))

        # Earlier this used to exist, but not as of October 2019
        # so now it will usually go into else
        # where no author information available
        # and lesser dateinformation available as well
        if byline_div is not None:
            spans = byline_div.findAll('span', attrs={"class":"c-byline__item"})
            if len(spans) == 2:
                logger.debug("Found detailed author and date information")
                author = spans[0].find('a').text
                _date = spans[1].find('time')['datetime']
                existing_article_infos = add_to_dictionary(
                    existing_article_infos, _date, title, author, address
                )
                continue
        
        logger.debug("Couldnt find detailed author and date information, storing whatever found")
        _date_match_obj = regex_compiled_pattern.search(address)
        _datetime = datetime(
            year = int(_date_match_obj.group('year')), 
            month = int(_date_match_obj.group('month')),
            day = int(_date_match_obj.group('day'))
        )
        mm_datetime_format = "%Y-%m-%dT%H:%M:%S+00:00"
        _datetime_string = _datetime.strftime(mm_datetime_format)
        existing_article_infos = add_to_dictionary(
            existing_article_infos, _datetime_string, title, 'unknown', address
        )
        
    return existing_article_infos


def scrape_from_sbnation(months, years, 
    outfile_path, existing_article_infos,
    webdriver_executable_path, archives_root_url):
    """
    Scrapes from Sports Nation Website using a selenium chromedriver
    """
    driver = initialize_webdriver_for_sb(
        webdriver_executable_path = webdriver_executable_path,
        archives_root_url = archives_root_url
    )

    # Loop through all the years and months combinations
    for year in years:
        time.sleep(5)
        for month in months:
            content = get_fully_loaded_html_page(month, year, driver, archives_root_url)
            existing_article_infos = extract_links_from_html(content, existing_article_infos)
            logger.info("Processed articles for (year-month = {}-{}) No. of articles now = {}"
                .format(year, month, len(existing_article_infos)))
    logger.info("Done processing articles")
    driver.quit()

    logger.info("Writing json to {} file".format(outfile_path))
    with open(outfile_path, 'w') as outfile:
        json.dump(existing_article_infos, outfile)

"""
Change these parameters to scrape article links list you are interested in
Requires selenium chrome webdriver
"""
if __name__ == '__main__':
    outfile_path = "scrapped_data/bb/bb_article_list.json"
    archives_root_url = "https://www.barcablaugranes.com/archives/"
    webdriver_executable_path = "/Users/ankurs4/Downloads/chromedriver"
    article_infos = get_existing_articles_list(fname=outfile_path)
    months = range(1, 10, 1)
    years = range(2019, 2020, 1)
    scrape_from_sbnation(
        months, years, 
        existing_article_infos = article_infos,
        outfile_path = outfile_path,
        webdriver_executable_path = webdriver_executable_path,
        archives_root_url = archives_root_url
    )