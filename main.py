import os
import hmac
import hashlib
import time
import requests
import json
from datetime import datetime
from urllib.parse import urlencode
import random

# 1. API 키 설정 (검증 완료됨)
ACCESS_KEY = os.environ.get('COUPANG_ACCESS_KEY')
SECRET_KEY = os.environ.get('COUPANG_SECRET_KEY')

# 2. 검색 키워드 설정 (수익률 좋은 키워드들)
modifiers = ["가성비", "학생용", "자취생", "사무용", "선물용", "특가", "인기", "추천", "세일", "베스트", "국민", "필수"]
brands = ["삼성", "LG", "애플", "샤오미", "나이키", "아디다스", "뉴발란스", "폴로", "타미힐피거", "지오다노", "햇반", "비비고", "다이슨", "테팔", "필립스", "파타고니아", "노스페이스", "에잇세컨즈"]
products = ["노트북", "모니터", "마우스", "키보드", "반팔티", "후드티", "슬랙스", "러닝화", "백팩", "생수", "라면", "에어프라이어", "캠핑의자", "텐트", "배변패드", "물티슈", "청소기", "영양제", "오메가3", "유산균"]
specs = ["대용량", "무라벨", "고속충전", "경량", "오버핏", "무소음", "접이식", "미니", "휴대용", "화이트", "블랙"]

def get_random_keyword():
    return f"{random.choice(modifiers)} {random.choice(brands)} {random.choice(products)} {random.choice(specs)}"

def get_authorization_header(method, path, query_string):
    datetime_gmt = time.strftime('%y%m%dT%H%M%SZ', time.gmtime())
    message = datetime_gmt + method + path + query_string
    signature = hmac.new(bytes(SECRET_KEY, 'utf-8'), msg=bytes(message, 'utf-8'), digestmod=hashlib.sha256).hexdigest()
    return f"CEA algorithm=HmacSHA256, access-key={ACCESS_KEY}, signed-date={datetime_gmt}, signature={signature}"

def fetch_data(keyword):
    DOMAIN = "https://api-gateway.coupang.com"
    path = "/v2/providers/affiliate_open_api/apis/openapi/v1/products/search"
    params = {"keyword": keyword, "limit": 20}
    query_string = urlencode(params)
    url = f"{DOMAIN}{path}?{query_string}"
    headers = {"Authorization": get_authorization_header("GET", path, query_string), "Content-Type": "application/json"}
    try:
        response = requests.get(url, headers=headers, timeout=15)
        return response.json()
    except Exception as e:
        print(f"Error fetching data: {e}")
        return None

def main():
    os.makedirs("posts", exist_ok=True)
    
    # 3. 상품 데이터 수집
    target = get_random_keyword()
    print(f"오늘의 검색어: {target}")
    res = fetch_data(target)
    
    # 4. 개별 상품 상세 페이지 생성
    if res and 'data' in res and res['data'].get('productData'):
        clean_target = target.replace(" ", "_")
        for item in res['data']['productData']:
            p_id = item['productId']
            filename = f"posts/{datetime.now().strftime('%Y%m%d')}_{clean_target}_{p_id}.html"
            
            if os.path.exists(filename): continue 

            with open(filename, "w", encoding="utf-8") as f:
                f.write(f"""<!DOCTYPE html><html lang='ko'><head><meta charset='UTF-8'><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>{item['productName']}</title>
                <style>
                    body {{ font-family: 'Apple SD Gothic Neo', sans-serif; background: #f5f6f8; margin: 0; padding: 20px; text-align: center; }}
                    .container {{ max-width: 600px; margin: auto; background: white; padding: 30px; border-radius: 20px; box-shadow: 0 4px 20px rgba(0,0,0,0.05); }}
                    h2 {{ color: #333; line-height: 1.4; font-size: 1.2rem; margin-bottom: 20px; }}
                    img {{ width: 100%; border-radius: 15px; margin-bottom: 20px; }}
                    .price {{ font-size: 1.5rem; color: #e44d26; font-weight: bold; margin-bottom: 20px; }}
                    .btn {{ background: linear-gradient(135deg, #e44d26, #f16529); color: white; padding: 18px 40px; text-decoration: none; border-radius: 50px; display: inline-block; font-weight: bold; font-size: 1.1rem; box-shadow: 0 4px 15px rgba(228, 77, 38, 0.3); transition: 0.3s; }}
                    .btn:hover {{ transform: scale(1.05); }}
                    .disclaimer {{ color: #888; font-size: 0.8rem; margin-top: 30px; line-height: 1.5; }}
                </style></head><body>
                <div class='container'>
                    <h2>{item['productName']}</h2>
                    <img src='{item['productImage']}'>
                    <div class='price'>{format(item['productPrice'], ',')}원</div>
                    <a href='{item['productUrl']}' class='btn'>👉 쿠팡 최저가 보기</a>
                    <div class='disclaimer'>
                        <p>이 포스팅은 쿠팡 파트너스 활동의 일환으로,<br>이에 따른 일정액의 수수료를 제공받습니다.</p>
                    </div>
                </div></body></html>""")
    
    # 5. [핵심] 메인 쇼핑몰 화면 (index.html) 업데이트
    files = sorted([f for f in os.listdir("posts") if f.endswith(".html")], reverse=True)
    
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(f"""<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>초특가 핫딜 셔틀</title>
    <style>
        body {{ font-family: 'Apple SD Gothic Neo', sans-serif; background: #f0f2f5; margin: 0; padding: 20px; text-align: center; }}
        .header {{ background: white; padding: 40px 20px; border-radius: 20px; margin-bottom: 30px; box-shadow: 0 4px 15px rgba(0,0,0,0.05); }}
        h1 {{ color: #e44d26; margin: 0 0 10px 0; font-size: 2rem; }}
        .desc {{ color: #666; font-size: 0.9rem; }}
        .grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 20px; max-width: 1000px; margin: auto; }}
        .card {{ background: white; padding: 20px; border-radius: 15px; border: 1px solid #eee; display: flex; flex-direction: column; justify-content: space-between; text-decoration: none; color: #333; transition: 0.3s; height: 100%; min-height: 180px; }}
        .card:hover {{ border-color: #e44d26; transform: translateY(-5px); box-shadow: 0 5px 15px rgba(0,0,0,0
