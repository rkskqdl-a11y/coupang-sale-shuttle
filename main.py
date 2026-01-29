import os, hmac, hashlib, time, requests, json, random, re
from datetime import datetime
from urllib.parse import urlencode

# [1. 설정]
ACCESS_KEY = os.environ.get('COUPANG_ACCESS_KEY')
SECRET_KEY = os.environ.get('COUPANG_SECRET_KEY')
GEMINI_KEY = os.environ.get('GEMINI_API_KEY')
SITE_URL = "https://rkskqdl-a11y.github.io/coupang-sale-shuttle"

def fetch_data(keyword):
    """💎 API 상태를 로그에 명확히 출력합니다."""
    try:
        DOMAIN = "https://api-gateway.coupang.com"
        path = "/v2/providers/affiliate_open_api/apis/openapi/v1/products/search"
        params = {"keyword": keyword, "limit": 10}
        query_string = urlencode(params)
        url = f"{DOMAIN}{path}?{query_string}"
        
        # 키 검사 (Secrets 설정 누락 확인용)
        if not ACCESS_KEY or not SECRET_KEY:
            print("❌ 에러: 쿠팡 API 키가 환경 변수에 설정되지 않았습니다.")
            return []

        headers = {"Authorization": get_authorization_header("GET", path, query_string), "Content-Type": "application/json"}
        response = requests.get(url, headers=headers, timeout=15)
        
        print(f"📡 API 응답 코드: {response.status_code}")
        if response.status_code != 200:
            print(f"❌ API 오류 메시지: {response.text}")
            return []
            
        data = response.json().get('data', {}).get('productData', [])
        return data
    except Exception as e:
        print(f"❌ 시스템 에러: {e}")
        return []

def generate_ai_content(item):
    """스텔스 모드 AI 리뷰 생성 (기존 로직 유지)"""
    if not GEMINI_KEY: return "분석 중..."
    raw_name = item.get('productName')
    price = format(item.get('productPrice', 0), ',')
    # 브랜드명 제거 로직
    clean_name = re.sub(r'나이키|NIKE|삼성|SAMSUNG|LG|애플|APPLE', '', raw_name, flags=re.I)
    short_name = " ".join(clean_name.split()[:3]).strip()
    
    url = f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent?key={GEMINI_KEY}"
    prompt_text = f"이 모델({short_name}, 가격 {price}원)의 특징과 장점을 전문 분석 보고서 스타일로 500자 내외로 써줘. <h3> 태그 사용."
    
    try:
        payload = {"contents": [{"parts": [{"text": prompt_text}]}]}
        response = requests.post(url, json=payload, timeout=25)
        res_data = response.json()
        if 'candidates' in res_data:
            return res_data['candidates'][0]['content']['parts'][0]['text'].replace("\n", "<br>")
        return f"<h3>📝 추천 이유</h3>{short_name}은 {price}원에 만나볼 수 있는 최적의 선택입니다."
    except: return "내용 생성 중입니다."

def get_authorization_header(method, path, query_string):
    datetime_gmt = time.strftime('%y%m%dT%H%M%SZ', time.gmtime())
    message = datetime_gmt + method + path + query_string
    signature = hmac.new(bytes(SECRET_KEY, 'utf-8'), msg=bytes(message, 'utf-8'), digestmod=hashlib.sha256).hexdigest()
    return f"CEA algorithm=HmacSHA256, access-key={ACCESS_KEY}, signed-date={datetime_gmt}, signature={signature}"

def main():
    os.makedirs("posts", exist_ok=True)
    # 💎 키워드를 조금 더 명확하게 수정
    keyword_list = ["삼성 갤럭시북", "나이키 운동화", "애플 아이패드", "LG 모니터"]
    target = random.choice(keyword_list)
    
    print(f"🚀 진단 모드 가동: {target}")
    products = fetch_data(target)
    print(f"📦 수집된 상품 수: {len(products)}개")
    
    if not products:
        print("⚠️ 수집된 상품이 없어 작업을 종료합니다.")
        return

    for item in products:
        # (기존 포스팅 생성 로직 유지)
        p_id = item['productId']
        filename = f"posts/{datetime.now().strftime('%Y%m%d')}_{p_id}.html"
        if os.path.exists(filename): 
            print(f"⏭️ {p_id} 이미 존재함")
            continue
        
        print(f"📝 {item['productName'][:20]}... 생성 중")
        ai_content = generate_ai_content(item)
        img = item['productImage'].split('?')[0]
        price = format(item['productPrice'], ',')
        
        with open(filename, "w", encoding="utf-8") as f:
            f.write(f"<html><head><title>{item['productName']}</title></head><body><h2>{item['productName']}</h2><img src='{img}'><div class='content'>{ai_content}</div><b>{price}원</b></body></html>")
        time.sleep(10)

    # 인덱스 및 사이트맵 업데이트
    files = sorted([f for f in os.listdir("posts") if f.endswith(".html")], reverse=True)
    with open("index.html", "w", encoding="utf-8") as f:
        f.write("<!DOCTYPE html><html><body><h1>🚀 실시간 핫딜</h1>")
        for file in files[:50]:
            f.write(f"<li><a href='posts/{file}'>{file}</a></li>")
        f.write("</body></html>")
    print("✨ 모든 동기화 완료!")

if __name__ == "__main__":
    main()
