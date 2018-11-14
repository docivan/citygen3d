import json

settings = None


def load(filename):
    global settings

    print("Loading config file \"{}\"".format(filename))

    with open(filename, "r") as f:
        # NB! this will fail if // is contained within a comment
        settings = json.loads('\n'.join([row for row in f.readlines() if len(row.split('//')) == 1]))
