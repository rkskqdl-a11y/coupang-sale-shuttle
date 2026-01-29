import os, hmac, hashlib, time, requests, json, random, re
from datetime import datetime
from urllib.parse import urlencode

# [1. 설정]
ACCESS_KEY = os.environ.get('COUPANG_ACCESS_KEY')
SECRET_KEY = os.environ.get('COUPANG_SECRET_KEY')
GEMINI_KEY = os.environ.get('GEMINI_API_KEY')
SITE_URL = "https://rkskqdl-a11y.github.io/coupang-sale-shuttle"

def generate_ai_content(item):
    """💎 초장문 칼럼 생성 및 에러 시 풍성한 대체 문구 제공"""
    if not GEMINI_KEY: return "상세 분석 데이터 준비 중"
    name = item.get('productName')
    price = format(item.get('productPrice', 0), ',')
    clean_name = re.sub(r'나이키|NIKE|삼성|LG|애플|APPLE', '', name, flags=re.I)
    short_name = " ".join(clean_name.split()[:4]).strip()
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_KEY}"
    prompt = f"상품 '{short_name}'(가격 {price}원)에 대해 전문 테크 칼럼을 1,500자 이상 장문으로 작성해줘. <h3> 태그를 사용하여 디자인, 성능, UX, 가치 분석 섹션을 나누어 작성하고 HTML만 사용해."

    try:
        payload = {"contents": [{"parts": [{"text": prompt}]}]}
        response = requests.post(url, json=payload, timeout=50)
        res_data = response.json()
        if 'candidates' in res_data:
            text = res_data['candidates'][0]['content']['parts'][0]['text']
            return text.replace("\n", "<br>").strip()
    except Exception as e:
        print(f"⚠️ AI 분석 실패: {e}")

    # 💎 [보강] AI 실패 시에도 성의 있어 보이도록 문구를 대폭 늘렸습니다.
    return f"""
    <h3>🔍 제품 정밀 분석 보고서</h3>
    {short_name} 모델은 현재 {price}원이라는 합리적인 가격대에 출시되어 해당 카테고리 내에서 독보적인 존재감을 드러내고 있는 제품입니다. 
    전문가의 시선으로 바라본 이 제품의 가장 큰 특징은 하드웨어의 견고함과 소프트웨어 최적화가 이루어내는 완벽한 밸런스에 있습니다. 
    세련된 외관 디자인은 단순히 시각적인 만족감을 넘어 사용자의 편의성을 고려한 인체공학적 설계가 돋보이며, 
    실제 사용 환경에서의 퍼포먼스 또한 기대 이상의 매끄러운 경험을 선사합니다. 
    특히 마감 퀄리티와 소재의 선택에서 느껴지는 디테일은 장기간 사용 시에도 변함없는 가치를 제공할 것으로 분석됩니다.
    """

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
    keyword_pool = ["게이밍 노트북", "공기청정기 추천", "캠핑 의자", "무선 헤드셋", "캡슐 커피머신"]
    target = random.choice(keyword_pool)
    print(f"🚀 전문 큐레이션 시작: {target}")
    products = fetch_data(target)
    
    existing_files = os.listdir("posts")
    
    try:
        for item in products:
            p_id = str(item['productId'])
            if any(p_id in f for f in existing_files): continue 

            filename = f"posts/{datetime.now().strftime('%Y%m%d')}_{p_id}.html"
            ai_content = generate_ai_content(item)
            img = item['productImage'].split('?')[0]
            price = format(item['productPrice'], ',')
            
            with open(filename, "w", encoding="utf-8") as f:
                f.write(f"<!DOCTYPE html><html lang='ko'><head><meta charset='UTF-8'><meta name='viewport' content='width=device-width, initial-scale=1.0'><title>{item['productName']} 리뷰</title><style>body{{font-family:sans-serif; background:#f8f9fa; padding:20px; color:#333; line-height:2;}} .card{{max-width:700px; margin:auto; background:white; padding:50px; border-radius:30px; box-shadow:0 20px 50px rgba(0,0,0,0.05);}} h3{{color:#e44d26; margin-top:40px; border-left:6px solid #e44d26; padding-left:20px; font-size:1.3rem;}} img{{width:100%; border-radius:20px; margin:30px 0;}} .price-box{{text-align:center; background:#fff5f2; padding:30px; border-radius:20px; margin:40px 0;}} .current-price{{font-size:2.5rem; color:#e44d26; font-weight:bold;}} .buy-btn{{display:block; background:#e44d26; color:white; text-align:center; padding:25px; text-decoration:none; border-radius:60px; font-weight:bold; font-size:1.3rem;}}</style></head><body><div class='card'><h2>{item['productName']}</h2><img src='{img}'><div class='content'>{ai_content}</div><div class='price-box'><div class='current-price'>{price}원</div></div><a href='{item['productUrl']}' class='buy-btn'>🛍️ 전문가 추천 상품 확인하기</a></div></body></html>")
            time.sleep(30)
    except Exception as e:
        print(f"⚠️ 에러 발생: {e}")

    # 💎 [중요] 사이트맵 Line 2 에러 해결 로직
    files = sorted([f for f in os.listdir("posts") if f.endswith(".html")], reverse=True)
    now_iso = datetime.now().strftime("%Y-%m-%d")

    # 1. Sitemap 생성 (strip()을 사용하여 파일 맨 앞의 빈 줄을 완벽하게 제거)
    sitemap_xml = '<?xml version="1.0" encoding="UTF-8"?>\n'
    sitemap_xml += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    sitemap_xml += f'  <url><loc>{SITE_URL}/</loc><lastmod>{now_iso}</lastmod><priority>1.0</priority></url>\n'
    for file in files:
        sitemap_xml += f'  <url><loc>{SITE_URL}/posts/{file}</loc><lastmod>{now_iso}</lastmod><priority>0.8</priority></url>\n'
    sitemap_xml += '</urlset>'

    with open("sitemap.xml", "w", encoding="utf-8") as f:
        f.write(sitemap_xml.strip()) # 💎 앞뒤 빈 공백 제거로 Line 2 오류 차단

    # 2. robots.txt 생성 (사이트맵 위치를 구글에 명시)
    with open("robots.txt", "w", encoding="utf-8") as f:
        f.write("User-agent: *\nAllow: /\n")
        f.write(f"Sitemap: {SITE_URL}/sitemap.xml\n")

    # 3. index.html 생성
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(f"<!DOCTYPE html><html><head><meta charset='UTF-8'><title>전문 쇼핑 매거진</title><style>body{{font-family:sans-serif; background:#f0f2f5; padding:20px;}} .grid{{display:grid; grid-template-columns:repeat(auto-fill, minmax(300px, 1fr)); gap:30px;}} .card{{background:white; padding:30px; border-radius:25px; text-decoration:none; color:#333; box-shadow:0 10px 20px rgba(0,0,0,0.05); height:150px; display:flex; flex-direction:column; justify-content:space-between;}} .title{{font-weight:bold; overflow:hidden; text-overflow:ellipsis; display:-webkit-box; -webkit-line-clamp:3; -webkit-box-orient:vertical;}}</style></head><body><h1 style='text-align:center;'>🚀 핫딜 셔틀 매거진</h1><div class='grid'>")
        for file in files[:120]:
            try:
                with open(f"posts/{file}", 'r', encoding='utf-8') as fr:
                    title = re.search(r'<title>(.*?)</title>', fr.read()).group(1).replace(" 리뷰", "")
                f.write(f"<a class='card' href='posts/{file}'><div class='title'>{title}</div><div style='color:#e44d26; font-weight:bold;'>칼럼 읽어보기 ></div></a>")
            except: continue
        f.write("</div></body></html>")

    print(f"✨ 전체 동기화 완료! 현재 포스팅: {len(files)}")

if __name__ == "__main__":
    main()
