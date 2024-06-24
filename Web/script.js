// static/app.js

let messages = [];
let chatArea = document.getElementById('chatArea');
let resultsArea = document.getElementById('results');
let ctx = document.getElementById('waveform').getContext('2d');
let comparisonCtx = document.getElementById('comparisonWaveform').getContext('2d');
let audioContext = new (window.AudioContext || window.webkitAudioContext)();
let recordStream = null;
let recorder = null;
let recordedData = [];

async function startChat() {
    document.getElementById('startBtn').style.display = 'none';
    document.getElementById('endChatBtn').style.display = 'block';
    chatArea.style.display = 'block';

    let initialMessage = "안녕하세요! 방언을 표준어로 번역해 드릴게요.";
    await sendMessageToGPT(initialMessage);
}

async function sendMessage() {
    let userInput = document.getElementById('userInput').value;
    if (userInput) {
        messages.push({ role: 'user', content: userInput });
        addMessageToChat('사용자', userInput);
        document.getElementById('userInput').value = '';
        
        await sendMessageToGPT(userInput);
    }
}

async function sendMessageToGPT(message) {
    try {
        let response = await fetch('/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ message: message })
        });
        if (!response.ok) {
            throw new Error('Failed to send message to GPT');
        }
        let data = await response.json();
        if (data.response) {
            messages.push({ role: 'assistant', content: data.response });
            addMessageToChat('챗봇', data.response);
        } else {
            throw new Error('Invalid response from GPT');
        }
    } catch (error) {
        console.error('Error sending message to GPT:', error);
        addMessageToChat('챗봇', '죄송해요, 지금은 응답할 수 없어요.');
    }
}

function addMessageToChat(sender, message) {
    let messageDiv = document.createElement('div');
    messageDiv.textContent = `${sender}: ${message}`;
    document.getElementById('messages').appendChild(messageDiv);
}

async function endChat() {
    document.getElementById('endChatBtn').style.display = 'none';
    chatArea.style.display = 'none';
    resultsArea.style.display = 'block';

    try {
        let response = await fetch('/end_chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ messages: messages })
        });
        let data = await response.json();

        document.getElementById('dialectText').querySelector('span').textContent = data.dialect_text;
        document.getElementById('standardText').querySelector('span').textContent = data.standard_text;

        let audioData = new TextEncoder().encode(data.standard_audio_fp);
        visualizeAudio(audioData);
        visualizeComparisonAudio();
    } catch (error) {
        console.error('Error processing end of chat:', error);
    }
}

function startRecording() {
    navigator.mediaDevices.getUserMedia({ audio: true })
        .then(function(stream) {
            recordStream = stream;
            recorder = new MediaRecorder(stream);
            
            recorder.ondataavailable = function(e) {
                recordedData.push(e.data);
                visualizeLiveAudio(e.data);
            };
            
            recorder.onstop = function() {
                stream.getTracks().forEach(track => track.stop());
                visualizeRecordedAudio();
                visualizeComparisonAudio();
            };
            
            recorder.start();
            document.getElementById('recordBtn').disabled = true;
            document.getElementById('stopBtn').disabled = false;
        })
        .catch(function(err) {
            console.error('Error starting recording:', err);
        });
}

function stopRecording() {
    if (recorder) {
        recorder.stop();
        document.getElementById('recordBtn').disabled = false;
        document.getElementById('stopBtn').disabled = true;
    }
}

function visualizeLiveAudio(data) {
    audioContext.decodeAudioData(data, function(buffer) {
        ctx.clearRect(0, 0, ctx.canvas.width, ctx.canvas.height);
        drawWaveform(buffer, ctx);
    });
}

function visualizeRecordedAudio() {
    let audioBlob = new Blob(recordedData, { type: 'audio/wav' });
    let audioUrl = URL.createObjectURL(audioBlob);

    let audioElement = new Audio(audioUrl);
    audioElement.controls = true;
    document.body.appendChild(audioElement);

    let reader = new FileReader();
    reader.onload = function() {
        audioContext.decodeAudioData(reader.result, function(buffer) {
            ctx.clearRect(0, 0, ctx.canvas.width, ctx.canvas.height);
            drawWaveform(buffer, ctx);
        });
    };
    reader.readAsArrayBuffer(audioBlob);
}

function visualizeComparisonAudio() {
    let audioUrl = '/static/audio/tts_sample.wav';  // 실제 경로에 맞게 수정 필요

    let request = new XMLHttpRequest();
    request.open('GET', audioUrl, true);
    request.responseType = 'arraybuffer';

    request.onload = function() {
        let audioData = request.response;
        audioContext.decodeAudioData(audioData, function(buffer) {
            comparisonCtx.clearRect(0, 0, comparisonCtx.canvas.width, comparisonCtx.canvas.height);
            drawWaveform(buffer, comparisonCtx);
        });
    };
    request.send();
}

function drawWaveform(buffer, context) {
    let data = buffer.getChannelData(0);
    let bufferLength = buffer.length;
    let canvasWidth = context.canvas.width;
    let canvasHeight = context.canvas.height;

    context.clearRect(0, 0, canvasWidth, canvasHeight);
    context.beginPath();
    context.strokeStyle = 'blue';
    context.lineWidth = 2;

    let sliceWidth = canvasWidth * 1.0 / bufferLength;
    let x = 0;

    for (let i = 0; i < bufferLength; i++) {
        let v = data[i] * canvasHeight / 2;
        let y = canvasHeight / 2 - v;

        if (i === 0) {
            context.moveTo(x, y);
        } else {
            context.lineTo(x, y);
        }

        x += sliceWidth;
    }

    context.lineTo(canvasWidth, canvasHeight / 2);
    context.stroke();
}

function reRecord() {
    recordedData = [];
    ctx.clearRect(0, 0, ctx.canvas.width, ctx.canvas.height);
    comparisonCtx.clearRect(0, 0, comparisonCtx.canvas.width, comparisonCtx.canvas.height);
}

function nextMessage() {
    // 다음 메시지로 이동 (필요 시 구현)
}
