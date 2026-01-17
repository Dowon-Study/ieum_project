import os
import pandas as pd
import numpy as np
import torch
import traceback
import time
import httpx
import asyncio
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sentence_transformers import SentenceTransformer, util
from typing import List, Dict, Any
from dotenv import load_dotenv
from openai import OpenAI

# [1] 환경 설정 및 AI 모델 로딩
load_dotenv()
os.environ['KMP_DUPLICATE_LIB_OK'] = 'True'

app = FastAPI(title="이음(IEUM) 실시간 API 및 AI 분석 통합 서버")

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

print("🔄 AI 모델 로딩 중...")
device = "cuda" if torch.cuda.is_available() else "cpu"
model = SentenceTransformer('BM-K/KoSimCSE-roberta-multitask', device=device)
print(f"✅ 모델 로드 완료! (Device: {device})")

# --- 2. 분석 대상 및 매핑 정의 ---
EXTINCTION_RISK_MAP = {
    "26710": "부산 기장군", "41250": "경기 동두천시", "41650": "경기 포천시",
    "41670": "경기 여주시", "41800": "경기 연천군", "41820": "경기 가평군",
    "41830": "경기 양평군", "44800": "충남 예산군", "44790": "충남 청양군",
    "51150": "강원 강릉시", "51770": "강원 정선군", "51750": "강원 영월군",
    "52210": "전북 김제시", "46110": "전남 목포시"
}

PROVINCE_JOB_MAP = {
    "경기": ["41250", "41650", "41670", "41800", "41820", "41830"],
    "강원": ["51150", "51770", "51750"], "충남": ["44800", "44790"],
    "전북": ["52210"], "전남": ["46110"], "부산": ["26710"]
}

class RecommendationRequest(BaseModel):
    user_interest: str
    policy_query: str
    budget: int
    rent_budget: int

class RegionDetailRequest(BaseModel):
    regionCode: str
    user_interest: str
    policy_query: str
    budget: int
    rent_budget: int

# --- 3. 실시간 데이터 수집 함수 (API Fetchers) ---

async def fetch_api_data(url: str, params: dict):
    async with httpx.AsyncClient(timeout=10.0) as client:
        response = await client.get(url, params=params)
        if response.status_code != 200:
            return []
        return response.json()

async def get_all_policies():
    """청년정책 API 호출 및 데이터프레임 변환"""
    # 실제 운영 시 페이지네이션 처리가 필요할 수 있습니다.
    data = await fetch_api_data(os.getenv("POLICY_API_URL"), {"apiKey": os.getenv("POLICY_API_KEY"), "display": 100})
    # API 응답 구조에 맞게 리스트 추출 (예: data['policies'])
    policies = data.get('policies', []) if isinstance(data, dict) else []
    return pd.DataFrame(policies).fillna("")

async def get_all_jobs():
    """공공기관 채용 API 호출"""
    data = await fetch_api_data(os.getenv("JOB_API_URL"), {"apiKey": os.getenv("JOB_API_KEY")})
    jobs = data.get('jobs', []) if isinstance(data, dict) else []
    return pd.DataFrame(jobs).fillna("")

async def get_real_estate(region_code: str):
    """국토부 실거래가 API 호출 (특정 지역)"""
    params = {
        "serviceKey": os.getenv("REAL_ESTATE_API_KEY"),
        "LAWD_CD": region_code[:5],
        "DEAL_YMD": "202512" # 최근 데이터 기준
    }
    data = await fetch_api_data(os.getenv("REAL_ESTATE_API_URL"), params)
    items = data.get('response', {}).get('body', {}).get('items', {}).get('item', [])
    # API 필드명을 기존 CSV 컬럼명으로 매핑
    df = pd.DataFrame(items)
    if not df.empty:
        df = df.rename(columns={
            "아파트": "아파트명", "보증금액": "보증금(만원)", 
            "월세금액": "월세(만원)", "전용면적": "전용면적(m2)",
            "층": "층수", "건축년도": "건축년도", "법정동": "법정동"
        })
        df["보증금(만원)"] = df["보증금(만원)"].str.replace(",", "").astype(int)
        df["월세(만원)"] = df["월세(만원)"].str.replace(",", "").astype(int)
    return df.fillna(0)

# --- 4. 기존 유틸리티 및 AI 로직 (유지) ---

def normalize_scores(score_dict: Dict[str, float]):
    if not score_dict: return score_dict
    max_val = max(score_dict.values())
    return {k: (v / max_val) * 100 if max_val > 0 else 0.0 for k, v in score_dict.items()}

def is_relevant_policy(zip_str: str, inst_name: str, target_code: str):
    if not zip_str: return False
    region_info = EXTINCTION_RISK_MAP.get(target_code, "")
    if not region_info: return False
    
    province_name, city_name = region_info.split()[0], region_info.split()[1]
    city_short = city_name.replace("시", "").replace("군", "")
    
    zip_list = [z.strip() for z in str(zip_str).split(',')]
    code_match = any(c in zip_list for c in [target_code, target_code[:2] + "000", "00000"])
    
    if not code_match: return False
    
    national_keywords = ["중앙", "정부", "국가", "진흥원", "재단", "본부", "위원회", "공사"]
    inst_match = (city_short in str(inst_name) or province_name in str(inst_name) or any(k in str(inst_name) for k in national_keywords))
    return inst_match

