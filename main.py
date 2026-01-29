import os, hmac, hashlib, time, requests, json, random, re
from datetime import datetime
from urllib.parse import urlencode

# [1. 설정]
ACCESS_KEY = os.environ.get('COUPANG_ACCESS_KEY')
SECRET_KEY = os.environ.get('COUPANG_SECRET_KEY')
GEMINI_KEY = os.environ.get('GEMINI_API_KEY')
# 본인의 GitHub Pages 주소를 정확히 입력하세요
SITE_URL = "https://rkskqdl-a11y.github.io/coupang-sale-shuttle"

def generate_ai_content(item):
    """💎 브랜드명을 숨기고 SEO 최적화된 HTML 콘텐츠를 생성합니다."""
    if not GEMINI_KEY: return "상세 분석 데이터를 불러오는 중입니다."
    
    name = item.get('productName')
    price = format(item.get('productPrice', 0), ',')
    
    # 브랜드 스텔스 처리: 주요 브랜드 키워드 제거 [사용자 요청 반영]
    clean_name = re.sub(r'나이키|NIKE|삼성|LG|애플|APPLE|샤오미|다이슨|나인봇', '', name, flags=re.I)
    short_name = " ".join(clean_name.split()[:4]).strip()
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_KEY}"
    
    # SEO를 위한 구체적인 페르소나와 구조 요청
    prompt = (
        f"당신은 IT/라이프스타일 전문 리뷰어입니다. 상품명 '{short_name}'(가격 {price}원)에 대해 리뷰를 작성하세요.\n"
        "1. 브랜드명은 절대 언급하지 말고 '이 모델' 또는 '해당 제품'으로 지칭하세요.\n"
        "2. <h3> 태그로 '세련된 디자인', '혁신적인 성능', '실제 사용 만족도' 섹션을 나누세요.\n"
        "3. 각 섹션은 2~3문장으로 전문적이고 친절한 해요체로 작성하세요.\n"
        "4. 마지막에 '추천 대상'을 불렛 포인트로 정리하세요. HTML 태그만 사용하세요."
    )
    
    try:
        payload = {"contents": [{"parts": [{"text": prompt}]}]}
        response = requests.post(url, json=payload, timeout=30)
        res_data = response.json()
        if 'candidates' in res_data:
            content = res_data['candidates']['content']['parts']['text']
            return content.replace("```html", "").replace("```", "").strip()
        return f"<h3>🔍 에디터 추천</h3>{short_name}은 현재 {price}원의 가격대에서 가장 탄탄한 기본기를 갖춘 모델입니다."
    except:
        return "전문적인 분석 데이터가 준비되었습니다."

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
        return response.json().get('data', {}).get('productData',)
    except: return

