import os, hmac, hashlib, time, requests, json, random, re
from datetime import datetime
from urllib.parse import urlencode

# [1. 설정 정보]
ACCESS_KEY = os.environ.get('COUPANG_ACCESS_KEY', '').strip()
SECRET_KEY = os.environ.get('COUPANG_SECRET_KEY', '').strip()
GEMINI_KEY = os.environ.get('GEMINI_API_KEY', '').strip()
SITE_URL = "https://rkskqdl-a11y.github.io/coupang-sale-shuttle"

def generate_ai_content(item):
    """💎 제미나이 Pro 1.5로 1,500자 이상의 초장문 리뷰 생성"""
    if not GEMINI_KEY: return "상세 분석 데이터 준비 중"
    name = item.get('productName')
    price = format(item.get('productPrice', 0), ',')
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_KEY}"
    prompt = f"상품 '{name}'(가격 {price}원)에 대해 전문적인 제품 분석 칼럼을 1,500자 이상 장문으로 작성해줘. <h3> 태그를 활용해 섹션을 나누고 HTML만 사용해. '할인' 언급 절대 금지."

    try:
        payload = {"contents": [{"parts": [{"text": prompt}]}]}
        response = requests.post(url, json=payload, timeout=60)
        res_data = response.json()
        if 'candidates' in res_data and len(res_data['candidates']) > 0:
            return res_data['candidates'][0]['content']['parts'][0]['text'].replace("\n", "<br>").strip()
    except: pass
    return f"<h3>🔍 제품 상세 분석</h3>{name}은 {price}원대에 출시된 모델로, 탄탄한 완성도와 세련된 디자인이 돋보이는 제품입니다."

