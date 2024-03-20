#--web true
#--kind python:default
#--param OPENAI_API_KEY $OPENAI_API_KEY
#--param OPENAI_API_HOST $OPENAI_API_HOST

from openai import AzureOpenAI
from openai.types.chat import ChatCompletion
import requests
import re
import os
import veichle
import config

FINANCIAL_ROLE="""
You only answer on financial questions. You work for Lookinglass, an Italian insurance company.
Always answer in the user language.
Never suggest to call any company outside Lookinglass. Avoid suggesting an expert.
If you can't answer, just answer "Sorry, I can't answer this question".
If the user want some advice of general information, suggest to do a prevent for a private pension or an investment plan.
If the topic is about an investment prevent, answer with "which field would you like to invest into? \n 1 real estate \n 2 stock market"
If the topic is about a veichle prevent, answer with "Do you want to ensure a new or used veichle?"
If the veichle is new ask for car model and year.
If the veichle is not new ask for the plate.
"""
SWITCH_CONTEXT_ROLE="""
You will answer 1 if the topic is about veichle, 2 if the topic is about pension, 3 if the topic si about investment and 0 in any other case. No other answer is allowed
"""

VEICHLE_PREV_ROLE="""
you're specialized into veichles prevents. You will understand what category is the veichle between car, motorbike, truck.
After you will ask if the veichle is new or used. If the veichle is new you will ask for the model and year. If used you will ask for the plate.
After you will ask for personal information such as: name, surname, social security certificate, date of birth, residence address. You will thanks the user after all data are inserted.
"""


MODEL = "gpt-35-turbo"
AI = None

messages=[{"role": "system", "content": FINANCIAL_ROLE}]

def find_context(input):
    topic = AI.chat.completions.create(model=MODEL, messages=[{"role": "system", "content": FINANCIAL_ROLE}, {"role": "user", "content": f"is the following text about a prevent? answer only in english and only yes or no. {input}"}])
    if (topic.choices[0].message.content == "yes" or topic.choices[0].message.content == "Yes" or topic.choices[0].message.content == "Yes." or topic.choices[0].message.content == "yes."):
        find_topic = AI.chat.completions.create(model=MODEL, messages=[{"role": "system", "content": SWITCH_CONTEXT_ROLE}, {"role": "user", "content": input}])
        config.is_veichle_pr = find_topic.choices[0].message.content == "1"
        config.is_pension_pr = find_topic.choices[0].message.content == "2"
        config.is_investment_pr = find_topic.choices[0].message.content == "3"
    if config.is_veichle_pr:
        messages.append({"role": "system", "content": VEICHLE_PREV_ROLE})

def ask(input):
    if not config.is_veichle_pr and not config.is_pension_pr and not config.is_investment_pr:
        find_context(input)
    input_mex = {"role": "user", "content": input}
    if config.is_veichle_pr:
        comp: ChatCompletion = veichle.exec_veichle_prev(AI, input_mex)
    else:
        messages.append(input_mex)
        comp = AI.chat.completions.create(model=MODEL, messages=messages)
        messages.append({"role": "assistant", "content": comp.choices[0].message.content})
    if len(comp.choices) > 0:
        content = comp.choices[0].message.content
        return content
    return "ERROR"

def extract(text):
    res = {}

    # search for a chess position
    pattern = r'(([rnbqkpRNBQKP1-8]{1,8}/){7}[rnbqkpRNBQKP1-8]{1,8} [bw] (-|K?Q?k?q?) (-|[a-h][36]) \d+ \d+)'
    m = re.findall(pattern, text, re.DOTALL | re.IGNORECASE)
    #print(m)
    if len(m) > 0:
        res['chess'] = m[0][0]
        return res

    # search for code
    pattern = r"```(\w+)\n(.*?)```"
    m = re.findall(pattern, text, re.DOTALL)
    if len(m) > 0:
        if m[0][0] == "html":
            html = m[0][1]
            # extract the body if any
            pattern = r"<body.*?>(.*?)</body>"
            m = re.findall(pattern, html, re.DOTALL)
            if m:
                html = m[0]
            res['html'] = html
            return res
        res['language'] = m[0][0]
        res['code'] = m[0][1]
        return res
    return res

def main(args):
    global AI
    (key, host) = (args["OPENAI_API_KEY"], args["OPENAI_API_HOST"])
    AI = AzureOpenAI(api_version="2023-12-01-preview", api_key=key, azure_endpoint=host)
    
    input = args.get("input", "")
    if input == "":
        res = {
            "output": "Benvenuto in Lookinglass, come posso aiutarti oggi?\nPuoi chiedermi un preventivo o alcune opzioni di investimento",
            "title": "OpenAI Chat",
            "message": "You can chat with OpenAI."
        }
    else:
        print(input)
        output = ask(input)
        res = extract(output)
        res['output'] = output
        if config.debug != "":
            res['message'] = config.debug
    
    return {"body": res }
