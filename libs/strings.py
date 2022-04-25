import json
import os
import sys

default_locale = "en-gb"
cached_strings = {}

path_to_file = os.path.join(
    os.path.dirname(sys.argv[0]), f"strings/{default_locale}.json"
)


def refresh():
    print("Refreshing...")
    global cached_strings
    with open(path_to_file) as f:
        cached_strings = json.load(f)


def gettext(name):
    return cached_strings[name]


refresh()
