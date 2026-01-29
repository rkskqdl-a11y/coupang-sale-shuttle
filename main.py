import os, hmac, hashlib, time, requests, json, random, re
from datetime import datetime
from urllib.parse import urlencode

# [1. 설정 정보]
ACCESS_KEY = os.environ.get('COUPANG_ACCESS_KEY', '').strip()
SECRET_KEY = os.environ.get('COUPANG_SECRET_KEY', '').strip()
GEMINI_KEY = os.environ.get('GEMINI_API_KEY', '').strip()
SITE_URL = "https://rkskqdl-a11y.github.io/coupang-sale-shuttle"

def generate_ai_content(item):
    """💎 제미나이 Pro를 활용한 1,500자 이상의 초장문 칼럼 생성"""
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

def fetch_data(keyword, page):
    """💎 특정 키워드와 페이지에서 상품 수집"""
    try:
        DOMAIN = "https://api-gateway.coupang.com"
        path = "/v2/providers/affiliate_open_api/apis/openapi/v1/products/search"
        params = {"keyword": keyword, "limit": 25, "page": page}
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
    
    # 💎 [끝장 추적용 광폭 키워드] 브랜드와 카테고리를 조합하여 중복을 피합니다.
    brands = ["삼성", "LG", "위니아", "샤오미", "나이키", "아디다스", "필립스", "테팔", "로지텍"]
    items = ["세탁기", "건조기", "린넨셔츠", "가습기", "노트북", "운동화", "모니터", "에어프라이어", "마우스"]
    
    success_count = 0
    max_target = 10 # 💎 이번 실행에서 무조건 새로 만들 목표 수량
    
    # 기존 상품 ID 리스트를 미리 확보
    existing_ids = {f.split('_')[-1].replace('.html', '') for f in os.listdir("posts") if '_' in f}
    
    print(f"🕵️ 현재 포스팅 수: {len(existing_ids)}개. 목표: 새 상품 {max_target}개 찾기")
    
    # 💎 목표를 채울 때까지 무한 반복 (최대 20번 시도)
    for attempt in range(20):
        if success_count >= max_target: break
        
        target_keyword = f"{random.choice(brands)} {random.choice(items)}"
        random_page = random.randint(1, 50)
        print(f"🔄 [{attempt+1}차 시도] 키워드: {target_keyword} / 페이지: {random_page}")
        
        products = fetch_data(target_keyword, random_page)
        
        for item in products:
            p_id = str(item['productId'])
            if p_id in existing_ids:
                continue # 이미 있는 건 무시

            # 💎 신규 상품 발견 시 포스팅 생성
            filename = f"posts/{datetime.now().strftime('%Y%m%d')}_{p_id}.html"
            ai_content = generate_ai_content(item)
            img = item['productImage'].split('?')[0]
            price = format(item['productPrice'], ',')
            
            with open(filename, "w", encoding="utf-8") as f:
                f.write(f"<!DOCTYPE html><html lang='ko'><head><meta charset='UTF-8'><meta name='viewport' content='width=device-width, initial-scale=1.0'><title>{item['productName']} 리뷰</title><style>body{{font-family:sans-serif; background:#f8f9fa; padding:20px; color:#333; line-height:2.2;}} .card{{max-width:700px; margin:auto; background:white; padding:50px; border-radius:30px; box-shadow:0 20px 50px rgba(0,0,0,0.05);}} h3{{color:#e44d26; margin-top:40px; border-left:6px solid #e44d26; padding-left:20px;}} img{{width:100%; border-radius:20px; margin:30px 0;}} .price-box{{text-align:center; background:#fff5f2; padding:30px; border-radius:20px; margin:40px 0;}} .p-val{{font-size:2.5rem; color:#e44d26; font-weight:bold;}} .buy-btn{{display:block; background:#e44d26; color:white; text-align:center; padding:25px; text-decoration:none; border-radius:60px; font-weight:bold; font-size:1.3rem;}}</style></head><body><div class='card'><h2>{item['productName']}</h2><img src='{img}'><div class='content'>{ai_content}</div><div class='price-box'><div class='p-val'>{price}원</div></div><a href='{item['productUrl']}' class='buy-btn'>🛍️ 상세 정보 확인하기</a></div></body></html>")
            
            existing_ids.add(p_id)
            success_count += 1
            print(f"   ✅ 신규 생성 ({success_count}/{max_target}): {p_id}")
            time.sleep(30) # API 안정성 확보
            
            if success_count >= max_target: break

    # 💎 [SEO 동기화] 새로운 글 생성 여부와 상관없이 무조건 갱신
    files = sorted([f for f in os.listdir("posts") if f.endswith(".html")], reverse=True)
    now_iso = datetime.now().strftime("%Y-%m-%d")

    sitemap_xml = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    sitemap_xml += f'  <url><loc>{SITE_URL}/</loc><lastmod>{now_iso}</lastmod><priority>1.0</priority></url>\n'
    for file in files:
        sitemap_xml += f'  <url><loc>{SITE_URL}/posts/{file}</loc><lastmod>{now_iso}</lastmod></url>\n'
    sitemap_xml += '</urlset>'
    with open("sitemap.xml", "w", encoding="utf-8") as f: f.write(sitemap_xml.strip())

    with open("index.html", "w", encoding="utf-8") as f:
        f.write(f"<!DOCTYPE html><html lang='ko'><head><meta charset='UTF-8'><title>전문 쇼핑 매거진</title><style>body{{font-family:sans-serif; background:#f0f2f5; padding:20px;}} .grid{{display:grid; grid-template-columns:repeat(auto-fill, minmax(300px, 1fr)); gap:30px;}} .card{{background:white; padding:30px; border-radius:25px; text-decoration:none; color:#333; box-shadow:0 10px 20px rgba(0,0,0,0.05); height:150px; display:flex; flex-direction:column; justify-content:space-between;}} .title{{font-weight:bold; overflow:hidden; text-overflow:ellipsis; display:-webkit-box; -webkit-line-clamp:3; -webkit-box-orient:vertical; font-size:0.9rem;}}</style></head><body><h1 style='text-align:center;'>🚀 끝장 전수 조사 매거진</h1><div class='grid'>")
        for file in files[:120]:
            try:
                with open(f"posts/{file}", 'r', encoding='utf-8') as fr:
                    content = fr.read()
                    match = re.search(r'<title>(.*?)</title>', content)
                    title = match.group(1).replace(" 리뷰", "") if match else file
                f.write(f"<a class='card' href='posts/{file}'><div class='title'>{title}</div><div style='color:#e44d26; font-weight:bold;'>칼럼 읽기 ></div></a>")
            except: continue
        f.write("</div></body></html>")
    
    print(f"🏁 작업 종료! 총 포스팅 수: {len(files)}")

if __name__ == "__main__":
    main()
