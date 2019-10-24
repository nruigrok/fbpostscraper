# Facebook Post Scraper

Python/selenium scraper for FB post based in part on [harismuneer/Ultimate-Facebook-Scraper](https://github.com/harismuneer/Ultimate-Facebook-Scraper)

Warning: This is only intended for use on public pages, e.g. newspapers. Use only with express permission from Facebook as using it may otherwise violate the terms & conditions and/or other laws or regulations. We are not your lawyer and this is not legal advice. 

## Installing

First, you need to download and install chromedriver and make sure your chrome version matches the chromedriver version. See: http://chromedriver.chromium.org/downloads

To install using pip:

```
pip3 install fbpostscraper
```

To install by cloning from github (e.g. to edit the scraper):

```
git clone https://github.com/nruigrok/fbpostscraper
cd fbpostscraper
python3 -m venv env
env/bin/pip install -e .
```

## Usage

To scrape e.g. the New York Times facebook posts into a `posts.csv` file:

```
python3 -m fbpostscraper -u USERNAME -p PASSWORD nytimes > posts.csv
```
or if you installed python in a virtual environment `env`:
```
env/bin/python3 -m fbpostscraper -u USERNAME -p PASSWORD nytimes > posts.csv
```




Since having your facebook password in your bash history is probably not a good idea, it is recommended
to copy the [fbcredentials_example.py](fbcredentials_example.py) file to fbcredentials.py and enter your credentials there.
After that, you can omit the username and password from the call. 
