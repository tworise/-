# TeamA_DokeyDokey_2024_Capstone Design
방언 교정기 프로그램
# Team Introdution
이상승 - 내 목소리 딥보이스 모델 개발자, Web Designer
   
권주연 - 아나운서 딥보이스 모델 개발자, Web Designer

한은영 - LLM, Transform 개발자, Web Designer

김지윤 - 방언, 표준어 매핑, 데이터 수집 및 전처리, Web Designer

# 개발 목적
방언 사용자들이 표준어를 자연스럽고 정확하게 구사하도록 돕는 과정
사용자 친화적인 애플리케이션 인터페이스, 방언-표준어 매핑 데이터베이스, 
TTS 모델, 딥보이스 기술, 그리고 주파수 스펙트럼 분석 알고리즘을 통해 
사용자는 표준어 학습에 필요한 도구를 제공받아 교육 및 직업 기회가 확대됨 
또한, 이 과정은 방언 사용자의 서비스 접근성 개선에 도움을 줍니다.

# 사용법
CSV 파일의 저장 경로를 App.py 내에서 실행해주시기 바랍니다.

대화를 시작하고 녹음시작과 종료를 하면 음성이 자동으로 채팅박스에 등록됩니다.

부정확하게 인식된 Text는 수정하여 보내고, 챗봇과 대화를 할 수 있습니다.

학습페이지로 넘어가 아나운서의 목소리로 표준어를 들을 수 있으며, 내 목소리로 표준어를 들을 수 도 있습니다.

내 목소리로 표준어를 듣기 위해서는 Voice Convertor 모델이 필요합니다.

VC파일의 압축을 풀어 Install을 실행시켜 모듈을 다운받고, Run을 실행합니다.

Voice Convertor 모델을 학습하기 위해 최소 10분 가량의 내 목소리 파일이 필요합니다.

44100Hz, 모노, Wav파일로 내 목소리를 녹음해주시고 학습을 진행시켜 모델을 만들어 주십시오.
일반적으로 VRAM 8GB 이상의 그래픽카드를 권장합니다.

주파수 비교하기 버튼을 누르면 내 음성과 비교해 볼 수 있습니다.

# Reference
https://github.com/IAHispano/Applio

https://www.ncloud.com/product/aiService/clovaVoice

