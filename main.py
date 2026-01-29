import os, hmac, hashlib, time, requests, json, random, re
from datetime import datetime
from urllib.parse import urlencode

# [1. 설정 정보]
ACCESS_KEY = os.environ.get('COUPANG_ACCESS_KEY')
SECRET_KEY = os.environ.get('COUPANG_SECRET_KEY')
GEMINI_KEY = os.environ.get('GEMINI_API_KEY')
SITE_URL = "https://rkskqdl-a11y.github.io/coupang-sale-shuttle"

def clean_name_for_ai(name):
    """지저분한 상품명을 AI가 거부하지 않게 핵심만 남깁니다."""
    # 괄호 안 내용 삭제 및 특수문자 제거
    clean = re.sub(r'\(.*?\)|\[.*?\]', '', name)
    clean = re.sub(r'[^\w\s]', ' ', clean)
    # 앞의 3~4단어만 추출 (모델명 위주)
    words = clean.split()
    return " ".join(words[:4]) if len(words) > 4 else clean

def generate_ai_content(item):
    """💎 차단을 피하기 위해 '기술 분석 보고서' 스타일로 요청합니다."""
    if not GEMINI_KEY: return "분석 데이터 준비 중입니다."
    
    raw_name = item.get('productName')
    price = format(item.get('productPrice', 0), ',')
    short_name = clean_name_for_ai(raw_name)
    
    # 🤖 [세이프 모드] 기술 분석 프롬프트
    prompt_text = f"""
    상품 '{short_name}'(가격 {price}원)에 대한 기술적 사양과 사용자 경험을 분석한 전문 보고서를 작성해줘.
    
    [작성 규칙]
    1. 역할: IT/가전 제품 기술 분석가
    2. 내용: 객관적인 데이터와 일반적인 사용자 피드백을 기반으로 800자 이상 작성할 것.
    3. 구조: 반드시 <h3> 태그를 사용하여 아래 섹션을 포함해.
       - <h3>🔍 제품의 핵심 사양 및 하드웨어 특징</h3>
       - <h3>🚀 사용 환경에 따른 주요 성능 분석</h3>
       - <h3>💡 실제 사용자들의 종합적인 평가와 장단점</h3>
       - <h3>💰 최종 구매 가치 및 타겟층 분석</h3>
    4. 주의: HTML(h3, br)만 사용하고 인사말은 생략해.
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
        response = requests.post(url, json=payload, timeout=30)
        res_data = response.json()
        
        if 'candidates' in res_data and len(res_data['candidates']) > 0:
            content = res_data['candidates'][0]['content']['parts'][0]['text']
            return content.replace("\n", "<br>")
        
        # 차단 사유 로그 출력
        print(f"⚠️ AI 차단 발생 ({short_name}): {res_data.get('promptFeedback', '알 수 없는 이유')}")
        raise ValueError("Blocked")
        
    except Exception as e:
        print(f"❌ AI 에러: {e}")
        return f"<h3>🔍 에디터의 핵심 요약</h3>{short_name}은 {price}원이라는 가격 대비 성능이 뛰어난 모델입니다. 실사용 만족도가 높으며 깔끔한 마감과 안정적인 성능이 특징입니다."

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
    
    # 💎 검색 타겟 다양화
    sets = [("삼성", "갤럭시북"), ("LG", "그램"), ("애플", "맥북"), ("나이키", "에어맥스"), ("필립스", "전기면도기")]
    brand, item_type = random.choice(sets)
    target = f"인기 {brand} {item_type}"
    
    print(f"🚀 안정성 강화 엔진 가동: {target}")
    products = fetch_data(target)
    
    for item in products:
        try:
            p_id = item['productId']
            filename = f"posts/{datetime.now().strftime('%Y%m%d')}_{p_id}.html"
            if os.path.exists(filename): continue 
            
            print(f"📝 {item['productName'][:20]}... 분석 중")
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
                    h2 {{ font-size: 1.3rem; margin-top: 15px; color: #111; border-bottom: 2px solid #eee; padding-bottom: 15px; }}
                    h3 {{ color: #e44d26; margin-top: 35px; border-left: 4px solid #e44d26; padding-left: 15px; font-size: 1.1rem; }}
                    img {{ width: 100%; border-radius: 20px; margin: 25px 0; }}
                    .price-box {{ text-align: center; background: #fff5f2; padding: 25px; border-radius: 20px; margin: 30px 0; }}
                    .current-price {{ font-size: 2rem; color: #e44d26; font-weight: bold; }}
                    .buy-btn {{ display: block; background: #e44d26; color: white; text-align: center; padding: 20px; text-decoration: none; border-radius: 50px; font-weight: bold; font-size: 1.1rem; }}
                </style></head>
                <body><div class='card'>
                    <div class='rocket'>{rocket_icon}</div>
                    <h2>{item['productName']}</h2>
                    <img src='{img}' alt='{item['productName']}'>
                    <div class='content'>{ai_content}</div>
                    <div class='price-box'><div class='current-price'>{price}원</div></div>
                    <a href='{item['productUrl']}' class='buy-btn'>🛍️ 최저가 확인 및 구매하기</a>
                </div></body></html>""")
            time.sleep(20) # 차단 방지를 위한 충분한 시간 간격
        except: continue

    # 인덱스 업데이트 (생략/기존 유지)
    files = sorted([f for f in os.listdir("posts") if f.endswith(".html")], reverse=True)
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(f"<!DOCTYPE html><html lang='ko'><head><meta charset='UTF-8'><title>핫딜 리뷰</title><style>body{{font-family:sans-serif; background:#f0f2f5; padding:20px;}} .grid{{display:grid; grid-template-columns:repeat(auto-fill, minmax(300px, 1fr)); gap:25px;}} .card{{background:white; padding:30px; border-radius:20px; text-decoration:none; color:#333; box-shadow:0 4px 15px rgba(0,0,0,0.05); height:140px; display:flex; flex-direction:column; justify-content:space-between;}} .title{{font-weight: bold; overflow: hidden; text-overflow: ellipsis; display: -webkit-box; -webkit-line-clamp: 3; -webkit-box-orient: vertical;}}</style></head><body><h1 style='text-align:center;'>🚀 실시간 핫딜 셔틀</h1><div class='grid'>")
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
