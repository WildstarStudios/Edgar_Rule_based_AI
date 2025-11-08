import queue
import sounddevice as sd
import sys
import json
import time
from vosk import Model, KaldiRecognizer

# 🔧 CONFIGURATION
MODEL_PATH = "speech/vosk-model-small-en-us-0.15"
SAMPLE_RATE = 16000
BLOCK_SIZE = 2048
CHANNELS = 1
DTYPE = 'int16'

# ⏱ Silence timeouts
ACTIVE_SILENCE_TIMEOUT = 2.5  # After speech starts
IDLE_SILENCE_TIMEOUT = 5.0    # After "hey edgar" if no speech follows

# 🎙️ Load Vosk model
print("⏳ Loading Vosk model...")
try:
    model = Model(MODEL_PATH)
    recognizer = KaldiRecognizer(model, SAMPLE_RATE)
    recognizer.SetWords(True)
    print("✅ Model loaded successfully!")
except Exception as e:
    print(f"❌ Failed to load model: {e}")
    sys.exit(1)

# 🎧 Audio queue
audio_queue = queue.Queue()

# 🎤 Callback to capture audio
def callback(indata, frames, time_info, status):
    if status:
        print(f"⚠️ {status}", file=sys.stderr)
    audio_queue.put(bytes(indata))

# 🧠 State variables
listening = False
last_spoken_time = None
activated_time = None

# 🚀 Start audio stream
print("🎤 Say 'hey edgar' to begin...")
with sd.RawInputStream(samplerate=SAMPLE_RATE,
                       blocksize=BLOCK_SIZE,
                       dtype=DTYPE,
                       channels=CHANNELS,
                       callback=callback):
    try:
        while True:
            data = audio_queue.get()
            if recognizer.AcceptWaveform(data):
                result = json.loads(recognizer.Result())
                text = result.get("text", "").lower()

                if not listening and "hey edgar" in text:
                    listening = True
                    activated_time = time.time()
                    last_spoken_time = None
                    print("\n👂 Listening activated...")

                elif listening and text:
                    print(f"\r✅ {text}")
                    last_spoken_time = time.time()

            else:
                partial = json.loads(recognizer.PartialResult())
                partial_text = partial.get("partial", "").lower()

                if listening and partial_text:
                    print(f"\r📝 {partial_text}", end="")
                    last_spoken_time = time.time()

            # ⏱ Silence handling
            now = time.time()
            if listening:
                if last_spoken_time:
                    if now - last_spoken_time > ACTIVE_SILENCE_TIMEOUT:
                        print(f"\n🛑 No speech detected for {ACTIVE_SILENCE_TIMEOUT} seconds. Listening stopped.")
                        listening = False
                        last_spoken_time = None
                        activated_time = None
                        print("\n🎤 Say 'hey edgar' to begin...")
                elif activated_time and now - activated_time > IDLE_SILENCE_TIMEOUT:
                    print(f"\n🛑 No speech after activation for {IDLE_SILENCE_TIMEOUT} seconds. Listening stopped.")
                    listening = False
                    activated_time = None
                    print("\n🎤 Say 'hey edgar' to begin...")
    except KeyboardInterrupt:
        print("\n🛑 Program terminated.")
