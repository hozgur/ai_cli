import sys
import os
import json
import platform
import subprocess
import urllib.request
import urllib.error
from dotenv import load_dotenv, set_key
from colorama import init, Fore
import openai
from openai import OpenAI
from pydantic import BaseModel

VERSION = "1.1.0"

# Initialize colorama for colored output
init(autoreset=True)

# Get path to the current directory
path = os.path.dirname(os.path.realpath(__file__))

# File paths
last_message_file = os.path.join(path, "last_message.json")
config_path = os.path.join(path, "config.json")
last_command_path = os.path.join(path, "last_command.bat" if platform.system() == "Windows" else "last_command.sh")
command_history_path = os.path.join(path, "command_history.json")
env_file_path = os.path.join(path, ".env")

# Load environment variables from the .env next to app.py
load_dotenv(env_file_path)

PROVIDERS = ("ollama", "openai")
DEFAULT_PROVIDER = "ollama"
DEFAULT_OPENAI_MODEL = "gpt-4o-2024-08-06"
DEFAULT_OLLAMA_HOST = "http://localhost:11434"


def read_json(file_path, default):
    if not os.path.exists(file_path):
        return default
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (OSError, json.JSONDecodeError):
        return default


def write_json(file_path, data, **kwargs):
    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, **kwargs)


# Load configuration
config = read_json(config_path, {})
# Migrate legacy config: "model" used to always mean an OpenAI model
if "model" in config and "openai_model" not in config:
    config["openai_model"] = config["model"]
config.pop("model", None)

provider = os.getenv("ASK_PROVIDER") or config.get("provider", DEFAULT_PROVIDER)
if provider not in PROVIDERS:
    print(Fore.RED + f"Unknown provider: {provider}. Use one of: {', '.join(PROVIDERS)}")
    sys.exit(1)


def save_config():
    write_json(config_path, config, indent=2)


def ollama_host():
    host = (os.getenv("OLLAMA_HOST") or DEFAULT_OLLAMA_HOST).strip().rstrip("/")
    if "://" not in host:
        host = "http://" + host
    # 0.0.0.0 is a valid bind address for the server but not for a client
    return host.replace("://0.0.0.0", "://localhost")


