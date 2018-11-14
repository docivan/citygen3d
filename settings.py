import json

settings = None


def load(filename):
    global settings

    print("Loading config file \"{}\"".format(filename))
    with open(filename, "r") as f:
         settings = json.load(f)
