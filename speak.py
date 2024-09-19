import io
import sys
import os
from pathlib import Path
from openai import OpenAI
from dotenv import load_dotenv
from colorama import init, Fore
import simpleaudio as sa
from pydub import AudioSegment
from pydub.playback import play


load_dotenv()
# Initialize colorama for colored output
init(autoreset=True)
# Load the API key from the .env file
OPENAI_KEY = os.getenv("OPENAI_KEY")

if not OPENAI_KEY:
    print(Fore.RED + "Error: OPENAI_KEY is not set in the .env file.")
    sys.exit(1)

# Create an instance of the OpenAI class
client = OpenAI(api_key=OPENAI_KEY)

response = client.audio.speech.create(
  model="tts-1-hd",
  voice="nova",
  #input="Merhaba! Bugün nasılsın? hm Senin için gerçekten güzel bir gün olmasını diliyorum."
  input="hmmm nasıl desem... bu böyle olmayacak sanırım. Bir de şöyle deneyelim: yaz şuraya"
)

speech_file_path = Path(__file__).parent / "speech.mp3"
# Save the response content (audio data) to a file
with open(speech_file_path, "wb") as f:
    f.write(response.content)

# Load the audio file
audio = AudioSegment.from_file(speech_file_path, format="mp3")

# Play the audio
play(audio)
