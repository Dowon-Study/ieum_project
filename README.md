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
recruitment-mcp> python fastapi_server.py             

Front 터미널 실행 명령어 
FRONT-END\ieum-frontend> npm install axios


FRONT-END\ieum-frontend> npm run dev
