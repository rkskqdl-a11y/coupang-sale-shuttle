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

# [핵심 기능] 테스트용 상품 페이지 생성 (API 실패 시 작동)
def create_fallback_post():
    os.makedirs("posts", exist_ok=True)
    filename = f"posts/{datetime.now().strftime('%Y%m%d')}_test_item.html"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(f"""<!DOCTYPE html><html lang='ko'><head><meta charset='UTF-8'><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>테스트 상품</title></head><body>
        <div style='text-align:center; padding:50px;'>
            <h1>🎉 웹사이트 연결 성공! 🎉</h1>
            <p>이 화면이 보이면 기술적인 문제는 해결된 것입니다.</p>
            <p>현재 쿠팡 API 키를 확인해주세요.</p>
            <a href='../index.html' style='background:blue; color:white; padding:10px; text-decoration:none; border-radius:5px;'>홈으로 돌아가기</a>
        </div></body></html>""")
    return [filename.split('/')[-1]] # 파일명 반환

def main():
    # 1. 무조건 폴더 생성
    os.makedirs("posts", exist_ok=True)
    
    # 2. 상품 수집 시도
    keywords = ["노트북", "생수", "라면", "물티슈", "키보드"]
    target = random.choice(keywords)
    print(f"검색어: {target}")
    
    res = fetch_data(target)
    files = []
    
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
    
    # 3. 파일 목록 다시 읽기 (없으면 테스트 파일 생성)
    files = sorted([f for f in os.listdir("posts") if f.endswith(".html")], reverse=True)
    if not files:
        print("상품 없음 -> 테스트 파일 생성")
        files = create_fallback_post()

    # 4. [가장 중요] index.html 무조건 덮어쓰기
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(f"""<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>핫딜 셔틀 - 접속 성공</title>
    <style>
        body {{ font-family: sans-serif; background: #e9ecef; margin: 0; padding: 20px; text-align: center; }}
        .header {{ background: white; padding: 20px; border-radius: 10px; margin-bottom: 20px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }}
        .item {{ display: block; background: white; padding: 15px; margin: 10px auto; max-width: 600px; border-radius: 8px; text-decoration: none; color: #333; font-weight: bold; border-left: 5px solid #FF4500; }}
        .item:hover {{ transform: scale(1.02); transition: 0.2s; }}
    </style>
</head>
<body>
    <div class="header">
        <h1 style="color:#FF4500;">🚀 핫딜 셔틀 가동 중</h1>
        <p>업데이트 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
    </div>
    <div id="list">
""")
        for file in files[:30]:
            name = file.replace(".html", "").replace("_", " ")
            f.write(f'        <a class="item" href="posts/{file}">🔥 {name} 확인하기</a>\n')
        
        f.write("""    </div>
</body>
</html>""")

    # 5. README.md는 이제 헷갈리지 않게 단순 링크만 제공
    with open("README.md", "w", encoding="utf-8") as f:
        f.write(f"# [클릭] 여기를 눌러 웹사이트로 이동하세요\n\n")
        f.write(f"https://rkskqdl-a11y.github.io/coupang-sale-shuttle/index.html\n\n")
        f.write(f"(업데이트됨: {datetime.now()})")

    # 6. .nojekyll 생성
    with open(".nojekyll", "w") as f: f.write("")

if __name__ == "__main__":
    main()
