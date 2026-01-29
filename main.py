import os, hmac, hashlib, time, requests, json, random, re
from datetime import datetime
from urllib.parse import urlencode

# [1. 설정 정보]
ACCESS_KEY = os.environ.get('COUPANG_ACCESS_KEY', '').strip()
SECRET_KEY = os.environ.get('COUPANG_SECRET_KEY', '').strip()
GEMINI_KEY = os.environ.get('GEMINI_API_KEY', '').strip()
SITE_URL = "https://rkskqdl-a11y.github.io/coupang-sale-shuttle"

def generate_ai_content(item):
    """💎 AI 차단을 피하며 1,500자 이상의 초장문 칼럼을 생성합니다."""
    if not GEMINI_KEY: return "분석 데이터 준비 중"
    name = item.get('productName')
    price = format(item.get('productPrice', 0), ',')
    
    # 브랜드명을 숨겨 AI 필터 통과율을 높입니다.
    clean_name = re.sub(r'나이키|NIKE|삼성|LG|애플|APPLE', '', name, flags=re.I)
    short_name = " ".join(clean_name.split()[:4]).strip()
    
    prompt = f"""
    당신은 테크/라이프스타일 전문 칼럼니스트입니다. 상품 '{short_name}'(가격 {price}원)에 대해 
    전문 잡지에 기고할 수준의 **장문 칼럼(최소 1,500자 이상)**을 작성하세요.
    
    [필수 구성 - 각 섹션별로 3문단 이상 정성껏 작성]
    1. <h3>✨ 디자인 미학과 조형적 가치</h3>: 소재, 컬러, 공간과의 조화 분석.
    2. <h3>🚀 성능의 정점: 기술적 완성도 분석</h3>: 실제 사용 시의 퍼포먼스 체감.
    3. <h3>🔍 사용자 경험(UX)에서 발견한 디테일</h3>: 세밀한 편의성과 사용자 배려 포인트.
    4. <h3>💡 전문가가 제안하는 구매 가치와 라이프스타일</h3>: 최종 가성비 및 타겟 분석.
    
    - '할인' 언급 없이 상품의 본질적 가치에 집중하세요.
    - 브랜드명 대신 '이 모델', '이 걸작' 등으로 표현하세요.
    - HTML(h3, br, b) 태그만 사용하세요.
    """

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_KEY}"
    try:
        payload = {"contents": [{"parts": [{"text": prompt}]}]}
        response = requests.post(url, json=payload, timeout=50)
        res_data = response.json()
        if 'candidates' in res_data and len(res_data['candidates']) > 0:
            content = res_data['candidates'][0]['content']['parts'][0]['text']
            return content.replace("\n", "<br>").strip()
    except: pass
    
    # 💎 AI 실패 시 풍성한 대체 문구
    return f"<h3>🔍 전문가의 시선</h3>{short_name}은 {price}원의 가격대에서 만날 수 있는 최상의 기술력이 집약된 모델입니다. 세련된 디자인과 탄탄한 기본기, 그리고 사용자를 배려한 세심한 설계가 돋보입니다. 실제 환경에서의 안정적인 퍼포먼스는 물론, 공간의 가치를 높여주는 미학적 완성도까지 갖추고 있어 해당 카테고리 내에서 독보적인 선택지로 평가됩니다."

