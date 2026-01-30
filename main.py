import os, hmac, hashlib, time, requests, json, random, re
from datetime import datetime
from urllib.parse import urlencode

# 🚀 [System] AF7053799 전용 무결점 엔진 가동...
print("🚀 [System] 400 에러 교정 및 저인망 수집 엔진이 가동됩니다.")

# [1. 설정 정보]
ACCESS_KEY = os.environ.get('COUPANG_ACCESS_KEY', '').strip()
SECRET_KEY = os.environ.get('COUPANG_SECRET_KEY', '').strip()
GEMINI_KEY = os.environ.get('GEMINI_API_KEY', '').strip()
MY_PARTNERS_ID = "AF7053799"
SITE_URL = "https://rkskqdl-a11y.github.io/coupang-sale-shuttle"

def generate_hmac_pro(method, path, query_string):
    """💎 20년 차 시니어급 HMAC 서명 생성 로직"""
    timestamp = time.strftime('%y%m%dT%H%M%SZ', time.gmtime())
    message = timestamp + method + path + query_string
    signature = hmac.new(bytes(SECRET_KEY, 'utf-8'), 
                         msg=bytes(message, 'utf-8'), 
                         digestmod=hashlib.sha256).hexdigest()
    return f"CEA algorithm=HmacSHA256, access-key={ACCESS_KEY}, signed-date={timestamp}, signature={signature}"

def fetch_data(keyword, page):
    """💎 limit 범위를 10으로 조정하여 400 에러를 원천 차단합니다."""
    try:
        DOMAIN = "https://api-gateway.coupang.com"
        path = "/v2/providers/affiliate_open_api/apis/openapi/v1/products/search"
        
        # ⚠️ 보수적인 세팅: limit=10, 정렬된 파라미터
        params = [('keyword', keyword), ('limit', 10), ('page', page)]
        query_string = urlencode(params)
        
        headers = {
            "Authorization": generate_hmac_pro("GET", path, query_string),
            "Content-Type": "application/json"
        }
        
        response = requests.get(f"{DOMAIN}{path}?{query_string}", headers=headers, timeout=15)
        
        if response.status_code == 200:
            res_data = response.json()
            items = res_data.get('data', {}).get('productData', [])
            if items:
                print(f"   ✅ [수신성공] {len(items)}개 상품 확보 (Keyword: {keyword})")
            return items
        else:
            print(f"   ❌ [API 에러] {response.status_code}: {response.json().get('rMessage')}")
            return []
    except Exception as e:
        print(f"   ⚠️ 통신 오류: {e}")
        return []

def generate_ai_content(p_name):
    """💎 제미나이 AI 기반 1,000자 장문 분석 칼럼 생성"""
    if not GEMINI_KEY: return "상세 분석 준비 중"
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_KEY}"
    try:
        prompt = f"상품 '{p_name}'에 대해 쇼핑 전문가가 작성한 1,000자 이상의 분석 칼럼을 써줘. <h3> 사용, HTML만 사용, 해요체 사용. '할인' 단어 금지."
        res = requests.post(url, json={"contents": [{"parts": [{"text": prompt}]}]}, timeout=60)
        return res.json()['candidates'][0]['content']['parts'][0]['text'].replace("\n", "<br>")
    except: return f"<h3>🔍 제품 분석</h3>{p_name}은 품질이 우수한 추천 상품입니다."

def main():
    os.makedirs("posts", exist_ok=True)
    existing_ids = {f.split('_')[-1].replace('.html', '') for f in os.listdir("posts") if '_' in f}
    
    success_count, max_target = 0, 10
    
    # 💎 쿠팡의 모든 상품을 건드리기 위한 다양한 시드 키워드
    seeds = ["삼성전자", "LG가전", "노트북", "캠핑", "운동화", "물티슈", "영양제", "주방용품", "아이폰", "갤럭시"]
    random.shuffle(seeds)
    
    print(f"🕵️ 현재 {len(existing_ids)}개 노출 중. 전수 조사 하베스팅 시작!")

    for target in seeds:
        if success_count >= max_target: break
        # 안전한 수집을 위해 1~5페이지 무작위 수색
        page = random.randint(1, 5)
        print(f"🔍 '{target}' {page}페이지 수색 중...")
        
        products = fetch_data(target, page)
        if not products: continue

        for item in products:
            p_id = str(item['productId'])
            if p_id in existing_ids: continue

            print(f"   ✨ 발견! [{success_count+1}/10] {item['productName'][:20]}...")
            content = generate_ai_content(item['productName'])
            
            img, price = item['productImage'].split('?')[0], format(int(item['productPrice']), ',')
            
            filename = f"posts/{datetime.now().strftime('%Y%m%d')}_{p_id}.html"
            with open(filename, "w", encoding="utf-8") as f:
                f.write(f"<!DOCTYPE html><html lang='ko'><head><meta charset='UTF-8'><meta name='viewport' content='width=device-width, initial-scale=1.0'><title>{item['productName']} 리뷰</title><style>body{{font-family:sans-serif; background:#f8f9fa; padding:20px; line-height:2.2;}} .card{{max-width:750px; margin:auto; background:white; padding:50px; border-radius:30px; box-shadow:0 20px 50px rgba(0,0,0,0.05);}} img{{width:100%; border-radius:20px; margin:30px 0;}} .p-val{{font-size:2.5rem; color:#e44d26; font-weight:bold; text-align:center;}} .buy-btn{{display:block; background:#e44d26; color:white; text-align:center; padding:25px; text-decoration:none; border-radius:60px; font-weight:bold;}}</style></head><body><div class='card'><h2>{item['productName']}</h2><img src='{img}'><div class='content'>{content}</div><div class='p-val'>{price}원</div><a href='{item['productUrl']}' class='buy-btn'>🛍️ 상세 정보 확인하기</a></div></body></html>")
            
            existing_ids.add(p_id)
            success_count += 1
            time.sleep(35) # 제미나이 안전 대기
            if success_count >= max_target: break

    # [SEO 해결] 사이트맵 네임스페이스 및 인덱스 갱신
    files = sorted([f for f in os.listdir("posts") if f.endswith(".html")], reverse=True)
    now_iso = datetime.now().strftime("%Y-%m-%d")
    
    with open("sitemap.xml", "w", encoding="utf-8") as f:
        # 💎 xmlns 표준 속성을 추가하여 구글 서치 콘솔 오류를 영구 해결했습니다.
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n')
        f.write(f'  <url><loc>{SITE_URL}/</loc><lastmod>{now_iso}</lastmod><priority>1.0</priority></url>\n')
        for file in files:
            f.write(f'  <url><loc>{SITE_URL}/posts/{file}</loc><lastmod>{now_iso}</lastmod></url>\n')
        f.write('</urlset>')

    print(f"🏁 작업 완료. 총 {len(files)}개 노출. (신규: {success_count}개)")

if __name__ == "__main__":
    main()