def main():
    os.makedirs("posts", exist_ok=True)
    # 자동화 시 다양한 카테고리를 공략하기 위한 키워드 셋
    keyword_pool = ["가성비 노트북", "인기 무선청소기", "캠핑 필수템", "자취생 추천 가전", "신상 운동화"]
    target_keyword = random.choice(keyword_pool)
    
    print(f"🚀 검색 엔진 가동: {target_keyword}")
    products = fetch_data(target_keyword)
    
    processed_count = 0
    for item in products:
        try:
            # 할인율 필터링 강화
            if item.get('discountRate', 0) < 5: continue 

            p_id = item['productId']
            filename = f"posts/{datetime.now().strftime('%Y%m%d')}_{p_id}.html"
            if os.path.exists(filename): continue 

            ai_content = generate_ai_content(item)
            img_url = item['productImage'].split('?')
            price = format(item['productPrice'], ',')
            
            # 구글 검색용 JSON-LD 구조화 데이터 추가
            json_ld = {
                "@context": "https://schema.org/",
                "@type": "Product",
                "name": item['productName'],
                "image": img_url,
                "offers": {
                    "@type": "Offer",
                    "price": item['productPrice'],
                    "priceCurrency": "KRW",
                    "availability": "https://schema.org/InStock"
                }
            }

            with open(filename, "w", encoding="utf-8") as f:
                f.write(f"""<!DOCTYPE html><html lang='ko'>
                <head><meta charset='UTF-8'><meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>{item['productName']} 상세 리뷰 및 가격 정보</title>
                <meta name="description" content="{item['productName']}의 성능, 디자인, 실사용 후기를 전문 에디터가 분석했습니다.">
                <script type="application/ld+json">{json.dumps(json_ld)}</script>
                <style>body{{font-family:'Apple SD Gothic Neo',sans-serif; background:#f4f7f6; padding:20px; color:#333; line-height:1.8;}}.card{{max-width:600px; margin:auto; background:white; padding:30px; border-radius:15px; box-shadow:0 10px 25px rgba(0,0,0,0.05);}} h2{{font-size:1.4rem; color:#222; margin-bottom:20px;}} h3{{color:#ff4d4d; margin-top:25px; border-left:5px solid #ff4d4d; padding-left:15px;}} img{{width:100%; border-radius:10px; margin:20px 0;}}.price-tag{{background:#fff0f0; padding:20px; text-align:center; border-radius:10px; margin:25px 0;}}.p-val{{font-size:2.2rem; color:#ff4d4d; font-weight:900;}}.buy-btn{{display:block; background:linear-gradient(to right, #ff4d4d, #ff8000); color:white; text-align:center; padding:20px; text-decoration:none; border-radius:50px; font-weight:bold; font-size:1.1rem;}}.disc{{font-size:0.7rem; color:#999; text-align:center; margin-top:30px;}}</style></head>
                <body><div class='card'><h2>{item['productName']}</h2><img src='{img_url}' alt='{item['productName']}'><div>{ai_content}</div><div class='price-tag'><div class='p-val'>{price}원</div></div><a href='{item['productUrl']}' class='buy-btn' target='_blank' rel='nofollow noopener'>🔥 특가 확인하고 구매하기</a><p class='disc'>파트너스 활동의 일환으로 일정액의 수수료를 제공받을 수 있습니다.</p></div></body></html>""")
            
            processed_count += 1
            time.sleep(35) # 제미나이 RPM(분당 호출수) 제한 준수
            if processed_count >= 10: break # 한 번에 너무 많은 포스팅 방지
        except: continue

    # 인덱스 및 사이트맵 자동 갱신 로직
    files = sorted([f for f in os.listdir("posts") if f.endswith(".html")], reverse=True)
    with open("index.html", "w", encoding="utf-8") as f:
        f.write("<!DOCTYPE html><html><head><meta charset='UTF-8'><title>실시간 핫딜 정보</title><style>body{font-family:sans-serif; background:#f0f2f5; padding:20px;}.grid{display:grid; grid-template-columns:repeat(auto-fill, minmax(280px, 1fr)); gap:20px;}.card{background:white; padding:20px; border-radius:15px; text-decoration:none; color:#333; box-shadow:0 4px 6px rgba(0,0,0,0.05); transition:0.3s;}.card:hover{transform:translateY(-5px);}</style></head><body><h1 style='text-align:center; color:#ff4d4d;'>🚀 핫딜 셔틀 리스트</h1><div class='grid'>")
        for file in files[:120]:
            f.write(f"<a class='card' href='posts/{file}'><div>{file[:8]} 추천상품</div><div style='color:#ff4d4d; font-size:0.8rem; margin-top:10px;'>상세보기 ></div></a>")
        f.write("</div></body></html>")

    # Sitemap.xml 자동 갱신
    with open("sitemap.xml", "w", encoding="utf-8") as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n')
        f.write(f'<url><loc>{SITE_URL}/</loc><priority>1.0</priority></url>\n')
        for file in files: f.write(f'<url><loc>{SITE_URL}/posts/{file}</loc></url>\n')
        f.write('</urlset>')

if __name__ == "__main__":
    main()
