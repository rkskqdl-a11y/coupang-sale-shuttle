import os, hmac, hashlib, time, requests, json, random, re
from datetime import datetime
from urllib.parse import urlencode

# [1. 설정 정보]
ACCESS_KEY = os.environ.get('COUPANG_ACCESS_KEY')
SECRET_KEY = os.environ.get('COUPANG_SECRET_KEY')
GEMINI_KEY = os.environ.get('GEMINI_API_KEY')
SITE_URL = "https://rkskqdl-a11y.github.io/coupang-sale-shuttle"

def generate_ai_content(item):
    """💎 모든 카테고리를 전문가 수준으로 깊이 있게 분석하여 장문의 리뷰를 생성합니다."""
    if not GEMINI_KEY: return "상세 정보를 분석 중입니다."
    
    name = item.get('productName')
    price = format(item.get('productPrice', 0), ',')
    
    # AI가 헷갈리지 않게 상품명을 핵심만 추출
    short_name = " ".join(re.sub(r'[^\w\s]', '', name).split()[:3])
    
    # 🤖 전 카테고리 대응 고급 프롬프트
    prompt_text = f"""
    너는 15년 경력의 베테랑 쇼핑 매거진 편집장이야. 상품 '{short_name}'(가격 {price}원)을 
    실제로 일주일간 심도 있게 테스트했다고 가정하고, 독자들에게 전문적인 인사이트를 제공하는 칼럼을 써줘. 
    
    [작성 가이드 - 필수!]
    1. **절대 상품명이나 제목으로 시작하지 마.** 독자의 호기심을 자극하는 문장으로 시작해.
    2. 말투: 지적이면서도 친근한 전문가의 '해요체'.
    3. 분량: 최소 800자 이상의 풍성한 텍스트를 생성해.
    4. 구성: 아래 4가지 섹션을 반드시 <h3> 태그를 사용하여 작성해.
       - <h3>✨ 에디터가 느낀 첫인상과 디자인 미학</h3>: 소재의 느낌, 마감 처리, 첫 대면 시의 만족감.
       - <h3>성능과 실용성: 기대 이상의 포인트</h3>: 실제 생활에서 이 제품이 주는 편리함과 압도적인 장점 3가지.
       - <h3>🔍 전문가의 시선에서 본 디테일한 분석</h3>: 내구성, 가성비, 혹은 기술적 특징에 대한 심층 분석.
       - <h3>💡 이런 라이프스타일을 가진 분들께 추천</h3>: 이 제품이 가장 빛을 발할 사용자 환경 제안.
    5. HTML(h3, br)만 사용하여 가독성 있게 작성해줘.
    """

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_KEY}"
    payload = {
        "contents": [{"parts": [{"text": prompt_text}]}],
        "safetySettings": [
            {"category": c, "threshold": "BLOCK_NONE"} for c in 
            ["HARM_CATEGORY_HARASSMENT", "HARM_CATEGORY_HATE_SPEECH", "HARM_CATEGORY_SEXUALLY_EXPLICIT", "HARM_CATEGORY_DANGEROUS_CONTENT"]
        ]
    }

    try:
        response = requests.post(url, json=payload, timeout=30) # 장문 생성을 위해 타임아웃 연장
        res_data = response.json()
        if 'candidates' in res_data and len(res_data['candidates']) > 0:
            return res_data['candidates'][0]['content']['parts'][0]['text'].replace("\n", "<br>")
        raise ValueError("AI Response Blocked")
    except Exception as e:
        print(f"⚠️ AI 생성 실패({e}): 비상용 문구로 대체합니다.")
        return f"<h3>🔍 에디터의 핵심 요약</h3>{short_name}은 현재 {price}원의 가격대에서 가장 탄탄한 기본기를 갖춘 모델입니다. 실제 사용자들 사이에서 만족도가 매우 높으며, 깔끔한 디자인과 실용성으로 많은 사랑을 받고 있는 제품입니다."

def fetch_data(keyword):
    """쿠팡 API 데이터 수집"""
    try:
        DOMAIN = "https://api-gateway.coupang.com"
        path = "/v2/providers/affiliate_open_api/apis/openapi/v1/products/search"
        params = {"keyword": keyword, "limit": 10}
        query_string = urlencode(params)
        url = f"{DOMAIN}{path}?{query_string}"
        headers = {"Authorization": get_authorization_header("GET", path, query_string), "Content-Type": "application/json"}
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code == 200:
            return response.json().get('data', {}).get('productData', [])
        return []
    except: return []

def get_authorization_header(method, path, query_string):
    datetime_gmt = time.strftime('%y%m%dT%H%M%SZ', time.gmtime())
    message = datetime_gmt + method + path + query_string
    signature = hmac.new(bytes(SECRET_KEY, 'utf-8'), msg=bytes(message, 'utf-8'), digestmod=hashlib.sha256).hexdigest()
    return f"CEA algorithm=HmacSHA256, access-key={ACCESS_KEY}, signed-date={datetime_gmt}, signature={signature}"

