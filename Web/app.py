import os
import csv
from flask import Flask, render_template, request, jsonify, redirect, url_for
from werkzeug.utils import secure_filename
from transformers import pipeline
from gtts import gTTS
import io
import numpy as np
import matplotlib.pyplot as plt
from scipy.io import wavfile
import openai

app = Flask(__name__)

# OpenAI API 키 설정
openai.api_key = os.getenv("OPENAI_API_KEY")

# 매핑 데이터를 저장할 딕셔너리 초기화
dialect_to_standard = {}

# CSV 파일 목록
csv_files = [
    r"C:\Users\tkdtm\Downloads\Web\Adjective (1).csv",
    r"C:\Users\tkdtm\Downloads\Web\Adverb.csv",
    r"C:\Users\tkdtm\Downloads\Web\nonfinal ending.csv",
    r"C:\Users\tkdtm\Downloads\Web\voca(1).csv",
    r"C:\Users\tkdtm\Downloads\Web\voca(2).csv",
    r"C:\Users\tkdtm\Downloads\Web\voca(3).csv"
]

# 각 CSV 파일에서 데이터를 읽어와 딕셔너리에 추가
for file_path in csv_files:
    with open(file_path, mode='r', encoding='utf-8') as file:
        reader = csv.DictReader(file)
        for row in reader:
            dialect = row['dialect']  # '방언' 열 이름에 맞게 수정
            standard = row['standard']  # '표준어' 열 이름에 맞게 수정
            dialect_to_standard[dialect] = standard

# 파일 업로드 경로 설정
UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# 메인 페이지 라우팅
@app.route('/')
def index():
    return render_template('index.html')

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
            # API 응답에서 챗봇의 답변 추출
            gpt_message = response.choices[0].message['content']
            return jsonify({"response": gpt_message})
        except Exception as e:
            return jsonify({"error": str(e)})

    return jsonify({"error": "No message provided"}), 400

# 파일 업로드 처리 API
@app.route('/upload', methods=['POST'])
def upload_file():
    file = request.files.get('file')
    if file:
        filename = secure_filename(file.filename)
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)

        # 음성 파일을 텍스트로 변환
        dialect_text = speech_to_text(filepath)

        # 방언 텍스트를 표준어로 번역
        standard_text = dialect_to_standard.get(dialect_text, "해당 방언에 대한 표준어를 찾을 수 없습니다.")

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

# 음성 파일을 텍스트로 변환하는 함수
def speech_to_text(filepath):
    # 여기서 실제 음성 인식을 수행해야 함
    # 예시로 간단하게 파일명을 리턴하도록 구현
    return os.path.splitext(os.path.basename(filepath))[0]

# 텍스트를 음성으로 변환하는 함수
def text_to_speech(text, lang='ko'):
    tts = gTTS(text=text, lang=lang)
    audio_fp = io.BytesIO()
    tts.write_to_fp(audio_fp)
    audio_fp.seek(0)
    return audio_fp

# 대화 기록 관리를 위한 리스트
conversation_history = []

@app.route('/learning', methods=['GET', 'POST'])
def learning():
    if request.method == 'POST':
        data = request.form.get('data')
        if data:
            conversation_history.append(data)
    return render_template('learning.html', conversation_history=conversation_history)

# 그래프 표시를 위한 데이터 준비
def plot_waveform(audio_data, title):
    plt.figure(figsize=(10, 4))
    plt.plot(audio_data, color='blue', label='User Voice')
    plt.xlabel('Time')
    plt.ylabel('Amplitude')
    plt.title(title)
    plt.legend(loc='upper right')
    plt.grid(True)
    return plt

# 녹음하기 API
@app.route('/record', methods=['GET', 'POST'])
def record():
    if request.method == 'POST':
        # 여기서 녹음을 수행하고 파형을 그래프로 표시해야 함 (실제 녹음 구현은 생략)
        # 예시로 랜덤한 데이터로 그래프를 그리는 코드를 작성했습니다.
        audio_data_user = np.random.rand(100)
        audio_data_deepvoice = np.random.rand(100)

        plt_user = plot_waveform(audio_data_user, 'User Voice')
        plt_deepvoice = plot_waveform(audio_data_deepvoice, 'DeepVoice Standard')

        # 두 그래프를 하나의 이미지로 합쳐서 전송
        fig, ax = plt.subplots()
        ax.plot(audio_data_user, color='blue', label='User Voice')
        ax.plot(audio_data_deepvoice, color='red', label='DeepVoice Standard')
        ax.set_xlabel('Time')
        ax.set_ylabel('Amplitude')
        ax.set_title('Comparison of User Voice and DeepVoice Standard')
        ax.legend(loc='upper right')
        ax.grid(True)

        # 그래프 이미지를 바이트 형태로 변환하여 전송
        buf = io.BytesIO()
        plt.savefig(buf, format='png')
        buf.seek(0)
        plt.close()

        return buf.read(), 200, {'Content-Type': 'image/png'}

    return render_template('record.html')

if __name__ == "__main__":
    app.run(port=5000, debug=True)
