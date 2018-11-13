import json

settings = None

def load(filename):
    global settings

    print("Importing settings file \"{}\"".format(filename))
    with open(filename, "r") as f:
         settings = json.load(f)
