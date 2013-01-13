# coding=utf-8

"""
Simple test.
"""

import json
import os.path

from dialogue import dialogue


def main():
    """
    Simple dialogue test
    """
    js = json.load(open(os.path.join("samples/test_dialogue.json"), "r"))
    d = dialogue.Dialogue(js)
    ce = dialogue.ConsoleEngine(d)
    ce.run()


if __name__ == "__main__":
    main()