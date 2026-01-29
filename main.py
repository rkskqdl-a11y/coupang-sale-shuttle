import os, hmac, hashlib, time, requests, json, random, re
from datetime import datetime
from urllib.parse import urlencode

# [1. 설정]
ACCESS_KEY = os.environ.get('COUPANG_ACCESS_KEY')
SECRET_KEY = os.environ.get('COUPANG_SECRET_KEY')
GEMINI_KEY = os.environ.get('GEMINI_API_KEY')
SITE_URL = "https://rkskqdl-a11y.github.io/coupang-sale-shuttle"

def generate_ai_content(item):
    """💎 제미나이가 상품 정보를 분석하여 실사용 느낌의 리뷰를 씁니다."""
    if not GEMINI_KEY: return "상세 분석 데이터를 불러오는 중입니다."
    
    name = item.get('productName')
    price = format(item.get('productPrice', 0), ',')
    clean_name = re.sub(r'나이키|NIKE|삼성|LG|애플|APPLE|샤오미|다이슨', '', name, flags=re.I)
    short_name = " ".join(clean_name.split()[:4]).strip()
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_KEY}"
    prompt = (
        f"당신은 쇼핑 에디터입니다. '{short_name}'(가격 {price}원)에 대해 리뷰를 작성하세요.\n"
        "1. 브랜드명은 빼고 '이 모델'로 지칭할 것.\n"
        "2. <h3> 태그로 디자인, 성능, 만족도 섹션을 나눌 것.\n"
        "3. 전문적이고 친절한 해요체로 작성하고 추천 대상을 정리할 것. HTML 태그만 사용하세요."
    )
    
    try:
        payload = {"contents": [{"parts": [{"text": prompt}]}]}
        response = requests.post(url, json=payload, timeout=30)
        res_data = response.json()
        # 💎 버그 수정: 리스트 인덱스 [0] 추가
        if 'candidates' in res_data:
            content = res_data['candidates'][0]['content']['parts'][0]['text']
            return content.replace("```html", "").replace("```", "").strip()
        return f"<h3>🔍 에디터 추천</h3>{short_name}은 {price}원에 만날 수 있는 최적의 선택입니다."
    except: return "전문 분석 데이터가 준비되었습니다."

def fetch_data(keyword):
    """쿠팡 API로 상품 수집"""
    try:
        DOMAIN = "https://api-gateway.coupang.com"
        path = "/v2/providers/affiliate_open_api/apis/openapi/v1/products/search"
        params = {"keyword": keyword, "limit": 10}
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
    keyword_pool = ["가성비 노트북", "인기 무선청소기", "캠핑 필수템", "자취생 가전", "신상 운동화"]
    target = random.choice(keyword_pool)
    print(f"🚀 검색 가동: {target}")
    products = fetch_data(target)
    
    for item in products:
        try:
            if item.get('discountRate', 0) < 5: continue 
            p_id = item['productId']
            filename = f"posts/{datetime.now().strftime('%Y%m%d')}_{p_id}.html"
            if os.path.exists(filename): continue 

            ai_content = generate_ai_content(item)
            # 💎 버그 수정: 리스트가 아닌 문자열로 가져옴
            img_url = item['productImage'].split('?')[0]
            price = format(item['productPrice'], ',')

            with open(filename, "w", encoding="utf-8") as f:
                f.write(f"""<!DOCTYPE html><html lang='ko'>
                <head><meta charset='UTF-8'><meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>{item['productName']} 리뷰</title>
                <style>body{{font-family:sans-serif; background:#f4f7f6; padding:20px; color:#333; line-height:1.8;}}.card{{max-width:600px; margin:auto; background:white; padding:30px; border-radius:15px; box-shadow:0 10px 25px rgba(0,0,0,0.05);}} h2{{font-size:1.2rem; color:#222;}} h3{{color:#ff4d4d; margin-top:25px; border-left:5px solid #ff4d4d; padding-left:15px;}} img{{width:100%; border-radius:10px; margin:20px 0;}}.price{{font-size:2rem; color:#ff4d4d; font-weight:bold; text-align:center;}}.buy-btn{{display:block; background:#ff4d4d; color:white; text-align:center; padding:15px; text-decoration:none; border-radius:50px; font-weight:bold;}}</style></head>
                <body><div class='card'><h2>{item['productName']}</h2><img src='{img_url}'><div class='content'>{ai_content}</div><div class='price'>{price}원</div><a href='{item['productUrl']}' class='buy-btn' target='_blank'>🔥 특가 확인 및 구매하기</a></div></body></html>""")
            
            print(f"✅ 생성 완료: {p_id}")
            time.sleep(35) # 제미나이 무료 버전 속도 제한 준수
        except: continue

    # 인덱스 페이지 업데이트
    files = sorted([f for f in os.listdir("posts") if f.endswith(".html")], reverse=True)
    with open("index.html", "w", encoding="utf-8") as f:
        f.write("<!DOCTYPE html><html><head><meta charset='UTF-8'><title>핫딜 리스트</title><style>body{font-family:sans-serif; padding:20px;} .grid{display:grid; grid-template-columns:repeat(auto-fill, minmax(250px, 1fr)); gap:20px;} .card{padding:20px; border:1px solid #ddd; border-radius:10px; text-decoration:none; color:black;}</style></head><body><h1>🚀 핫딜 리스트</h1><div class='grid'>")
        for file in files[:100]:
            f.write(f"<a class='card' href='posts/{file}'><div>{file[:8]} 추천상품</div></a>")
        f.write("</div></body></html>")

if __name__ == "__main__":
    main()
