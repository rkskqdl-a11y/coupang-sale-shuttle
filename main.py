import os, hmac, hashlib, time, requests, json, random, re
from datetime import datetime
from urllib.parse import urlencode

# [1. 설정 정보]
ACCESS_KEY = os.environ.get('COUPANG_ACCESS_KEY', '').strip()
SECRET_KEY = os.environ.get('COUPANG_SECRET_KEY', '').strip()
GEMINI_KEY = os.environ.get('GEMINI_API_KEY', '').strip()
SITE_URL = "https://rkskqdl-a11y.github.io/coupang-sale-shuttle"

def generate_ai_content(item):
    """💎 제미나이 Pro 1.5를 활용한 1,500자 이상의 고품질 칼럼 생성"""
    if not GEMINI_KEY: return "상세 분석 데이터 준비 중"
    name = item.get('productName')
    price = format(item.get('productPrice', 0), ',')
    clean_name = re.sub(r'나이키|NIKE|삼성|LG|애플|APPLE', '', name, flags=re.I)
    short_name = " ".join(clean_name.split()[:4]).strip()
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_KEY}"
    prompt = f"상품 '{short_name}'(가격 {price}원)에 대해 전문 테크/리뷰 칼럼을 1,500자 이상 장문으로 작성해줘. <h3> 태그를 사용하고 HTML만 사용해. '할인' 언급 절대 금지."

    try:
        payload = {"contents": [{"parts": [{"text": prompt}]}]}
        response = requests.post(url, json=payload, timeout=60)
        res_data = response.json()
        if 'candidates' in res_data and len(res_data['candidates']) > 0:
            return res_data['candidates'][0]['content']['parts'][0]['text'].replace("\n", "<br>").strip()
    except: pass
    return f"<h3>🔍 전문가 분석</h3>{short_name}은 {price}원대에서 만날 수 있는 최상의 선택입니다."

def fetch_data_with_paging(keyword):
    """💎 상품이 발견될 때까지 랜덤 페이지를 뒤져 전수 조사를 수행합니다."""
    DOMAIN = "https://api-gateway.coupang.com"
    path = "/v2/providers/affiliate_open_api/apis/openapi/v1/products/search"
    
    # 1~50페이지 중 5개를 무작위로 골라 순차적으로 탐색합니다.
    target_pages = random.sample(range(1, 51), 5)
    
    for page in target_pages:
        try:
            params = {"keyword": keyword, "limit": 20, "page": page}
            query_string = urlencode(params)
            url = f"{DOMAIN}{path}?{query_string}"
            headers = {"Authorization": get_authorization_header("GET", path, query_string), "Content-Type": "application/json"}
            response = requests.get(url, headers=headers, timeout=15)
            products = response.json().get('data', {}).get('productData', [])
            
            if products:
                print(f"✅ [{keyword}] 검색 - 페이지 {page}에서 상품 발견!")
                return products
        except: continue
    return []

def get_authorization_header(method, path, query_string):
    datetime_gmt = time.strftime('%y%m%dT%H%M%SZ', time.gmtime())
    message = datetime_gmt + method + path + query_string
    signature = hmac.new(bytes(SECRET_KEY, 'utf-8'), msg=bytes(message, 'utf-8'), digestmod=hashlib.sha256).hexdigest()
    return f"CEA algorithm=HmacSHA256, access-key={ACCESS_KEY}, signed-date={datetime_gmt}, signature={signature}"

