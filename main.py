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
        # 💎 수정: 수집 개수를 10개에서 40개로 늘렸습니다.
        params = {"keyword": keyword, "limit": 40}
        query_string = urlencode(params)
        url = f"{DOMAIN}{path}?{query_string}"
        headers = {"Authorization": get_authorization_header("GET", path, query_string), "Content-Type": "application/json"}
        response = requests.get(url, headers=headers, timeout=15)
        return response.json()
    except: return None

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
    brands = [
        "삼성", "LG", "애플", "샤오미", "다이슨", "테팔", "필립스", "브라운", "쿠쿠", "쿠첸", 
        "나이키", "아디다스", "뉴발란스", "휠라", "언더아머", "노스페이스", "파타고니아", 
        "농심", "오뚜기", "CJ", "비비고", "햇반", "동원", "서울우유", "종근당", "정관장",
        "크리넥스", "코디", "다우니", "피죤", "페브리즈", "유한킴벌리", "3M"
    ]
    products = [
        "노트북", "모니터", "마우스", "키보드", "아이패드", "갤럭시탭", "에어팟", "버즈", "스마트워치",
        "라면", "생수", "햇반", "김치", "통조림", "커피", "우유", "두유", "영양제", "유산균", "오메가3",
        "물티슈", "휴지", "세제", "섬유유연제", "샴푸", "바디워시", "치약", "칫솔", "마스크",
        "청소기", "로봇청소기", "공기청정기", "제습기", "선풍기", "에어프라이어", "전자레인지", "건조기",
        "반팔티", "후드티", "슬랙스", "청바지", "패딩", "바람막이", "운동화", "슬리퍼", "양말"
    ]
    specs = ["대용량", "1+1", "세트", "번들", "무료배송", "로켓배송", "새벽배송", "고속충전", "무선", "저소음", "게이밍", "미니", "휴대용"]
    
    strategy = random.choice([1, 2, 3])
    if strategy == 1: return f"{random.choice(modifiers)} {random.choice(products)}"
    elif strategy == 2: return f"{random.choice(brands)} {random.choice(products)}"
    else: return f"{random.choice(brands)} {random.choice(products)} {random.choice(specs)}"

def generate_ai_content(product_name):
    if not GEMINI_KEY:
        return f"<p>{product_name} 제품은 현재 가장 인기가 많은 베스트셀러 중 하나입니다.</p>"
    
    try:
        model = genai.GenerativeModel('gemini-1.5-pro')
        
        prompt = f"""
        당신은 10년 차 전문 쇼핑 칼럼니스트입니다.
        상품명: '{product_name}'
        
        이 상품에 대한 매력적이고 상세한 리뷰 포스팅을 HTML 태그 없이 줄글로 작성해주세요.
        
        [작성 조건]
        1. 독자: 합리적인 소비를 지향하는 스마트 컨슈머
        2. 말투: 전문적이지만 친절하고 신뢰감 있는 '해요체' (이모지 ✨, 🔥, 👍 적절히 사용)
        3. 내용:
           - 도입: 이 제품이 왜 요즘 인기인지 흥미 유발
           - 본문: 제품의 핵심 장점 2~3가지를 구체적인 상황(출근, 육아, 자취 등)에 빗대어 설명
           - 결론: 고민은 배송만 늦출 뿐이라는 식의 세련된 추천
        4. 길이: 공백 포함 400자 내외로 풍성하게.
        5. 주의: 거짓 정보를 지어내지 말고, 일반적인 장점을 서술할 것.
        """
        
        response = model.generate_content(prompt)
        return response.text.replace("\n", "<br>")
    except Exception as e:
        print(f"AI Error: {e}")
        return f"<p>{product_name} 제품은 독보적인 가성비와 성능으로 소비자 만족도가 매우 높은 제품입니다. 품절 임박 상품이니 서둘러 확인해보세요!</p>"

