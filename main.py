import os, hmac, hashlib, time, requests, json, random, re
from datetime import datetime
from urllib.parse import urlencode
from google import genai

# [1. 설정]
ACCESS_KEY = os.environ.get('COUPANG_ACCESS_KEY')
SECRET_KEY = os.environ.get('COUPANG_SECRET_KEY')
GEMINI_KEY = os.environ.get('GEMINI_API_KEY')
SITE_URL = "https://rkskqdl-a11y.github.io/coupang-sale-shuttle"

# 💎 404 에러 방지: v1 정식 버전을 사용하도록 설정합니다
client = None
if GEMINI_KEY:
    client = genai.Client(
        api_key=GEMINI_KEY,
        http_options={'api_version': 'v1'}
    )

def get_title_from_html(filepath):
    """파일 안에서 실제 상품명을 찾아 인덱스에 표시합니다."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            # <title> 태그 안의 내용을 가져옵니다.
            match = re.search(r'<title>(.*?)</title>', content)
            if match:
                title = match.group(1).replace(" 리뷰", "").strip()
                # 너무 길면 자르기
                return (title[:40] + '..') if len(title) > 40 else title
    except: pass
    return "상품 상세 정보"

def generate_ai_content(product_name, price):
    """중복 문구 방지 및 고품질 리뷰 생성"""
    if not client: return "상세 리뷰를 준비 중입니다."
    
    # AI가 헷갈리지 않게 상품명을 3단어 정도로 요약
    short_name = " ".join(product_name.split()[:3])
    try:
        # 🤖 AI에게 본론만 쓰라고 명령 (제목/인사 생략)
        response = client.models.generate_content(
            model='gemini-1.5-flash',
            contents=f"상품 '{short_name}'({price}원)의 리뷰를 써줘. 제목이나 상품명은 절대 다시 쓰지 말고, <h3> 태그를 사용해 장점과 특징만 500자 내외로 바로 시작해줘. HTML(h3, br)만 사용해."
        )
        return response.text.replace("\n", "<br>")
    except Exception as e:
        print(f"❌ AI 에러: {e}")
        return f"<h3>🔍 에디터의 한줄 평</h3>{short_name}은 현재 {price}원의 가격대에서 가장 믿음직한 선택입니다. 뛰어난 가성비와 깔끔한 디자인으로 많은 사용자들에게 호평을 받고 있는 제품입니다."

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
    target = f"{random.choice(['인기', '추천'])} {random.choice(['삼성', '나이키', 'LG'])} {random.choice(['노트북', '방한화', '운동화'])}"
    print(f"🚀 안정화 모드로 실행 중: {target}")
    products = fetch_data(target)
    
    for item in products:
        try:
            p_id = item['productId']
            clean_img_url = item['productImage'].split('?')[0]
            price_str = format(item['productPrice'], ',')
            
            # 파일명을 날짜_ID로 단순화하여 중복 방지
            filename = f"posts/{datetime.now().strftime('%Y%m%d')}_{p_id}.html"
            if os.path.exists(filename): continue 
            
            ai_content = generate_ai_content(item['productName'], price_str)
            
            with open(filename, "w", encoding="utf-8") as f:
                f.write(f"""<!DOCTYPE html><html lang='ko'>
                <head><meta charset='UTF-8'><meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>{item['productName']} 리뷰</title>
                <style>
                    body {{ font-family: sans-serif; background: #f4f7f6; padding: 20px; line-height: 1.8; color: #333; }}
                    .card {{ max-width: 600px; margin: auto; background: white; padding: 40px; border-radius: 20px; box-shadow: 0 10px 20px rgba(0,0,0,0.05); }}
                    h2 {{ font-size: 1.3rem; color: #222; margin-bottom: 25px; border-left: 5px solid #e44d26; padding-left: 15px; }}
                    h3 {{ color: #e44d26; margin-top: 30px; border-bottom: 1px solid #eee; padding-bottom: 5px; }}
                    img {{ width: 100%; border-radius: 15px; margin: 20px 0; }}
                    .price {{ font-size: 1.8rem; color: #e44d26; font-weight: bold; text-align: center; margin: 30px 0; }}
                    .buy-btn {{ display: block; background: #e44d26; color: white; text-align: center; padding: 18px; text-decoration: none; border-radius: 50px; font-weight: bold; font-size: 1.1rem; }}
                </style></head>
                <body><div class='card'>
                    <h2>{item['productName']}</h2>
                    <img src='{clean_img_url}'>
                    <div class='content'>{ai_content}</div>
                    <div class='price'>{price_str}원</div>
                    <a href='{item['productUrl']}' class='buy-btn'>🛍️ 최저가 확인 및 구매하기</a>
                    <p style='font-size: 0.75rem; color: #999; margin-top: 30px; text-align: center;'>본 포스팅은 쿠팡 파트너스 활동의 일환으로 수수료를 제공받을 수 있습니다.</p>
                </div></body></html>""")
            time.sleep(35)
        except: continue

    # [인덱스 업데이트]
    files = sorted([f for f in os.listdir("posts") if f.endswith(".html")], reverse=True)
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(f"<!DOCTYPE html><html><head><meta charset='UTF-8'><title>핫딜 셔틀</title><style>body{{font-family:sans-serif; background:#f0f2f5; padding:20px;}} .grid{{display:grid; grid-template-columns:repeat(auto-fill, minmax(280px, 1fr)); gap:20px;}} .card{{background:white; padding:25px; border-radius:15px; text-decoration:none; color:#333; box-shadow:0 2px 10px rgba(0,0,0,0.05); height: 130px; display: flex; flex-direction: column; justify-content: space-between;}} .title{{font-weight: bold; font-size: 0.95rem; overflow: hidden; text-overflow: ellipsis; display: -webkit-box; -webkit-line-clamp: 3; -webkit-box-orient: vertical;}}</style></head><body><h1 style='text-align:center;'>🚀 실시간 핫딜 쇼핑몰</h1><div class='grid'>")
        for file in files[:100]:
            # 💎 파일 내부의 진짜 제목을 가져옵니다.
            display_title = get_title_from_html(f"posts/{file}")
            f.write(f"<a class='card' href='posts/{file}'><div class='title'>{display_title}</div><div style='color:#e44d26; font-size:0.8rem;'>상세 리뷰 보기 ></div></a>")
        f.write("</div></body></html>")
    
    # 사이트맵 및 기타 파일 유지
    with open("sitemap.xml", "w", encoding="utf-8") as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n')
        f.write(f'<url><loc>{SITE_URL}/</loc><priority>1.0</priority></url>\n')
        for file in files: f.write(f'<url><loc>{SITE_URL}/posts/{file}</loc><priority>0.8</priority></url>\n')
        f.write('</urlset>')
    with open("robots.txt", "w", encoding="utf-8") as f:
        f.write(f"User-agent: *\nAllow: /\nSitemap: {SITE_URL}/sitemap.xml")

if __name__ == "__main__":
    main()
