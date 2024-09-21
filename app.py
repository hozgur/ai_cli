import sys
import os
import json
import platform
import subprocess
from dotenv import load_dotenv
from colorama import init, Fore, Style
import openai
from openai import OpenAI
from pydantic import BaseModel

# Load environment variables
load_dotenv()

# Load the API key from the .env file
OPENAI_KEY = os.getenv("OPENAI_KEY")
if not OPENAI_KEY:
    print(Fore.RED + "Error: OPENAI_KEY is not set in the .env file.")
    sys.exit(1)

# Initialize OpenAI client
client = OpenAI(api_key=OPENAI_KEY)

# Initialize colorama for colored output
init(autoreset=True)

# Get path to the current directory
path = os.path.dirname(os.path.realpath(__file__))

# File paths
last_message_file = os.path.join(path, "last_message.json")
config_path = os.path.join(path, "config.json")
last_command_path = os.path.join(path, "last_command.bat" if platform.system() == "Windows" else "last_command.sh")

# Load configuration
config = {}
if os.path.exists(config_path):
    with open(config_path, "r") as f:
        config = json.load(f)

model = config.get("model", "gpt-4o-2024-08-06")

# System prompt template
system_prompt_template = "You are a CLI command creator for {os}. If you need to add a description, keep it short and simple. Otherwise, only the command, no description."
os_display_names = {"Windows": "Windows", "Darwin": "macOS", "Linux": "Linux"}
os_name = platform.system()
os_display_name = os_display_names.get(os_name, None)

if os_display_name is None:
    print(f"Unsupported OS: {os_name}")
    sys.exit(1)

system_prompt = system_prompt_template.format(os=os_display_name)

class Response(BaseModel):
    command: str
    description: str

def run_command(command):
    try:
        result = subprocess.run(command, shell=True, check=True, text=True)
        print(Fore.GREEN + "Command executed successfully.")
    except subprocess.CalledProcessError as e:
        print(Fore.RED + f"Command failed with error: {e}")

def ask(message):
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": message}
    ]

    # Load the last message and response from the file
    if os.path.exists(last_message_file):
        with open(last_message_file, "r") as f:
            last_data = json.load(f)
            messages.extend([last_data["last_message"], last_data["last_response"]])
            
    messages.append({"role": "user", "content": message})
    # Call the OpenAI API
    try:
        api_response = client.beta.chat.completions.parse(
            model=model,
            messages=messages,
            response_format=Response
        )
    except openai.OpenAIError as e:
        print(Fore.RED + f"OpenAI API error: {e}")
        sys.exit(1)
    

    response = api_response.choices[0].message.parsed

    # Save the last message and response to the file
    last_data = {
        "last_message": {"role": "user", "content": message},
        "last_response": {"role": "assistant", "content": response.command + " Description: " + response.description}
    }
    with open(last_message_file, "w") as f:
        json.dump(last_data, f)

    # Print the response
    if response.description:
        print(f"Description: {response.description}")
    if response.command:
        print(f"Command: {Fore.CYAN}{response.command}")
        with open(last_command_path, "w") as f:
            f.write(response.command)

    # Ask the user if they want to run the command
    run_choice = input(Fore.GREEN + "Run this command? (Y/N, press Enter for Yes): " + Fore.RESET).strip().lower()
    if response.command and run_choice in ['y', '']:
        run_command(response.command)        
    else:
        print(Fore.RED + "Command not executed.")

def usage():
    print(Fore.GREEN + "Usage: ask [message]")
    print(Fore.GREEN + "Example: ask 'delete png files on my ~/images folder'")
    print(Fore.GREEN + "If you want to reset the last message and response, run:" + Fore.CYAN + " ask new" + Fore.GREEN)
    print(Fore.GREEN + "If you want to run the last command, run:" + Fore.CYAN + " ask run" + Fore.GREEN)
    print(Fore.GREEN + "If you want to see the last command, run:" + Fore.CYAN + " ask last" + Fore.GREEN)
    print(Fore.GREEN + "If you want to see the usage, run:" + Fore.CYAN + " ask help" + Fore.GREEN)
    print(Fore.GREEN + "If you want to see the version, run:" + Fore.CYAN + " ask version")
    print(Fore.GREEN + "If you want to see current model, run:" + Fore.CYAN + " ask model")
    print(Fore.GREEN + "If you want to see available models, run:" + Fore.CYAN + " ask models")
    print(Fore.GREEN + "If you want to change the model, run:" + Fore.CYAN + " ask --model [model_name]" + Fore.RESET)
    

def list_available_models():
    try:
        models = openai.models.list()
        return [model.id for model in models]
    except Exception as e:
        print(f"Error fetching models: {e}")
        return []

def main():
    argc = len(sys.argv)
    if argc < 2:
        usage()
        exit()
    message = sys.argv[1]
    if argc == 2:
        if message == "new":
            if os.path.exists(last_message_file):
                os.remove(last_message_file)
            print("reseted")
            exit()
        if message == "run":
            if os.path.exists(last_command_path):
                with open(last_command_path, "r") as f:
                    command = f.read()
                    print(Fore.CYAN + "Command: " + command)
                    run_command(command)                    
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
    if argc == 3 and message == "--model":
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
        message = " ".join(sys.argv[1:])
    print("message: " + message + "\n")
    ask(message)

if __name__ == '__main__':
    main()