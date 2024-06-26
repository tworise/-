import os
import io
import re
import time
import json
import base64
import subprocess
import openai
import tempfile
import stat
import csv
import numpy as np
import matplotlib.pyplot as plt
import pyperclip
from datetime import datetime, timedelta
from scipy.io import wavfile

from flask import Flask, render_template, request, jsonify, send_file, redirect, url_for, Response
from werkzeug.utils import secure_filename
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager
import pyperclip
from gtts import gTTS
import speech_recognition as sr
import csv
from pydub import AudioSegment

app = Flask(__name__)

# OpenAI API 키 설정
openai.api_key = os.getenv("OPENAI_API_KEY")

# 사용자 디렉토리 내 경로 설정
UPLOAD_FOLDER = os.path.join(os.path.expanduser('~'), 'uploads')
UPLOAD_TXT_FOLDER = os.path.join(UPLOAD_FOLDER, 'txt')
os.makedirs(UPLOAD_TXT_FOLDER, exist_ok=True)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['UPLOAD_TXT_FOLDER'] = UPLOAD_TXT_FOLDER

# 디렉토리에 대한 읽기, 쓰기 및 실행 권한 설정
os.chmod(UPLOAD_TXT_FOLDER, stat.S_IRWXU | stat.S_IRWXG | stat.S_IRWXO)

# 매핑 데이터를 저장할 딕셔너리 초기화
dialect_to_standard = {}

# CSV 파일 목록
csv_files = [
    r"C:/Users/chang/OneDrive/Desktop/-/University/3학년 1학기/캡스톤 디자인/방언 교정/Web/Adjective (1).csv",
    r"C:/Users/chang/OneDrive/Desktop/-/University/3학년 1학기/캡스톤 디자인/방언 교정/Web/Adverb.csv",
    r"C:/Users/chang/OneDrive/Desktop/-/University/3학년 1학기/캡스톤 디자인/방언 교정/Web/nonfinal ending.csv",
    r"C:/Users/chang/OneDrive/Desktop/-/University/3학년 1학기/캡스톤 디자인/방언 교정/Web/voca(1).csv",
    r"C:/Users/chang/OneDrive/Desktop/-/University/3학년 1학기/캡스톤 디자인/방언 교정/Web/voca(2).csv",
    r"C:/Users/chang/OneDrive/Desktop/-/University/3학년 1학기/캡스톤 디자인/방언 교정/Web/voca(3).csv"
]

# 각 CSV 파일에서 데이터를 읽어와 딕셔너리에 추가
for file_path in csv_files:
    with open(file_path, mode='r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        for row in reader:
            dialect = row['dialect']
            standard = row['standard']
            dialect_to_standard[dialect] = standard
            print(f"Loaded mapping: {dialect} -> {standard}")  # 로드된 데이터 로그 출력

# 메인 페이지 라우팅
@app.route('/')
def index():
    return render_template('index.html')

@app.route('/save_message', methods=['POST'])
def save_message():
    data = request.json
    message = data.get('message')
    
    if message:
        # 파일 이름으로 사용할 수 없는 문자를 제거
        filename = secure_filename(message) + '.txt'
        if not filename.strip():  # 만약 파일 이름이 비어 있으면
            filename = "empty_message.txt"  # 기본 파일 이름 지정
        filepath = os.path.join(app.config['UPLOAD_TXT_FOLDER'], filename)
        
        try:
            with open(filepath, 'w', encoding='utf-8') as file:
                file.write(message)
            return jsonify({'success': True})
        except PermissionError:
            return jsonify({'success': False, 'error': 'Permission denied'}), 500
        except Exception as e:
            return jsonify({'success': False, 'error': str(e)}), 500

    return jsonify({'success': False, 'error': 'No message provided'}), 400

# 챗봇 대화 처리 API
@app.route("/chat", methods=["POST"])
def chat():
    user_message = request.json.get("message")
    if user_message:
        try:
            response = openai.ChatCompletion.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant."},
                    {"role": "user", "content": user_message}
                ]
            )
            gpt_message = response.choices[0].message['content']
            return jsonify({"response": gpt_message})
        except Exception as e:
            return jsonify({"error": str(e)})

    return jsonify({"error": "No message provided"}), 400

