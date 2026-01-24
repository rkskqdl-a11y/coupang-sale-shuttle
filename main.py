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

# [롱테일 무한 조합 박스]
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

    for item in res['data']['productData']:
        p_id = item['productId']
        filename = f"posts/{datetime.now().strftime('%Y%m%d')}_{p_id}.md"
        if os.path.exists(filename): continue 

        with open(filename, "w", encoding="utf-8") as f:
            f.write(f"<div align='center'>\n\n")
            f.write(f"# 🏷️ {item['productName']}\n\n")
            f.write(f"![상품이미지]({item['productImage']})\n\n")
            
            f.write(f"### ⚡ 한정수량 및 실시간 가격 확인\n")
            f.write(f"<a href='{item['productUrl']}' style='background: linear-gradient(135deg, #FF4500 0%, #FF8C00 100%); color: white; padding: 18px 35px; text-decoration: none; border-radius: 50px; font-weight: bold; font-size: 1.3em; display: inline-block; box-shadow: 0 4px 15px rgba(255, 69, 0, 0.4); transition: all 0.3s ease;'>👉 초특가 구매 기회 확인하기 🛒</a>\n\n")
            f.write(f"<br><br>\n\n")
            
            f.write(f"## 📋 제품 상세 정보\n")
            f.write(f"| 구분 | 상세 내용 |\n| :--- | :--- |\n")
            f.write(f"| **현재 가격** | <b style='color:#FF4500; font-size:1.25em;'>{format(item['productPrice'], ',')}원</b> |\n")
            f.write(f"| **배송 서비스** | 🚀 쿠팡 로켓배송 / 무료배송 지원 |\n")
            f.write(f"| **추천 키워드** | #{target.replace(' ', ' #')} |\n\n")
            
            f.write(f"</div>\n\n---\n<p align='center' style='font-size: 0.85em; color: #888;'>이 포스팅은 파트너스 활동의 일환으로 소정의 수수료를 제공받을 수 있습니다.</p>")

    update_index()
    update_sitemap() # 구글용 지도 생성 추가

def update_index():
    if not os.path.exists("posts"): return
    files = sorted([f for f in os.listdir("posts") if f.endswith(".md")], reverse=True)
    
    # 1. README.md 업데이트
    with open("README.md", "w", encoding="utf-8") as f:
        f.write(f"<div align='center'>\n\n# 🛒 24시 실시간 핫딜 정보 센터 🏆\n\n## 📅 최신 업데이트 상품 리스트\n")
        for file in files[:50]:
            f.write(f"#### [{file.replace('.md','')}](posts/{file})\n")
        f.write(f"</div>")

    # 2. 웹 매장 정문 index.html 생성 (404 에러 해결용)
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(f"""
        <!DOCTYPE html>
        <html lang="ko">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>실시간 가성비 핫딜 쇼핑몰</title>
            <style>
                body {{ font-family: 'Apple SD Gothic Neo', 'Malgun Gothic', sans-serif; text-align: center; padding: 20px; line-height: 1.6; background-color: #f9f9f9; }}
                .container {{ max-width: 800px; margin: auto; background: white; padding: 30px; border-radius: 20px; box-shadow: 0 4px 20px rgba(0,0,0,0.05); }}
                .product-link {{ display: block; padding: 20px; margin: 15px 0; border: 1px solid #eee; border-radius: 15px; text-decoration: none; color: #333; font-weight: bold; transition: 0.3s; background: #fff; }}
                .product-link:hover {{ transform: translateY(-3px); border-color: #FF4500; box-shadow: 0 5px 15px rgba(255,69,0,0.1); }}
                h1 {{ color: #FF4500; font-size: 2em; }}
                p {{ color: #666; }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🏆 실시간 초특가 핫딜 리스트</h1>
                <p>매일 40개씩 업데이트되는 최저가 상품 정보입니다.</p>
                <hr style="border: 0; height: 1px; background: #eee; margin: 20px 0;">
        """)
        for file in files[:50]:
            display_name = file.replace('.md','').replace('_', ' ')
            # 링크 주소에서 .md를 제거하여 Pages 경로에 맞춤
            f.write(f'        <a class="product-link" href="posts/{file.replace(".md","")}">🔥 {display_name} 상세 보기</a>\n')
        
        f.write("""
            </div>
        </body>
        </html>
        """)

def update_sitemap():
    # 실제 주소에 맞춰 베이스 URL 설정
    base_url = "https://rkskqdl-a11y.github.io/coupang-sale-shuttle/"
    if not os.path.exists("posts"): return
    files = [f for f in os.listdir("posts") if f.endswith(".md")]
    
    with open("sitemap.xml", "w", encoding="utf-8") as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        f.write('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n')
        f.write(f'  <url><loc>{base_url}</loc><priority>1.0</priority></url>\n')
        for file in files:
            page_name = file.replace(".md", "")
            f.write(f'  <url><loc>{base_url}posts/{page_name}</loc><priority>0.8</priority></url>\n')
        f.write('</urlset>')

if __name__ == "__main__":
    save_products()
