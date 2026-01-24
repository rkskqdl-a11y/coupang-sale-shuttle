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
    
    # 1. 상품 데이터 수집
    keywords = ["노트북", "생수", "라면", "물티슈", "키보드", "마우스", "아이패드"]
    target = random.choice(keywords)
    print(f"검색어: {target}")
    
    res = fetch_data(target)
    
    # 2. [변경] 상품 페이지를 .md 파일로 생성 (내용은 HTML)
    if res and 'data' in res and res['data'].get('productData'):
        for item in res['data']['productData']:
            p_id = item['productId']
            # 파일 확장자를 .md로 변경
            filename = f"posts/{datetime.now().strftime('%Y%m%d')}_{target}_{p_id}.md"
            if not os.path.exists(filename):
                with open(filename, "w", encoding="utf-8") as f:
                    f.write(f"""---
layout: default
title: {item['productName']}
---
<div style='max-width:600px; margin:auto; text-align:center; padding:20px; font-family:sans-serif;'>
    <h2 style='color:#333;'>{item['productName']}</h2>
    <img src='{item['productImage']}' style='width:100%; border-radius:10px;'>
    <br><br>
    <a href='{item['productUrl']}' style='background:linear-gradient(135deg, #FF4500, #FF8C00); color:white; padding:15px 30px; text-decoration:none; border-radius:30px; font-weight:bold; display:inline-block; box-shadow:0 4px 10px rgba(0,0,0,0.2);'>👉 최저가 보러가기 (클릭)</a>
    <br><br>
    <p style='color:gray; font-size:0.8em;'>파트너스 활동으로 수수료를 받을 수 있음</p>
</div>
""")

    # 3. [핵심] 메인 페이지를 index.md로 생성 (깃허브가 이걸 홈으로 인식함)
    files = sorted([f for f in os.listdir("posts") if f.endswith(".md")], reverse=True)
    
    with open("index.md", "w", encoding="utf-8") as f:
        f.write("""---
layout: default
title: 핫딜 셔틀
---
<div style='text-align:center; padding:20px; font-family:sans-serif;'>
    <h1 style='color:#FF4500;'>🚀 실시간 핫딜 리스트</h1>
    <p>매일 자동으로 업데이트됩니다.</p>
</div>
<div style='max-width:600px; margin:auto;'>
""")
        # 상품이 없을 경우 안내 메시지
        if not files:
            f.write("<div style='padding:40px; text-align:center; background:#eee; border-radius:10px;'><h3>🚧 상품 준비 중</h3><p>API 키를 확인해주세요.</p></div>")

        for file in files[:40]:
            name = file.replace(".md", "").replace("_", " ")
            # 링크도 .md가 아닌 깃허브 페이지 경로로 자동 변환됨
            f.write(f"""
    <div style='background:white; margin:10px 0; padding:15px; border-radius:10px; box-shadow:0 2px 5px rgba(0,0,0,0.05); border-left:5px solid #FF4500;'>
        <a href='posts/{file.replace('.md', '.html')}' style='text-decoration:none; color:#333; font-weight:bold; display:block;'>
            🔥 {name} <span style='float:right; color:#FF4500;'>확인하기 ></span>
        </a>
    </div>
""")
        f.write("</div>")

    # 4. README.md 업데이트
    with open("README.md", "w", encoding="utf-8") as f:
        f.write(f"# 🛒 쇼핑몰 가동 중\n\n")
        f.write(f"### 👇 아래 링크를 클릭하세요 👇\n\n")
        # 끝에 index.html을 붙이지 않고 루트 주소만 입력
        f.write(f"[🚀 실시간 핫딜 사이트 바로가기 (클릭)](https://rkskqdl-a11y.github.io/coupang-sale-shuttle/)\n\n")
        f.write(f"(시스템 업데이트: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')})")

    # 5. .nojekyll 삭제 (Jekyll 기능을 켜서 .md를 .html로 변환하게 함)
    if os.path.exists(".nojekyll"):
        os.remove(".nojekyll")

if __name__ == "__main__":
    main()
