import os, hmac, hashlib, time, requests, json, random, re
from datetime import datetime
from urllib.parse import urlencode

# [1. 설정]
ACCESS_KEY = os.environ.get('COUPANG_ACCESS_KEY')
SECRET_KEY = os.environ.get('COUPANG_SECRET_KEY')
GEMINI_KEY = os.environ.get('GEMINI_API_KEY')
SITE_URL = "https://rkskqdl-a11y.github.io/coupang-sale-shuttle"

def generate_ai_content(item):
    if not GEMINI_KEY: return "상세 정보를 분석 중입니다."
    name = item.get('productName')
    price = format(item.get('productPrice'), ',')
    discount = item.get('discountRate', 0)
    rocket = "로켓배송 가능" if item.get('isRocket') else "일반배송"
    
    prompt_text = f"너는 쇼핑 전문가야. '{name}'({price}원, 할인율 {discount}%)의 실사용 리뷰를 <h3> 태그를 써서 블로그 스타일로 써줘. HTML만 사용."

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_KEY}"
    payload = {"contents": [{"parts": [{"text": prompt_text}]}]}

    try:
        response = requests.post(url, json=payload, timeout=20)
        res_data = response.json()
        if 'candidates' in res_data:
            return res_data['candidates'][0]['content']['parts'][0]['text'].replace("\n", "<br>")
        return "상세 리뷰 분석 중입니다."
    except:
        return f"가성비 최고의 {name}을 추천합니다."

def fetch_data(keyword):
    """💎 진단용 로그가 추가된 상품 수집 함수"""
    try:
        DOMAIN = "https://api-gateway.coupang.com"
        path = "/v2/providers/affiliate_open_api/apis/openapi/v1/products/search"
        params = {"keyword": keyword, "limit": 10}
        query_string = urlencode(params)
        url = f"{DOMAIN}{path}?{query_string}"
        headers = {"Authorization": get_authorization_header("GET", path, query_string), "Content-Type": "application/json"}
        
        response = requests.get(url, headers=headers, timeout=15)
        # 📡 응답 코드를 출력하여 상태를 확인합니다.
        print(f"📡 쿠팡 API 응답 상태: {response.status_code}")
        
        if response.status_code != 200:
            print(f"❌ API 오류 내용: {response.text}")
            return []
            
        return response.json().get('data', {}).get('productData', [])
    except Exception as e:
        print(f"❌ 데이터 수집 중 시스템 에러: {e}")
        return []

def get_authorization_header(method, path, query_string):
    datetime_gmt = time.strftime('%y%m%dT%H%M%SZ', time.gmtime())
    message = datetime_gmt + method + path + query_string
    signature = hmac.new(bytes(SECRET_KEY, 'utf-8'), msg=bytes(message, 'utf-8'), digestmod=hashlib.sha256).hexdigest()
    return f"CEA algorithm=HmacSHA256, access-key={ACCESS_KEY}, signed-date={datetime_gmt}, signature={signature}"

def main():
    os.makedirs("posts", exist_ok=True)
    sets = [("삼성", "노트북"), ("LG", "생활가전"), ("애플", "아이패드"), ("나이키", "러닝화"), ("필립스", "면도기")]
    brand, item_type = random.choice(sets)
    target = f"인기 {brand} {item_type}"
    
    print(f"🔍 검색어: {target}")
    products = fetch_data(target)
    # 📦 수집된 상품 개수를 출력합니다.
    print(f"📦 수집된 상품 수: {len(products)}개")
    
    if not products:
        print("⚠️ 수집된 상품이 없어 작업을 종료합니다. API 키나 검색어를 확인하세요.")
        return
    
    for item in products:
        try:
            p_id = item['productId']
            filename = f"posts/{datetime.now().strftime('%Y%m%d')}_{p_id}.html"
            
            if os.path.exists(filename):
                print(f"⏭️ {p_id} 상품은 이미 존재하여 건너뜁니다.")
                continue 
            
            print(f"📝 {item['productName'][:20]}... 포스팅 생성 중")
            ai_content = generate_ai_content(item)
            
            # (기존 파일 저장 로직 동일)
            img = item['productImage'].split('?')[0]
            price = format(item['productPrice'], ',')
            discount = item.get('discountRate', 0)
            with open(filename, "w", encoding="utf-8") as f:
                f.write(f"<!DOCTYPE html><html><head><title>{item['productName']} 리뷰</title></head><body><h2>{item['productName']}</h2><img src='{img}'><p>{ai_content}</p><b>{price}원</b></body></html>")
            
            # API 과부하 방지를 위한 대기
            time.sleep(10) # 테스트를 위해 대기시간을 조금 줄였습니다.
        except Exception as e:
            print(f"❌ 개별 상품 처리 중 에러: {e}")
            continue

    # (인덱스 업데이트 로직 동일)
    print("✨ 모든 작업이 완료되었습니다.")

if __name__ == "__main__":
    main()
