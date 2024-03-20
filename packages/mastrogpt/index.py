#--web true
import json

def main(arg):
    data = {
        "services": [
            { 
                "name": "Demo", 
                "url": "mastrogpt/demo",
            },
            {
                "name": "Lookinglass",
                "url": "openai/chat"
            },
            {
                "name": "OpenAI",
                "url": "openai/gpt"
            }
        ]
    }
    return {"body": data}

