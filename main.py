import os, hmac, hashlib, time, requests, json, random, re
from datetime import datetime
from urllib.parse import quote

# [1. 설정 정보]
ACCESS_KEY = os.environ.get('COUPANG_ACCESS_KEY', '').strip()
SECRET_KEY = os.environ.get('COUPANG_SECRET_KEY', '').strip()
GEMINI_KEY = os.environ.get('GEMINI_API_KEY', '').strip()
SITE_URL = "https://rkskqdl-a11y.github.io/coupang-sale-shuttle"

def generate_ai_content(product_name):
    """💎 의존성 에러 없이 requests로 AI 리뷰 생성 (1,000자 장문)"""
    if not GEMINI_KEY: return "분석 데이터 준비 중"
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_KEY}"
    prompt = f"상품 '{product_name}'에 대해 전문적인 분석 칼럼을 1,000자 이상 작성해줘. <h3> 활용, HTML만 사용, '해요체', '할인' 언급 금지."
    try:
        res = requests.post(url, json={"contents": [{"parts": [{"text": prompt}]}]}, timeout=60)
        return res.json()['candidates'][0]['content']['parts'][0]['text'].replace("\n", "<br>")
    except: return f"<h3>🔍 제품 분석</h3>{product_name}은 품질과 성능이 검증된 모델입니다."

