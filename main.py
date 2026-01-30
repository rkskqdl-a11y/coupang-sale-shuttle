import os, hmac, hashlib, time, requests, json, random, re
from datetime import datetime
from time import gmtime, strftime
from urllib.parse import urlencode

# [1. 설정 정보]
ACCESS_KEY = os.environ.get('COUPANG_ACCESS_KEY', '').strip()
SECRET_KEY = os.environ.get('COUPANG_SECRET_KEY', '').strip()
GEMINI_KEY = os.environ.get('GEMINI_API_KEY', '').strip()
SITE_URL = "https://rkskqdl-a11y.github.io/coupang-sale-shuttle"

def generate_hmac_official(method, path, query_string, access_key, secret_key):
    """💎 공식 문서의 generateHmac 로직을 GET 방식에 맞게 완벽 이식"""
    # 공식 문서 포맷: YYMMDDTHHMMSSZ
    datetime_gmt = strftime('%y%m%d', gmtime()) + 'T' + strftime('%H%M%S', gmtime()) + 'Z'
    
    # 메시지 조합: 날짜 + 메서드 + 경로 + 쿼리스트링
    message = datetime_gmt + method + path + query_string

    signature = hmac.new(bytes(secret_key, "utf-8"),
                         message.encode("utf-8"),
                         hashlib.sha256).hexdigest()

    return "CEA algorithm=HmacSHA256, access-key={}, signed-date={}, signature={}".format(access_key, datetime_gmt, signature)

def fetch_data(keyword, page):
    """💎 공식 가이드대로 파라미터를 구성하여 0개 수신 문제를 해결합니다."""
    DOMAIN = "https://api-gateway.coupang.com"
    path = "/v2/providers/affiliate_open_api/apis/openapi/v1/products/search"
    
    # 💎 중요: 쿠팡 서버가 예상하는 순서대로 파라미터 나열 (keyword -> limit -> page)
    params = [('keyword', keyword), ('limit', 20), ('page', page)]
    query_string = urlencode(params)
    
    # 공식 인증 함수 호출
    authorization = generate_hmac_official("GET", path, query_string, ACCESS_KEY, SECRET_KEY)
    
    headers = {
        "Authorization": authorization,
        "Content-Type": "application/json"
    }
    
    try:
        url = f"{DOMAIN}{path}?{query_string}"
        response = requests.get(url, headers=headers, timeout=15)
        
        # 공식 에러 메시지 검토를 위해 상태 코드 확인
        if response.status_code != 200:
            print(f"   ⚠️ 공식 에러 발생: {response.json().get('message')}")
            return []
            
        data = response.json()
        items = data.get('data', {}).get('productData', [])
        if items: print(f"   📦 {len(items)}개 상품 수신 성공")
        return items
    except: return []

# ... (generate_ai_content, get_title_from_html 등 기존 함수 유지) ...

def main():
    os.makedirs("posts", exist_ok=True)
    existing_ids = {f.split('_')[-1].replace('.html', '') for f in os.listdir("posts") if '_' in f}
    
    # 💎 무차별 수집을 위한 가장 강력한 시드 키워드
    target = random.choice(["노트북", "운동화", "가습기", "영양제", "물티슈", "기저귀"])
    
    success_count, max_target = 0, 10
    print(f"🕵️ 현재 {len(existing_ids)}개 노출 중. '{target}' 공식 로직 수색 시작!")

    for page in range(1, 31):
        if success_count >= max_target: break
        
        print(f"🔍 [페이지 {page}] 분석 중...")
        products = fetch_data(target, page)
        
        if not products: continue

        for item in products:
            p_id = str(item['productId'])
            if p_id in existing_ids: continue

            p_name = item['productName']
            print(f"   ✨ 신규 발견! [{success_count+1}/10] {p_name[:25]}...")
            
            # (기존 포스팅 생성 로직 실행)
            # ...
            success_count += 1
            time.sleep(30)
            if success_count >= max_target: break

    # (인덱스 및 사이트맵 갱신 로직 실행 - xmlns 포함 필수)
    # ...
