import os
import hmac
import hashlib
import time
import requests
import json
from datetime import datetime
from urllib.parse import urlencode
import random

# 1. 설정
ACCESS_KEY = os.environ.get('COUPANG_ACCESS_KEY')
SECRET_KEY = os.environ.get('COUPANG_SECRET_KEY')

def get_authorization_header(method, path, query_string):
    datetime_gmt = time.strftime('%y%m%dT%H%M%SZ', time.gmtime())
    message = datetime_gmt + method + path + query_string
    signature = hmac.new(bytes(SECRET_KEY, 'utf-8'), msg=bytes(message, 'utf-8'), digestmod=hashlib.sha256).hexdigest()
    return f"CEA algorithm=HmacSHA256, access-key={ACCESS_KEY}, signed-date={datetime_gmt}, signature={signature}"

def fetch_data(keyword):
    try:
        DOMAIN = "https://api-gateway.coupang.com"
        path = "/v2/providers/affiliate_open_api/apis/openapi/v1/products/search"
        params = {"keyword": keyword, "limit": 20}
        query_string = urlencode(params)
        url = f"{DOMAIN}{path}?{query_string}"
        headers = {"Authorization": get_authorization_header("GET", path, query_string), "Content-Type": "application/json"}
        response = requests.get(url, headers=headers, timeout=15)
        return response.json()
    except:
        return None

def main():
    print("🚀 로봇 가동 시작")
    os.makedirs("posts", exist_ok=True)

    # 2. 상품 데이터 수집 시도
    keywords = ["라면", "생수", "노트북", "물티슈", "키보드", "휴지", "햇반"]
    target = random.choice(keywords)
    print(f"검색어: {target}")
    
    res = fetch_data(target)
    
    # 3. 상품 파일 생성
    if res and 'data' in res and res['data'].get('productData'):
        for item in res['data']['productData']:
            try:
                p_id = item['productId']
                filename = f"posts/{datetime.now().strftime('%Y%m%d')}_{target}_{p_id}.html"
                if os.path.exists(filename): continue
                
                with open(filename, "w", encoding="utf-8") as f:
                    f.write(f"""<!DOCTYPE html><html><head><meta charset='UTF-8'><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>{item['productName']}</title></head><body>
                    <div style='text-align:center; padding:20px;'>
                        <h2>{item['productName']}</h2>
                        <img src='{item['productImage']}' style='width:100%; max-width:400px; border-radius:10px;'>
                        <h3 style='color:#e44d26;'>{format(item['productPrice'], ',')}원</h3>
                        <a href='{item['productUrl']}' style='background:#e44d26; color:white; padding:15px; text-decoration:none; border-radius:10px;'>👉 쿠팡 최저가 보기</a>
                    </div></body></html>""")
            except: continue

    # 4. [핵심] index.html 무조건 생성 (에러 방지 처리 완료)
    files = sorted([f for f in os.listdir("posts") if f.endswith(".html")], reverse=True)
    
    html_content = f"""<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>초특가 핫딜</title>
    <style>
        body {{ font-family: sans-serif; background: #f0f2f5; margin: 0; padding: 20px; text-align: center; }}
        .header {{ background: white; padding: 30px; border-radius: 20px; margin-bottom: 20px; }}
        h1 {{ color: #e44d26; }}
        .grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(150px, 1fr)); gap: 15px; max-width: 800px; margin: auto; }}
        .card {{ background: white; padding: 15px; border-radius: 15px; text-decoration: none; color: #333; display: block; border: 1px solid #eee; }}
        .card:hover {{ border-color: #e44d26; transform: translateY(-3px); }}
        .title {{ font-size: 0.9rem; margin-bottom: 10px; overflow: hidden; white-space: nowrap; text-overflow: ellipsis; }}
        .badge {{ color: #e44d26; font-size: 0.8rem; font-weight: bold; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🚀 실시간 핫딜 쇼핑몰</h1>
        <p>업데이트: {datetime.now().strftime('%Y-%m-%d %H:%M')}</p>
    </div>
    <div class="grid">
"""
    
    if files:
        for file in files[:50]:
            parts = file.replace(".html", "").split("_")
            name = parts[1] if len(parts) > 1 else "특가 상품"
            html_content += f"""
        <a class="card" href="posts/{file}">
            <div class="title">🔥 {name}</div>
            <div class="badge">최저가 보기 ></div>
        </a>"""
    else:
        html_content += """<div class="card" style="grid-column: 1/-1;"><h3>상품 준비 중...</h3><p>잠시 후 다시 접속해주세요.</p></div>"""

    html_content += """    </div></body></html>"""

    # 파일 쓰기
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(html_content)

    # 5. 마무리
    with open("README.md", "w", encoding="utf-8") as f:
        f.write("# 🛒 쇼핑몰 가동 중\n\n[웹사이트 바로가기](https://rkskqdl-a11y.github.io/coupang-sale-shuttle/)")
    with open(".nojekyll", "w", encoding="utf-8") as f: f.write("")
    
    print("✅ index.html 생성 완료")

if __name__ == "__main__":
    main()