@app.route('/upload_wav', methods=['POST'])
def upload_wav():
    file = request.files.get('file')
    if file:
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        try:
            # PCM 형식으로 변환
            pcm_filepath = os.path.splitext(filepath)[0] + '_pcm.wav'
            command = f'ffmpeg -i "{filepath}" -acodec pcm_s16le -ar 16000 "{pcm_filepath}"'
            subprocess.run(command, shell=True, check=True)
            
            # STT 적용
            recognizer = sr.Recognizer()
            with sr.AudioFile(pcm_filepath) as source:
                audio_data = recognizer.record(source)
                text = recognizer.recognize_google(audio_data, language='ko-KR')
                
            return jsonify({'text': text})
        except Exception as e:
            return jsonify({'error': str(e)})
        finally:
            try:
                if os.path.exists(pcm_filepath):
                    os.remove(pcm_filepath)  # 변환된 PCM 파일 삭제
            except Exception as e:
                print(f"Error removing PCM file: {e}")
    else:
        return jsonify({'error': '파일 업로드 실패'}), 400

def update_progress(task_id, percentage, status):
    progress[task_id] = {'percentage': percentage, 'status': status}
    
# CSV 데이터 제공 API
@app.route('/get_csv_data', methods=['GET'])
def get_csv_data():
    return jsonify(dialect_to_standard)  # CSV 데이터를 JSON 형태로 반환

# 파일 업로드 처리 API
@app.route('/upload', methods=['POST'])
def upload_file():
    file = request.files.get('file')  # 업로드된 파일 가져오기
    if file:
        filename = secure_filename(file.filename)  # 파일명 안전하게 처리
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)  # 파일 경로 설정
        file.save(filepath)  # 파일 저장

        # 음성 파일을 텍스트로 변환
        dialect_text = speech_to_text(filepath)

        # 방언 텍스트를 표준어로 번역
        standard_text = translate_dialect_to_standard(dialect_text)

        # 표준어 텍스트를 음성으로 변환
        standard_audio_fp = text_to_speech(standard_text)
        standard_audio_fp.seek(0)
        standard_audio_data = standard_audio_fp.read()

        # 결과 반환
        return jsonify({
            'dialect_text': dialect_text,
            'standard_text': standard_text,
            'standard_audio_fp': standard_audio_data.decode('latin1')
        })
    else:
        return jsonify({'error': 'No file uploaded'})

# 텍스트 파일 읽기 API
@app.route('/read_text', methods=['POST'])
def read_text():
    file = request.files.get('file')
    if file:
        text = file.read().decode('utf-8')
        return jsonify({'text': text})
    else:
        return jsonify({'error': 'No file uploaded'}), 400

# 음성 파일을 텍스트로 변환하는 함수
def speech_to_text(filepath):
    return os.path.splitext(os.path.basename(filepath))[0]

# 텍스트를 음성으로 변환하는 함수
def text_to_speech(text, lang='ko'):
    tts = gTTS(text=text, lang=lang)
    audio_fp = io.BytesIO()
    tts.write_to_fp(audio_fp)
    audio_fp.seek(0)
    return audio_fp

# 방언 문장을 표준어로 번역하는 함수
def translate_dialect_to_standard(dialect_text):
    words = dialect_text.split()
    translated_words = []
    for word in words:
        translated_word = dialect_to_standard.get(word, word)  # 사전에 존재하면 변환, 없으면 원본 유지
        translated_words.append(translated_word)
    print(f"Original: {dialect_text}, Translated: {' '.join(translated_words)}")  # 변환 로그 출력
    return ' '.join(translated_words)  # 번역된 단어를 합쳐서 반환

# 대화 기록 관리를 위한 리스트
conversation_history = []

# 기존 learning 라우트 수정
@app.route('/learning', methods=['GET', 'POST'])
def learning():
    global conversation_history  # 전역으로 대화 기록 관리

    if request.method == 'POST':
        data = request.form.get('data')  # 클라이언트로부터 받은 데이터
        if data:
            conversation_history.append(data)  # 대화 기록에 추가

    return render_template('learning.html', conversation_history=conversation_history)

# Amplitude가 임계값을 초과하는 첫 번째 인덱스를 찾는 함수
def find_threshold_index(audio_data, threshold=0.2):
    for i in range(len(audio_data)):
        if np.abs(audio_data[i]) > threshold:
            return i
    return 0

