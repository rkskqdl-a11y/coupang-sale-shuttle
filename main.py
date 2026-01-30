import os, hmac, hashlib, time, requests, json, random, re
from datetime import datetime
from urllib.parse import urlencode

# [1. 설정 정보]
ACCESS_KEY = os.environ.get('COUPANG_ACCESS_KEY', '').strip()
SECRET_KEY = os.environ.get('COUPANG_SECRET_KEY', '').strip()
GEMINI_KEY = os.environ.get('GEMINI_API_KEY', '').strip()
SITE_URL = "https://rkskqdl-a11y.github.io/coupang-sale-shuttle"

def generate_ai_content(product_name):
    """💎 제미나이 AI를 활용한 고품질 칼럼 생성 (requests 기반)"""
    if not GEMINI_KEY: return "분석 데이터 준비 중"
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_KEY}"
    prompt = f"상품 '{product_name}'에 대해 전문적인 분석 칼럼을 1,000자 이상 장문으로 작성해줘. <h3> 태그를 활용해 섹션을 나누고 HTML만 사용해. '할인' 언급 절대 금지."
    try:
        response = requests.post(url, json={"contents": [{"parts": [{"text": prompt}]}]}, timeout=45)
        res_data = response.json()
        if 'candidates' in res_data:
            return res_data['candidates'][0]['content']['parts'][0]['text'].replace("\n", "<br>").strip()
    except: pass
    return f"<h3>🔍 제품 정밀 분석</h3>{product_name}은 탄탄한 설계와 실용성이 돋보이는 모델입니다."

def fetch_data(keyword, page):
    """💎 [전문가 교정] 파라미터 정렬 및 인증 오류 완벽 해결"""
    try:
        DOMAIN = "https://api-gateway.coupang.com"
        path = "/v2/providers/affiliate_open_api/apis/openapi/v1/products/search"
        
        # 💎 중요: 파라미터는 반드시 알파벳 순서(keyword -> limit -> page)여야 합니다.
        params = [
            ("keyword", keyword),
            ("limit", 20),
            ("page", page)
        ]
        query_string = urlencode(params)
        
        # 서명 생성 및 헤더 구성
        datetime_gmt = time.strftime('%y%m%dT%H%M%SZ', time.gmtime())
        message = datetime_gmt + "GET" + path + query_string
        signature = hmac.new(bytes(SECRET_KEY, 'utf-8'), msg=bytes(message, 'utf-8'), digestmod=hashlib.sha256).hexdigest()
        
        headers = {
            "Authorization": f"CEA algorithm=HmacSHA256, access-key={ACCESS_KEY}, signed-date={datetime_gmt}, signature={signature}",
            "Content-Type": "application/json"
        }
        
        response = requests.get(f"{DOMAIN}{path}?{query_string}", headers=headers, timeout=15)
        
        # [디버깅] 서버 응답 상태 확인
        if response.status_code != 200:
            print(f"   ⚠️ 쿠팡 서버 응답 에러: {response.status_code}")
            return []
            
        return response.json().get('data', {}).get('productData', [])
    except Exception as e:
        print(f"   ⚠️ 시스템 오류: {e}")
        return []

