from openai import OpenAI
from pydantic import BaseModel
import sys
import os
import pickle
import json
import platform
import subprocess
from dotenv import load_dotenv
from colorama import init, Fore, Style
import openai
load_dotenv()
# Load the API key from the .env file
OPENAI_KEY = os.getenv("OPENAI_KEY")

if not OPENAI_KEY:
    print(Fore.RED + "Error: OPENAI_KEY is not set in the .env file.")
    sys.exit(1)

# Create an instance of the OpenAI class
client = OpenAI(api_key=OPENAI_KEY)

# Get path to the current directory
path = os.path.dirname(os.path.realpath(__file__))

# We will store the last message and response in a file to use it in the next call
last_message_file = os.path.join(path, "last_message.pkl")

# Template for the system prompt
system_prompt_template = "You are a CLI command creator for {os}. If you need to add a description, keep it short and simple. Otherwise, only the command, no description."

# Mapping OS names to their display names
os_display_names = {
    "Windows": "Windows",
    "Darwin": "macOS",
    "Linux": "Linux"
}

# Get the current OS name
os_name = platform.system()

# Get the display name for the OS, or exit if unsupported
os_display_name = os_display_names.get(os_name, None)

if os_display_name is None:
    print(f"Unsupported OS: {os_name}")
    sys.exit(1)

last_command_path = ""
if os_name == "Windows":
    last_command_path = os.path.join(path, "last_command.bat")
else:
    last_command_path = os.path.join(path, "last_command.sh")

config_path = os.path.join(path, "config.json")

config = {}
if os.path.exists(config_path):
    with open(config_path, "r") as f:
        config = json.load(f)

model = config.get("model", "gpt-4o-2024-08-06")
# Initialize colorama for colored output
init(autoreset=True)

# Create the system prompt using the template
system_prompt = system_prompt_template.format(os=os_display_name)

class Response(BaseModel):
    command: str
    description: str

def ask(message):    
    messages=[
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": "delete png files on my ~/images folder"},
        {"role": "assistant", "content": "rm  ~/images/*.png"},
        {"role": "user", "content": "show me my external ip"},
        {"role": "assistant", "content": "curl ifconfig.me"},
    ]
    # Load the last message and response from the file
    if(os.path.exists(last_message_file)):
        with open(last_message_file, "rb") as f:
            last_message = pickle.load(f)
            last_response = pickle.load(f)
            messages.append(last_message)
            messages.append(last_response)

    # Add the new message to the list
    messages.append({"role": "user", "content": message})
    # Call the OpenAI API
    api_response = client.beta.chat.completions.parse(
        model=model,
        messages=messages,
        response_format=Response
    )
    response = api_response.choices[0].message.parsed
    
    # Save the last message and response to the file
    last_message  = {"role": "user", "content": message}
    last_response = {"role": "assistant", "content": response.command + " " + response.description}
    with open(last_message_file, "wb") as f:
        pickle.dump(last_message, f)
        pickle.dump(last_response, f)

    # Print the response
    if response.description:
        print(f"Description: {response.description}")
    if response.command:
        print(f"Command: {Fore.CYAN}{response.command}")
        #save the command to a file                
        with open(last_command_path, "w") as f:
            f.write(response.command)
        
    # Ask the user if they want to run the command
    run_choice = input(Fore.GREEN + "Run this command? (Y/N, press Enter for Yes): "+Fore.RESET).strip().lower()
    if response.command:
        if run_choice in ['y', '']:                    
            try:
                # Use subprocess to run the command
                result = subprocess.run(response.command, shell=True, check=True, text=True)
                print(Fore.GREEN + "Command executed successfully.")
            except subprocess.CalledProcessError as e:
                print(Fore.RED + f"Command failed with error: {e}")
        else:
            print(Fore.RED + "Command not executed.")
        

def usage():
    print(Fore.GREEN + "Usage: ask [message]")
    print(Fore.GREEN + "Example: ask 'delete png files on my ~/images folder'")
    print(Fore.GREEN + "If you want to reset the last message and response, run:" + Fore.CYAN + " ask new" + Fore.GREEN )
    print(Fore.GREEN + "If you want to run the last command, run:" + Fore.CYAN + " ask run" + Fore.GREEN)
    print(Fore.GREEN + "If you want to see the last command, run:" + Fore.CYAN + " ask last" + Fore.GREEN)
    print(Fore.GREEN + "If you want to see the usage, run:" + Fore.CYAN + " ask help" + Fore.GREEN)
    print(Fore.GREEN + "If you want to see the version, run:" + Fore.CYAN + " ask version" + Fore.RESET + "\n")
    print(Fore.GREEN + "If you want to see current model, run:" + Fore.CYAN + " ask model" + Fore.RESET)

def list_available_models():
    try:
        models = openai.models.list()
        model_names = [model.id for model in models]  # Extract model names
        return model_names
    except Exception as e:
        print(f"Error fetching models: {e}")
        return []

if __name__ == '__main__':
    argc = len(sys.argv)
    if argc < 2:
        usage()
        exit()
    if argc == 2:
        message = sys.argv[1]
        if message == "new":
            os.remove(last_message_file)
            print("reseted")
            exit()
        if message == "run":
            if os.path.exists(last_command_path):
                with open(last_command_path, "r") as f:
                    command = f.read()
                    print(Fore.CYAN + "Command: " + command)
                    result = subprocess.run(command, shell=True, check=True, text=True)
                    print(Fore.GREEN + "Command executed successfully.")
            else:
                print(Fore.RED + "No last command found.")
            exit()
        if message == "help":
            usage()
            exit()
        if message == "version":
            print(Fore.GREEN + "ask version 1.0.0")
            exit()
        if message == "last":
            if os.path.exists(last_command_path):
                with open(last_command_path, "r") as f:
                    command = f.read()
                    print(Fore.CYAN + "Command: " + command)                    
            else:
                print(Fore.RED + "No last command found.")
            exit()
        if message == "model":
            print(Fore.CYAN + "Current model: " + model)
            exit()
        if message == "models":
            print(Fore.CYAN + "Available models: ")
            for m in list_available_models():
                print(Fore.CYAN + "Model: " + m)
            exit()        
    if  argc == 3:
        message = sys.argv[1]
        if message == "--model":
            new_model = sys.argv[2]
            if new_model in list_available_models():                
                model = new_model
                config["model"] = model
                with open(config_path, "w") as f:
                    json.dump(config, f)
                print(Fore.CYAN + "Model set to: " + model)
            else:
                print(Fore.RED + "Model not found.")
            exit()
    if argc > 2:
        message = sys.argv[1]
        for i in range(2, argc):
            message += " " + sys.argv[i]

    print("message: " + message + "\n")
    ask(message)