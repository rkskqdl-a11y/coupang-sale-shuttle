import os, hmac, hashlib, time, requests, json, random, re
from datetime import datetime
from urllib.parse import urlencode

# [1. 설정]
ACCESS_KEY = os.environ.get('COUPANG_ACCESS_KEY')
SECRET_KEY = os.environ.get('COUPANG_SECRET_KEY')
GEMINI_KEY = os.environ.get('GEMINI_API_KEY')
SITE_URL = "https://rkskqdl-a11y.github.io/coupang-sale-shuttle"

def generate_ai_content(product_name, price):
    """💎 안전 필터 차단을 방지하고, 실패 시에도 상품명을 지킵니다."""
    if not GEMINI_KEY: return "상세 정보를 분석 중입니다."
    
    # AI가 헷갈리지 않게 상품명을 핵심만 추출
    short_name = " ".join(re.sub(r'[^\w\s]', '', product_name).split()[:3])
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_KEY}"
    headers = {'Content-Type': 'application/json'}
    
    payload = {
        "contents": [{"parts": [{"text": f"너는 쇼핑 가이드야. '{short_name}'({price}원) 제품에 대해 장점 3가지를 포함한 400자 내외 리뷰를 써줘. 제목이나 인사말은 생략하고 <h3> 태그로 시작해줘. HTML(h3, br)만 사용해."}]}],
        "safetySettings": [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"}
        ]
    }

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=20)
        res_data = response.json()
        
        # 💎 답변 추출 및 검증
        if 'candidates' in res_data and len(res_data['candidates']) > 0:
            candidate = res_data['candidates'][0]
            if 'content' in candidate:
                return candidate['content']['parts'][0]['text'].replace("\n", "<br>")
        
        # 💎 AI가 거부했을 때의 다이나믹 비상 문구 (상품명을 반드시 포함!)
        return f"<h3>🔍 에디터 추천 이유</h3>{short_name}은 현재 {price}원이라는 합리적인 가격대에 만날 수 있는 최고의 선택입니다. 품질과 디자인 모두 만족스러운 제품입니다."
            
    except Exception as e:
        print(f"❌ AI 통신 실패: {e}")
        return f"<h3>🛍️ 상품 특징 안내</h3>{short_name} 제품의 상세 특징과 최저가 정보를 확인해보세요. 뛰어난 가성비를 자랑하는 추천 상품입니다."

