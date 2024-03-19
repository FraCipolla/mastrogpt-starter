from openai import AzureOpenAI
from openai.types.chat import ChatCompletion
import requests
import re
import os
import config
import json

VEICHLE_PREV_ROLE="""
Always answer in the user language.
Never suggest to call any company outside Lookinglass. Avoid suggesting an expert.
you're specialized into veichles prevents such as moto, auto and truck.
Ask only this questions in this order one at a time:
"the veichle is new?"
"what type of veichle is? option: moto, auto, truck"
"model of the veichle?"
"engine size?"
"year?"
"How many km?"
Repeat any question with an incorrect answer
After you will ask for personal information such as:
name
surname
social security certificate (in italian "codice fiscale")
date of birth
Repeat any question with an incorrect answer
After you have collected all the informations show the user all the data and ask: "this if data is correct?"
if data is correct thank the user
"""
MODEL="gpt-35-turbo"
messages=[{"role": "system", "content": VEICHLE_PREV_ROLE}]
veichle_data = {
    "new": None,
    "type": None,
    "cc": None,
    "model": None,
    "year": None,
    "km": None,
    }
user_data = {
    "name": None,
    "surname": None,
    "date_of_birth": None,
    "ssc": None,
    "address": None,
    "email": None
}

form_validation = False

def extract_data_from_chat(data = dict[str, any]):
    for x in data:
        print(str(x))

def exec_veichle_prev(AI = AzureOpenAI, input = dict[str, any]) -> ChatCompletion:
    global form_validation
    messages.append(input)
    if form_validation:
        print("input " + input['content'])
        form_validation = False
        config.is_veichle_pr = False
    fun = [
        {
            "name": "extract_data_from_chat",
            "description": "Extract veichle informations and user informations",
            "parameters": {
                "type": "object",
                "properties": {
                    "data": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "type" : {"type": "string", "description": "type of veichle"},
                                "model" : {"type": "string", "description": "veichle model"},
                                "cc" : {"type": "string", "description": "engine size of veichle"},
                                "name" : {"type": "string", "description": "user name"},
                                "surname": { "type": "string", "description": "user surname"},
                                "date_of_birth": { "type": "string", "description": "user date of birth"},
                                "ssc": { "type": "string", "description": "user social security certificate"}
                                },
                                "required": ["type", "model", "cc", "name", "surname", "date_of_birth", "ssc"]
                            }
                        }
                    },
                    "required": ["user"]
                }
            }
        ]
    comp = AI.chat.completions.create(model=MODEL, messages=messages)
    extract = AI.chat.completions.create(model=MODEL, messages=messages, functions=fun, function_call={"name": "extract_data_from_chat"})
    encoded_data = extract.choices[0].message.function_call.arguments
    print("func " + json.dumps(json.loads(encoded_data), indent=4))
    if ((comp.choices[0].message.content.find("veicolo") != -1 or comp.choices[0].message.content.find("Veicolo") != -1)
        and (comp.choices[0].message.content.find("Modello") != -1 or comp.choices[0].message.content.find("modello") != -1)
        and (comp.choices[0].message.content.find("Cilindrata") != -1 or comp.choices[0].message.content.find("cilindrata") != -1)
        and (comp.choices[0].message.content.find("Nome") != -1 or comp.choices[0].message.content.find("nome") != -1)
        and (comp.choices[0].message.content.find("Cognome") != -1 or comp.choices[0].message.content.find("cognome") != -1)
        and (comp.choices[0].message.content.find("Data di nascita") != -1 or comp.choices[0].message.content.find("data di nascita") != -1)):
        print("form: " + comp.choices[0].message.content)
        form_validation = True
    messages.append({"role": "assistant", "content": comp.choices[0].message.content})

    return comp