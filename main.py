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

# 조합 박스
modifiers = ["가성비", "학생용", "자취생", "사무용", "선물용", "특가", "인기", "추천", "세일", "베스트", "국민", "필수"]
brands = ["삼성", "LG", "애플", "샤오미", "나이키", "아디다스", "뉴발란스", "폴로", "타미힐피거", "지오다노", "햇반", "비비고", "다이슨", "테팔", "필립스", "파타고니아", "노스페이스", "에잇세컨즈"]
products = ["노트북", "모니터", "마우스", "키보드", "반팔티", "후드티", "슬랙스", "러닝화", "백팩", "생수", "라면", "에어프라이어", "캠핑의자", "텐트", "배변패드", "물티슈", "청소기"]
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
    params = {"keyword": keyword, "limit": 10}
    query_string = urlencode(params)
    url = f"{DOMAIN}{path}?{query_string}"
    headers = {"Authorization": get_authorization_header("GET", path, query_string), "Content-Type": "application/json"}
    try:
        response = requests.get(url, headers=headers, timeout=15)
        return response.json()
    except: return None

def save_products():
    os.makedirs("posts", exist_ok=True)
    target = get_random_keyword()
    res = fetch_data(target)
    
    if not res or 'data' not in res or not res['data'].get('productData'):
        return

    clean_target = target.replace(" ", "_")

    for item in res['data']['productData']:
        p_id = item['productId']
        # .html로 생성하여 웹 브라우저가 즉시 렌더링하도록 함
        filename = f"posts/{datetime.now().strftime('%Y%m%d')}_{clean_target}_{p_id}.html"
        if os.path.exists(filename): continue 

        with open(filename, "w", encoding="utf-8") as f:
            f.write(f"""<!DOCTYPE html><html lang='ko'><head><meta charset='UTF-8'>
            <meta name='viewport' content='width=device-width, initial-scale=1.0'>
            <title>{item['productName']}</title>
            <style>
                body {{ font-family: sans-serif; background: #f0f2f5; margin: 0; padding: 20px; color: #333; }}
                .container {{ max-width: 600px; margin: auto; background: white; padding: 20px; border-radius: 15px; box-shadow: 0 4px 12px rgba(0,0,0,0.1); text-align: center; }}
                img {{ width: 100%; border-radius: 10px; margin-bottom: 20px; }}
                .price {{ color: #ff4500; font-size: 1.5em; font-weight: bold; }}
                .btn {{ background: linear-gradient(135deg, #FF4500, #FF8C00); color: white; padding: 15px 30px; text-decoration: none; border-radius: 50px; display: inline-block; font-weight: bold; margin-top: 20px; font-size: 1.2em; }}
                .btn:hover {{ opacity: 0.9; }}
            </style></head><body>
            <div class='container'>
                <h2>{item['productName']}</h2>
                <img src='{item['productImage']}'>
                <a href='{item['productUrl']}' class='btn'>👉 초특가 혜택 확인하기 🛒</a>
                <p class='price'>{format(item['productPrice'], ',')}원</p>
                <p>🚀 로켓배송 / 무료배송 지원</p>
                <hr style='border:0; height:1px; background:#eee;'>
                <p style='color:gray; font-size:0.8em;'>본 포스팅은 파트너스 활동의 일환으로 수수료를 제공받을 수 있습니다.</p>
            </div></body></html>""")

    update_index()
    update_sitemap()

def update_index():
    if not os.path.exists("posts"): return
    files = sorted([f for f in os.listdir("posts") if f.endswith(".html")], reverse=True)
    
    # 웹 브라우저가 가장 먼저 읽는 정문 index.html
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(f"""<!DOCTYPE html><html lang="ko"><head><meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>24시 실시간 핫딜 정보 센터</title>
        <style>
            body {{ font-family: sans-serif; background: #f9f9f9; text-align: center; padding: 20px; }}
            .card {{ display: block; background: white; padding: 20px; margin: 10px auto; max-width: 600px; border-radius: 15px; text-decoration: none; color: #333; box-shadow: 0 2px 10px rgba(0,0,0,0.05); font-weight: bold; transition: 0.3s; }}
            .card:hover {{ border: 2px solid #FF4500; background: #fffaf9; transform: translateY(-3px); }}
            h1 {{ color: #FF4500; }}
            .date {{ font-size: 0.8em; color: #999; }}
        </style></head><body>
        <h1>🏆 실시간 초특가 핫딜 리스트</h1>
        <p>매일 40개씩 자동으로 엄선되는 상품 정보입니다.</p>
        <div id="list">""")
        for file in files[:50]:
            # 파일명에서 날짜와 키워드만 추출하여 예쁘게 출력
            parts = file.replace('.html','').split('_')
            display_name = " ".join(parts[1:-1]) if len(parts) > 2 else file
            date_str = parts[0]
            f.write(f'<a class="card" href="posts/{file}"><span class="date">[{date_str}]</span><br>🔥 {display_name} 상세정보 확인</a>')
        f.write("</div></body></html>")

    # README.md는 깃허브 관리용으로만 남김
    with open("README.md", "w", encoding="utf-8") as f:
        f.write("# 🛒 쿠팡 파트너스 자동화 공장 가동 중\n\n[웹사이트 접속하기](https://rkskqdl-a11y.github.io/coupang-sale-shuttle/)")

def update_sitemap():
    base_url = "https://rkskqdl-a11y.github.io/coupang-sale-shuttle/"
    files = [f for f in os.listdir("posts") if f.endswith(".html")]
    with open("sitemap.xml", "w", encoding="utf-8") as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n')
        f.write(f'  <url><loc>{base_url}</loc></url>\n')
        for file in files:
            f.write(f'  <url><loc>{base_url}posts/{file}</loc></url>\n')
        f.write('</urlset>')

if __name__ == "__main__":
    save_products()