# 소리 크기 맞추기 함수
def match_volume(audio_data1, audio_data2):
    max1 = np.max(np.abs(audio_data1))
    max2 = np.max(np.abs(audio_data2))
    scaling_factor = max1 / max2
    scaled_audio_data2 = audio_data2 * scaling_factor
    return audio_data1, scaled_audio_data2

# 길이를 맞추는 함수
def match_length(audio_data1, audio_data2):
    min_length = min(len(audio_data1), len(audio_data2))
    return audio_data1[:min_length], audio_data2[:min_length]

# 잡음 제거 함수 (RMS 기반)
def remove_noise(audio_data, sample_rate, frame_length=2048, hop_length=512, threshold_db=40):
    frame_count = (len(audio_data) - frame_length) // hop_length + 1
    rms = np.array([np.sqrt(np.mean(audio_data[i * hop_length:i * hop_length + frame_length] ** 2)) for i in range(frame_count)])
    rms_db = 20 * np.log10(rms + 1e-10)

    threshold = 40  # dB
    frames = np.nonzero(rms_db > threshold)
    indices = frames[0] * hop_length

    return audio_data[indices[0]:]

# 앞부분의 침묵을 제거하고 길이를 맞추는 함수
def remove_silence_and_match_length(audio_data1, audio_data2, threshold=0.2):
    start_idx1 = find_threshold_index(audio_data1, threshold)
    start_idx2 = find_threshold_index(audio_data2, threshold)
    audio_data1 = audio_data1[start_idx1:]
    audio_data2 = audio_data2[start_idx2:]
    return match_length(audio_data1, audio_data2)

# 이미지 생성 함수
def create_image(audio_data1, audio_data2, filename, sample_rate1):
    fig, ax = plt.subplots(figsize=(10, 4))
    
    # 1초 앞당김 (샘플링 레이트에 따라 조정)
    shift_samples = sample_rate1 // 2
    audio_data1_shifted = np.pad(audio_data1[shift_samples:], (0, shift_samples), 'constant')
    
    line1, = ax.plot(audio_data1_shifted, color='blue', label='Dialect Voice')
    line2, = ax.plot(audio_data2, color='red', alpha=0.4, label='Standard Voice')
    ax.set_xlabel('Time')
    ax.set_ylabel('Amplitude')
    ax.set_title('Comparison of Dialect Voice and Standard Voice')
    ax.legend(loc='upper right')
    ax.grid(True)
    plt.savefig(filename)
    plt.close(fig)

@app.route('/compare', methods=['POST'])
def compare():
    if 'audio1' not in request.files or 'audio2' not in request.files:
        return jsonify({'error': 'Two audio files must be provided'}), 400

    file1 = request.files['audio1']
    file2 = request.files['audio2']

    # 파일을 WAV 형식으로 변환 및 저장
    audio1 = AudioSegment.from_file(file1)
    audio2 = AudioSegment.from_file(file2)
    file1_path = os.path.join(UPLOAD_FOLDER, 'audio1.wav')
    file2_path = os.path.join(UPLOAD_FOLDER, 'audio2.wav')
    audio1.export(file1_path, format='wav')
    audio2.export(file2_path, format='wav')
    
    wav_io1 = io.BytesIO()
    wav_io2 = io.BytesIO()
    audio1.export(wav_io1, format='wav')
    audio2.export(wav_io2, format='wav')
    wav_io1.seek(0)
    wav_io2.seek(0)
    
    sample_rate1, audio_data1 = wavfile.read(wav_io1)
    sample_rate2, audio_data2 = wavfile.read(wav_io2)
    
    # 잡음 제거
    audio_data1 = remove_noise(audio_data1, sample_rate1)
    
    # 소리 크기 맞추기
    audio_data1, audio_data2 = match_volume(audio_data1, audio_data2)
    
    # 앞부분의 침묵을 제거하고 길이 맞추기
    audio_data1, audio_data2 = remove_silence_and_match_length(audio_data1, audio_data2, threshold=0.2)
    
    # Amplitude가 임계값을 초과하는 첫 번째 인덱스 찾기
    start_idx1 = find_threshold_index(audio_data1, threshold=0.2)
    start_idx2 = find_threshold_index(audio_data2, threshold=0.2)
    
    # 데이터를 임계값을 초과하는 지점부터 사용
    audio_data1 = audio_data1[start_idx1:]
    audio_data2 = audio_data2[start_idx2:]
    
    # 이미지 생성
    image_filename = os.path.join(UPLOAD_FOLDER, 'comparison.png')
    create_image(audio_data1, audio_data2, image_filename, sample_rate1)

    return send_file(image_filename, mimetype='image/png')

