import os, hmac, hashlib, time, requests, json, random, re
from datetime import datetime
from urllib.parse import quote

# 🚀 [System] 엔진 가동 로그
print("🚀 쿠팡 자동화 엔진이 공식 가이드 규격으로 가동됩니다...")

# [1. 설정 정보]
ACCESS_KEY = os.environ.get('COUPANG_ACCESS_KEY', '').strip()
SECRET_KEY = os.environ.get('COUPANG_SECRET_KEY', '').strip()
GEMINI_KEY = os.environ.get('GEMINI_API_KEY', '').strip()
SITE_URL = "https://rkskqdl-a11y.github.io/coupang-sale-shuttle"

def get_authorization_header(method, path, query_string):
    """💎 공식 문서 스타일의 HMAC 생성 로직"""
    datetime_gmt = time.strftime('%y%m%dT%H%M%SZ', time.gmtime())
    message = datetime_gmt + method + path + query_string
    signature = hmac.new(bytes(SECRET_KEY, 'utf-8'), msg=bytes(message, 'utf-8'), digestmod=hashlib.sha256).hexdigest()
    return f"CEA algorithm=HmacSHA256, access-key={ACCESS_KEY}, signed-date={datetime_gmt}, signature={signature}"

def fetch_data(keyword, page):
    """💎 파라미터 정렬 및 인코딩을 공식 문서 규격에 100% 맞춥니다."""
    try:
        DOMAIN = "https://api-gateway.coupang.com"
        path = "/v2/providers/affiliate_open_api/apis/openapi/v1/products/search"
        
        # 💎 중요: 알파벳 순서 강제 고정 (keyword -> limit -> page)
        query_string = f"keyword={quote(keyword)}&limit=20&page={page}"
        
        headers = {
            "Authorization": get_authorization_header("GET", path, query_string),
            "Content-Type": "application/json"
        }
        
        response = requests.get(f"{DOMAIN}{path}?{query_string}", headers=headers, timeout=15)
        
        if response.status_code != 200:
            print(f"   ⚠️ API 서버 오류: {response.status_code}")
            return []
            
        data = response.json()
        items = data.get('data', {}).get('productData', [])
        
        # 💎 수신 결과 로그 (진단용)
        if items:
            print(f"   📦 {len(items)}개의 상품을 API로부터 성공적으로 수신했습니다.")
        else:
            print(f"   ❓ API 응답은 정상이나 상품 데이터가 비어있습니다. (키워드/권한 확인 필요)")
            
        return items
    except Exception as e:
        print(f"   ❌ 연결 오류 발생: {e}")
        return []

def generate_ai_content(product_name):
    """💎 1,000자 이상 전문가 칼럼 생성 (JSON 파싱 구조 수정)"""
    if not GEMINI_KEY: return "분석 데이터 준비 중입니다."
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_KEY}"
    prompt = f"상품 '{product_name}'에 대해 IT/라이프스타일 전문가가 작성한 분석 칼럼을 1,000자 이상 장문으로 작성해줘. <h3> 섹션으로 디자인, 기능, 실용성을 나누고 HTML 태그만 사용. 친절한 해요체 사용. '할인' 언급 금지."
    try:
        payload = {"contents": [{"parts": [{"text": prompt}]}]}
        response = requests.post(url, json=payload, timeout=60)
        res_data = response.json()
        # 💎 정석 인덱싱 구조로 수정
        return res_data['candidates'][0]['content']['parts'][0]['text'].replace("\n", "<br>")
    except:
        return f"<h3>🔍 제품 상세 분석</h3>{product_name}은 뛰어난 완성도를 자랑하는 추천 모델입니다."

