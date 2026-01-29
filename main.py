import os, hmac, hashlib, time, requests, json, random, re
from datetime import datetime
from urllib.parse import urlencode

# [1. 설정]
ACCESS_KEY = os.environ.get('COUPANG_ACCESS_KEY')
SECRET_KEY = os.environ.get('COUPANG_SECRET_KEY')
GEMINI_KEY = os.environ.get('GEMINI_API_KEY')
SITE_URL = "https://rkskqdl-a11y.github.io/coupang-sale-shuttle"

def generate_ai_content(item):
    """💎 API 데이터를 종합 분석하여 실사용 느낌의 전문 리뷰를 생성합니다."""
    if not GEMINI_KEY: return "상세 정보를 분석 중입니다."
    
    # AI에게 전달할 데이터 정리
    name = item.get('productName')
    price = format(item.get('productPrice'), ',')
    discount = item.get('discountRate', 0)
    rocket = "로켓배송 가능" if item.get('isRocket') else "일반배송"
    
    # 🤖 고도화된 실사용 리뷰 프롬프트
    prompt_text = f"""
    너는 100만 구독자를 보유한 쇼핑 전문 유튜버이자 리뷰어야. 
    상품 '{name}'에 대해 인터넷의 실사용 후기와 테크니컬 데이터를 종합 분석해서 블로그 글을 써줘.
    
    [상품 데이터]
    - 가격: {price}원 (할인율: {discount}%)
    - 배송: {rocket}
    
    [작성 가이드]
    1. 말투: 독자에게 직접 말하는 듯한 친근하고 전문적인 '해요체'
    2. 내용: 마치 일주일간 직접 사용해본 것처럼 구체적인 장단점을 묘사해줘. 
    3. 구성: 아래 섹션을 포함하고 <h3> 태그를 사용해줘.
       - <h3>🔍 실물 체감 및 첫인상</h3>: 디자인이나 마감 처리 등에 대해 언급.
       - <h3>🚀 직접 써보고 느낀 '진짜' 장점</h3>: 실제 생활에서 얼마나 편리한지 3가지 포인트.
       - <h3>⚠️ 구매 전 고려해야 할 점</h3>: 사용자가 놓칠 수 있는 단점이나 주의사항.
       - <h3>종합 평가</h3>: 현재 {discount}% 할인율이 갖는 메리트와 최종 추천 점수.
    4. 주의: 상품명을 너무 반복하지 말고 '이 제품', '이 녀석' 등으로 자연스럽게 표현해. HTML(h3, br)만 사용.
    """

    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_KEY}"
    payload = {
        "contents": [{"parts": [{"text": prompt_text}]}],
        "safetySettings": [{"category": c, "threshold": "BLOCK_NONE"} for c in ["HARM_CATEGORY_HARASSMENT", "HARM_CATEGORY_HATE_SPEECH", "HARM_CATEGORY_SEXUALLY_EXPLICIT", "HARM_CATEGORY_DANGEROUS_CONTENT"]]
    }

    try:
        response = requests.post(url, json=payload, timeout=20)
        res_data = response.json()
        if 'candidates' in res_data:
            return res_data['candidates'][0]['content']['parts'][0]['text'].replace("\n", "<br>")
        return "상세 리뷰 분석 중 에러가 발생했습니다."
    except:
        return f"<h3>💡 에디터의 추천 포인트</h3>{name}은 현재 {discount}% 할인된 {price}원에 만나보실 수 있는 절호의 기회입니다. 실사용 만족도가 매우 높은 제품입니다."