# "대화 종료" 버튼 클릭 시 호출되는 함수
@app.route('/end_conversation', methods=['POST'])
def end_conversation():
    global conversation_history  # 전역으로 대화 기록 관리
    conversation_history = []  # 대화 기록 초기화
    return redirect(url_for('learning'))  # 학습 페이지로 리디렉션

# 학습하기 페이지에서 문장과 번역된 결과를 하나씩 보여주는 라우트 추가
@app.route('/learning_display/<int:index>', methods=['GET', 'POST'])
def learning_display(index):
    if index < len(conversation_history):
        dialect_text = conversation_history[index]  # 인덱스에 해당하는 방언 텍스트
        standard_text = translate_dialect_to_standard(dialect_text)  # 방언 텍스트를 표준어로 변환
        return render_template('learning_display.html', dialect_text=dialect_text, standard_text=standard_text, index=index)
    else:
        return render_template('learning_complete.html')  # 모든 문장을 학습했을 때



progress = {}

@app.route('/announcer_tts', methods=['POST'])
def announcer_tts():
    file = request.files.get('file')
    task_id = request.form.get('task_id')
    if file:
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        
        try:
            file.save(filepath)
            print(f"File saved at {filepath}")
        except Exception as e:
            print(f"Failed to save file: {e}")
            return jsonify({'error': f"Failed to save file: {str(e)}"}), 500

        try:
            standard_text = read_text_from_file(filepath)
            print(f"Standard text read from file: {standard_text}")
        except Exception as e:
            print(f"Failed to read text from file: {e}")
            return jsonify({'error': f"Failed to read text from file: {str(e)}"}), 500

        try:
            naver_service = NaverLoginService(task_id)
            naver_service.open_web_mode()
            naver_service.login()
        except Exception as e:
            print(f"Failed to initiate NaverLoginService: {e}")
            return jsonify({'error': f"Failed to initiate NaverLoginService: {str(e)}"}), 500

        try:
            naver_service.driver.get("https://clovadubbing.naver.com/project/3431210")
            WebDriverWait(naver_service.driver, 30).until(EC.presence_of_element_located((By.ID, "dubbing_track_1")))

            final_text = standard_text
            script = f"""
            var inputField = document.getElementById('dubbing_track_1');
            inputField.setAttribute('contenteditable', 'true');
            inputField.focus();
            inputField.textContent = '';  
            inputField.textContent = {json.dumps(final_text)};
            
            var event = new Event('input', {{ bubbles: true }});
            inputField.dispatchEvent(event);
            
            var keyboardEvent = new KeyboardEvent('keydown', {{ bubbles: true, cancelable: true, key: 'Enter', charCode: 13, code: 'Enter', keyCode: 13, which: 13 }});
            inputField.dispatchEvent(keyboardEvent);
            
            keyboardEvent = new KeyboardEvent('keyup', {{ bubbles: true, cancelable: true, key: 'Enter', charCode: 13, code: 'Enter', keyCode: 13, which: 13 }});
            inputField.dispatchEvent(keyboardEvent);
            """
            naver_service.driver.execute_script(script)

            update_progress(task_id, 50, 'in_progress')
            print("첫 번째 위치에 입력 이벤트가 시뮬레이션되었습니다.")

            first_target_selector = "body.overscroll"
            WebDriverWait(naver_service.driver, 30).until(EC.presence_of_element_located((By.CSS_SELECTOR, first_target_selector)))
            first_target_element = naver_service.driver.find_element(By.CSS_SELECTOR, first_target_selector)
            naver_service.driver.execute_script("arguments[0].scrollIntoView(true);", first_target_element)
            time.sleep(1)
            actions = ActionChains(naver_service.driver)
            actions.click(first_target_element).perform()
            print(f"Element with selector {first_target_selector} has been clicked.")

            second_target_selector = "span.track_index"
            WebDriverWait(naver_service.driver, 30).until(EC.presence_of_element_located((By.CSS_SELECTOR, second_target_selector)))
            second_target_element = naver_service.driver.find_element(By.CSS_SELECTOR, second_target_selector)
            naver_service.driver.execute_script("arguments[0].scrollIntoView(true);", second_target_element)
            time.sleep(1)
            actions.click(second_target_element).perform()
            print(f"Element with selector {second_target_selector} has been clicked.")

            update_progress(task_id, 75, 'in_progress')

            download_button_selector = "button.btn.type_download"
            WebDriverWait(naver_service.driver, 30).until(EC.presence_of_element_located((By.CSS_SELECTOR, download_button_selector)))
            download_button_element = naver_service.driver.find_element(By.CSS_SELECTOR, download_button_selector)
            naver_service.driver.execute_script("arguments[0].scrollIntoView(true);", download_button_element)
            time.sleep(1)
            actions.click(download_button_element).perform()
            print(f"Download button with selector {download_button_selector} has been clicked.")

            third_target_selector = "button.btn.type_remove"
            WebDriverWait(naver_service.driver, 30).until(EC.presence_of_element_located((By.CSS_SELECTOR, third_target_selector)))
            third_target_element = naver_service.driver.find_element(By.CSS_SELECTOR, third_target_selector)
            actions.click(third_target_element).perform()
            print(f"Element with selector {third_target_selector} has been clicked.")

            modal_selector = "div.modal_inner.type_default"
            WebDriverWait(naver_service.driver, 30).until(EC.presence_of_element_located((By.CSS_SELECTOR, modal_selector)))
            confirm_button_selector = "//a[contains(text(), '확인')]"
            confirm_button_element = naver_service.driver.find_element(By.XPATH, confirm_button_selector)
            actions.click(confirm_button_element).perform()
            print(f"Confirm button with text '확인' has been clicked.")

            cutoff_time = datetime.now() - timedelta(seconds=30)
            for _ in range(30):
                new_files = [f for f in os.listdir(UPLOAD_FOLDER)
                             if os.path.getctime(os.path.join(UPLOAD_FOLDER, f)) > cutoff_time.timestamp()]
                if new_files:
                    download_path = os.path.join(UPLOAD_FOLDER, new_files[0])
                    break
                time.sleep(1)
            else:
                update_progress(task_id, 100, 'failed')
                raise FileNotFoundError("다운로드한 파일을 찾을 수 없습니다.")

            with open(download_path, "rb") as audio_file:
                audio_data = audio_file.read()
                audio_base64 = base64.b64encode(audio_data).decode('utf-8')

            update_progress(task_id, 100, 'completed')

            return jsonify({
                'standard_text': standard_text,
                'standard_audio_base64': audio_base64
            })

        except Exception as e:
            update_progress(task_id, 100, 'failed')
            print(f"오류가 발생했습니다: {e}")
            return jsonify({'error': str(e)})

        finally:
            naver_service.close_browser()

    else:
        return jsonify({'error': 'No file uploaded'})

