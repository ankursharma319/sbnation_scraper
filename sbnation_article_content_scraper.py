from bs4 import BeautifulSoup
import json
import requests
import os.path
import logging
from sbnation_article_list_scraper import get_existing_articles_list
from collections import defaultdict
from datetime import datetime
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

# Each article_info (article_list) dictionary contains the following data
# hash(author, title, date) : author, title, date, url
# Each article dictionary additionaly contains the 'content' key:value pair
def print_articles_summary_details(dic):
    """
    Log some summary details for the dictionary containing articles
    """
    mm_datetime_format = "%Y-%m-%dT%H:%M:%S+00:00"
    yearmonth_format = "%Y%m"
    author_counts = defaultdict(int)
    month_counts = defaultdict(int)
    for value in dic.values():
        _datetime = datetime.strptime(value['date'], mm_datetime_format)
        month_counts[_datetime.strftime(yearmonth_format)] += 1
        author_counts[value['author']] += 1

    logger.debug("Author article counts")
    logger.debug(pformat(author_counts, indent=2, compact=True))
    logger.info("Month article counts")
    logger.info(pformat(month_counts, indent=2, compact=True))


def get_existing_articles(fname):
    """
    Load existing articles into the memory (so as not to overwrite them)
    """
    if os.path.isfile(fname):
        articles = {}
        with open(fname, 'r') as articles_file:
            articles = json.load(articles_file)
        logger.info("Total Current number of articles = {}".format(len(articles)))
        _first_key = list(articles.keys())[0]
        logger.debug("First entry : {}".format(articles[_first_key]))
        print_articles_summary_details(articles)
        return articles
    else:
        logger.info("Couldnt find any existing articles")
        return {}

# Print iterations progress
def print_progress_bar (iteration, total, prefix = '', suffix = '', decimals = 1, length = 100, fill = '.'):
    """
    Call in a loop to create terminal progress bar
    @params:
        iteration   - Required  : current iteration (Int)
        total       - Required  : total iterations (Int)
        prefix      - Optional  : prefix string (Str)
        suffix      - Optional  : suffix string (Str)
        decimals    - Optional  : positive number of decimals in percent complete (Int)
        length      - Optional  : character length of bar (Int)
        fill        - Optional  : bar fill character (Str)
    """
    percent = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))
    filled_length = int(length * iteration // total)
    bar = fill * filled_length + '-' * (length - filled_length)
    print('\r%s |%s| %s%% %s\n' % (prefix, bar, percent, suffix), end='')
    # Print New Line on Complete
    if iteration == total:
        print()


def add_article(articles, key, date, title, url, author, body, summary):
    logger.debug("Added article with title {}".format(title))
    content = title + "\n" + summary + "\n" + "By " + author + "\n" + body
    articles[key] = {"date": date, "title": title, "url": url, "author": author, "content": content}
    return articles


def write_articles_to_file(articles, outfile_path):
    with open(outfile_path, 'w') as outfile:
        json.dump(articles, outfile)


def scrap_content(article_infos, articles, outfile_path):
    i = 0
    _max = len(article_infos)
    articles_skipped = 0
    summary_skipped = 0
    logger.info("Started scraping content for articles")
    # Initial call to print 0% progress
    print_progress_bar(0, _max, prefix = 'Progress:', suffix = 'Complete', length = 100)

    for key in article_infos:
        i += 1
        logger.debug("{} articles either processed or skipped".format(i))
        # After every 100 article_infos are processed, dump the contents into json and update progress bar
        if i%500 == 0:
            print_progress_bar(i, _max, prefix='Progress:', suffix='Complete', length=100)
            write_articles_to_file(articles, outfile_path)
            logger.info("Total Processed articles = {}, Skipped Articles = {} Skipped Summaries = {}".format(
                i, articles_skipped, summary_skipped
            ))
        if key not in articles:
            value = article_infos[key]
            url = value['url']
            author = value['author']
            response = requests.get(url, timeout=15)
            try:
                soup = BeautifulSoup(response.content, "html.parser")
                header_div = soup.find('div', attrs={"class":"c-entry-hero c-entry-hero--default"})
                # title = soup.find('h1', attrs={"class":"c-page-title"}).text
                summary = ""
                try:
                    summary = header_div.find('h2', attrs={"class":"c-entry-summary"}).text
                except BaseException:
                    summary_skipped += 1
                if author=="unknown":
                    author = header_div.find('span', attrs={"class":"c-byline__author-name"}).text
                body = soup.find('div', attrs={"class":"c-entry-content"}).text
                articles = add_article(articles, key, value['date'], value['title'], url, author, body, summary)
            except BaseException:
                articles_skipped += 1

    logger.info("Total articles skipped {}".format(articles_skipped))
    logger.info("Total summaries skipped {}".format(summary_skipped))

    logger.info("Dumping final {} articles into json file {}".format(len(articles), outfile_path))
    write_articles_to_file(articles, outfile_path)


if __name__=="__main__":
    infos_fname = "scrapped_data/bb/bb_article_list.json"
    fname = "scrapped_data/bb/bb_articles.json"
    article_infos = get_existing_articles_list(infos_fname)
    articles = get_existing_articles(fname)
    scrap_content(article_infos, articles, outfile_path=fname)