def generate_ai_report(name, job, policy, j_count, re_count, p_count, top_jobs, top_policies):
    try:
        prompt = f"""지역:{name}, 희망직무:{job}, 정책관심:{policy}, 결과:일자리{j_count}건, 매물{re_count}건, 정책{p_count}건. 
        위 데이터를 기반으로 이 지역의 특징과 추천 이유를 2문장 내외의 전문적인 한국어로 작성하세요."""
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "system", "content": "지역 정착 컨설턴트 '이음'입니다."}, {"role": "user", "content": prompt}],
            max_tokens=200
        )
        return response.choices[0].message.content.strip()
    except:
        return f"{name}은 {job} 관련 기회가 풍부하여 정착하기에 우수한 환경을 갖추고 있습니다."

# --- 5. API 엔드포인트 구현 ---

@app.post("/api/recommendation/integrated-ranking")
async def get_integrated_ranking(req: RecommendationRequest):
    try:
        # 실시간 데이터 로드
        df_p, df_j = await asyncio.gather(get_all_policies(), get_all_jobs())
        
        # 유사도 계산
        p_unique = df_p['plcyNm'].unique().tolist()
        p_sim_map = dict(zip(p_unique, util.cos_sim(model.encode([req.policy_query]), model.encode(p_unique))[0].tolist()))
        df_j['sim'] = util.cos_sim(model.encode([req.user_interest]), model.encode(df_j['ncsCdNmLst'].astype(str).tolist()))[0].tolist()

        p_scores, j_scores, re_counts, p_m, j_m = {}, {}, {}, {}, {}

        for code, name in EXTINCTION_RISK_MAP.items():
            # 정책/일자리 필터링
            p_reg = df_p[df_p.apply(lambda x: is_relevant_policy(x['zipCd'], x['sprvsnInstCdNm'], code), axis=1)].copy()
            p_reg['sim'] = p_reg['plcyNm'].map(p_sim_map)
            p_scores[code] = float(p_reg['sim'].sum())
            p_m[code] = int(len(p_reg[p_reg['sim'] >= 0.3]))

            city_short = name.split()[-1]
            j_reg = df_j[df_j['workRgnNmLst'].str.contains(city_short) | 
                         df_j['workRgnNmLst'].apply(lambda x: any(p in str(x) for p, cs in PROVINCE_JOB_MAP.items() if code in cs))]
            j_scores[code] = float(j_reg['sim'].sum())
            j_m[code] = int(len(j_reg[j_reg['sim'] >= 0.3]))

            # 부동산은 랭킹 단계에서는 대표 샘플링 혹은 통계 API 사용 가능 (여기서는 빈값 처리 후 상세에서 호출)
            re_counts[code] = 10 # 시뮬레이션 데이터

        p_norm, j_norm = normalize_scores(p_scores), normalize_scores(j_scores)

        final_ranking = []
        for code, name in EXTINCTION_RISK_MAP.items():
            total = (p_norm.get(code,0) + j_norm.get(code,0)) / 2
            final_ranking.append({
                "regionName": name, "regionCode": code, "score": round(float(total), 2),
                "houseCount": re_counts[code], "jobCount": j_m[code], "policyCount": p_m[code]
            })

        return sorted(final_ranking, key=lambda x: x['score'], reverse=True)[:6]
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/recommendation/region-detail")
async def get_region_detail(req: RegionDetailRequest):
    code, name = req.regionCode, EXTINCTION_RISK_MAP.get(req.regionCode, "알 수 없는 지역")
    try:
        # 실시간 데이터 병렬 수집
        df_p, df_j, df_re = await asyncio.gather(get_all_policies(), get_all_jobs(), get_real_estate(code))
        
        # 1. 일자리
        city_short = name.split()[-1]
        j_f = df_j[df_j['workRgnNmLst'].str.contains(city_short) | df_j['workRgnNmLst'].apply(lambda x: any(p in str(x) for p, cs in PROVINCE_JOB_MAP.items() if code in cs))].copy()
        j_sims = util.cos_sim(model.encode([req.user_interest]), model.encode(j_f['ncsCdNmLst'].astype(str).tolist()))[0].tolist()
        j_f['sim'] = j_sims
        jobs_list = j_f.sort_values('sim', ascending=False).head(15).to_dict('records')

        # 2. 부동산 (예산 필터링 적용)
        re_f = df_re[(df_re['보증금(만원)'] <= req.budget) & (df_re['월세(만원)'] <= req.rent_budget)]
        re_list = re_f.head(20).to_dict('records')

        # 3. 정책
        p_f = df_p[df_p.apply(lambda x: is_relevant_policy(x['zipCd'], x['sprvsnInstCdNm'], code), axis=1)].copy()
        p_sims = util.cos_sim(model.encode([req.policy_query]), model.encode(p_f['plcyNm'].tolist()))[0].tolist()
        p_f['sim'] = p_sims
        policies_list = p_f.sort_values('sim', ascending=False).head(15).to_dict('records')

        # 4. AI 리포트
        ai_report = generate_ai_report(name, req.user_interest, req.policy_query, len(j_f[j_f['sim'] >= 0.3]), len(re_f), len(p_f[p_f['sim'] >= 0.3]), [j['recrutPbancTtl'] for j in jobs_list], [p['plcyNm'] for p in policies_list])

        return {
            "summary": {"success": True, "summary": {"total_jobs": len(j_f[j_f['sim'] >= 0.3]), "total_properties": len(re_f), "total_policies": len(p_f[p_f['sim'] >= 0.3]), "region_name": name, "text": ai_report}, "region_info": {"name": name}},
            "jobs": {"success": True, "jobs": jobs_list},
            "realestate": {"success": True, "properties": re_list},
            "policies": {"success": True, "policies": policies_list}
        }
    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8003)