def read_text_from_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        return file.read()

class NaverLoginService():

    def __init__(self, task_id):
        self.driver = None
        self.task_id = task_id

    def open_web_mode(self):
        prefs = {'download.default_directory': app.config['UPLOAD_FOLDER']}
        options = webdriver.ChromeOptions()
        options.add_experimental_option('prefs', prefs)
        options.add_argument("--start-maximized")
        self.driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=options)
        self.driver.set_page_load_timeout(20)

    def close_browser(self):
        if self.driver:
            self.driver.quit()
            self.driver = None

    def login(self):
        self.driver.get("https://nid.naver.com/nidlogin.login")
        time.sleep(2)

        test_id = "kwonjy3433"  # 네이버 아이디를 입력하세요
        test_passwd = "wndus3433@"  # 네이버 비밀번호를 입력하세요

        id_input = self.driver.find_element(By.ID, "id")
        id_input.click()
        pyperclip.copy(test_id)
        actions = ActionChains(self.driver)
        actions.key_down(Keys.CONTROL).send_keys('v').key_up(Keys.CONTROL).perform()
        time.sleep(1)

        pw_input = self.driver.find_element(By.ID, "pw")
        pw_input.click()
        pyperclip.copy(test_passwd)
        actions = ActionChains(self.driver)
        actions.key_down(Keys.CONTROL).send_keys('v').key_up(Keys.CONTROL).perform()
        time.sleep(1)

        self.driver.find_element(By.ID, "log.login").click()

        try:
            element = WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "span.btn_cancel"))
            )
            element.click()
        except:
            print("기기 등록 '등록안함' 버튼을 찾을 수 없습니다.")

if __name__ == "__main__":
    app.run(port=5000, debug=True)