def fetch_data(keyword, page):
    """💎 쿠팡 API 검색 실행"""
    try:
        DOMAIN = "https://api-gateway.coupang.com"
        path = "/v2/providers/affiliate_open_api/apis/openapi/v1/products/search"
        params = {"keyword": keyword, "limit": 30, "page": page}
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
    
    # 💎 [광대역 카테고리] 쿠팡의 모든 상품을 아우르는 대분류 키워드
    category_pool = [
        "가전디지털", "패션의류", "주방용품", "생활용품", "뷰티", "스포츠레저", "홈인테리어", 
        "반려동물용품", "완구취미", "문구오피스", "도서", "헬스건강식품", "자동차용품"
    ]
    
    # 중복 체크를 위해 기존 파일의 제목과 ID를 모두 수집
    existing_posts = os.listdir("posts")
    existing_ids = {f.split('_')[-1].replace('.html', '') for f in existing_posts if '_' in f}
    
    success_count = 0
    max_target = 10 # 💎 실행마다 무조건 새로 만들 목표 수량
    print(f"🕵️ 현재 포스팅 수: {len(existing_posts)}개. 목표: 새 상품 {max_target}개 찾기")

    # 💎 목표 달성 시까지 무한 탐색 (최대 100회 시도)
    for attempt in range(100):
        if success_count >= max_target: break
        
        target = random.choice(category_pool)
        page = random.randint(1, 50) # 최대 50페이지까지 딥 탐색
        print(f"🔄 [{attempt+1}차] 탐색 중: {target} (페이지: {page})")
        
        products = fetch_data(target, page)
        if not products: continue
        random.shuffle(products) # 검색 결과 내에서도 순서를 섞어 노출 극대화

        for item in products:
            p_id = str(item['productId'])
            p_name = item['productName']
            
            # ID 중복 체크 (이름만 다르면 포스팅하라는 조건 반영)
            if p_id in existing_ids: continue

            # 신규 상품 포스팅 생성
            filename = f"posts/{datetime.now().strftime('%Y%m%d')}_{p_id}.html"
            ai_content = generate_ai_content(item)
            img = item['productImage'].split('?')[0]
            price = format(item['productPrice'], ',')
            
            with open(filename, "w", encoding="utf-8") as f:
                f.write(f"<!DOCTYPE html><html lang='ko'><head><meta charset='UTF-8'><meta name='viewport' content='width=device-width, initial-scale=1.0'><title>{p_name} 리뷰</title><style>body{{font-family:sans-serif; background:#f8f9fa; padding:20px; color:#333; line-height:2.2;}} .card{{max-width:750px; margin:auto; background:white; padding:50px; border-radius:30px; box-shadow:0 20px 50px rgba(0,0,0,0.05);}} h3{{color:#e44d26; margin-top:40px; border-left:6px solid #e44d26; padding-left:20px;}} img{{width:100%; border-radius:20px; margin:30px 0;}} .price-box{{text-align:center; background:#fff5f2; padding:30px; border-radius:20px; margin:40px 0;}} .p-val{{font-size:2.5rem; color:#e44d26; font-weight:bold;}} .buy-btn{{display:block; background:#e44d26; color:white; text-align:center; padding:25px; text-decoration:none; border-radius:60px; font-weight:bold; font-size:1.3rem;}}</style></head><body><div class='card'><h2>{p_name}</h2><img src='{img}'><div class='content'>{ai_content}</div><div class='price-box'><div class='p-val'>{price}원</div></div><a href='{item['productUrl']}' class='buy-btn'>🛍️ 상세 정보 확인하기</a></div></body></html>")
            
            existing_ids.add(p_id)
            success_count += 1
            print(f"   ✅ 신규 ({success_count}/{max_target}): {p_name[:30]}...")
            time.sleep(30) # 할당량 준수
            
            if success_count >= max_target: break

    # 💎 [SEO 동기화] 네임스페이스 오류 해결 및 인덱스 갱신
    files = sorted([f for f in os.listdir("posts") if f.endswith(".html")], reverse=True)
    now_iso = datetime.now().strftime("%Y-%m-%d")
    
    sitemap = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    sitemap += f'  <url><loc>{SITE_URL}/</loc><lastmod>{now_iso}</lastmod><priority>1.0</priority></url>\n'
    for f in files: sitemap += f'  <url><loc>{SITE_URL}/posts/{f}</loc><lastmod>{now_iso}</lastmod></url>\n'
    sitemap += '</urlset>'
    with open("sitemap.xml", "w", encoding="utf-8") as f: f.write(sitemap.strip())

    with open("robots.txt", "w", encoding="utf-8") as f:
        f.write(f"User-agent: *\nAllow: /\nSitemap: {SITE_URL}/sitemap.xml\n")

    with open("index.html", "w", encoding="utf-8") as f:
        f.write(f"<!DOCTYPE html><html lang='ko'><head><meta charset='UTF-8'><title>전문 쇼핑 매거진</title><style>body{{font-family:sans-serif; background:#f0f2f5; padding:20px;}} .grid{{display:grid; grid-template-columns:repeat(auto-fill, minmax(320px, 1fr)); gap:30px;}} .card{{background:white; padding:30px; border-radius:25px; text-decoration:none; color:#333; box-shadow:0 10px 20px rgba(0,0,0,0.05); height:160px; display:flex; flex-direction:column; justify-content:space-between;}} .title{{font-weight:bold; overflow:hidden; text-overflow:ellipsis; display:-webkit-box; -webkit-line-clamp:3; -webkit-box-orient:vertical; font-size:0.95rem;}}</style></head><body><h1 style='text-align:center;'>🚀 쿠팡 전수 조사 매거진</h1><div class='grid'>")
        for file in files[:150]:
            try:
                with open(f"posts/{file}", 'r', encoding='utf-8') as fr:
                    content = fr.read()
                    match = re.search(r'<title>(.*?)</title>', content)
                    title = match.group(1).replace(" 리뷰", "") if match else file
                f.write(f"<a class='card' href='posts/{file}'><div class='title'>{title}</div><div style='color:#e44d26; font-weight:bold;'>칼럼 읽기 ></div></a>")
            except: continue
        f.write("</div></body></html>")
    
    print(f"🏁 작업 완료! 총 {len(files)}개의 상품이 노출 중입니다.")

if __name__ == "__main__":
    main()