def main():
    os.makedirs("posts", exist_ok=True)
    
    # 💎 [일반 키워드 풀] 상품군이 수만 개에 달하는 대표 명사 위주
    keyword_pool = [
        "린넨셔츠", "세탁기", "가습기", "노트북", "청소기", "공기청정기", "커피머신", "운동화", "캠핑의자", 
        "단백질보충제", "선크림", "면도기", "블루투스이어폰", "모니터", "키보드", "침대매트리스", "프라이팬"
    ]
    
    target = random.choice(keyword_pool)
    print(f"🚀 일반 카테고리 전수 조사 시작: {target}")
    
    products = fetch_data_with_paging(target)
    # 중복 체크 효율화를 위한 Set 구성
    existing_ids = {f.split('_')[-1].replace('.html', '') for f in os.listdir("posts") if '_' in f}
    
    success_count = 0
    for item in products:
        try:
            p_id = str(item['productId'])
            if p_id in existing_ids: continue # 이미 올린 상품이면 패스

            filename = f"posts/{datetime.now().strftime('%Y%m%d')}_{p_id}.html"
            ai_content = generate_ai_content(item)
            img = item['productImage'].split('?')[0]
            price = format(item['productPrice'], ',')
            
            with open(filename, "w", encoding="utf-8") as f:
                f.write(f"<!DOCTYPE html><html lang='ko'><head><meta charset='UTF-8'><meta name='viewport' content='width=device-width, initial-scale=1.0'><title>{item['productName']} 리뷰</title><style>body{{font-family:sans-serif; background:#f8f9fa; padding:20px; color:#333; line-height:2.2;}} .card{{max-width:700px; margin:auto; background:white; padding:50px; border-radius:30px; box-shadow:0 20px 50px rgba(0,0,0,0.05);}} h3{{color:#e44d26; margin-top:40px; border-left:6px solid #e44d26; padding-left:20px;}} img{{width:100%; border-radius:20px; margin:30px 0;}} .price-box{{text-align:center; background:#fff5f2; padding:30px; border-radius:20px; margin:40px 0;}} .p-val{{font-size:2.5rem; color:#e44d26; font-weight:bold;}} .buy-btn{{display:block; background:#e44d26; color:white; text-align:center; padding:25px; text-decoration:none; border-radius:60px; font-weight:bold; font-size:1.3rem;}}</style></head><body><div class='card'><h2>{item['productName']}</h2><img src='{img}'><div class='content'>{ai_content}</div><div class='price-box'><div class='p-val'>{price}원</div></div><a href='{item['productUrl']}' class='buy-btn'>🛍️ 상세 정보 확인하기</a></div></body></html>")
            
            success_count += 1
            print(f"✅ 포스팅 생성 완료 ({success_count}/10): {p_id}")
            time.sleep(35) # Gemini 및 Coupang API 할당량 준수
            if success_count >= 10: break
        except: continue

    # 💎 [SEO 동기화] 새로운 글이 없더라도 사이트맵과 인덱스는 무조건 갱신
    files = sorted([f for f in os.listdir("posts") if f.endswith(".html")], reverse=True)
    now_iso = datetime.now().strftime("%Y-%m-%d")

    # 사이트맵 네임스페이스 오류 해결
    sitemap_xml = '<?xml version="1.0" encoding="UTF-8"?>\n'
    sitemap_xml += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    sitemap_xml += f'  <url><loc>{SITE_URL}/</loc><lastmod>{now_iso}</lastmod><priority>1.0</priority></url>\n'
    for file in files:
        sitemap_xml += f'  <url><loc>{SITE_URL}/posts/{file}</loc><lastmod>{now_iso}</lastmod></url>\n'
    sitemap_xml += '</urlset>'
    with open("sitemap.xml", "w", encoding="utf-8") as f: f.write(sitemap_xml.strip())

    with open("robots.txt", "w", encoding="utf-8") as f:
        f.write(f"User-agent: *\nAllow: /\nSitemap: {SITE_URL}/sitemap.xml\n")

    # index.html (진짜 상품명 추출 및 갱신)
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(f"<!DOCTYPE html><html lang='ko'><head><meta charset='UTF-8'><title>전문 쇼핑 매거진</title><style>body{{font-family:sans-serif; background:#f0f2f5; padding:20px;}} .grid{{display:grid; grid-template-columns:repeat(auto-fill, minmax(300px, 1fr)); gap:30px;}} .card{{background:white; padding:30px; border-radius:25px; text-decoration:none; color:#333; box-shadow:0 10px 20px rgba(0,0,0,0.05); height:150px; display:flex; flex-direction:column; justify-content:space-between;}} .title{{font-weight:bold; overflow:hidden; text-overflow:ellipsis; display:-webkit-box; -webkit-line-clamp:3; -webkit-box-orient:vertical; font-size:0.9rem;}}</style></head><body><h1 style='text-align:center;'>🚀 카테고리 전수 조사 매거진</h1><div class='grid'>")
        for file in files[:120]:
            try:
                with open(f"posts/{file}", 'r', encoding='utf-8') as fr:
                    content = fr.read()
                    match = re.search(r'<title>(.*?)</title>', content)
                    title = match.group(1).replace(" 리뷰", "") if match else file
                f.write(f"<a class='card' href='posts/{file}'><div class='title'>{title}</div><div style='color:#e44d26; font-weight:bold;'>칼럼 읽기 ></div></a>")
            except: continue
        f.write("</div></body></html>")
    
    print(f"✨ 전체 동기화 완료! 현재 포스팅 수: {len(files)}")

if __name__ == "__main__":
    main()