def get_title_from_html(filepath):
    """💎 SEO 최적화를 위해 실제 HTML 내부 타이틀을 긁어옵니다."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            match = re.search(r'<title>(.*?)</title>', content)
            if match: return match.group(1).replace(" 리뷰", "")
    except: pass
    return "추천 상품"

def main():
    os.makedirs("posts", exist_ok=True)
    existing_posts = os.listdir("posts")
    existing_ids = {f.split('_')[-1].replace('.html', '') for f in existing_posts if '_' in f}
    
    success_count, max_target = 0, 10
    attempts = 0
    
    # 💎 무엇이든 1페이지를 가득 채우는 저인망 수집 키워드들
    seeds = ["가전", "노트북", "운동화", "샴푸", "비타민", "물티슈", "기저귀", "양말", "베개", "보조배터리"]
    target = random.choice(seeds)
    
    print(f"🕵️ 현재 {len(existing_ids)}개 데이터 노출 중. '{target}' 기반 저인망 수색 시작!")

    # 💎 10개를 채울 때까지 무작위 페이지를 넘기며 무차별 발행
    while success_count < max_target and attempts < 20:
        page = random.randint(1, 50) # 1~50페이지 무작위 타격
        print(f"🔄 [시도 {attempts+1}] {page}페이지 분석 중...")
        
        products = fetch_data(target, page)
        attempts += 1
        
        if not products: continue

        for item in products:
            p_id = str(item['productId'])
            if p_id in existing_ids: continue # 중복 건너뛰기

            p_name = item['productName']
            print(f"   ✨ 발견! [{success_count+1}/10] {p_name[:20]}...")
            
            ai_content = generate_ai_content(p_name)
            img = item['productImage'].split('?')[0] 
            price = format(item['productPrice'], ',')
            
            filename = f"posts/{datetime.now().strftime('%Y%m%d')}_{p_id}.html"
            with open(filename, "w", encoding="utf-8") as f:
                f.write(f"<!DOCTYPE html><html lang='ko'><head><meta charset='UTF-8'><meta name='viewport' content='width=device-width, initial-scale=1.0'><title>{p_name} 리뷰</title><style>body{{font-family:sans-serif; background:#f8f9fa; padding:20px; color:#333; line-height:2.2;}} .card{{max-width:750px; margin:auto; background:white; padding:50px; border-radius:30px; box-shadow:0 20px 50px rgba(0,0,0,0.05);}} h3{{color:#e44d26; margin-top:40px; border-left:6px solid #e44d26; padding-left:20px;}} img{{width:100%; border-radius:20px; margin:30px 0;}} .p-val{{font-size:2.5rem; color:#e44d26; font-weight:bold; text-align:center;}} .buy-btn{{display:block; background:#e44d26; color:white; text-align:center; padding:25px; text-decoration:none; border-radius:60px; font-weight:bold; font-size:1.3rem;}}</style></head><body><div class='card'><h2>{p_name}</h2><img src='{img}'><div class='content'>{ai_content}</div><div class='p-val'>{price}원</div><a href='{item['productUrl']}' class='buy-btn'>🛍️ 상세 정보 확인하기</a></div></body></html>")
            
            existing_ids.add(p_id)
            success_count += 1
            time.sleep(35) # 안전 발행 대기
            if success_count >= max_target: break

    # [동기화] 사이트맵 네임스페이스 및 인덱스 갱신
    files = sorted([f for f in os.listdir("posts") if f.endswith(".html")], reverse=True)
    now_iso = datetime.now().strftime("%Y-%m-%d")
    
    with open("sitemap.xml", "w", encoding="utf-8") as f:
        # 💎 구글 서치 콘솔 오류를 해결하기 위한 정식 XML 네임스페이스 삽입
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n')
        f.write(f'  <url><loc>{SITE_URL}/</loc><lastmod>{now_iso}</lastmod><priority>1.0</priority></url>\n')
        for file in files:
            f.write(f'  <url><loc>{SITE_URL}/posts/{file}</loc><lastmod>{now_iso}</lastmod></url>\n')
        f.write('</urlset>')
    
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(f"<!DOCTYPE html><html lang='ko'><head><meta charset='UTF-8'><title>쿠팡 핫딜 셔틀</title><style>body{{font-family:sans-serif; background:#f0f2f5; padding:20px;}} .grid{{display:grid; grid-template-columns:repeat(auto-fill, minmax(300px, 1fr)); gap:20px;}} .card{{background:white; padding:25px; border-radius:20px; text-decoration:none; color:#333; box-shadow:0 5px 15px rgba(0,0,0,0.05);}}</style></head><body><h1 style='text-align:center;'>🚀 실시간 쿠팡 전수 조사 매거진</h1><div class='grid'>")
        for file in files[:150]:
            title = get_title_from_html(f"posts/{file}")
            f.write(f"<a class='card' href='posts/{file}'><div>{title}</div><div style='color:#e44d26; font-weight:bold; margin-top:15px;'>칼럼 읽기 ></div></a>")
        f.write("</div></body></html>")

    print(f"🏁 작업 완료! 총 {len(files)}개 노출. (신규: {success_count}개)")

if __name__ == "__main__":
    main()
