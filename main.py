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
    # [핵심 1] 방해꾼 README.md가 있으면 무조건 삭제
    if os.path.exists("README.md"):
        os.remove("README.md")
        print("기존 README.md 삭제 완료 (웹사이트 강제 노출을 위해)")

    os.makedirs("posts", exist_ok=True)
    
    # 1. 상품 수집 (가짜 데이터라도 만듦)
    keywords = ["노트북", "생수", "라면", "물티슈", "키보드"]
    target = random.choice(keywords)
    res = fetch_data(target)
    
    files = []
    # 데이터가 있으면 HTML 생성
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
    else:
        # API 안되면 테스트 파일 생성
        test_file = f"posts/{datetime.now().strftime('%Y%m%d')}_test.html"
        with open(test_file, "w", encoding="utf-8") as f:
            f.write("<html><body><h1>테스트 상품입니다</h1></body></html>")

    files = sorted([f for f in os.listdir("posts") if f.endswith(".html")], reverse=True)

    # [핵심 2] index.html 생성 (이게 유일한 대문이 됨)
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(f"""<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>쿠팡 핫딜 셔틀</title>
    <style>
        body {{ font-family: sans-serif; background: #222; color: white; text-align: center; padding: 20px; }}
        .card {{ display: block; background: #333; padding: 15px; margin: 10px auto; max-width: 600px; border-radius: 10px; text-decoration: none; color: white; border: 1px solid #444; }}
        .card:hover {{ border-color: #FF4500; background: #444; }}
    </style>
</head>
<body>
    <h1 style="color:#FF4500;">🎉 드디어 성공했습니다! 🎉</h1>
    <p>배경이 검은색으로 보이면 진짜 웹사이트입니다.</p>
    <p>업데이트: {datetime.now().strftime('%H:%M:%S')}</p>
    <hr style="border-color:#555;">
    <div id="list">
""")
        for file in files[:30]:
            name = file.replace(".html", "").replace("_", " ")
            f.write(f'        <a class="card" href="posts/{file}">🔥 {name}</a>\n')
        f.write("</div></body></html>")

    # [핵심 3] .nojekyll 생성 (필수)
    with open(".nojekyll", "w") as f: f.write("")

if __name__ == "__main__":
    main()
