import json

settings = None


def load(filename):
    global settings

    print("Loading config file \"{}\"".format(filename))

    with open(filename, "r") as f:
        # NB! this will fail if // is contained within a comment
        settings = json.loads("\n".join(line.split("//")[0].replace("\n", "") for line in f.readlines()))