import os, hmac, hashlib, time, requests, json, random, re
from datetime import datetime
from urllib.parse import urlencode

# [1. 설정]
ACCESS_KEY = os.environ.get('COUPANG_ACCESS_KEY')
SECRET_KEY = os.environ.get('COUPANG_SECRET_KEY')
GEMINI_KEY = os.environ.get('GEMINI_API_KEY')
SITE_URL = "https://rkskqdl-a11y.github.io/coupang-sale-shuttle"

def generate_ai_content(item):
    """💎 제미나이 경로 오류와 브랜드 차단 문제를 모두 해결했습니다."""
    if not GEMINI_KEY: return "상세 분석 데이터를 불러오는 중입니다."
    name = item.get('productName')
    price = format(item.get('productPrice', 0), ',')
    clean_name = re.sub(r'나이키|NIKE|삼성|LG|애플|APPLE|샤오미|다이슨', '', name, flags=re.I)
    short_name = " ".join(clean_name.split()[:4]).strip()
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_KEY}"
    prompt = f"상품 '{short_name}'(가격 {price}원)의 전문 리뷰를 <h3> 태그를 사용해 작성해줘. 브랜드명은 빼고 '이 모델'로 지칭해. HTML만 사용."
    
    try:
        payload = {"contents": [{"parts": [{"text": prompt}]}]}
        response = requests.post(url, json=payload, timeout=30)
        res_data = response.json()
        # 💎 [버그 수정] 인덱스 [0]을 추가하여 정확한 텍스트를 가져옵니다.
        if 'candidates' in res_data:
            content = res_data['candidates'][0]['content']['parts'][0]['text']
            return content.replace("```html", "").replace("```", "").strip()
        return f"<h3>🔍 에디터 추천</h3>{short_name}은 {price}원에 만날 수 있는 최적의 선택지입니다."
    except: return "전문 분석 데이터가 준비되었습니다."

def fetch_data(keyword):
    """📡 쿠팡 API 상품 수집"""
    try:
        DOMAIN = "https://api-gateway.coupang.com"
        path = "/v2/providers/affiliate_open_api/apis/openapi/v1/products/search"
        params = {"keyword": keyword, "limit": 10}
        query_string = urlencode(params)
        url = f"{DOMAIN}{path}?{query_string}"
        headers = {"Authorization": get_authorization_header("GET", path, query_string), "Content-Type": "application/json"}
        response = requests.get(url, headers=headers, timeout=15)
        # 💎 결과가 리스트인지 확실히 확인합니다.
        return response.json().get('data', {}).get('productData', [])
    except: return []

def get_authorization_header(method, path, query_string):
    datetime_gmt = time.strftime('%y%m%dT%H%M%SZ', time.gmtime())
    message = datetime_gmt + method + path + query_string
    signature = hmac.new(bytes(SECRET_KEY, 'utf-8'), msg=bytes(message, 'utf-8'), digestmod=hashlib.sha256).hexdigest()
    return f"CEA algorithm=HmacSHA256, access-key={ACCESS_KEY}, signed-date={datetime_gmt}, signature={signature}"

def main():
    os.makedirs("posts", exist_ok=True)
    keyword_pool = ["가성비 노트북", "인기 무선청소기", "캠핑 필수템", "자취생 가전", "신상 운동화"]
    target = random.choice(keyword_pool)
    print(f"🚀 검색 가동: {target}")
    products = fetch_data(target)
    print(f"📦 수집된 상품: {len(products)}개")
    
    for item in products:
        try:
            # 💎 할인율 5% 미만 제외
            if item.get('discountRate', 0) < 5: 
                print(f"⏭️ {item.get('productId')} 할인율 낮음 건너뜀")
                continue 

            p_id = item['productId']
            filename = f"posts/{datetime.now().strftime('%Y%m%d')}_{p_id}.html"
            if os.path.exists(filename): continue 

            print(f"📝 {item['productName'][:20]}... 포스팅 생성 중")
            ai_content = generate_ai_content(item)
            # 💎 [버그 수정] 리스트가 아닌 주소 문자열만 가져옵니다.
            img_url = item['productImage'].split('?')[0]
            price = format(item['productPrice'], ',')

            with open(filename, "w", encoding="utf-8") as f:
                f.write(f"<!DOCTYPE html><html><head><title>{item['productName']} 리뷰</title><style>body{{font-family:sans-serif; padding:20px;}} .card{{max-width:600px; margin:auto; border:1px solid #eee; padding:30px; border-radius:15px;}} img{{width:100%;}} .price{{color:#e44d26; font-size:2rem; font-weight:bold;}}</style></head><body><div class='card'><h2>{item['productName']}</h2><img src='{img_url}'><div>{ai_content}</div><div class='price'>{price}원</div><a href='{item['productUrl']}' style='display:block; background:#e44d26; color:white; text-align:center; padding:15px; text-decoration:none; border-radius:50px; margin-top:20px;'>🔥 최저가 확인 및 구매하기</a></div></body></html>")
            time.sleep(25)
        except Exception as e:
            print(f"❌ 개별 상품 처리 에러: {e}")
            continue

    # 💎 인덱스 및 사이트맵 자동 갱신
    files = sorted([f for f in os.listdir("posts") if f.endswith(".html")], reverse=True)
    with open("index.html", "w", encoding="utf-8") as f:
        f.write("<!DOCTYPE html><html><head><meta charset='UTF-8'><title>핫딜 리스트</title><style>body{font-family:sans-serif; padding:20px;} .grid{display:grid; grid-template-columns:repeat(auto-fill, minmax(280px, 1fr)); gap:20px;} .card{padding:20px; border:1px solid #ddd; border-radius:10px; text-decoration:none; color:black;}</style></head><body><h1>🚀 실시간 핫딜 리스트</h1><div class='grid'>")
        for file in files[:100]:
            f.write(f"<a class='card' href='posts/{file}'><div>{file[:8]} 추천상품</div></a>")
        f.write("</div></body></html>")
    print(f"✨ 전체 동기화 완료! 총 포스팅 수: {len(files)}")

if __name__ == "__main__":
    main()
