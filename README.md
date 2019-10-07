# SB Nation websites scrapper

A python selenium based web scraper for extracting articles from SBNation websites such as [Managing Madrid](https://www.managingmadrid.com/), [Barca Blauguranes](https://www.barcablaugranes.com/) etc. 

## Getting Started

### Prerequisites

Simply download or clone the repository into your local machine.
Make sure you have python 3 and it is highly recommended that you use pip.

```
pip install -r ./requirements.txt
```

You also need to download a selenium webdriver executable for your browser/os combination if you want to run the article list scrapper module. (Author tested using selenium chrome driver on macOS and Windows). You do not need this for content scraper and text file compiler.

### Usage

Look under `if __name__=="__main__"` blocks towards the end of the files to see how to use and which parameters need to be passed.

There are 3 main files:
`sbnation_article_list_scraper.py` compiles a list of article links available under the archives section of the website and saves them into a json file for later use.

`sbnation_article_content_scraper.py` uses the article list compiled above to actually extract the article content (body) and save these into a new json file.

`sbnation_text_file_compiler.py` uses the articles json file and compiles them to a text file, adding boundary tokens between the different articles appropriate for use with GPT2

Running is as simple as `python3 sbnation_article_list_scraper.py` (for example)

There are comments in the code which may prove helpful if modifications are required or when debugging.

## Contributing

All contributions are welcome! Please open a pull request and the author will consider your contribution.

## Authors

* **Ankur Sharma** - *All work* - [ankursharma319](https://github.com/ankursharma319)

## Notice

Please use this at your own risk. Author is not responsible for the potential legal or ethical consequences arising from the use of the code provided.

## License

This project is licensed under the Apache License 2.0 - see the [LICENSE.md](LICENSE.md) file for details

## Acknowledgments

* Thanks to the kind writers and editors at SBNation websites for providing wonderful content
* Inspiration for this came from OpenAI's GPT2 Text generation model. The articles on SBNation provide high quality language content which can be used to finetune GPT2 and generate some accurate or humorous pieces.