def ollama_request(endpoint, payload=None):
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(ollama_host() + endpoint, data=data,
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.load(resp)


def ollama_unreachable(e):
    print(Fore.RED + f"Cannot reach Ollama at {ollama_host()}: {e}")
    print(Fore.YELLOW + "Is Ollama running? Start it with 'ollama serve' or set OLLAMA_HOST.")
    sys.exit(1)


def ollama_chat_models():
    """Installed Ollama models that can generate text (skips embedding-only models)."""
    try:
        names = [m["name"] for m in ollama_request("/api/tags").get("models", [])]
        chat_models = []
        for name in names:
            caps = ollama_request("/api/show", {"model": name}).get("capabilities")
            # Older Ollama versions don't report capabilities; assume the model can chat
            if caps is None or "completion" in caps:
                chat_models.append(name)
        return chat_models
    except (urllib.error.URLError, OSError) as e:
        ollama_unreachable(e)


def get_model():
    if provider == "openai":
        return config.get("openai_model", DEFAULT_OPENAI_MODEL)
    model = os.getenv("OLLAMA_MODEL") or config.get("ollama_model")
    if model:
        return model
    # No model chosen yet: pick the first installed chat model and remember it
    models = ollama_chat_models()
    if not models:
        print(Fore.RED + "No Ollama chat models installed. Install one, e.g.: ollama pull qwen3:8b")
        sys.exit(1)
    model = models[0]
    config["ollama_model"] = model
    save_config()
    print(Fore.YELLOW + f"No Ollama model configured, using '{model}'. Change it with: ask model [model_name]")
    return model


def make_client():
    if provider == "openai":
        key = os.getenv("OPENAI_KEY")
        if not key:
            print(Fore.RED + "Error: OPENAI_KEY is not set. Run: ask set-key [openai_key]")
            sys.exit(1)
        return OpenAI(api_key=key)
    # Ollama exposes an OpenAI-compatible API; the key is required by the SDK but ignored
    return OpenAI(base_url=ollama_host() + "/v1", api_key="ollama")


# System prompt template
system_prompt_template = "You are a CLI command creator for {os}. If you need to add a description, keep it short and simple. Otherwise, only the command, no description."
# subprocess.run(shell=True) uses cmd.exe on Windows and /bin/sh elsewhere, so ask for that syntax
os_display_names = {
    "Windows": "Windows. The command runs in cmd.exe; when PowerShell is needed, wrap it as: powershell -NoProfile -Command \"...\"",
    "Darwin": "macOS. The command runs in /bin/sh",
    "Linux": "Linux. The command runs in /bin/sh",
}
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
        subprocess.run(command, shell=True, check=True, text=True)
        print(Fore.GREEN + "Command executed successfully.")
    except subprocess.CalledProcessError as e:
        print(Fore.RED + f"Command failed with error: {e}")


def ask(message):
    model = get_model()
    client = make_client()
    messages = [{"role": "system", "content": system_prompt}]

    # Include the previous exchange so follow-up requests have context
    last_data = read_json(last_message_file, None)
    if last_data:
        messages.extend([last_data["last_message"], last_data["last_response"]])

    messages.append({"role": "user", "content": message})

    extra = {}
    if provider == "ollama":
        # Thinking models (qwen3, deepseek-r1...) are much slower and don't need to reason for this task
        extra["reasoning_effort"] = "none"

    try:
        api_response = client.chat.completions.parse(
            model=model,
            messages=messages,
            response_format=Response,
            **extra,
        )
    except openai.APIConnectionError as e:
        if provider == "ollama":
            ollama_unreachable(e)
        print(Fore.RED + f"Connection error: {e}")
        sys.exit(1)
    except openai.OpenAIError as e:
        print(Fore.RED + f"{provider} API error: {e}")
        sys.exit(1)

    response = api_response.choices[0].message.parsed
    if response is None:
        print(Fore.RED + "The model did not return a valid response. Try again or use another model.")
        sys.exit(1)

    # Save the last message and response to the file
    last_data = {
        "last_message": {"role": "user", "content": message},
        "last_response": {"role": "assistant", "content": response.command + " Description: " + response.description}
    }
    write_json(last_message_file, last_data)

    # Print the response
    if response.description:
        print(f"Description: {response.description}")
    if not response.command:
        print(Fore.RED + "No command returned.")
        return

    print(f"Command: {Fore.CYAN}{response.command}")
    with open(last_command_path, "w", encoding="utf-8") as f:
        f.write(response.command)
    update_command_history(response.command)

    # Ask the user if they want to run the command
    run_choice = input(Fore.GREEN + "Run this command? (Y/N, press Enter for Yes): " + Fore.RESET).strip().lower()
    if run_choice in ['y', '']:
        run_command(response.command)
    else:
        print(Fore.RED + "Command not executed.")


def usage():
    print(Fore.GREEN + "Usage: ask [message]")
    print(Fore.GREEN + "Example:" + Fore.CYAN + " ask delete png files on my ~/images folder" + Fore.GREEN)
    print(Fore.GREEN + "If you want to reset the last message, response and history, run:" + Fore.CYAN + " ask new" + Fore.GREEN)
    print(Fore.GREEN + "If you want to run the last command again, run:" + Fore.CYAN + " ask run" + Fore.GREEN)
    print(Fore.GREEN + "If you want to run a command from command history, run:" + Fore.CYAN + " ask run [command_number]" + Fore.GREEN)
    print(Fore.GREEN + "If you want to see the command history, run:" + Fore.CYAN + " ask last" + Fore.GREEN)
    print(Fore.GREEN + "If you want to see the usage, run:" + Fore.CYAN + " ask help" + Fore.GREEN)
    print(Fore.GREEN + "If you want to see the version, run:" + Fore.CYAN + " ask version")
    print(Fore.GREEN + "If you want to see current provider, run:" + Fore.CYAN + " ask provider")
    print(Fore.GREEN + "If you want to change the provider, run:" + Fore.CYAN + " ask provider [ollama|openai]")
    print(Fore.GREEN + "If you want to see current model, run:" + Fore.CYAN + " ask model")
    print(Fore.GREEN + "If you want to change the model, run:" + Fore.CYAN + " ask model [model_name]")
    print(Fore.GREEN + "If you want to see available models, run:" + Fore.CYAN + " ask models")
    print(Fore.GREEN + "If you want to set OpenAI API key, run:" + Fore.CYAN + " ask set-key [openai_key]" + Fore.RESET)


def list_available_models():
    if provider == "ollama":
        return ollama_chat_models()
    try:
        return [m.id for m in make_client().models.list()]
    except openai.OpenAIError as e:
        print(Fore.RED + f"Error fetching models: {e}")
        return []


def update_command_history(command):
    history = read_json(command_history_path, [])
    history.append(command)
    history = history[-10:]  # Keep last 10 commands
    write_json(command_history_path, history, indent=2)


def main():
    global provider
    argc = len(sys.argv)
    if argc < 2:
        usage()
        sys.exit()
    message = sys.argv[1]
    if argc == 2:
        if message == "new":
            for p in (last_message_file, last_command_path, command_history_path):
                if os.path.exists(p):
                    os.remove(p)
            print("all cleared.")
            sys.exit()
        if message == "run":
            if os.path.exists(last_command_path):
                with open(last_command_path, "r", encoding="utf-8") as f:
                    command = f.read()
                print(Fore.CYAN + "Command: " + command)
                run_command(command)
            else:
                print(Fore.RED + "No last command found.")
            sys.exit()
        if message == "help":
            usage()
            sys.exit()
        if message == "version":
            print(Fore.GREEN + f"ask version {VERSION}")
            sys.exit()
        if message == "last":
            history = read_json(command_history_path, None)
            if history is None:
                print(Fore.RED + "No command history found.")
            elif not history:
                print(Fore.RED + "Command history is empty.")
            else:
                print(Fore.YELLOW + "Last 10 commands:")
                for i, cmd in enumerate(history, 1):
                    print(f"  {i}. {cmd}")
            sys.exit()
        if message == "provider":
            print(Fore.CYAN + "Current provider: " + provider)
            if provider == "ollama":
                print(Fore.CYAN + "Ollama host: " + ollama_host())
            sys.exit()
        if message == "model":
            print(Fore.CYAN + f"Current model ({provider}): " + get_model())
            sys.exit()
        if message == "models":
            print(Fore.CYAN + f"Available models ({provider}): ")
            for m in list_available_models():
                print(Fore.CYAN + "Model: " + m)
            sys.exit()

    if argc == 3:
        if message == "run":
            history = read_json(command_history_path, [])
            try:
                index = int(sys.argv[2]) - 1
            except ValueError:
                print(Fore.RED + "Usage: ask run <command#>")
                sys.exit(1)
            if 0 <= index < len(history):
                command = history[index]
                print(Fore.CYAN + f"Running [#{index+1}]: {command}")
                run_command(command)
            else:
                print(Fore.RED + "Invalid command number.")
            sys.exit()
        if message == "provider":
            new_provider = sys.argv[2].lower()
            if new_provider not in PROVIDERS:
                print(Fore.RED + f"Unknown provider. Use one of: {', '.join(PROVIDERS)}")
                sys.exit(1)
            provider = new_provider
            config["provider"] = provider
            save_config()
            print(Fore.CYAN + "Provider set to: " + provider)
            sys.exit()
        if message == "model":
            new_model = sys.argv[2]
            available = list_available_models()
            # Ollama accepts "llama3.2" for "llama3.2:latest"
            if provider == "ollama" and new_model not in available and new_model + ":latest" in available:
                new_model += ":latest"
            if new_model in available:
                config[f"{provider}_model"] = new_model
                save_config()
                print(Fore.CYAN + f"Model ({provider}) set to: " + new_model)
            else:
                print(Fore.RED + "Model not found. See: ask models")
            sys.exit()
        if message == "set-key":
            key = sys.argv[2]
            if key.startswith("sk"):
                # Update only OPENAI_KEY, keep any other variables in .env
                set_key(env_file_path, "OPENAI_KEY", key, quote_mode="never")
                print(Fore.GREEN + "OpenAI key saved. Switch to OpenAI with: ask provider openai")
            else:
                print(Fore.RED + "Invalid key.")
            sys.exit()

    if argc > 2:
        message = " ".join(sys.argv[1:])
    ask(message)


if __name__ == '__main__':
    main()
