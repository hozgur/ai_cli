from openai import OpenAI
import sys
import os
import pickle

USE_COPY_TO_CLIPBOARD = False
OPENAI_KEY = "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"

client = OpenAI(api_key=OPENAI_KEY)

path = os.path.dirname(os.path.realpath(__file__))

last_message_file = os.path.join(path, "last_message.pkl")
def ask(message):

    messages=[
        {"role": "system", "content": "You are cli command creator for linux and mac. If you need to add description keep description short and simple. otherwise only command no description."},
        {"role": "user", "content": "delete png files on my ~/images folder"},
        {"role": "assistant", "content": "rm  ~/images/*.png"},
        {"role": "user", "content": "show me my external ip"},
        {"role": "assistant", "content": "curl ifconfig.me"},
    ]
    if(os.path.exists(last_message_file)):
        with open(last_message_file, "rb") as f:
            last_message = pickle.load(f)
            last_response = pickle.load(f)
            messages.append(last_message)
            messages.append(last_response)

    messages.append({"role": "user", "content": message})
    response = client.chat.completions.create(
    model="gpt-4-turbo",
    messages=messages,
    )
    last_message  = {"role": "user", "content": message}
    last_response = {"role": "assistant", "content": response.choices[0].message.content}

    with open(last_message_file, "wb") as f:
        pickle.dump(last_message, f)
        pickle.dump(last_response, f)
    response_txt = response.choices[0].message.content
    
    print(response.choices[0].message.content)

if __name__ == '__main__':
    argc = len(sys.argv)
    if argc < 2:
        message = "hello"
    if argc == 2:
        message = sys.argv[1]
        if message == "new":
            os.remove(last_message_file)
            print("reseted")
            exit()
    if argc > 2:
        message = sys.argv[1]
        for i in range(2, argc):
            message += " " + sys.argv[i]

    print("message: " + message + "\n")
    ask(message)