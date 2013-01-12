"""
Basic data structures needed to support dialogue system.
"""

from __future__ import print_function, unicode_literals
from collections import defaultdict

#todo: complex boolean conditionals
#todo: more flexible prompt (multi-line, multi-char)
#todo: fuzzy logic

class Condition(object):
    def __init__(self, condition):
        self.variable = condition["variable"]
        self.operation = condition["operation"]
        self.value = condition.get("value", None)

    def apply(self, globals):
        value = globals[self.variable]
        is_boolean_op = (self.operation == "set" or self.operation == "unset")

        if not is_boolean_op and value is None:
            raise ValueError("Non boolean op with no value")
        ret = {">": lambda: value > self.value,
               "<": lambda: value < self.value,
               "=": lambda: value == self.value,
               "==": lambda: value == self.value,
               ">=": lambda: value >= self.value,
               "<=": lambda: value <= self.value,
               "set": lambda: value == 1,
               "unset": lambda: value == 0}.get(self.operation)()
        return ret

    def __repr__(self):
        return "<variable: %s, operation: %s, value: %s>" % (self.variable, self.operation, self.value)


class Effect(object):
    def __init__(self, effect):
        self.variable = effect["variable"]
        self.operation = effect["operation"]
        self.value = effect.get("value", None)

    def apply(self, globals):
        if isinstance(self.value, unicode):
            if self.value.startswith("eval:"):
                self.value = eval(self.value[5:])
            else:
                self.value = globals[self.value]

        mutation = {"+": lambda x: x + self.value,
                    "-": lambda x: x - self.value,
                    "=": lambda x: self.value,
                    "set": lambda x: 1,
                    "unset": lambda x: 0}.get(self.operation)
        globals[self.variable] = mutation(globals[self.variable])


class Dialogue(object):
    """
    The Dialogue class is the public API to the dialogue system.
    """

    def __init__(self, prompt_dict):
        self.globals = defaultdict(int)
        self.globals.update(prompt_dict["defaults"])
        self.prompts = {}
        self._create_prompts(prompt_dict["prompts"])
        self.current_prompt = 0
        self.done = False

    def _create_prompts(self, prompt_list):
        for prompt in prompt_list:
            self.prompts[prompt["id"]] = Prompt(prompt)

    def is_done(self):
        """
        Returns true if there is nothing left to do in the dialogue.
        """
        return self.done

    def get_prompt(self):
        """
        Returns the prompt from the current conversation node.
        """
        if self.done is False:
            if not self.prompts[self.current_prompt].responses:
                self.done = True
            return self.prompts[self.current_prompt].text
        else:
            return None

    def get_responses(self):
        """
        Returns the list of available responses.
        """
        if self.done is False:
            return self.prompts[self.current_prompt].get_responses(self.globals)
        else:
            return None

    def answer(self, response_ix):
        """
        Answers the prompt with the chosen response index.  Responses are 0-indexed.
        """
        if not self.done:
            active_responses = [response for response in self.prompts[self.current_prompt].responses if
                                all([precondition.apply(self.globals) for precondition in response.preconditions])]
            chosen_response = active_responses[response_ix]
            chosen_response.apply_effects(self.globals)
            next = chosen_response.get_next(self.globals)
            self.current_prompt = next
            if self.current_prompt == -1:
                self.done = True
        else:
            raise Exception("Trying to answer a finished dialog")

    def get_globals(self):
        """
        Return the current dialog state.
        """
        return self.globals


class Prompt(object):
    def __init__(self, prompt):
        self.text = prompt["text"]
        self.id = prompt["id"]
        self.responses = []
        self._create_responses(prompt["responses"])

    def _create_responses(self, response_list):
        for response in response_list:
            self.responses.append(Response(response))

    def get_responses(self, globals):
        active_responses = [response.text for response in self.responses if
                            all([precondition.apply(globals) for precondition in response.preconditions])]
        return active_responses


class Response(object):
    def __init__(self, response):
        self.text = response["text"]
        self.effects = []
        self.transitions = []
        self.preconditions = []
        self._create_preconditions(response.get("preconditions", []))
        self._create_effects(response.get("effects", []))
        self._create_transitions(response["transitions"])

    def _create_preconditions(self, preconditions_list):
        for precondition in preconditions_list:
            self.preconditions.append(Condition(precondition))

    def _create_effects(self, effect_list):
        for effect in effect_list:
            self.effects.append(Effect(effect))

    def _create_transitions(self, next_list):
        for next in next_list:
            target = next["target"]
            conditions = []
            for condition in next["conditions"]:
                conditions.append(Condition(condition))
            self.transitions.append((target, conditions))

    def get_next(self, globals):
        ret = -1
        for target, conditions in self.transitions:
            if all([cond.apply(globals) for cond in conditions]):
                ret = target
                break
        return ret

    def apply_effects(self, globals):
        for effect in self.effects:
            effect.apply(globals)


class ConsoleEngine(object):
    def __init__(self, dialog):
        self.dialog = dialog

    def run(self):
        while True:
            print("(globals: ", self.dialog.get_globals(), ")")
            print(self.dialog.get_prompt())
            if self.dialog.is_done():
                break

            ix = 1
            for response in self.dialog.get_responses():
                print("%d) %s" % (ix, response))
                ix += 1

            while True:
                res = input("> ")

                try:
                    res = int(res)
                except ValueError:
                    print("Response must be an int between %d and %d" % (1, ix - 1))
                    continue

                if res < 1 or res > ix - 1:
                    print("Response must be between %d and %d" % (1, ix - 1))
                else:
                    self.dialog.answer(res - 1)
                    break

            if self.dialog.is_done():
                break
            print()
