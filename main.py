import os, hmac, hashlib, time, requests, json, random, re
from datetime import datetime
from urllib.parse import urlencode

# [1. 설정 정보]
ACCESS_KEY = os.environ.get('COUPANG_ACCESS_KEY', '').strip()
SECRET_KEY = os.environ.get('COUPANG_SECRET_KEY', '').strip()
GEMINI_KEY = os.environ.get('GEMINI_API_KEY', '').strip()
SITE_URL = "https://rkskqdl-a11y.github.io/coupang-sale-shuttle"

def generate_ai_content(item):
    """💎 1,500자 이상의 초장문 리뷰 생성"""
    if not GEMINI_KEY: return "분석 데이터 준비 중"
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
    """💎 실제 물건 이름을 사용하여 검색 성공률을 높입니다."""
    try:
        DOMAIN = "https://api-gateway.coupang.com"
        path = "/v2/providers/affiliate_open_api/apis/openapi/v1/products/search"
        # 검색 제한을 최대치로 설정하여 더 많은 후보군 확보
        params = {"keyword": keyword, "limit": 50, "page": page}
        query_string = urlencode(params)
        url = f"{DOMAIN}{path}?{query_string}"
        headers = {"Authorization": get_authorization_header("GET", path, query_string), "Content-Type": "application/json"}
        response = requests.get(url, headers=headers, timeout=15)
        data = response.json().get('data', {}).get('productData', [])
        return data
    except: return []

def get_authorization_header(method, path, query_string):
    datetime_gmt = time.strftime('%y%m%dT%H%M%SZ', time.gmtime())
    message = datetime_gmt + method + path + query_string
    signature = hmac.new(bytes(SECRET_KEY, 'utf-8'), msg=bytes(message, 'utf-8'), digestmod=hashlib.sha256).hexdigest()
    return f"CEA algorithm=HmacSHA256, access-key={ACCESS_KEY}, signed-date={datetime_gmt}, signature={signature}"