def get_title_from_html(filepath):
    """파일 내부의 진짜 상품명을 추출하여 메인에 표시합니다."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            match = re.search(r'<title>(.*?)</title>', content)
            if match:
                return match.group(1).replace(" 리뷰", "").strip()
    except: pass
    return "상품 상세 정보"

def fetch_data(keyword):
    try:
        DOMAIN = "https://api-gateway.coupang.com"
        path = "/v2/providers/affiliate_open_api/apis/openapi/v1/products/search"
        params = {"keyword": keyword, "limit": 10}
        query_string = urlencode(params)
        url = f"{DOMAIN}{path}?{query_string}"
        headers = {"Authorization": get_authorization_header("GET", path, query_string), "Content-Type": "application/json"}
        response = requests.get(url, headers=headers, timeout=15)
        return response.json().get('data', {}).get('productData', [])
    except: return []

def get_authorization_header(method, path, query_string):
    datetime_gmt = time.strftime('%y%m%dT%H%M%SZ', time.gmtime())
    message = datetime_gmt + method + path + query_string
    signature = hmac.new(bytes(SECRET_KEY, 'utf-8'), msg=bytes(message, 'utf-8'), digestmod=hashlib.sha256).hexdigest()
    return f"CEA algorithm=HmacSHA256, access-key={ACCESS_KEY}, signed-date={datetime_gmt}, signature={signature}"

def main():
    os.makedirs("posts", exist_ok=True)
    
    # 💎 논리적인 키워드 조합 생성 (아디다스 노트북 방지)
    sets = [
        ("삼성", "노트북"), ("LG", "그램"), ("애플", "아이패드"),
        ("나이키", "운동화"), ("아디다스", "런닝화"), ("다이슨", "청소기")
    ]
    brand, item_type = random.choice(sets)
    target = f"{random.choice(['추천', '인기'])} {brand} {item_type}"
    
    print(f"🚀 최적화 검색 가동: {target}")
    products = fetch_data(target)
    
    for item in products:
        try:
            p_id = item['productId']
            clean_img_url = item['productImage'].split('?')[0]
            price_str = format(item['productPrice'], ',')
            filename = f"posts/{datetime.now().strftime('%Y%m%d')}_{p_id}.html"
            
            if os.path.exists(filename): continue 
            
            ai_content = generate_ai_content(item['productName'], price_str)
            
            with open(filename, "w", encoding="utf-8") as f:
                f.write(f"""<!DOCTYPE html><html lang='ko'>
                <head><meta charset='UTF-8'><meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>{item['productName']} 리뷰</title>
                <style>
                    body {{ font-family: sans-serif; background: #f4f7f6; padding: 20px; line-height: 1.8; color: #333; }}
                    .card {{ max-width: 600px; margin: auto; background: white; padding: 40px; border-radius: 20px; box-shadow: 0 10px 20px rgba(0,0,0,0.05); }}
                    h2 {{ font-size: 1.2rem; color: #222; margin-bottom: 25px; border-left: 5px solid #e44d26; padding-left: 15px; border-bottom: 1px solid #eee; padding-bottom: 10px; }}
                    h3 {{ color: #e44d26; margin-top: 30px; font-size: 1.1rem; }}
                    img {{ width: 100%; border-radius: 15px; margin: 20px 0; }}
                    .price {{ font-size: 1.8rem; color: #e44d26; font-weight: bold; text-align: center; margin: 30px 0; }}
                    .buy-btn {{ display: block; background: #e44d26; color: white; text-align: center; padding: 18px; text-decoration: none; border-radius: 50px; font-weight: bold; font-size: 1.1rem; }}
                </style></head>
                <body><div class='card'>
                    <h2>{item['productName']}</h2>
                    <img src='{clean_img_url}' alt='{item['productName']}'>
                    <div class='content'>{ai_content}</div>
                    <div class='price'>{price_str}원</div>
                    <a href='{item['productUrl']}' class='buy-btn'>🛍️ 최저가 확인 및 구매하기</a>
                    <p style='font-size: 0.75rem; color: #999; margin-top: 30px; text-align: center;'>본 포스팅은 쿠팡 파트너스 활동의 일환으로 수수료를 제공받을 수 있습니다.</p>
                </div></body></html>""")
            time.sleep(35)
        except: continue

    # [인덱스 페이지 생성]
    files = sorted([f for f in os.listdir("posts") if f.endswith(".html")], reverse=True)
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(f"<!DOCTYPE html><html><head><meta charset='UTF-8'><title>핫딜 셔틀</title><style>body{{font-family:sans-serif; background:#f0f2f5; padding:20px;}} .grid{{display:grid; grid-template-columns:repeat(auto-fill, minmax(280px, 1fr)); gap:20px;}} .card{{background:white; padding:25px; border-radius:15px; text-decoration:none; color:#333; box-shadow:0 2px 10px rgba(0,0,0,0.05); height: 150px; display: flex; flex-direction: column; justify-content: space-between;}} .title{{font-weight: bold; font-size: 0.85rem; overflow: hidden; text-overflow: ellipsis; display: -webkit-box; -webkit-line-clamp: 3; -webkit-box-orient: vertical; color:#222;}}</style></head><body><h1 style='text-align:center;'>🚀 실시간 핫딜 쇼핑몰</h1><div class='grid'>")
        for file in files[:100]:
            # 💎 파일 내부의 진짜 상품명을 가져와서 메인에 뿌립니다.
            real_name = get_title_from_html(f"posts/{file}")
            f.write(f"<a class='card' href='posts/{file}'><div class='title'>{real_name}</div><div style='color:#e44d26; font-size:0.75rem;'>상세 리뷰 보기 ></div></a>")
        f.write("</div></body></html>")
    
    # 사이트맵 및 로봇 파일 갱신
    with open("sitemap.xml", "w", encoding="utf-8") as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n')
        f.write(f'<url><loc>{SITE_URL}/</loc><priority>1.0</priority></url>\n')
        for file in files: f.write(f'<url><loc>{SITE_URL}/posts/{file}</loc><priority>0.8</priority></url>\n')
        f.write('</urlset>')
    with open("robots.txt", "w", encoding="utf-8") as f:
        f.write(f"User-agent: *\nAllow: /\nSitemap: {SITE_URL}/sitemap.xml")

if __name__ == "__main__":
    main()