def main():
    os.makedirs("posts", exist_ok=True)
    
    # 💎 모든 카테고리를 순환하도록 설정
    sets = [("삼성", "노트북"), ("LG", "생활가전"), ("애플", "아이패드"), ("나이키", "운동화"), ("다이슨", "청소기"), ("필립스", "면도기")]
    brand, item_type = random.choice(sets)
    target = f"인기 {brand} {item_type}"
    
    print(f"🚀 전 분야 전문 분석 가동: {target}")
    products = fetch_data(target)
    
    for item in products:
        try:
            p_id = item['productId']
            filename = f"posts/{datetime.now().strftime('%Y%m%d')}_{p_id}.html"
            if os.path.exists(filename): continue 
            
            print(f"📝 {item['productName'][:20]}... 장문 리뷰 작성 중")
            ai_content = generate_ai_content(item)
            
            img = item['productImage'].split('?')[0]
            price = format(item['productPrice'], ',')
            rocket_icon = "🚀 로켓배송" if item.get('isRocket') else ""
            
            with open(filename, "w", encoding="utf-8") as f:
                f.write(f"""<!DOCTYPE html><html lang='ko'>
                <head><meta charset='UTF-8'><meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>{item['productName']} 리뷰</title>
                <style>
                    body {{ font-family: sans-serif; background: #f8f9fa; padding: 20px; color: #333; line-height: 1.8; }}
                    .card {{ max-width: 650px; margin: auto; background: white; padding: 40px; border-radius: 30px; box-shadow: 0 20px 40px rgba(0,0,0,0.05); }}
                    .rocket {{ color: #0073e6; font-weight: bold; font-size: 0.9rem; }}
                    h2 {{ font-size: 1.3rem; margin-top: 15px; color: #111; border-bottom: 2px solid #f0f2f5; padding-bottom: 15px; }}
                    h3 {{ color: #e44d26; margin-top: 35px; border-left: 4px solid #e44d26; padding-left: 15px; font-size: 1.15rem; }}
                    img {{ width: 100%; border-radius: 20px; margin: 25px 0; }}
                    .price-box {{ text-align: center; background: #fff5f2; padding: 25px; border-radius: 20px; margin: 30px 0; }}
                    .current-price {{ font-size: 2.2rem; color: #e44d26; font-weight: bold; }}
                    .buy-btn {{ display: block; background: #e44d26; color: white; text-align: center; padding: 20px; text-decoration: none; border-radius: 50px; font-weight: bold; font-size: 1.2rem; }}
                </style></head>
                <body><div class='card'>
                    <div class='rocket'>{rocket_icon}</div>
                    <h2>{item['productName']}</h2>
                    <img src='{img}' alt='{item['productName']}'>
                    <div class='content'>{ai_content}</div>
                    <div class='price-box'><div class='current-price'>{price}원</div></div>
                    <a href='{item['productUrl']}' class='buy-btn'>🛍️ 최저가 확인 및 구매하기</a>
                    <p style='font-size: 0.75rem; color: #999; margin-top: 30px; text-align: center;'>본 포스팅은 쿠팡 파트너스 활동의 일환으로 수수료를 제공받을 수 있습니다.</p>
                </div></body></html>""")
            time.sleep(20) # 장문 작성을 위해 대기 시간을 살짝 늘렸습니다.
        except: continue

    # [인덱스 및 사이트맵 갱신 로직 동일]
    files = sorted([f for f in os.listdir("posts") if f.endswith(".html")], reverse=True)
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(f"<!DOCTYPE html><html lang='ko'><head><meta charset='UTF-8'><title>전문 핫딜 리뷰</title><style>body{{font-family:sans-serif; background:#f0f2f5; padding:20px;}} .grid{{display:grid; grid-template-columns:repeat(auto-fill, minmax(300px, 1fr)); gap:25px;}} .card{{background:white; padding:30px; border-radius:20px; text-decoration:none; color:#333; box-shadow:0 4px 15px rgba(0,0,0,0.05); height:140px; display:flex; flex-direction:column; justify-content:space-between;}} .title{{font-weight: bold; overflow: hidden; text-overflow: ellipsis; display: -webkit-box; -webkit-line-clamp: 3; -webkit-box-orient: vertical;}}</style></head><body><h1 style='text-align:center;'>🚀 실시간 핫딜 셔틀</h1><div class='grid'>")
        for file in files[:100]:
            try:
                with open(f"posts/{file}", 'r', encoding='utf-8') as fr:
                    content = fr.read()
                    title = re.search(r'<title>(.*?)</title>', content).group(1).replace(" 리뷰", "")
                f.write(f"<a class='card' href='posts/{file}'><div class='title'>{title[:50]}...</div><div style='color:#e44d26; font-weight:bold; font-size:0.85rem;'>상세 리뷰 보기 ></div></a>")
            except: continue
        f.write("</div></body></html>")
    
    with open("sitemap.xml", "w", encoding="utf-8") as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n')
        f.write(f'<url><loc>{SITE_URL}/</loc><priority>1.0</priority></url>\n')
        for file in files: f.write(f'<url><loc>{SITE_URL}/posts/{file}</loc><priority>0.8</priority></url>\n')
        f.write('</urlset>')

if __name__ == "__main__":
    main()
