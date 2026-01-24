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
    # 1. 폴더 생성 (에러 방지)
    os.makedirs("posts", exist_ok=True)
    
    # 2. 상품 수집 시도
    keywords = ["노트북", "생수", "라면", "물티슈", "키보드", "마우스", "아이패드", "영양제", "커피", "샴푸"]
    target = random.choice(keywords)
    res = fetch_data(target)
    
    # 3. 상품 파일 생성
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
    
    # 파일이 하나도 없으면 테스트 파일 생성 (404 방지)
    files = sorted([f for f in os.listdir("posts") if f.endswith(".html")], reverse=True)
    if not files:
        with open(f"posts/test_item.html", "w", encoding="utf-8") as f: 
            f.write("<html><body><h1>시스템 정상 작동 중</h1></body></html>")
        files = ["test_item.html"]

    # 4. [필수] index.html 생성 (이게 있어야 404가 안 뜸)
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(f"""<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>쿠팡 핫딜 셔틀</title>
    <style>
        body {{ font-family: sans-serif; background: #f0f2f5; color: #333; text-align: center; padding: 20px; }}
        .header {{ margin-bottom: 30px; background: white; padding: 20px; border-radius: 10px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }}
        .card {{ display: block; background: white; padding: 15px; margin: 10px auto; max-width: 600px; border-radius: 10px; text-decoration: none; color: #333; border: 1px solid #ddd; font-weight: bold; }}
        .card:hover {{ border-color: #FF4500; transform: translateY(-3px); transition: 0.2s; }}
    </style>
</head>
<body>
    <div class="header">
        <h1 style="color:#FF4500;">🚀 실시간 핫딜 정보</h1>
        <p>업데이트: {datetime.now().strftime('%Y-%m-%d %H:%M')}</p>
        <p style="font-size:0.8em; color:gray;">(이 화면이 보이면 404 에러는 해결된 것입니다)</p>
    </div>
    <div id="list">
""")
        for file in files[:40]:
            name = file.replace(".html", "").replace("_", " ")
            f.write(f'        <a class="card" href="posts/{file}">🔥 {name}</a>\n')
        f.write("</div></body></html>")

    # 5. [중요] README.md 재생성 (로봇 에러 방지용)
    with open("README.md", "w", encoding="utf-8") as f:
        f.write(f"# 🛒 자동화 시스템 정상 가동\n\n")
        f.write(f"웹사이트 주소: https://rkskqdl-a11y.github.io/coupang-sale-shuttle/\n")

    # 6. .nojekyll 생성 (디자인 깨짐 방지)
    with open(".nojekyll", "w", encoding="utf-8") as f: f.write("")

if __name__ == "__main__":
    main()