def main():
    os.makedirs("posts", exist_ok=True)
    
    target = get_random_keyword()
    print(f"이번 타임 검색어: {target}")
    
    res = fetch_data(target)
    
    if res and 'data' in res and res['data'].get('productData'):
        clean_target = target.replace(" ", "_")
        for item in res['data']['productData']:
            try:
                p_id = item['productId']
                filename = f"posts/{datetime.now().strftime('%Y%m%d')}_{clean_target}_{p_id}.html"
                if os.path.exists(filename): continue 
                
                print(f"💎 Gemini Pro 글쓰기 중... ({item['productName'][:10]}...)")
                ai_content = generate_ai_content(item['productName'])
                
                # 태그 생성
                keywords = item['productName'].split(" ")
                tags = " ".join([f"#{k}" for k in keywords if len(k) > 1][:5])
                
                with open(filename, "w", encoding="utf-8") as f:
                    f.write(f"""<!DOCTYPE html><html><head><meta charset='UTF-8'><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>{item['productName']} - 상세 리뷰 및 최저가</title>
                    <style>
                        body {{ font-family: 'Apple SD Gothic Neo', sans-serif; background: #f5f6f8; padding: 20px; color: #333; line-height: 1.6; }}
                        .container {{ max-width: 600px; margin: auto; background: white; padding: 30px; border-radius: 20px; box-shadow: 0 4px 20px rgba(0,0,0,0.05); }}
                        h2 {{ font-size: 1.3rem; margin-bottom: 20px; word-break: keep-all; }}
                        img {{ width: 100%; border-radius: 15px; margin-bottom: 20px; }}
                        .price {{ font-size: 1.6rem; color: #e44d26; font-weight: bold; margin-bottom: 20px; }}
                        .btn {{ background: linear-gradient(135deg, #e44d26, #f16529); color: white; padding: 18px 40px; text-decoration: none; border-radius: 50px; display: inline-block; font-weight: bold; font-size: 1.1rem; box-shadow: 0 4px 15px rgba(228, 77, 38, 0.3); transition: 0.3s; width: 80%; text-align: center; }}
                        .btn:hover {{ transform: scale(1.02); }}
                        .ai-review-box {{ background: #fdfdfd; padding: 25px; border-radius: 15px; margin: 30px 0; text-align: left; border: 1px solid #eee; font-size: 0.95rem; box-shadow: inset 0 0 10px rgba(0,0,0,0.01); }}
                        .ai-badge {{ background: #6c5ce7; color: white; padding: 5px 12px; border-radius: 15px; font-size: 0.75rem; font-weight: bold; margin-bottom: 15px; display: inline-block; }}
                        .tags {{ color: #888; font-size: 0.8rem; margin-top: 30px; }}
                        .disclosure {{ margin-top: 20px; padding: 15px; font-size: 0.75rem; color: #999; background: #fff; border: 1px solid #eee; border-radius: 5px; }}
                    </style></head><body>
                    <div class='container'>
                        <h2>{item['productName']}</h2>
                        <img src='{item['productImage']}'>
                        
                        <div class='ai-review-box'>
                            <div class='ai-badge'>🏆 에디터 추천 리뷰</div><br>
                            {ai_content}
                        </div>

                        <div class='price'>{format(item['productPrice'], ',')}원</div>
                        <a href='{item['productUrl']}' class='btn'>👉 초특가 혜택 확인하기</a>
                        
                        <div class='tags'>
                            관련 키워드: {tags}
                        </div>

                        <div class='disclosure'>
                            본 포스팅은 쿠팡 파트너스 활동의 일환으로, 이에 따른 일정액의 수수료를 제공받습니다.
                        </div>
                    </div></body></html>""")
            except: continue
            
            # 💎 제미나이 무료 버전 한도(1분에 2회 질문)를 지키기 위해 35초씩 대기합니다.
            # 40개 발행 시 로봇이 종료될 때까지 총 약 25분 정도 소요됩니다.
            time.sleep(35)

    # 4. 메인 화면 & 사이트맵 업데이트 (기존과 동일)
    files = sorted([f for f in os.listdir("posts") if f.endswith(".html")], reverse=True)
    
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(f"""<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>핫딜 셔틀 - 프리미엄 큐레이션</title>
    <style>
        body {{ font-family: 'Apple SD Gothic Neo', sans-serif; background: #f0f2f5; margin: 0; padding: 20px; }}
        .header {{ text-align: center; background: white; padding: 30px; border-radius: 20px; margin-bottom: 20px; box-shadow: 0 4px 10px rgba(0,0,0,0.05); }}
        h1 {{ color: #e44d26; margin: 0; font-size: 1.8rem; }}
        .grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(250px, 1fr)); gap: 15px; max-width: 1000px; margin: auto; }}
        .card {{ background: white; padding: 20px; border-radius: 15px; text-decoration: none; color: #333; display: flex; flex-direction: column; justify-content: space-between; min-height: 120px; border: 1px solid #eee; transition: 0.3s; }}
        .card:hover {{ border-color: #e44d26; transform: translateY(-3px); box-shadow: 0 5px 15px rgba(0,0,0,0.1); }} 
        .title {{ font-weight: bold; font-size: 1rem; margin-bottom: 10px; line-height: 1.4; overflow: hidden; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; }}
        .badge {{ color: #e44d26; font-size: 0.8rem; font-weight: bold; text-align: right; margin-top: auto; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🚀 실시간 핫딜 쇼핑몰</h1>
        <p style="color:#666;">전문가가 엄선한 최저가 상품 모음</p>
        <p style="font-size:0.8rem; color:#999;">최근 업데이트: {datetime.now().strftime('%Y-%m-%d %H:%M')}</p>
    </div>
    <div class="grid">
""")
        if files:
            for file in files[:100]:
                real_name = get_title_from_html(f"posts/{file}")
                f.write(f"""<a class="card" href="posts/{file}"><div class="title">{real_name}</div><div class="badge">최저가 확인하기 ></div></a>""")
        else:
            f.write("<div class='card'><h3>상품 수집 중...</h3><p>잠시 후 다시 접속해주세요.</p></div>")
        f.write("    </div></body></html>")

    with open("sitemap.xml", "w", encoding="utf-8") as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        f.write('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n')
        f.write(f'  <url><loc>{SITE_URL}/</loc><changefreq>daily</changefreq><priority>1.0</priority></url>\n')
        if files:
            for file in files:
                f.write(f'  <url><loc>{SITE_URL}/posts/{file}</loc><changefreq>monthly</changefreq><priority>0.8</priority></url>\n')
        f.write('</urlset>')

    with open("robots.txt", "w", encoding="utf-8") as f:
        f.write(f"User-agent: *\nAllow: /\nSitemap: {SITE_URL}/sitemap.xml")

    with open("README.md", "w", encoding="utf-8") as f:
        f.write("# 🛒 쇼핑몰 가동 중\n\n[웹사이트 바로가기](https://rkskqdl-a11y.github.io/coupang-sale-shuttle/)")
    with open(".nojekyll", "w", encoding="utf-8") as f: f.write("")

if __name__ == "__main__":
    main()