def main():
    os.makedirs("posts", exist_ok=True)
    
    # 💎 [씨앗 키워드 풀] 대분류 대신 실제 상품이 검색되는 단어들로 교체
    seed_keywords = [
        "티셔츠", "원피스", "운동화", "슬리퍼", "기저귀", "물티슈", "샴푸", "바디워시", "비타민", "유산균",
        "마스크", "멀티탭", "충전기", "케이블", "후라이팬", "냄비", "도마", "수저세트", "베개", "이불",
        "양말", "수건", "텀블러", "간절기자켓", "청바지", "슬랙스", "에코백", "백팩", "보조배터리", "이어폰"
    ]
    
    existing_posts = os.listdir("posts")
    existing_ids = {f.split('_')[-1].replace('.html', '') for f in existing_posts if '_' in f}
    
    success_count = 0
    max_target = 10 
    print(f"🕵️ 현재 {len(existing_ids)}개 노출 중. 새 상품 {max_target}개 무조건 찾아냅니다.")

    # 💎 목표 달성 시까지 무한 루프
    for attempt in range(200): # 탐색 횟수를 더 늘림
        if success_count >= max_target: break
        
        # 씨앗 키워드에 랜덤 접미사를 붙여 검색 결과의 다양성 확보
        raw_target = random.choice(seed_keywords)
        suffix = random.choice(["", "추천", "세트", "용품", "기획"])
        target = f"{raw_target} {suffix}".strip()
        
        page = random.randint(1, 40) 
        products = fetch_data(target, page)
        
        if not products:
            print(f"➖ [{attempt+1}차] '{target}' (p.{page}): 결과 없음. 패스.")
            continue

        print(f"🔍 [{attempt+1}차] '{target}' (p.{page}): {len(products)}개 발견! 분석 시작.")
        random.shuffle(products)

        for item in products:
            p_id = str(item['productId'])
            if p_id in existing_ids: continue

            # 포스팅 생성 로직
            p_name = item['productName']
            filename = f"posts/{datetime.now().strftime('%Y%m%d')}_{p_id}.html"
            ai_content = generate_ai_content(item)
            img = item['productImage'].split('?')[0]
            price = format(item['productPrice'], ',')
            
            with open(filename, "w", encoding="utf-8") as f:
                f.write(f"<!DOCTYPE html><html lang='ko'><head><meta charset='UTF-8'><meta name='viewport' content='width=device-width, initial-scale=1.0'><title>{p_name} 리뷰</title><style>body{{font-family:sans-serif; background:#f8f9fa; padding:20px; color:#333; line-height:2.2;}} .card{{max-width:750px; margin:auto; background:white; padding:50px; border-radius:30px; box-shadow:0 20px 50px rgba(0,0,0,0.05);}} h3{{color:#e44d26; margin-top:40px; border-left:6px solid #e44d26; padding-left:20px;}} img{{width:100%; border-radius:20px; margin:30px 0;}} .price-box{{text-align:center; background:#fff5f2; padding:30px; border-radius:20px; margin:40px 0;}} .p-val{{font-size:2.5rem; color:#e44d26; font-weight:bold;}} .buy-btn{{display:block; background:#e44d26; color:white; text-align:center; padding:25px; text-decoration:none; border-radius:60px; font-weight:bold; font-size:1.3rem;}}</style></head><body><div class='card'><h2>{p_name}</h2><img src='{img}'><div class='content'>{ai_content}</div><div class='price-box'><div class='p-val'>{price}원</div></div><a href='{item['productUrl']}' class='buy-btn'>🛍️ 상세 정보 확인하기</a></div></body></html>")
            
            existing_ids.add(p_id)
            success_count += 1
            print(f"   ✨ 성공 ({success_count}/{max_target}): {p_name[:25]}...")
            time.sleep(30) # API 안정성
            
            if success_count >= max_target: break

    # 💎 SEO 파일 강제 업데이트
    files = sorted([f for f in os.listdir("posts") if f.endswith(".html")], reverse=True)
    now_iso = datetime.now().strftime("%Y-%m-%d")
    sitemap = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    sitemap += f'  <url><loc>{SITE_URL}/</loc><lastmod>{now_iso}</lastmod><priority>1.0</priority></url>\n'
    for f in files: sitemap += f'  <url><loc>{SITE_URL}/posts/{f}</loc><lastmod>{now_iso}</lastmod></url>\n'
    sitemap += '</urlset>'
    with open("sitemap.xml", "w", encoding="utf-8") as f: f.write(sitemap.strip())
    with open("robots.txt", "w", encoding="utf-8") as f: f.write(f"User-agent: *\nAllow: /\nSitemap: {SITE_URL}/sitemap.xml\n")
    
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(f"<!DOCTYPE html><html lang='ko'><head><meta charset='UTF-8'><title>쿠팡 전수 조사 매거진</title><style>body{{font-family:sans-serif; background:#f0f2f5; padding:20px;}} .grid{{display:grid; grid-template-columns:repeat(auto-fill, minmax(320px, 1fr)); gap:30px;}} .card{{background:white; padding:30px; border-radius:25px; text-decoration:none; color:#333; box-shadow:0 10px 20px rgba(0,0,0,0.05); height:160px; display:flex; flex-direction:column; justify-content:space-between;}} .title{{font-weight:bold; overflow:hidden; text-overflow:ellipsis; display:-webkit-box; -webkit-line-clamp:3; -webkit-box-orient:vertical; font-size:0.95rem;}}</style></head><body><h1 style='text-align:center;'>🚀 쿠팡 전 상품 노출 프로젝트</h1><div class='grid'>")
        for file in files[:150]:
            try:
                with open(f"posts/{file}", 'r', encoding='utf-8') as fr:
                    title = re.search(r'<title>(.*?)</title>', fr.read()).group(1).replace(" 리뷰", "")
                f.write(f"<a class='card' href='posts/{file}'><div class='title'>{title}</div><div style='color:#e44d26; font-weight:bold;'>리뷰 읽기 ></div></a>")
            except: continue
        f.write("</div></body></html>")
    print(f"🏁 작업 완료! 총 {len(files)}개 상품 노출 중.")

if __name__ == "__main__":
    main()
