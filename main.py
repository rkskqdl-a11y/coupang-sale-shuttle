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

def generate_ai_content(product_name, price):
    """
    💎 고도화된 AI 프롬프트 전략 적용
    전문가 페르소나 부여 및 구조화된 HTML 출력 요청
    """
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        # AI에게 구체적인 역할과 형식을 부여합니다.
        prompt = f"""
        너는 10년 차 IT/쇼핑 전문 큐레이터야. 상품명 '{product_name}'(가격: {price}원)에 대해 구글 검색에 잘 노출될 수 있도록 전문적인 리뷰를 작성해줘.
        
        [작성 가이드]
        1. 말투: 친절하고 신뢰감 있는 '해요체'
        2. 분량: 공백 포함 800자 내외의 풍성한 내용
        3. 구조: 아래 3개의 섹션을 반드시 포함하고 섹션 제목은 <h3> 태그로 감싸줘.
           - <h3>이 제품을 선택해야 하는 핵심 이유</h3>
           - <h3>실제 사용자가 느끼는 확실한 장점 3가지</h3>
           - <h3>가성비 분석 및 이런 분들께 추천</h3>
        4. 특징: 단순 나열이 아닌, 이 가격대에서 왜 이 제품이 좋은지 분석적으로 써줘.
        5. 주의: HTML 태그(h3, br) 외에 마크다운 기호(#, *)는 사용하지 마.
        """
        response = model.generate_content(prompt)
        return response.text.replace("\n", "<br>")
    except:
        return f"<h3>{product_name} 가성비 리뷰</h3>{product_name}은 품질과 가격 모두 잡은 최고의 선택입니다. 현재 {price}원에 만나보실 수 있는 절호의 기회입니다."

def main():
    os.makedirs("posts", exist_ok=True)
    
    # 다양한 키워드 조합으로 검색 범위를 넓힙니다.
    target = f"{random.choice(['가성비', '인기', '추천'])} {random.choice(['삼성', '나이키', 'LG', '농심'])} {random.choice(['노트북', '운동화', '에어팟', '라면'])}"
    print(f"🔍 SEO 최적화 수집 시작: {target}")
    products = fetch_data(target)
    
    for item in products:
        try:
            p_id = item['productId']
            clean_img_url = item['productImage'].split('?')[0]
            clean_target = target.replace(" ", "_")
            
            filename = f"posts/{datetime.now().strftime('%Y%m%d')}_{clean_target}_{p_id}.html"
            if os.path.exists(filename): continue 
            
            # 가격 정보를 함께 전달하여 AI가 분석하게 합니다.
            formatted_price = format(item['productPrice'], ',')
            ai_content = generate_ai_content(item['productName'], formatted_price)
            
            # 💎 HTML 구조 강화 (Meta Description 추가)
            with open(filename, "w", encoding="utf-8") as f:
                f.write(f"""<!DOCTYPE html><html lang='ko'>
                <head>
                    <meta charset='UTF-8'>
                    <meta name="viewport" content="width=device-width, initial-scale=1.0">
                    <meta name="description" content="{item['productName']}의 상세 리뷰와 가성비 분석 정보를 확인하세요.">
                    <title>{item['productName']} 솔직 리뷰 및 최저가 안내</title>
                    <style>
                        body {{ font-family: 'Apple SD Gothic Neo', sans-serif; background: #f5f6f8; padding: 20px; color: #333; line-height: 1.8; }}
                        .container {{ max-width: 650px; margin: auto; background: white; padding: 40px; border-radius: 25px; box-shadow: 0 10px 30px rgba(0,0,0,0.05); }}
                        h2 {{ font-size: 1.5rem; color: #222; margin-bottom: 25px; border-bottom: 2px solid #e44d26; padding-bottom: 10px; }}
                        h3 {{ font-size: 1.2rem; color: #e44d26; margin-top: 30px; }}
                        img {{ width: 100%; border-radius: 20px; margin: 20px 0; }}
                        .price-tag {{ font-size: 1.8rem; color: #e44d26; font-weight: bold; text-align: center; margin: 30px 0; }}
                        .btn {{ background: #e44d26; color: white; padding: 20px; text-decoration: none; border-radius: 50px; display: block; text-align: center; font-weight: bold; font-size: 1.2rem; }}
                        .disclosure {{ font-size: 0.8rem; color: #999; margin-top: 40px; text-align: center; }}
                    </style>
                </head>
                <body>
                    <div class='container'>
                        <h2>{item['productName']}</h2>
                        <img src='{clean_img_url}' alt='{item['productName']} 이미지'>
                        <div class='content'>{ai_content}</div>
                        <div class='price-tag'>현재가: {formatted_price}원</div>
                        <a href='{item['productUrl']}' class='btn'>💰 최저가 확인하러 가기</a>
                        <p class='disclosure'>본 포스팅은 쿠팡 파트너스 활동의 일환으로, 이에 따른 일정액의 수수료를 제공받습니다.</p>
                    </div>
                </body></html>""")
            
            time.sleep(35)
        except: continue

    # 인덱스 및 사이트맵 자동 업데이트 로직 유지
    files = sorted([f for f in os.listdir("posts") if f.endswith(".html")], reverse=True)
    
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(f"<!DOCTYPE html><html lang='ko'><head><meta charset='UTF-8'><title>실시간 핫딜 정보</title><style>body{{font-family:sans-serif; background:#f0f2f5; padding:20px;}} .grid{{display:grid; grid-template-columns:repeat(auto-fill, minmax(280px, 1fr)); gap:20px;}} .card{{background:white; padding:25px; border-radius:15px; text-decoration:none; color:#333; box-shadow:0 2px 10px rgba(0,0,0,0.05);}}</style></head><body><h1 style='text-align:center;'>🚀 스마트 쇼핑 핫딜 셔틀</h1><div class='grid'>")
        for file in files[:100]:
            title = get_title_from_html(f"posts/{file}")
            f.write(f"<a class='card' href='posts/{file}'><div>{title}</div><div style='color:#e44d26; font-size:0.9rem; margin-top:15px;'>상세 리뷰 보기 ></div></a>")
        f.write("</div></body></html>")

    with open("sitemap.xml", "w", encoding="utf-8") as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n')
        f.write(f'<url><loc>{SITE_URL}/</loc><priority>1.0</priority></url>\n')
        for file in files:
            f.write(f'<url><loc>{SITE_URL}/posts/{file}</loc><priority>0.8</priority></url>\n')
        f.write('</urlset>')

    with open("robots.txt", "w", encoding="utf-8") as f:
        f.write(f"User-agent: *\nAllow: /\nSitemap: {SITE_URL}/sitemap.xml")

if __name__ == "__main__":
    main()