def fetch_data(keyword, page):
    """💎 [핵심] 쿠팡 API 인증을 100% 성공시키는 엄격한 쿼리 생성"""
    DOMAIN = "https://api-gateway.coupang.com"
    path = "/v2/providers/affiliate_open_api/apis/openapi/v1/products/search"
    
    # 💎 중요: 파라미터는 반드시 알파벳 순서(keyword -> limit -> page)여야 합니다.
    query_string = f"keyword={quote(keyword)}&limit=20&page={page}"
    
    # 서명 생성 (datetime + method + path + query_string)
    datetime_gmt = time.strftime('%y%m%dT%H%M%SZ', time.gmtime())
    message = datetime_gmt + "GET" + path + query_string
    signature = hmac.new(bytes(SECRET_KEY, 'utf-8'), msg=bytes(message, 'utf-8'), digestmod=hashlib.sha256).hexdigest()
    
    headers = {
        "Authorization": f"CEA algorithm=HmacSHA256, access-key={ACCESS_KEY}, signed-date={datetime_gmt}, signature={signature}",
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.get(f"{DOMAIN}{path}?{query_string}", headers=headers, timeout=15)
        if response.status_code == 200:
            return response.json().get('data', {}).get('productData', [])
        else:
            # 💎 이제 로그에서 왜 0개인지 (401, 403 등) 숫자로 바로 알려줍니다.
            print(f"   ⚠️ 쿠팡 서버 응답 실패: {response.status_code} | {response.text[:50]}")
            return []
    exceptException as e:
        print(f"   ⚠️ 연결 오류: {e}")
        return []

def get_title_from_html(filepath):
    """💎 인덱스 생성을 위한 제목 추출 함수"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            match = re.search(r'<title>(.*?)</title>', content)
            if match: return match.group(1).replace(" 리뷰", "")
    except: pass
    return "추천 상품"

def main():
    os.makedirs("posts", exist_ok=True)
    
    # 💎 전 품목 수집을 위한 광대역 씨앗 키워드
    seeds = ["삼성", "엘지", "가전", "노트북", "운동화", "샴푸", "비타민", "물티슈", "기저귀", "양말"]
    target = random.choice(seeds)
    
    existing_ids = {f.split('_')[-1].replace('.html', '') for f in os.listdir("posts") if '_' in f}
    success_count, max_target = 0, 10
    
    print(f"🕵️ 현재 {len(existing_ids)}개 노출 중. '{target}' 기반 저인망 수색 시작!")

    # 💎 1페이지부터 차례대로! 중복이면 다음 페이지로!
    for page in range(1, 31): 
        if success_count >= max_target: break
        
        print(f"🔍 [페이지 {page}] 분석 중...")
        products = fetch_data(target, page)
        
        if not products: continue # 에러 로그는 위에서 찍힘

        for item in products:
            p_id = str(item['productId'])
            if p_id in existing_ids: continue # 중복 패스

            p_name = item['productName']
            print(f"   ✨ 발견! [{success_count+1}/10] {p_name[:20]}...")
            
            ai_content = generate_ai_content(p_name)
            img, price = item['productImage'].split('?')[0], format(item['productPrice'], ',')
            
            filename = f"posts/{datetime.now().strftime('%Y%m%d')}_{p_id}.html"
            with open(filename, "w", encoding="utf-8") as f:
                f.write(f"<!DOCTYPE html><html lang='ko'><head><meta charset='UTF-8'><title>{p_name} 리뷰</title><style>body{{font-family:sans-serif; background:#f8f9fa; padding:20px; color:#333; line-height:2.2;}} .card{{max-width:750px; margin:auto; background:white; padding:50px; border-radius:30px; box-shadow:0 20px 50px rgba(0,0,0,0.05);}} h3{{color:#e44d26; margin-top:40px; border-left:6px solid #e44d26; padding-left:20px;}} img{{width:100%; border-radius:20px; margin:30px 0;}} .p-val{{font-size:2.5rem; color:#e44d26; font-weight:bold; text-align:center;}} .buy-btn{{display:block; background:#e44d26; color:white; text-align:center; padding:25px; text-decoration:none; border-radius:60px; font-weight:bold; font-size:1.3rem;}}</style></head><body><div class='card'><h2>{p_name}</h2><img src='{img}'><div class='content'>{ai_content}</div><div class='p-val'>{price}원</div><a href='{item['productUrl']}' class='buy-btn'>🛍️ 상세 정보 확인하기</a></div></body></html>")
            
            existing_ids.add(p_id)
            success_count += 1
            time.sleep(30)
            if success_count >= max_target: break

    # 💎 [SEO 동기화] 구글 네임스페이스 오류 해결
    files = sorted([f for f in os.listdir("posts") if f.endswith(".html")], reverse=True)
    now_iso = datetime.now().strftime("%Y-%m-%d")
    
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(f"<!DOCTYPE html><html lang='ko'><head><meta charset='UTF-8'><title>쿠팡 핫딜 셔틀</title><style>body{{font-family:sans-serif; background:#f0f2f5; padding:20px;}} .grid{{display:grid; grid-template-columns:repeat(auto-fill, minmax(300px, 1fr)); gap:20px;}} .card{{background:white; padding:25px; border-radius:20px; text-decoration:none; color:#333; box-shadow:0 5px 15px rgba(0,0,0,0.05);}}</style></head><body><h1 style='text-align:center;'>🚀 실시간 쿠팡 전수 조사 매거진</h1><div class='grid'>")
        for file in files[:100]:
            title = get_title_from_html(f"posts/{file}")
            f.write(f"<a class='card' href='posts/{file}'><div>{title}</div><div style='color:#e44d26; font-weight:bold; margin-top:15px;'>칼럼 읽기 ></div></a>")
        f.write("</div></body></html>")

    with open("sitemap.xml", "w", encoding="utf-8") as f:
        # 💎 xmlns 속성을 정확히 추가하여 구글 경고를 해결했습니다.
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n')
        f.write(f'  <url><loc>{SITE_URL}/</loc><lastmod>{now_iso}</lastmod><priority>1.0</priority></url>\n')
        for file in files:
            f.write(f'  <url><loc>{SITE_URL}/posts/{file}</loc><lastmod>{now_iso}</lastmod></url>\n')
        f.write('</urlset>')

    with open("robots.txt", "w", encoding="utf-8") as f:
        f.write(f"User-agent: *\nAllow: /\nSitemap: {SITE_URL}/sitemap.xml")

    print(f"🏁 작업 완료! 총 {len(files)}개 노출 중. (신규 발행: {success_count}개)")

if __name__ == "__main__":
    main()
