## 설치(conda)
# 1. 가상환경 생성
conda create -n mcp-project python=3.12

# 2. 활성화  
conda activate mcp-project

python -m pip install -U pip setuptools wheel

pip install mcp fastmcp httpx python-dotenv

pip install fastapi uvicorn python-multipart


실행

터미널 Back. Front 따로 실행해야함

Back 터미널 실행 명령어
\HUSS_AI\recruitment-mcp> python fastapi_server.py             

Front 터미널 실행 명령어 
HUSS_AI\FRONT-END\ieum-frontend> npm install axios
HUSS_AI\FRONT-END\ieum-frontend> npm run dev


------------------------------------------------
0817 04:00 수정 내용

정책 지역 매핑 수정
채용 공고 - 채용 구분 추가
+ 등등 수정

해야될 것
- 일자리 지역 매핑 불완전함. 수정 필요
- 정보 불러오는 개수 얼마로 정할지 논의 필요
- ui 수정
- 최종적으로 어떻게 보이게 할지, 디자인 및 이모티콘 등등 논의 가장 필요할 것 같음
- 17알 지정까지 제출할 것 많음 -> 다같이 정리해서 제출하기
- 실제로 청년들이 지방으로 이주하는 데 문제를 겪은 사례 찾기
--------------------------------------------------
push push baby