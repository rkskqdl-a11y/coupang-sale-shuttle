import os
import hmac
import hashlib
import time
import requests
import json
from datetime import datetime
from urllib.parse import urlencode
import random

# 1. API 키 설정
ACCESS_KEY = os.environ.get('COUPANG_ACCESS_KEY')
SECRET_KEY = os.environ.get('COUPANG_SECRET_KEY')

# 2. 검색 키워드
modifiers = ["가성비", "학생용", "자취생", "사무용", "특가", "인기", "추천", "세일", "베스트"]
brands = ["삼성", "LG", "애플", "샤오미", "나이키", "아디다스", "뉴발란스", "테팔", "필립스", "노스페이스"]
products = ["노트북", "모니터", "마우스", "키보드", "후드티", "러닝화", "생수", "라면", "물티슈", "청소기", "영양제"]
specs = ["고속충전", "경량", "오버핏", "무소음", "대용량"]

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
    except: return None

def main():
    os.makedirs("posts", exist_ok=True)
    
    # 3. 상품 데이터 수집
    target = get_random_keyword()
    print(f"검색어: {target}")
    res = fetch_data(target)
    
    # 4. 상품 HTML 생성
    if res and 'data' in res and res['data'].get('productData'):
        clean_target = target.replace(" ", "_")
        for item in res['data']['productData']:
            p_id = item['productId']
            filename = f"posts/{datetime.now().strftime('%Y%m%d')}_{clean_target}_{p_id}.html"
            if os.path.exists(filename): continue 
            
            with open(filename, "w", encoding="utf-8") as f:
                f.write(f"""<!DOCTYPE html><html><head><meta charset='UTF-8'><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>{item['productName']}</title>
                <style>
                    body {{ font-family: sans-serif; background: #f5f6f8; padding: 20px; text-align: center; }}
                    .container {{ max-width: 600px; margin: auto; background: white; padding: 20px; border-radius: 15px; }}
                    img {{ width: 100%; border-radius: 10px; }}
                    .btn {{ background: #e44d26; color: white; padding: 15px 30px; text-decoration: none; border-radius: 30px; display: inline-block; margin-top: 20px; font-weight: bold; }}
                </style></head><body>
                <div class='container'>
                    <h2>{item['productName']}</h2>
                    <img src='{item['productImage']}'>
                    <h3 style='color:#e44d26;'>{format(item['productPrice'], ',')}원</h3>
                    <a href='{item['productUrl']}' class='btn'>👉 쿠팡 최저가 보기</a>
                    <p style='font-size:0.8rem; color:#888; margin-top:20px;'>수수료를 제공받을 수 있음</p>
                </div></body></html>""")

    # 5. 메인 페이지(index.html) 덮어쓰기
    # 방금 수동으로 만든 '대기 중' 화면을 '진짜 상품 리스트'로 교체합니다.
    files = sorted([f for f in os.listdir("posts") if f.endswith(".html")], reverse=True)
    
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(f"""<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>초특가 핫딜</title>
    <style>
        body {{ font-family: sans-serif; background: #f0f2f5; margin: 0; padding: 20px; }}
        .header {{ text-align: center; background: white; padding: 30px; border-radius: 20px; margin-bottom: 20px; }}
        h1 {{ color: #e44d26; margin: 0; }}
        .grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 15px; max-width: 1000px; margin: auto; }}
        .card {{ background: white; padding: 15px; border-radius: 15px; text-decoration: none; color: #333; display: flex; flex-direction: column; justify-content: center; height: 120px; border: 1px solid #eee; }}
        .card:hover {{ border-color: #e44d26; transform: translateY(-2px); }} 
        .title {{ font-weight: bold; font-size: 0.95rem; margin-bottom: 5px; }}
        .badge {{ color: #e44d26; font-size: 0.8rem; font-weight: bold; text-align: right; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🚀 실시간 핫딜 쇼핑몰</h1>
        <p>업데이트: {datetime.now().strftime('%Y-%m-%d %H:%M')}</p>
    </div>
    <div class="grid">
""")
        if files:
            for file in files[:60]:
                parts = file.replace(".html", "").split("_")
                display_name = " ".join(parts[1:-1]) if len(parts) > 2 else "추천 상품"
                f.write(f"""
        <a class="card" href="posts/{file}">
            <div class="title">🔥 {display_name}</div>
            <div class="badge">가격 확인 ></div>
        </a>""")
        else:
            # 혹시라도 상품이 아직 없으면 기존 대기 화면과 비슷한 안내 유지
            f.write("<div class='card'><h3>상품 수집 중...</h3><p>잠시 후 다시 접속해주세요.</p></div>")
            
        f.write("    </div></body></html>")

    # 6. 마무리
    with open("README.md", "w", encoding="utf-8") as f:
        f.write("# 🛒 쇼핑몰 가동 중\n\n[웹사이트 바로가기](https://rkskqdl-a11y.github.io/coupang-sale-shuttle/)")
    with open(".nojekyll", "w", encoding="utf-8") as f: f.write("")

if __name__ == "__main__":
    main()