def fetch_data(keyword):
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
    sets = [("삼성", "노트북"), ("LG", "생활가전"), ("애플", "아이패드"), ("나이키", "러닝화"), ("필립스", "면도기")]
    brand, item_type = random.choice(sets)
    target = f"인기 {brand} {item_type}"
    products = fetch_data(target)
    
    for item in products:
        try:
            p_id = item['productId']
            img = item['productImage'].split('?')[0]
            price = format(item['productPrice'], ',')
            discount = item.get('discountRate', 0)
            rocket_icon = "🚀 로켓배송" if item.get('isRocket') else ""
            
            filename = f"posts/{datetime.now().strftime('%Y%m%d')}_{p_id}.html"
            if os.path.exists(filename): continue 
            
            ai_content = generate_ai_content(item)
            
            with open(filename, "w", encoding="utf-8") as f:
                f.write(f"""<!DOCTYPE html><html lang='ko'>
                <head><meta charset='UTF-8'><meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>{item['productName']} 리뷰</title>
                <style>
                    body {{ font-family: sans-serif; background: #f8f9fa; padding: 20px; color: #333; line-height: 1.8; }}
                    .card {{ max-width: 650px; margin: auto; background: white; padding: 40px; border-radius: 30px; box-shadow: 0 20px 40px rgba(0,0,0,0.05); }}
                    .badge {{ background: #e44d26; color: white; padding: 5px 12px; border-radius: 5px; font-weight: bold; font-size: 0.9rem; }}
                    .rocket {{ color: #0073e6; font-weight: bold; }}
                    h2 {{ font-size: 1.4rem; margin-top: 20px; color: #111; }}
                    h3 {{ color: #e44d26; margin-top: 35px; border-left: 4px solid #e44d26; padding-left: 15px; }}
                    img {{ width: 100%; border-radius: 20px; margin: 25px 0; }}
                    .price-box {{ text-align: center; background: #fff5f2; padding: 20px; border-radius: 20px; margin: 30px 0; }}
                    .old-price {{ text-decoration: line-through; color: #999; }}
                    .current-price {{ font-size: 2.2rem; color: #e44d26; font-weight: bold; }}
                    .buy-btn {{ display: block; background: #e44d26; color: white; text-align: center; padding: 20px; text-decoration: none; border-radius: 50px; font-weight: bold; font-size: 1.3rem; transition: 0.3s; }}
                </style></head>
                <body><div class='card'>
                    <div><span class='badge'>{discount}% SALE</span> <span class='rocket'>{rocket_icon}</span></div>
                    <h2>{item['productName']}</h2>
                    <img src='{img}'>
                    <div class='content'>{ai_content}</div>
                    <div class='price-box'>
                        <div class='current-price'>{price}원</div>
                    </div>
                    <a href='{item['productUrl']}' class='buy-btn'>🛍️ 최저가 확인 및 구매하기</a>
                    <p style='font-size: 0.8rem; color: #999; margin-top: 30px; text-align: center;'>본 포스팅은 쿠팡 파트너스 활동의 일환으로 수수료를 제공받을 수 있습니다.</p>
                </div></body></html>""")
            time.sleep(35)
        except: continue

    # [인덱스 업데이트]
    files = sorted([f for f in os.listdir("posts") if f.endswith(".html")], reverse=True)
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(f"<!DOCTYPE html><html><head><meta charset='UTF-8'><title>실시간 핫딜 셔틀</title><style>body{{font-family:sans-serif; background:#f0f2f5; padding:20px;}} .grid{{display:grid; grid-template-columns:repeat(auto-fill, minmax(300px, 1fr)); gap:25px;}} .card{{background:white; padding:30px; border-radius:20px; text-decoration:none; color:#333; box-shadow:0 4px 15px rgba(0,0,0,0.05); display: flex; flex-direction: column; justify-content: space-between;}} .discount{{color:#e44d26; font-weight:bold;}}</style></head><body><h1 style='text-align:center;'>🚀 실시간 핫딜 쇼핑몰</h1><div class='grid'>")
        for file in files[:100]:
            try:
                with open(f"posts/{file}", 'r', encoding='utf-8') as f_read:
                    content = f_read.read()
                    title = re.search(r'<title>(.*?)</title>', content).group(1).replace(" 리뷰", "")
                    disc = re.search(r"<span class='badge'>(.*?)</span>", content).group(1)
                f.write(f"<a class='card' href='posts/{file}'><div><span class='discount'>[{disc}]</span> {title[:40]}...</div><div style='color:#e44d26; margin-top:15px; font-weight:bold;'>상세 리뷰 보기 ></div></a>")
            except: continue
        f.write("</div></body></html>")
