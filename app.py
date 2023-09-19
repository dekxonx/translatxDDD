import re
import os
import time
import sys
import openai
import threading 
import requests
import keyboard

input_lang = "EN"
output_lang = "HU"

deepl_api_key = ''
openai.api_key = ''

script_dir = os.path.dirname(os.path.realpath(__file__))
last_progress_update_time = time.time()



print("")
# max_chars=int(input('Hány karaktert fordítsunk le? (0 = összes)\n)'
def preprocess_subtitle(input_subtitle_file, output_text_file, max_chars=None):
    os.system('cls')
    print("Felirat előfeldolgozása...")
    try:
        with open(input_subtitle_file, 'r', encoding='utf-8') as file:
            if max_chars:
                content = file.read(max_chars)
            else:
                content = file.read()
        timestamp_pattern = r'\d+:\d+:\d+,\d+ --> \d+:\d+:\d+,\d+'
        dialogue_segments = []
        include_line = True
        for line in content.splitlines():
            if re.match(timestamp_pattern, line.strip()):
                include_line = True
            elif re.match(r'^\d+$', line.strip()):
                include_line = False
            elif include_line:
                dialogue_segments.append(line.strip())
        with open(output_text_file, 'w', encoding='utf-8') as output_file:
            output_file.write('\n'.join(dialogue_segments[1:]))
        print("Előfeldolgozás befejezve.")
    except Exception as e:
        print(f"Hiba az előfeldolgozás közben: {str(e)}")

def translate_with_chatgpt(input_text, language=output_lang):
    conversation = [
        {"role": "system", "content": f"Translate the following English text to {language}:"},
        {"role": "user", "content": input_text},
    ]

    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=conversation,
        timeout=60
    )

    return response.choices[0].message["content"]


def seconds_to_minutes(seconds):
    minutes = seconds // 60
    seconds %= 60
    return minutes, seconds

def progress_monitor():
    global last_progress_update_time
    while True:
        time.sleep(10)  
        current_time = time.time()
        if current_time - last_progress_update_time > 20:
            print("\nÚgy tűnik, hogy az alkalmazás lefagyott. Nyomdd meg az 'r' gombot az újra próbálkozáshoz.")
            while True:
                if keyboard.is_pressed('r'):
                    print("Kézi újrapróbálkozás...")
                    return
                time.sleep(10)  

def translate_with_deepl(text, source_lang, target_lang):
    url = 'https://api-free.deepl.com/v2/translate'
    params = {
        'auth_key': deepl_api_key,
        'text': text,
        'source_lang': source_lang,
        'target_lang': target_lang,
    }

    response = requests.post(url, data=params)
    response.raise_for_status()
    translation = response.json()
    translated_text = translation['translations'][0]['text']

    return translated_text

def translate_to_hungarian_with_deepl(input_text_file, output_hungarian_file):
    print("Fordítás magyarra...")
    try:
        with open(input_text_file, 'r', encoding='utf-8') as file:
            content = file.readlines()

        total_chunks = sum(1 for line in content if line.strip())  # Calculate total chunks
        max_chunk_tokens = 50
        translated_content = []
        current_chunk = 0

        for line in content:
            line = line.strip()
            if line:
                if line.isdigit() and current_chunk == 0:
                    continue

                max_retries = 3
                retries = 0
                start_time = time.time() 

                while retries < max_retries:
                    try:
                        translated_line = translate_with_deepl(line, input_lang, output_lang)
                        translated_content.append(translated_line)
                        current_chunk += 1
                        progress = current_chunk / total_chunks
                        bar_length = 20
                        bar = "#" * int(bar_length * progress)
                        bar += "." * (bar_length - int(bar_length * progress))
                        elapsed_time = time.time() - start_time 
                        remaining_chunks = total_chunks - current_chunk
                        estimated_remaining_time = elapsed_time * remaining_chunks
                        remaining_minutes, remaining_seconds = divmod(int(estimated_remaining_time), 60)

                        sys.stdout.write(f"\rDarab {current_chunk}/{total_chunks} ")
                        sys.stdout.write(f"[{bar}] {int(progress * 100)}% ")
                        sys.stdout.write(f"ETA: {remaining_minutes}m {remaining_seconds}s ")
                        sys.stdout.flush()

                        break
                    except Exception as e:
                        print(f"Hiba a fordítás során (Próba {retries + 1}): {str(e)}")
                        retries += 1
                        time.sleep(5)

                if retries == max_retries:
                    print(f"A fordítás sikertelen {max_retries} próbálkozás után. Ezt a darabot kihagyjuk.")
                    translated_content.append("")
            else:
                translated_content.append("")

        print()
        with open(output_hungarian_file, 'w', encoding='utf-8') as output_file:
            output_file.write("\n".join(translated_content))
        print("Fordítás befejezve.")
    except Exception as e:
        print(f"Hiba a fordítás során: {str(e)}")

def extract_and_store_timestamps(input_subtitle_file, output_timestamps_file):
    with open(input_subtitle_file, 'r', encoding='utf-8') as file:
        content = file.readlines()
    timestamps = [line.strip() for line in content if re.match(r'\d+:\d+:\d+,\d+ --> \d+:\d+:\d+,\d+', line.strip())]
    with open(output_timestamps_file, 'w', encoding='utf-8') as timestamps_file:
        timestamps_file.write('\n'.join(timestamps))
    print("Az időbélyeg kivonása befejeződött.")

def combine_with_timestamps(input_subtitle_file, output_subtitle_file, translated_text_file, timestamps_file):
    with open(translated_text_file, 'r', encoding='utf-8') as file:
        translated_content = file.readlines()

    with open(timestamps_file, 'r', encoding='utf-8') as file:
        timestamps = file.readlines()
    combined_subtitles = []
    timestamp_index = 0
    counter = 1
    combined_subtitles.append(str(counter))
    counter += 1
    if timestamp_index < len(timestamps):
        combined_subtitles.append(timestamps[timestamp_index].strip())
        timestamp_index += 1
    for line in translated_content:
        line = line.strip()
        if not line:
            combined_subtitles.append("")
            combined_subtitles.append(str(counter))
            counter += 1
            if timestamp_index < len(timestamps):
                combined_subtitles.append(timestamps[timestamp_index].strip())
                timestamp_index += 1
        else:
            combined_subtitles.append(line)
    with open(output_subtitle_file, 'w', encoding='utf-8') as output_file:
        output_file.write('\n'.join(combined_subtitles))
    print("A felirat kombinálása elkészült")



folder_name = 'stuff'

if not os.path.exists(folder_name):
    os.mkdir(folder_name)

input_subtitle_file = os.path.join(script_dir, 'subtitle.srt')
output_text_file = os.path.join(folder_name, 'output_dialogue_original.txt')
output_hungarian_file = os.path.join(folder_name, 'translated_dialogue_hu.txt')
output_combined_subtitle_file = os.path.join(script_dir, folder_name, 'complete.srt')

preprocess_subtitle(input_subtitle_file, output_text_file)
translate_to_hungarian_with_deepl(output_text_file, output_hungarian_file)
extract_and_store_timestamps(input_subtitle_file, os.path.join(folder_name, 'timestamps.txt'))
combine_with_timestamps(
    input_subtitle_file,
    output_combined_subtitle_file,
    output_hungarian_file,
    os.path.join(script_dir, folder_name, 'timestamps.txt')
)

print("A fordítás elkészült.")
print("")
print(f'A lefordított fájl a "{folder_name}" mappában található. \nA fájl neve "complete.srt"')
print("")
input("Nyomja meg az Enter-t a kilépéshez...")
