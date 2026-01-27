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

# 1. 기본 설정
ACCESS_KEY = os.environ.get('COUPANG_ACCESS_KEY')
SECRET_KEY = os.environ.get('COUPANG_SECRET_KEY')
GEMINI_KEY = os.environ.get('GEMINI_API_KEY')
SITE_URL = "https://rkskqdl-a11y.github.io/coupang-sale-shuttle"

# 제미나이 설정
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
        # 💎 한 번에 40개를 가져오도록 설정
        params = {"keyword": keyword, "limit": 40}
        query_string = urlencode(params)
        url = f"{DOMAIN}{path}?{query_string}"
        headers = {"Authorization": get_authorization_header("GET", path, query_string), "Content-Type": "application/json"}
        response = requests.get(url, headers=headers, timeout=15)
        data = response.json()
        
        # 💎 상태 로그 출력
        if 'data' in data and data['data'].get('productData'):
            print(f"✅ 쿠팡에서 '{keyword}' 검색 결과 {len(data['data']['productData'])}개의 상품을 찾았습니다.")
        else:
            print(f"❌ '{keyword}' 검색 결과가 없습니다. API 응답: {data}")
        return data
    except Exception as e:
        print(f"❌ 쿠팡 API 연결 에러: {e}")
        return None

def get_title_from_html(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            match = re.search(r'<title>(.*?)</title>', content)
            if match: return match.group(1)
    except: pass
    return "추천 상품"

def get_random_keyword():
    modifiers = ["가성비", "인기", "추천", "세일", "베스트", "특가", "국민", "필수", "요즘 뜨는", "대박", "자취생", "학생용", "사무용", "선물용"]
    brands = ["삼성", "LG", "애플", "샤오미", "다이슨", "테팔", "필립스", "브라운", "쿠쿠", "쿠첸", "나이키", "아디다스", "농심", "오뚜기", "CJ", "종근당"]
    products = ["노트북", "모니터", "마우스", "아이패드", "에어팟", "스마트워치", "라면", "생수", "햇반", "김치", "커피", "영양제", "물티슈", "세제", "샴푸", "청소기", "에어프라이어", "운동화"]
    
    strategy = random.choice([1, 2, 3])
    if strategy == 1: return f"{random.choice(modifiers)} {random.choice(products)}"
    elif strategy == 2: return f"{random.choice(brands)} {random.choice(products)}"
    else: return f"{random.choice(modifiers)} {random.choice(brands)} {random.choice(products)}"

def generate_ai_content(product_name):
    if not GEMINI_KEY:
        return f"<p>{product_name} 제품은 현재 인기가 많은 상품입니다.</p>"
    try:
        model = genai.GenerativeModel('gemini-1.5-pro')
        prompt = f"상품명 '{product_name}'에 대해 10년 차 쇼핑 전문가처럼 친절한 해요체로 400자 내외 상세 리뷰를 HTML 없이 작성해줘. 장점 3가지 포함."
        response = model.generate_content(prompt)
        return response.text.replace("\n", "<br>")
    except Exception as e:
        print(f"⚠️ AI 글쓰기 실패: {e}")
        return f"<p>{product_name}은 가성비와 성능이 뛰어난 추천 제품입니다.</p>"

def main():
    os.makedirs("posts", exist_ok=True)
    target = get_random_keyword()
    print(f"🔍 작업 시작 키워드: {target}")
    
    res = fetch_data(target)
    
    count = 0
    if res and 'data' in res and res['data'].get('productData'):
        clean_target = target.replace(" ", "_")
        for item in res['data']['productData']:
            try:
                p_id = item['productId']
                filename = f"posts/{datetime.now().strftime('%Y%m%d')}_{clean_target}_{p_id}.html"
                
                if os.path.exists(filename):
                    print(f"⏩ 중복 건너뜀: {item['productName'][:15]}")
                    continue 
                
                print(f"💎 ({count+1}/40) AI 리뷰 생성 중: {item['productName'][:15]}...")
                ai_content = generate_ai_content(item['productName'])
                
                keywords = item['productName'].split(" ")
                tags = " ".join([f"#{k}" for k in keywords if len(k) > 1][:5])
                
                with open(filename, "w", encoding="utf-8") as f:
                    f.write(f"""<!DOCTYPE html><html><head><meta charset='UTF-8'><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>{item['productName']} 리뷰</title>
                    <style>
                        body {{ font-family: 'Apple SD Gothic Neo', sans-serif; background: #f5f6f8; padding: 20px; color: #333; line-height: 1.6; }}
                        .container {{ max-width: 600px; margin: auto; background: white; padding: 30px; border-radius: 20px; box-shadow: 0 4px 20px rgba(0,0,0,0.05); }}
                        h2 {{ font-size: 1.3rem; margin-bottom: 20px; }}
                        img {{ width: 100%; border-radius: 15px; margin-bottom: 20px; }}
                        .price {{ font-size: 1.6rem; color: #e44d26; font-weight: bold; margin-bottom: 20px; }}
                        .btn {{ background: linear-gradient(135deg, #e44d26, #f16529); color: white; padding: 18px 40px; text-decoration: none; border-radius: 50px; display: inline-block; font-weight: bold; width: 80%; text-align: center; }}
                        .ai-review-box {{ background: #fdfdfd; padding: 25px; border-radius: 15px; margin: 30px 0; border: 1px solid #eee; }}
                        .ai-badge {{ background: #6c5ce7; color: white; padding: 5px 12px; border-radius: 15px; font-size: 0.75rem; font-weight: bold; }}
                        .disclosure {{ margin-top: 20px; font-size: 0.75rem; color: #999; }}
                    </style></head><body>
                    <div class='container'>
                        <h2>{item['productName']}</h2>
                        <img src='{item['productImage']}'>
                        <div class='ai-review-box'><span class='ai-badge'>🏆 에디터 추천</span><br><br>{ai_content}</div>
                        <div class='price'>{format(item['productPrice'], ',')}원</div>
                        <a href='{item['productUrl']}' class='btn'>👉 특가 확인하기</a>
                        <p style='color:#888; font-size:0.8rem;'>{tags}</p>
                        <div class='disclosure'>본 포스팅은 쿠팡 파트너스 활동의 일환으로, 이에 따른 일정액의 수수료를 제공받습니다.</div>
                    </div></body></html>""")
                
                count += 1
                time.sleep(35) # 💎 제미나이 무료 한도 준수
            except Exception as e:
                print(f"❌ 에러 발생: {e}")
                continue

    # 메인 페이지 및 사이트맵 업데이트 (기존 로직 유지)
    files = sorted([f for f in os.listdir("posts") if f.endswith(".html")], reverse=True)
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(f"<!DOCTYPE html><html lang='ko'><head><meta charset='UTF-8'><title>핫딜 셔틀</title><style>body{{font-family:sans-serif; background:#f0f2f5; padding:20px;}} .grid{{display:grid; grid-template-columns:repeat(auto-fill, minmax(250px, 1fr)); gap:15px;}} .card{{background:white; padding:20px; border-radius:15px; text-decoration:none; color:#333; border:1px solid #eee;}}</style></head><body><h1 style='text-align:center; color:#e44d26;'>🚀 실시간 핫딜 쇼핑몰</h1><p style='text-align:center; color:#999;'>업데이트: {datetime.now().strftime('%Y-%m-%d %H:%M')}</p><div class='grid'>")
        for file in files[:100]:
            title = get_title_from_html(f"posts/{file}")
            f.write(f"<a class='card' href='posts/{file}'><div>{title}</div><div style='color:#e44d26; font-size:0.8rem; margin-top:10px;'>최저가 보기 ></div></a>")
        f.write("</div></body></html>")

    with open("sitemap.xml", "w", encoding="utf-8") as f:
        f.write(f'<?xml version="1.0" encoding="UTF-8"?><urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9"><url><loc>{SITE_URL}/</loc><priority>1.0</priority></url>')
        for file in files: f.write(f'<url><loc>{SITE_URL}/posts/{file}</loc></url>')
        f.write('</urlset>')

    print(f"✨ 작업 완료! 총 {count}개의 새 포스팅이 생성되었습니다.")

if __name__ == "__main__":
    main()