def main():
    os.makedirs("posts", exist_ok=True)
    
    # 💎 무조건 결과가 나오는 마르지 않는 씨앗 키워드
    seeds = ["노트북", "운동화", "세탁기", "건조기", "린넨셔츠", "가습기", "커피머신", "모니터", "단백질보충제", "샴푸", "물티슈", "기저귀", "수건", "베개", "후라이팬", "멀티탭"]
    
    existing_ids = {f.split('_')[-1].replace('.html', '') for f in os.listdir("posts") if '_' in f}
    success_count, max_target = 0, 10
    attempts = 0
    
    print(f"🕵️ 현재 {len(existing_ids)}개 노출 중. 목표 {max_target}개 수집 시작!")

    # 💎 10개를 채울 때까지 끈질기게 시도 (최대 100회)
    while success_count < max_target and attempts < 100:
        attempts += 1
        target = random.choice(seeds)
        page = random.randint(1, 10) # 확실한 결과를 위해 10페이지 이내 공략
        
        products = fetch_data(target, page)
        if not products:
            continue

        print(f"   🔍 [{attempts}차] '{target}' p.{page}에서 {len(products)}개 발견!")
        random.shuffle(products)

        for item in products:
            p_id = str(item['productId'])
            if p_id in existing_ids: continue # 중복 체크

            p_name = item['productName']
            print(f"   ✍️  발행 중: {p_name[:20]}...")
            
            ai_content = generate_ai_content(p_name)
            img, price = item['productImage'].split('?')[0], format(item['productPrice'], ',')
            
            filename = f"posts/{datetime.now().strftime('%Y%m%d')}_{p_id}.html"
            with open(filename, "w", encoding="utf-8") as f:
                f.write(f"<!DOCTYPE html><html lang='ko'><head><meta charset='UTF-8'><meta name='viewport' content='width=device-width, initial-scale=1.0'><title>{p_name} 리뷰</title><style>body{{font-family:sans-serif; background:#f8f9fa; padding:20px; color:#333; line-height:2.2;}} .card{{max-width:750px; margin:auto; background:white; padding:50px; border-radius:30px; box-shadow:0 20px 50px rgba(0,0,0,0.05);}} h3{{color:#e44d26; margin-top:40px; border-left:6px solid #e44d26; padding-left:20px;}} img{{width:100%; border-radius:20px; margin:30px 0;}} .price-box{{text-align:center; background:#fff5f2; padding:30px; border-radius:20px; margin:40px 0;}} .p-val{{font-size:2.5rem; color:#e44d26; font-weight:bold;}} .buy-btn{{display:block; background:#e44d26; color:white; text-align:center; padding:25px; text-decoration:none; border-radius:60px; font-weight:bold; font-size:1.3rem;}}</style></head><body><div class='card'><h2>{p_name}</h2><img src='{img}'><div class='content'>{ai_content}</div><div class='price-box'><div class='p-val'>{price}원</div></div><a href='{item['productUrl']}' class='buy-btn'>🛍️ 상세 정보 확인하기</a></div></body></html>")
            
            existing_ids.add(p_id)
            success_count += 1
            time.sleep(30)
            if success_count >= max_target: break

    # 💎 [중요: 사이트맵 오류 해결] 네임스페이스 및 선언부 교정
    files = sorted([f for f in os.listdir("posts") if f.endswith(".html")], reverse=True)
    now_iso = datetime.now().strftime("%Y-%m-%d")
    
    # 💎 xmlns 속성을 정확히 추가하여 구글의 경고를 제거합니다.
    sitemap = '<?xml version="1.0" encoding="UTF-8"?>\n'
    sitemap += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    sitemap += f'  <url><loc>{SITE_URL}/</loc><lastmod>{now_iso}</lastmod><priority>1.0</priority></url>\n'
    for f in files:
        sitemap += f'  <url><loc>{SITE_URL}/posts/{f}</loc><lastmod>{now_iso}</lastmod></url>\n'
    sitemap += '</urlset>'
    
    with open("sitemap.xml", "w", encoding="utf-8") as f: f.write(sitemap.strip())
    with open("robots.txt", "w", encoding="utf-8") as f: f.write(f"User-agent: *\nAllow: /\nSitemap: {SITE_URL}/sitemap.xml\n")
    
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(f"<!DOCTYPE html><html lang='ko'><head><meta charset='UTF-8'><title>쿠팡 핫딜 매거진</title><style>body{{font-family:sans-serif; background:#f0f2f5; padding:20px;}} .grid{{display:grid; grid-template-columns:repeat(auto-fill, minmax(320px, 1fr)); gap:30px;}} .card{{background:white; padding:30px; border-radius:25px; text-decoration:none; color:#333; box-shadow:0 10px 20px rgba(0,0,0,0.05); height:160px; display:flex; flex-direction:column; justify-content:space-between;}} .title{{font-weight:bold; overflow:hidden; text-overflow:ellipsis; display:-webkit-box; -webkit-line-clamp:3; -webkit-box-orient:vertical; font-size:0.95rem;}}</style></head><body><h1 style='text-align:center;'>🚀 실시간 쿠팡 전수 조사 매거진</h1><div class='grid'>")
        for file in files[:150]:
            try:
                with open(f"posts/{file}", 'r', encoding='utf-8') as fr:
                    title = re.search(r'<title>(.*?)</title>', fr.read()).group(1).replace(" 리뷰", "")
                f.write(f"<a class='card' href='posts/{file}'><div class='title'>{title}</div><div style='color:#e44d26; font-weight:bold;'>칼럼 읽기 ></div></a>")
            except: continue
        f.write("</div></body></html>")
    
    print(f"🏁 작업 완료! 총 {len(files)}개 노출 중. (시도: {attempts})")

if __name__ == "__main__":
    main()
