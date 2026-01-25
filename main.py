import os
import hmac
import hashlib
import time
import requests
import json
from datetime import datetime
from urllib.parse import urlencode
import random
import traceback

# 1. API 키 설정
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
    except Exception as e:
        print(f"API Error: {e}")
        return None

def main():
    print("🚀 불도저 로봇 가동 시작")
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    try:
        os.makedirs("posts", exist_ok=True)

        # 2. 상품 데이터 수집
        keywords = ["라면", "생수", "노트북", "휴지", "물티슈", "키보드", "마우스", "영양제"]
        target = random.choice(keywords)
        print(f"검색어: {target}")
        
        res = fetch_data(target)
        
        # 3. 상품 파일 생성 (실패해도 무시하고 계속 진행)
        if res and 'data' in res and res['data'].get('productData'):
            for item in res['data']['productData']:
                try:
                    p_id = item['productId']
                    filename = f"posts/{datetime.now().strftime('%Y%m%d')}_{target}_{p_id}.html"
                    if os.path.exists(filename): continue
                    
                    with open(filename, "w", encoding="utf-8") as f:
                        f.write(f"""<!DOCTYPE html><html><head><meta charset='UTF-8'><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>{item['productName']}</title></head><body>
                        <div style='text-align:center; padding:20px; font-family:sans-serif;'>
                            <img src='{item['productImage']}' style='width:100%; max-width:400px; border-radius:10px;'>
                            <h2>{item['productName']}</h2>
                            <h3 style='color:#e44d26;'>{format(item['productPrice'], ',')}원</h3>
                            <a href='{item['productUrl']}' style='background:#e44d26; color:white; padding:15px 30px; text-decoration:none; border-radius:30px; font-weight:bold; display:inline-block;'>👉 최저가 보기</a>
                        </div></body></html>""")
                except: continue

        # 4. [핵심] index.html 강제 덮어쓰기
        # 파일이 있든 없든, 에러가 났든 말든 무조건 씁니다.
        files = sorted([f for f in os.listdir("posts") if f.endswith(".html")], reverse=True)
        
        html_content = f"""<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>핫딜 셔틀 (업데이트됨)</title>
    <style>
        body {{ font-family: 'Apple SD Gothic Neo', sans-serif; background: #f0f2f5; margin: 0; padding: 20px; text-align: center; }}
        .header {{ background: white; padding: 30px; border-radius: 20px; margin-bottom: 20px; box-shadow: 0 4px 10px rgba(0,0,0,0.05); }}
        h1 {{ color: #e44d26; margin: 0; }}
        .grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 15px; max-width: 1000px; margin: auto; }}
        .card {{ background: white; padding: 20px; border-radius: 15px; text-decoration: none; color: #333; display: flex; flex-direction: column; justify-content: center; min-height: 120px; border: 1px solid #eee; }}
        .card:hover {{ border-color: #e44d26; transform: translateY(-3px); }}
        .status {{ color: #e44d26; font-weight: bold; font-size: 0.9rem; margin-top: 10px; }}
        .debug {{ color: gray; font-size: 0.8rem; margin-top: 20px; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🚀 실시간 핫딜 쇼핑몰</h1>
        <p>최근 업데이트: {current_time}</p>
        <p class="debug">검색어: {target}</p>
    </div>
    <div class="grid">
"""
        # 상품 리스트 추가
        if files:
            for file in files[:60]:
                parts = file.replace(".html", "").split("_")
                display_name = parts[1] if len(parts) > 1 else "추천 상품"
                html_content += f"""
        <a class="card" href="posts/{file}">
            <h3>🔥 {display_name}</h3>
            <div class="status">가격 확인하기 ></div>
        </a>"""
        else:
            # 상품이 없어도 이 화면이 떠야 함
            html_content += f"""
            <div class="card">
                <h3>🚧 상품 가져오는 중...</h3>
                <p>로봇이 열심히 일하고 있습니다.</p>
                <div class="status">잠시 후 새로고침 해주세요</div>
            </div>"""

        html_content += """    </div></body></html>"""

        # 파일 쓰기 실행
        with open("index.html", "w", encoding="utf-8") as f:
            f.write(html_content)
        
        print("✅ index.html 업데이트 성공")

    except Exception as e:
        # 🚨 치명적인 에러 발생 시에도 화면에 에러를 띄움
        print(f"❌ 치명적 오류: {e}")
        error_msg = traceback.format_exc()
        with open("index.html", "w", encoding="utf-8") as f:
             f.write(f"<h1>⚠️ 로봇 오류 발생</h1><pre>{error_msg}</pre>")

    # 5. 마무리 (README도 복구)
    with open("README.md", "w", encoding="utf-8") as f:
        f.write("# 🛒 쇼핑몰 가동 중\n\n[웹사이트 바로가기](https://rkskqdl-a11y.github.io/coupang-sale-shuttle/)")
    with open(".nojekyll", "w", encoding="utf-8") as f: f.write("")

if __name__ == "__main__":
    main()
