from dialogue import dialogue
import json
import os.path

js = json.load(open(os.path.join("samples/test_dialogue.json"), "r"))

d = dialogue.Dialogue(js)

ce = dialogue.ConsoleEngine(d)

ce.run()