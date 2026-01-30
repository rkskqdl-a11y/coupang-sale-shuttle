
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

# 1. 설정
ACCESS_KEY = os.environ.get('COUPANG_ACCESS_KEY')
SECRET_KEY = os.environ.get('COUPANG_SECRET_KEY')
GEMINI_KEY = os.environ.get('GEMINI_API_KEY')
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
            return data['data']['productData']
        return []
    except: return []

def get_title_from_html(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            match = re.search(r'<title>(.*?)</title>', content)
            if match: return match.group(1)
    except: pass
    return "추천 상품"

def generate_ai_content(product_name):
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        prompt = f"상품명 '{product_name}'에 대해 쇼핑 전문가처럼 친절한 해요체로 400자 내외 상세 리뷰를 HTML 없이 작성해줘. 장점 3가지 포함."
        response = model.generate_content(prompt)
        return response.text.replace("\n", "<br>")
    except:
        return f"{product_name}은 품질과 가격 모두 잡은 최고의 선택입니다."

def main():
    os.makedirs("posts", exist_ok=True)
   
    target = f"{random.choice(['가성비', '인기', '추천'])} {random.choice(['삼성', '나이키', 'LG'])} {random.choice(['노트북', '운동화', '에어팟'])}"
    print(f"🔍 이번 타임 검색어: {target}")
    products = fetch_data(target)
   
    for item in products:
        try:
            p_id = item['productId']
            # 💎 [수정] 이미지 URL 버그 해결 (리스트가 아닌 문자열로 추출)
            clean_img_url = item['productImage'].split('?')[0]
            clean_target = target.replace(" ", "_")
           
            # 파일명에 키워드를 넣어 SEO를 강화합니다.
            filename = f"posts/{datetime.now().strftime('%Y%m%d')}_{clean_target}_{p_id}.html"
            if os.path.exists(filename): continue
           
            ai_content = generate_ai_content(item['productName'])
           
            with open(filename, "w", encoding="utf-8") as f:
                f.write(f"""<!DOCTYPE html><html><head><meta charset='UTF-8'><title>{item['productName']} 리뷰</title>
                <style>body{{font-family:sans-serif; background:#f5f6f8; padding:20px; color:#333;}} .container{{max-width:600px; margin:auto; background:white; padding:30px; border-radius:20px;}} img{{width:100%; border-radius:15px;}}</style></head>
                <body><div class='container'>
                <h2>{item['productName']}</h2>
                <img src='{clean_img_url}'>
                <div style='margin:20px 0; background:#f9f9f9; padding:20px; border-radius:10px;'>{ai_content}</div>
                <div style='font-size:1.5rem; color:#e44d26; font-weight:bold;'>{format(item['productPrice'], ',')}원</div>
                <a href='{item['productUrl']}' style='display:block; background:#e44d26; color:white; padding:15px; text-align:center; text-decoration:none; border-radius:50px; margin-top:20px;'>👉 최저가 확인하기</a>
                <p style='font-size:0.7rem; color:#999; margin-top:30px;'>본 포스팅은 쿠팡 파트너스 활동의 일환으로 수수료를 제공받을 수 있습니다.</p>
                </div></body></html>""")
           
            time.sleep(35)
        except: continue

    # 💎 [핵심] 인덱스, 사이트맵, robots.txt 통합 갱신
    files = sorted([f for f in os.listdir("posts") if f.endswith(".html")], reverse=True)
   
    # 1. index.html 갱신
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(f"<!DOCTYPE html><html lang='ko'><head><meta charset='UTF-8'><title>핫딜 셔틀</title><style>body{{font-family:sans-serif; background:#f0f2f5; padding:20px;}} .grid{{display:grid; grid-template-columns:repeat(auto-fill, minmax(250px, 1fr)); gap:15px;}} .card{{background:white; padding:20px; border-radius:15px; text-decoration:none; color:#333; border:1px solid #eee;}}</style></head><body><h1 style='text-align:center; color:#e44d26;'>🚀 실시간 핫딜 쇼핑몰</h1><div class='grid'>")
        for file in files[:100]:
            title = get_title_from_html(f"posts/{file}")
            f.write(f"<a class='card' href='posts/{file}'><div>{title}</div><div style='color:#e44d26; font-size:0.8rem; margin-top:10px;'>보기 ></div></a>")
        f.write("</div></body></html>")

    # 2. sitemap.xml 갱신
    with open("sitemap.xml", "w", encoding="utf-8") as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n')
        f.write(f'<url><loc>{SITE_URL}/</loc><priority>1.0</priority></url>\n')
        for file in files:
            f.write(f'<url><loc>{SITE_URL}/posts/{file}</loc><priority>0.8</priority></url>\n')
        f.write('</urlset>')

    # 3. robots.txt 갱신
    with open("robots.txt", "w", encoding="utf-8") as f:
        f.write(f"User-agent: *\nAllow: /\nSitemap: {SITE_URL}/sitemap.xml")

    print(f"✨ 모든 페이지 동기화 완료! 현재 포스팅 수: {len(files)}")

if __name__ == "__main__":
    main()
