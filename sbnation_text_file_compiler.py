from sbnation_article_content_scraper import (
    get_existing_articles, print_progress_bar
)
import logging

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


def write_to_txt_file(text, output_txt_file_path):
    with open(output_txt_file_path, 'w', encoding='utf-8') as outfile:
        outfile.write(text)
    logger.info("Done writing to file {}, text length = {}".format(output_txt_file_path, len(text)))


def compile_txt_file(json_file_path, output_txt_file_path, author=None):
    logger.info("Compiling articles in {} to text file at {} where author is {}".
        format(json_file_path, output_txt_file_path, author))
    articles = get_existing_articles(json_file_path)
    text = ""
    _max = len(articles)
    i = 0
    # Initial call to print 0% progress
    print_progress_bar(0, _max, prefix = 'Progress:', suffix = 'Complete', length = 100)
    for key in articles:
        # After every 500 article_infos are added, log and update progress bar
        if i%500 == 0:
            print_progress_bar(i, _max, prefix='Progress:', suffix='Complete', length=100)
            logger.info("Total articles added to string = {}".format(i))
        if (author and author.lower().strip() == articles[key]['author'].lower().strip()) or author is None:
            i += 1
            text = ''.join((text, "<|startoftext|>\n", articles[key]['content'], "\n<|endoftext|>\n"))
    write_to_txt_file(text, output_txt_file_path)


if __name__ == "__main__":
    json_file_path = "scrapped_data/mm/mm_articles.json"
    output_txt_file_path = "scrapped_data/mm/mm_text_lucas.txt"

    # compile only articles from this author
    # pass None to compile from all authors
    author = "Lucas Navarrete" # or None
    compile_txt_file(
        json_file_path=json_file_path,
        output_txt_file_path=output_txt_file_path,
        author = author
    )
