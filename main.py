import os
import hmac
import hashlib
import time
import requests
import json
from datetime import datetime
from urllib.parse import urlencode
import random
import re
import google.generativeai as genai

# 1. 기본 설정 (반드시 본인의 정보로 수정)
ACCESS_KEY = os.environ.get('COUPANG_ACCESS_KEY')
SECRET_KEY = os.environ.get('COUPANG_SECRET_KEY')
GEMINI_KEY = os.environ.get('GEMINI_API_KEY')
# [중요] 본인의 GitHub Pages 실제 주소로 넣으세요 (끝에 / 빼기)
SITE_URL = "https://rkskqdl-a11y.github.io/coupang-sale-shuttle"

if GEMINI_KEY:
    genai.configure(api_key=GEMINI_KEY)

def get_authorization_header(method, path, query_string):
    datetime_gmt = time.strftime('%y%m%dT%H%M%SZ', time.gmtime())
    message = datetime_gmt + method + path + query_string
    signature = hmac.new(bytes(SECRET_KEY, 'utf-8'), msg=bytes(message, 'utf-8'), digestmod=hashlib.sha256).hexdigest()
    return f"CEA algorithm=HmacSHA256, access-key={ACCESS_KEY}, signed-date={datetime_gmt}, signature={signature}"

def fetch_data(keyword):
    try:
        DOMAIN = "https://api-gateway.coupang.com"
        path = "/v2/providers/affiliate_open_api/apis/openapi/v1/products/search"
        params = {"keyword": keyword, "limit": 10}
        query_string = urlencode(params)
        url = f"{DOMAIN}{path}?{query_string}"
        headers = {"Authorization": get_authorization_header("GET", path, query_string), "Content-Type": "application/json"}
        response = requests.get(url, headers=headers, timeout=15)
        data = response.json()
        if 'data' in data and data['data'].get('productData'):
            return data['data']
        return
    except: return

def get_title_from_html(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            match = re.search(r'<title>(.*?)</title>', content)
            if match: return match.group(1)
    except: pass
    return "추천 상품"

def generate_ai_content(product_name):
    if not GEMINI_KEY: return "상품 리뷰를 준비 중입니다."
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        prompt = f"상품명 '{product_name}'에 대해 쇼핑 전문가처럼 친절한 해요체로 400자 내외 상세 리뷰를 HTML 없이 작성해줘. 장점 3가지 포함."
        response = model.generate_content(prompt)
        return response.text.replace("\n", "<br>")
    except:
        return f"{product_name}은 품질과 가격 모두 잡은 최고의 선택입니다. 지금 바로 확인해보세요!"

def main():
    os.makedirs("posts", exist_ok=True)
    total_count = 0
    
    keywords = ["가성비 삼성 노트북", "인기 애플 아이패드", "세일 샤오미 가전", "대박 캠핑 용품"]
    target = random.choice(keywords)
    products = fetch_data(target)
    
    if products:
        for item in products:
            try:
                p_id = item['productId']
                filename = f"posts/{datetime.now().strftime('%Y%m%d')}_{p_id}.html"
                if os.path.exists(filename): continue 
                
                ai_content = generate_ai_content(item['productName'])
                # 버그 수정: 리스트가 아닌 문자열로 가져옴
                img_url = item['productImage'].split('?')
                
                with open(filename, "w", encoding="utf-8") as f:
                    f.write(f"""<!DOCTYPE html><html lang='ko'><head><meta charset='UTF-8'><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>{item['productName']} 리뷰</title>
                    <style>
                        body {{ font-family: sans-serif; background: #f5f6f8; padding: 20px; line-height: 1.6; }}
                       .container {{ max-width: 600px; margin: auto; background: white; padding: 25px; border-radius: 15px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
                        img {{ width: 100%; border-radius: 10px; }}
                       .price {{ font-size: 1.5rem; color: #e44d26; font-weight: bold; margin: 15px 0; }}
                       .btn {{ background: #e44d26; color: white; padding: 15px; text-decoration: none; border-radius: 5px; display: block; text-align: center; font-weight: bold; }}
                    </style></head><body>
                    <div class='container'>
                        <h2>{item['productName']}</h2>
                        <img src='{img_url}' alt='{item['productName']}'>
                        <div class='price'>{format(item['productPrice'], ',')}원</div>
                        <div style='margin: 20px 0;'>{ai_content}</div>
                        <a href='{item['productUrl']}' class='btn' target='_blank' rel='nofollow noopener'>👉 최저가 확인하기</a>
                        <p style='font-size: 0.8rem; color: #999; margin-top: 20px;'>본 포스팅은 쿠팡 파트너스 활동의 일환으로, 이에 따른 일정액의 수수료를 제공받습니다.</p>
                    </div></body></html>""")
                total_count += 1
                time.sleep(31) # Gemini 무료 한도 준수
            except: continue

    # 인덱스 및 SEO 파일 갱신
    files = sorted([f for f in os.listdir("posts") if f.endswith(".html")], reverse=True)
    
    # index.html
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(f"<!DOCTYPE html><html lang='ko'><head><meta charset='UTF-8'><title>실시간 핫딜</title></head><body><h1>🚀 핫딜 리스트</h1>")
        for file in files[:100]:
            title = get_title_from_html(f"posts/{file}")
            f.write(f"<p><a href='posts/{file}'>{title}</a></p>")
        f.write("</body></html>")

    # sitemap.xml
    now = datetime.now().strftime("%Y-%m-%d")
    sitemap = f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    sitemap += f'<url><loc>{SITE_URL}/</loc><lastmod>{now}</lastmod><priority>1.0</priority></url>\n'
    for file in files:
        sitemap += f'<url><loc>{SITE_URL}/posts/{file}</loc><lastmod>{now}</lastmod></url>\n'
    sitemap += '</urlset>'
    with open("sitemap.xml", "w", encoding="utf-8") as f: f.write(sitemap)

    # robots.txt
    with open("robots.txt", "w", encoding="utf-8") as f:
        f.write(f"User-agent: *\nAllow: /\nSitemap: {SITE_URL}/sitemap.xml")

if __name__ == "__main__":
    main()
