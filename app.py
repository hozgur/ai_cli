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

# Declare client as a global variable
client = None

def init_client():
    global client
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
command_history_path = os.path.join(path, "command_history.json")
env_file_path = os.path.join(path,".env")
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
    init_client()  # Ensure client is initialized
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
        update_command_history(response.command)

    # Ask the user if they want to run the command
    run_choice = input(Fore.GREEN + "Run this command? (Y/N, press Enter for Yes): " + Fore.RESET).strip().lower()
    if response.command and run_choice in ['y', '']:
        run_command(response.command)        
    else:
        print(Fore.RED + "Command not executed.")

def usage():
    print(Fore.GREEN + "Usage: ask [message]")
    print(Fore.GREEN + "Example:" + Fore.CYAN + " ask delete png files on my ~/images folder" + Fore.GREEN)
    print(Fore.GREEN + "If you want to reset the last message and response, run:" + Fore.CYAN + " ask new" + Fore.GREEN)
    print(Fore.GREEN + "If you want to run the a command from command history, run:" + Fore.CYAN + " ask run [command_number]" + Fore.GREEN)
    print(Fore.GREEN + "If you want to see the command history, run:" + Fore.CYAN + " ask last" + Fore.GREEN)
    print(Fore.GREEN + "If you want to see the usage, run:" + Fore.CYAN + " ask help" + Fore.GREEN)
    print(Fore.GREEN + "If you want to see the version, run:" + Fore.CYAN + " ask version")
    print(Fore.GREEN + "If you want to see current model, run:" + Fore.CYAN + " ask model")
    print(Fore.GREEN + "If you want to change the model, run:" + Fore.CYAN + " ask model [model_name]")
    print(Fore.GREEN + "If you want to see available models, run:" + Fore.CYAN + " ask models")    
    print(Fore.GREEN + "If you want to set OpenAI API key, run:" + Fore.CYAN + " ask set-key [openai_key]" + Fore.RESET)

def list_available_models():
    init_client()  # Ensure client is initialized
    try:
        models = client.models.list()
        return [model.id for model in models]
    except Exception as e:
        print(f"Error fetching models: {e}")
        return []

def update_command_history(command):
    history = []
    if os.path.exists(command_history_path):
        with open(command_history_path, "r") as f:
            history = json.load(f)
    history.append(command)
    history = history[-10:]  # Keep last 10 commands
    with open(command_history_path, "w") as f:
        json.dump(history, f, indent=2)

def main():
    global model
    argc = len(sys.argv)
    if argc < 2:
        usage()
        exit()
    message = sys.argv[1]
    if argc == 2:
        if message == "new":
            if os.path.exists(last_message_file):
                os.remove(last_message_file)
            if os.path.exists(last_command_path):
                os.remove(last_command_path)
            if os.path.exists(command_history_path):
                os.remove(command_history_path)
            print("all cleared.")
            exit()
        if message == ("run"):
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
            if os.path.exists(command_history_path):
                with open(command_history_path, "r") as f:
                    history = json.load(f)
                    if history:
                        print(Fore.YELLOW + "Last 10 commands:")
                        for i, cmd in enumerate(history, 1):
                            print(f"  {i}. {cmd}")
                    else:
                        print(Fore.RED + "Command history is empty.")
            else:
                print(Fore.RED + "No command history found.")
            return
            
        if message == "model":
            print(Fore.CYAN + "Current model: " + model)
            exit()
        if message == "models":
            print(Fore.CYAN + "Available models: ")
            for m in list_available_models():
                print(Fore.CYAN + "Model: " + m)
            exit()

    if argc == 3:
        if message == "run":
            try:
                print ("run------")
                index = int(sys.argv[2]) - 1
                with open(command_history_path, "r") as f:
                    history = json.load(f)
                if 0 <= index < len(history):
                    command = history[index]
                    print(Fore.CYAN + f"Running [#{index+1}]: {command}")
                    run_command(command)
                else:
                    print(Fore.RED + "Invalid command number.")
            except (IndexError, ValueError):
                print(Fore.RED + "Usage: run <command#>")
            return

        if message == "model":
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
        if message == "set-key":
            key = sys.argv[2]
            if key.startswith("sk"):
                with open(env_file_path,"w") as f:
                    f.write(f'OPENAI_KEY={key}')
            else:
                print(Fore.RED+"Invalid key.")
            exit()
    if argc > 2:
        message = " ".join(sys.argv[1:])
    print("message: " + message + "\n")
    ask(message)

if __name__ == '__main__':
    main()