# -*- coding: utf-8 -*-

import re, json, pickle
from ConfigParser import ConfigParser
from os.path import isfile, expanduser
from urllib2 import urlopen, HTTPError, URLError

from jinja2 import Environment, PackageLoader
from opengraph import OpenGraph
from TwitterAPI import TwitterAPI

def get_config(filename):
    config = ConfigParser()
    config.read(filename)
    return config


def load_favorites(config):
    api = TwitterAPI(
            config.get('twitter', 'ConsumerKey'),
            config.get('twitter', 'ConsumerSecret'),
            config.get('twitter', 'AccessTokenKey'),
            config.get('twitter', 'AccessTokenSecret'))

    print config.items('twitter')

    r = api.request('favorites/list', {'count': 200})
    return list(r)

def get_url_data(url):
    try:
        raw = urlopen(url)

        if raw is None:
            return None

        html = raw.read()
        data = OpenGraph(html=html, scrape=True)

        if data.is_valid():
            return dict(data)
        else:
            return None

    except (HTTPError, URLError, AttributeError):
        return None

def get_all_url_data(favorites):
    cachepath = expanduser('~/.favorites.urlcache')

    if isfile(cachepath):
        with open(cachepath, 'r') as cachefile:
            cache = pickle.load(cachefile)
    else:
        cache = {}

    data = {}
    for fav in favorites:
        for url in [url['expanded_url'] for url in fav['entities']['urls']]:
            if url in cache:
                data[url] = cache[url]
            else:
                data[url] = get_url_data(url)

    with open(cachepath, 'w') as cachefile:
        pickle.dump(data, cachefile)

    return data

def render_favorites(favorites):
    env = Environment(loader=PackageLoader('render', 'templates'))
    env.filters['twitter_links'] = twitter_links

    favorites = [fav for fav in favorites if 'entities' in fav and len(fav['entities']['urls']) > 0]
    url_data = get_all_url_data(favorites)
    template = env.get_template('index.html')
    print template.render(favorites=favorites, url_data=url_data).encode('utf-8')

def twitter_links(tweet):
    return re.sub(r'(\s)@([a-zA-Z0-9_]+)', r'\1<a href="https://twitter.com/\2">@\2</a>', tweet)


if __name__ == '__main__':
    config = get_config(expanduser('~/.favorites.cfg'))
    favs = load_favorites(config)
    render_favorites(favs)

