import os
import hmac
import hashlib
import time
import requests
import json
from datetime import datetime
from urllib.parse import urlencode
import random

# API 키 설정
ACCESS_KEY = os.environ.get('COUPANG_ACCESS_KEY')
SECRET_KEY = os.environ.get('COUPANG_SECRET_KEY')

def get_authorization_header(method, path, query_string):
    datetime_gmt = time.strftime('%y%m%dT%H%M%SZ', time.gmtime())
    message = datetime_gmt + method + path + query_string
    signature = hmac.new(bytes(SECRET_KEY, 'utf-8'), msg=bytes(message, 'utf-8'), digestmod=hashlib.sha256).hexdigest()
    return f"CEA algorithm=HmacSHA256, access-key={ACCESS_KEY}, signed-date={datetime_gmt}, signature={signature}"

def fetch_data(keyword):
    DOMAIN = "https://api-gateway.coupang.com"
    path = "/v2/providers/affiliate_open_api/apis/openapi/v1/products/search"
    params = {"keyword": keyword, "limit": 10}
    query_string = urlencode(params)
    url = f"{DOMAIN}{path}?{query_string}"
    headers = {"Authorization": get_authorization_header("GET", path, query_string), "Content-Type": "application/json"}
    try:
        response = requests.get(url, headers=headers, timeout=15)
        return response.json()
    except: return None

def main():
    os.makedirs("posts", exist_ok=True)
    
    # 1. 상품 수집
    keywords = ["노트북", "생수", "라면", "물티슈", "키보드", "마우스", "아이패드"]
    target = random.choice(keywords)
    res = fetch_data(target)
    
    # 2. 개별 상품 페이지 생성
    if res and 'data' in res and res['data'].get('productData'):
        for item in res['data']['productData']:
            p_id = item['productId']
            filename = f"posts/{datetime.now().strftime('%Y%m%d')}_{target}_{p_id}.html"
            if not os.path.exists(filename):
                with open(filename, "w", encoding="utf-8") as f:
                    f.write(f"""<!DOCTYPE html><html lang='ko'><head><meta charset='UTF-8'><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>{item['productName']}</title></head><body>
                    <div style='max-width:600px; margin:auto; text-align:center; padding:20px;'>
                        <h2>{item['productName']}</h2>
                        <img src='{item['productImage']}' style='width:100%; border-radius:10px;'>
                        <br><br>
                        <a href='{item['productUrl']}' style='background:#FF4500; color:white; padding:15px 30px; text-decoration:none; border-radius:30px; font-weight:bold; display:inline-block;'>👉 최저가 보러가기</a>
                    </div></body></html>""")
    
    # 3. 파일 목록 읽기 (없으면 테스트 파일 생성)
    files = sorted([f for f in os.listdir("posts") if f.endswith(".html")], reverse=True)
    if not files:
        with open(f"posts/test_item.html", "w", encoding="utf-8") as f: f.write("<html><body>Test Item</body></html>")
        files = ["test_item.html"]

    # 4. [핵심] index.html 생성 (이게 유일한 메인 화면)
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(f"""<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>쿠팡 핫딜 셔틀</title>
    <style>
        body {{ font-family: sans-serif; background: #1a1a1a; color: white; text-align: center; padding: 20px; }}
        .header {{ margin-bottom: 30px; border-bottom: 2px solid #FF4500; padding-bottom: 20px; }}
        .card {{ display: block; background: #333; padding: 15px; margin: 10px auto; max-width: 600px; border-radius: 10px; text-decoration: none; color: white; border: 1px solid #444; font-weight: bold; }}
        .card:hover {{ border-color: #FF4500; background: #444; transform: scale(1.02); transition: 0.2s; }}
    </style>
</head>
<body>
    <div class="header">
        <h1 style="color:#FF4500;">🎉 웹사이트 접속 성공! 🎉</h1>
        <p>검은 배경이 보이면 성공입니다.</p>
        <p>최근 업데이트: {datetime.now().strftime('%H:%M:%S')}</p>
    </div>
    <div id="list">
""")
        for file in files[:30]:
            name = file.replace(".html", "").replace("_", " ")
            f.write(f'        <a class="card" href="posts/{file}">🔥 {name} 확인하기</a>\n')
        f.write("</div></body></html>")

    # 5. .nojekyll 생성
    with open(".nojekyll", "w") as f: f.write("")

if __name__ == "__main__":
    main()
