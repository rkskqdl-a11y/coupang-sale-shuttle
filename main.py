import os, hmac, hashlib, time, requests, json, random, re
from datetime import datetime
from urllib.parse import urlencode
import google.generativeai as genai

# [설정]
ACCESS_KEY = os.environ.get('COUPANG_ACCESS_KEY')
SECRET_KEY = os.environ.get('COUPANG_SECRET_KEY')
GEMINI_KEY = os.environ.get('GEMINI_API_KEY')
SITE_URL = "https://rkskqdl-a11y.github.io/coupang-sale-shuttle"

if GEMINI_KEY:
    genai.configure(api_key=GEMINI_KEY)

def clean_product_name(name):
    """💎 지저분한 쿠팡 상품명을 핵심만 남기고 청소합니다."""
    # 쉼표, 괄호, 특수문자 뒤의 지저분한 키워드 제거
    clean = re.sub(r'\(.*?\)|\[.*?\]', '', name)
    clean = clean.split(',')[0].split('+')[0].strip()
    # 너무 긴 제목은 앞의 5단어만 사용
    words = clean.split()
    return " ".join(words[:5]) if len(words) > 5 else clean

def generate_ai_content(full_name, price):
    """💎 상품명을 정제하여 AI에게 고품질 리뷰를 요청합니다."""
    if not GEMINI_KEY: return "리뷰 준비 중..."
    
    clean_name = clean_product_name(full_name) # 핵심 이름 추출
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        # 🤖 AI에게 명확한 '구조'를 명령합니다.
        prompt = f"""
        너는 베테랑 쇼핑 에디터야. 상품 '{clean_name}'(가격 {price}원)의 상세 리뷰를 작성해줘.
        단순 나열이 아닌, 실제 사용자가 궁금해할 정보를 800자 내외로 풍성하게 써야 해.

        [필수 포함 내용]
        1. <h3>🌟 이 상품만의 독보적인 매력</h3>: 경쟁 제품과 차별화되는 점
        2. <h3>✅ 실사용자가 꼽은 최고의 장점</h3>: 실제 편리함 위주로 3가지 설명
        3. <h3>💡 구매 전 꼭 알아야 할 팁</h3>: 사이즈 선택이나 관리법 등
        4. <h3>💰 가성비 최종 평가</h3>: 현재 가격 대비 가치 분석

        * 주의: 말투는 정중한 해요체로 하고, 마크다운(#, *)은 쓰지 말고 HTML 태그(h3, br)만 사용해.
        """
        response = model.generate_content(prompt)
        # ⚠️ AI가 빈 답변을 줬을 경우를 대비
        if not response.text: raise ValueError("AI 답변이 비어있음")
        return response.text.replace("\n", "<br>")
    except Exception as e:
        print(f"❌ AI 에러 발생: {e}") # 로그에 실패 원인 기록
        # 비상용 문구도 상품마다 다르게 나오도록 설정
        return f"<h3>{clean_name} 실속 리뷰</h3>{clean_name}은 현재 {price}원의 가격대에서 가장 합리적인 선택지 중 하나입니다. 품질과 디자인 모두 만족스러운 제품이니 놓치지 마세요!"

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
    target = f"{random.choice(['가성비', '인기', '추천'])} {random.choice(['삼성', '나이키', 'LG'])} {random.choice(['노트북', '운동화', '에어팟'])}"
    products = fetch_data(target)
    
    for item in products:
        try:
            p_id = item['productId']
            # 이미지 URL 버그 수정
            clean_img_url = item['productImage'].split('?')[0]
            price_str = format(item['productPrice'], ',')
            
            filename = f"posts/{datetime.now().strftime('%Y%m%d')}_{p_id}.html"
            if os.path.exists(filename): continue 
            
            print(f"💎 AI가 '{item['productName'][:20]}...' 리뷰를 작성 중입니다.")
            ai_content = generate_ai_content(item['productName'], price_str)
            
            with open(filename, "w", encoding="utf-8") as f:
                f.write(f"""<!DOCTYPE html><html lang='ko'>
                <head><meta charset='UTF-8'><meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>{item['productName']} 리뷰</title>
                <style>
                    body {{ font-family: sans-serif; background: #f4f7f6; padding: 20px; line-height: 1.8; color: #333; }}
                    .card {{ max-width: 600px; margin: auto; background: white; padding: 40px; border-radius: 20px; box-shadow: 0 10px 20px rgba(0,0,0,0.05); }}
                    h2 {{ font-size: 1.4rem; color: #222; margin-bottom: 20px; border-left: 5px solid #e44d26; padding-left: 15px; }}
                    h3 {{ color: #e44d26; margin-top: 30px; border-bottom: 1px solid #eee; padding-bottom: 5px; }}
                    img {{ width: 100%; border-radius: 15px; margin: 20px 0; }}
                    .price {{ font-size: 2rem; color: #e44d26; font-weight: bold; text-align: center; margin: 30px 0; }}
                    .buy-btn {{ display: block; background: #e44d26; color: white; text-align: center; padding: 20px; text-decoration: none; border-radius: 50px; font-weight: bold; font-size: 1.2rem; }}
                </style></head>
                <body><div class='card'>
                    <h2>{item['productName']}</h2>
                    <img src='{clean_img_url}' alt='{item['productName']}'>
                    <div class='content'>{ai_content}</div>
                    <div class='price'>{price_str}원</div>
                    <a href='{item['productUrl']}' class='buy-btn'>🛒 최저가 확인 및 구매하기</a>
                    <p style='font-size: 0.8rem; color: #999; margin-top: 30px; text-align: center;'>본 포스팅은 쿠팡 파트너스 활동의 일환으로 수수료를 제공받을 수 있습니다.</p>
                </div></body></html>""")
            time.sleep(35)
        except: continue

    # 인덱스 및 사이트맵 갱신 로직 (생략 - 기존 유지)
    files = sorted([f for f in os.listdir("posts") if f.endswith(".html")], reverse=True)
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(f"<!DOCTYPE html><html><head><meta charset='UTF-8'><title>핫딜 셔틀</title><style>body{{font-family:sans-serif; background:#f0f2f5; padding:20px;}} .grid{{display:grid; grid-template-columns:repeat(auto-fill, minmax(280px, 1fr)); gap:20px;}} .card{{background:white; padding:25px; border-radius:15px; text-decoration:none; color:#333; box-shadow:0 2px 10px rgba(0,0,0,0.05);}}</style></head><body><h1 style='text-align:center;'>🚀 실시간 핫딜 쇼핑몰</h1><div class='grid'>")
        for file in files[:100]:
            f.write(f"<a class='card' href='posts/{file}'><div>{file.split('_')[1] if '_' in file else '상품'}</div><div style='color:#e44d26; font-size:0.9rem; margin-top:15px;'>상세 리뷰 보기 ></div></a>")
        f.write("</div></body></html>")
    
    with open("sitemap.xml", "w", encoding="utf-8") as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n')
        f.write(f'<url><loc>{SITE_URL}/</loc><priority>1.0</priority></url>\n')
        for file in files: f.write(f'<url><loc>{SITE_URL}/posts/{file}</loc><priority>0.8</priority></url>\n')
        f.write('</urlset>')
    
    with open("robots.txt", "w", encoding="utf-8") as f:
        f.write(f"User-agent: *\nAllow: /\nSitemap: {SITE_URL}/sitemap.xml")

if __name__ == "__main__":
    main()