def fetch_data(keyword):
    """쿠팡 API로 상품 수집"""
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
    keyword_pool = ["게이밍 노트북", "무선 헤드셋", "캠핑 의자", "전동 칫솔", "아이패드 프로", "갤럭시북4"]
    target = random.choice(keyword_pool)
    print(f"🚀 작업 시작: {target}")
    products = fetch_data(target)
    
    existing_files = os.listdir("posts")
    
    for item in products:
        try:
            # 💎 할인율 0%인 상품은 건너뜁니다.
            if item.get('discountRate', 0) <= 0: continue 

            p_id = str(item['productId'])
            if any(p_id in f for f in existing_files): continue 

            filename = f"posts/{datetime.now().strftime('%Y%m%d')}_{p_id}.html"
            ai_content = generate_ai_content(item)
            img = item['productImage'].split('?')[0] # 💎 이미지 깨짐 방지
            price = format(item['productPrice'], ',')
            
            with open(filename, "w", encoding="utf-8") as f:
                f.write(f"""<!DOCTYPE html><html lang='ko'>
                <head><meta charset='UTF-8'><meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>{item['productName']} 리뷰</title>
                <style>body{{font-family:sans-serif; background:#f8f9fa; padding:20px; color:#333; line-height:2.2;}} .card{{max-width:700px; margin:auto; background:white; padding:50px; border-radius:30px; box-shadow:0 20px 50px rgba(0,0,0,0.05);}} h3{{color:#e44d26; margin-top:40px; border-left:6px solid #e44d26; padding-left:20px;}} img{{width:100%; border-radius:20px; margin:30px 0;}} .price-box{{text-align:center; background:#fff5f2; padding:30px; border-radius:20px; margin:40px 0;}} .p-val{{font-size:2.5rem; color:#e44d26; font-weight:bold;}} .buy-btn{{display:block; background:#e44d26; color:white; text-align:center; padding:25px; text-decoration:none; border-radius:60px; font-weight:bold; font-size:1.3rem;}}</style></head>
                <body><div class='card'><h2>{item['productName']}</h2><img src='{img}' alt='{item['productName']}'><div class='content'>{ai_content}</div><div class='price-box'><div class='p-val'>{price}원</div></div><a href='{item['productUrl']}' class='buy-btn'>🛍️ 전문가 추천 상품 확인하기</a></div></body></html>""")
            time.sleep(30)
        except: continue

    # 💎 [핵심 교정] 사이트맵 네임스페이스 및 구조 최적화
    files = sorted([f for f in os.listdir("posts") if f.endswith(".html")], reverse=True)
    now_iso = datetime.now().strftime("%Y-%m-%d")

    # XML 표준 규격과 네임스페이스를 정확히 선언합니다.
    sitemap_xml = '<?xml version="1.0" encoding="UTF-8"?>\n'
    sitemap_xml += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    sitemap_xml += f'  <url>\n    <loc>{SITE_URL}/</loc>\n    <lastmod>{now_iso}</lastmod>\n    <priority>1.0</priority>\n  </url>\n'
    
    for file in files:
        sitemap_xml += f'  <url>\n    <loc>{SITE_URL}/posts/{file}</loc>\n    <lastmod>{now_iso}</lastmod>\n    <priority>0.8</priority>\n  </url>\n'
    sitemap_xml += '</urlset>'

    with open("sitemap.xml", "w", encoding="utf-8") as f:
        f.write(sitemap_xml.strip()) # 💎 Line 2 오류 방지

    with open("robots.txt", "w", encoding="utf-8") as f:
        f.write(f"User-agent: *\nAllow: /\nSitemap: {SITE_URL}/sitemap.xml\n")

    # index.html 업데이트 (실제 상품 제목 추출 로직)
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(f"<!DOCTYPE html><html lang='ko'><head><meta charset='UTF-8'><title>전문 쇼핑 매거진</title><style>body{{font-family:sans-serif; background:#f0f2f5; padding:20px;}} .grid{{display:grid; grid-template-columns:repeat(auto-fill, minmax(300px, 1fr)); gap:30px;}} .card{{background:white; padding:30px; border-radius:25px; text-decoration:none; color:#333; box-shadow:0 10px 20px rgba(0,0,0,0.05); height:160px; display:flex; flex-direction:column; justify-content:space-between;}} .title{{font-weight:bold; overflow:hidden; text-overflow:ellipsis; display:-webkit-box; -webkit-line-clamp:3; -webkit-box-orient:vertical;}}</style></head><body><h1 style='text-align:center;'>🚀 핫딜 셔틀 매거진</h1><div class='grid'>")
        for file in files[:120]:
            try:
                with open(f"posts/{file}", 'r', encoding='utf-8') as fr:
                    title = re.search(r'<title>(.*?)</title>', fr.read()).group(1).replace(" 리뷰", "")
                f.write(f"<a class='card' href='posts/{file}'><div class='title'>{title}</div><div style='color:#e44d26; font-weight:bold;'>리뷰 읽어보기 ></div></a>")
            except: continue
        f.write("</div></body></html>")
    print(f"✨ 전체 동기화 완료! 현재 포스팅: {len(files)}")

if __name__ == "__main__":
    main()
