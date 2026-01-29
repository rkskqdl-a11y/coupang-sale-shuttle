import os, hmac, hashlib, time, requests, json, random, re
from datetime import datetime
from urllib.parse import urlencode
# 💎 최신 라이브러리로 변경 (import 방식이 달라졌습니다)
from google import genai

# [1. 기본 설정]
ACCESS_KEY = os.environ.get('COUPANG_ACCESS_KEY')
SECRET_KEY = os.environ.get('COUPANG_SECRET_KEY')
GEMINI_KEY = os.environ.get('GEMINI_API_KEY')
SITE_URL = "https://rkskqdl-a11y.github.io/coupang-sale-shuttle"

# 💎 최신 클라이언트 초기화
client = None
if GEMINI_KEY:
    client = genai.Client(api_key=GEMINI_KEY)

def clean_product_name(name):
    """지저분한 상품명을 AI가 처리하기 좋게 핵심만 남깁니다."""
    clean = re.sub(r'\(.*?\)|\[.*?\]', '', name)
    clean = clean.split(',')[0].split('+')[0].strip()
    words = clean.split()
    return " ".join(words[:4]) if len(words) > 4 else clean

def generate_ai_content(product_name, price):
    """💎 최신 google-genai 방식을 사용하여 리뷰를 생성합니다."""
    if not client: return "상품 상세 정보를 분석 중입니다."
    
    # SEO를 위해 핵심 이름만 추출
    short_name = clean_product_name(product_name)
    try:
        # 최신 SDK 호출 방식 (models.generate_content)
        response = client.models.generate_content(
            model='gemini-1.5-flash',
            contents=f"상품 '{short_name}'(가격 {price}원)의 쇼핑 리뷰를 블로그 포스팅 형식으로 써줘. 제목이나 상품명 반복은 피하고 <h3> 태그를 사용해 장점, 특징, 추천 대상을 600자 내외로 상세히 설명해줘. 마크다운 기호 없이 HTML(h3, br)만 써줘."
        )
        return response.text.replace("\n", "<br>")
    except Exception as e:
        print(f"❌ AI 에러 발생: {e}")
        return f"<h3>🔍 에디터 추천 이유</h3>이 제품은 현재 {price}원의 가격대에서 가장 우수한 성능을 보여주는 모델입니다. 세련된 디자인과 탄탄한 기본기를 갖춰 많은 사랑을 받고 있습니다."

def get_title_from_html(filepath):
    """파일 안에서 실제 제목을 읽어와 메인 페이지에 표시합니다."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            match = re.search(r'<title>(.*?)</title>', content)
            if match: return match.group(1).replace(" 리뷰", "")
    except: pass
    return "상세 리뷰 보기"

def fetch_data(keyword):
    try:
        DOMAIN = "https://api-gateway.coupang.com"
        path = "/v2/providers/affiliate_open_api/apis/openapi/v1/products/search"
        params = {"keyword": keyword, "limit": 10}
        query_string = urlencode(params)
        url = f"{DOMAIN}{path}?{query_string}"
        headers = {
            "Authorization": get_authorization_header("GET", path, query_string),
            "Content-Type": "application/json"
        }
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
    target = f"{random.choice(['인기', '추천'])} {random.choice(['나이키', '아디다스', '삼성'])} {random.choice(['운동화', '방한화', '노트북'])}"
    print(f"🚀 최신 AI 엔진 가동: {target}")
    products = fetch_data(target)
    
    for item in products:
        try:
            p_id = item['productId']
            clean_img_url = item['productImage'].split('?')[0]
            price_str = format(item['productPrice'], ',')
            
            filename = f"posts/{datetime.now().strftime('%Y%m%d')}_{p_id}.html"
            if os.path.exists(filename): continue 
            
            # 💎 AI 리뷰 생성
            ai_content = generate_ai_content(item['productName'], price_str)
            
            with open(filename, "w", encoding="utf-8") as f:
                f.write(f"""<!DOCTYPE html><html lang='ko'>
                <head><meta charset='UTF-8'><meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>{item['productName']} 리뷰</title>
                <style>
                    body {{ font-family: sans-serif; background: #f4f7f6; padding: 20px; line-height: 1.8; color: #333; }}
                    .card {{ max-width: 600px; margin: auto; background: white; padding: 40px; border-radius: 20px; box-shadow: 0 10px 20px rgba(0,0,0,0.05); }}
                    h2 {{ font-size: 1.4rem; color: #222; margin-bottom: 25px; border-left: 5px solid #e44d26; padding-left: 15px; }}
                    h3 {{ color: #e44d26; margin-top: 30px; border-bottom: 1px solid #eee; padding-bottom: 5px; }}
                    img {{ width: 100%; border-radius: 15px; margin: 20px 0; }}
                    .price {{ font-size: 2rem; color: #e44d26; font-weight: bold; text-align: center; margin: 30px 0; }}
                    .buy-btn {{ display: block; background: #e44d26; color: white; text-align: center; padding: 20px; text-decoration: none; border-radius: 50px; font-weight: bold; font-size: 1.2rem; }}
                </style></head>
                <body><div class='card'>
                    <h2>{item['productName']}</h2>
                    <img src='{clean_img_url}'>
                    <div class='content'>{ai_content}</div>
                    <div class='price'>{price_str}원</div>
                    <a href='{item['productUrl']}' class='buy-btn'>🛒 최저가 확인 및 구매하기</a>
                    <p style='font-size: 0.8rem; color: #999; margin-top: 30px; text-align: center;'>본 포스팅은 쿠팡 파트너스 활동의 일환으로 수수료를 제공받을 수 있습니다.</p>
                </div></body></html>""")
            time.sleep(35)
        except: continue

    # 💎 메인 페이지 업데이트 (중복 문제 해결)
    files = sorted([f for f in os.listdir("posts") if f.endswith(".html")], reverse=True)
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(f"<!DOCTYPE html><html><head><meta charset='UTF-8'><title>핫딜 셔틀</title><style>body{{font-family:sans-serif; background:#f0f2f5; padding:20px;}} .grid{{display:grid; grid-template-columns:repeat(auto-fill, minmax(280px, 1fr)); gap:20px;}} .card{{background:white; padding:25px; border-radius:15px; text-decoration:none; color:#333; box-shadow:0 2px 10px rgba(0,0,0,0.05); overflow:hidden; text-overflow:ellipsis; display:-webkit-box; -webkit-line-clamp:3; -webkit-box-orient:vertical; height: 120px;}}</style></head><body><h1 style='text-align:center;'>🚀 실시간 핫딜 쇼핑몰</h1><div class='grid'>")
        for file in files[:100]:
            real_title = get_title_from_html(f"posts/{file}")
            f.write(f"<a class='card' href='posts/{file}'><div>{real_title}</div><div style='color:#e44d26; font-size:0.8rem; margin-top:10px;'>상세 리뷰 보기 ></div></a>")
        f.write("</div></body></html>")
    
    # 사이트맵/로봇 파일 갱신 로직 유지
    with open("sitemap.xml", "w", encoding="utf-8") as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n')
        f.write(f'<url><loc>{SITE_URL}/</loc><priority>1.0</priority></url>\n')
        for file in files: f.write(f'<url><loc>{SITE_URL}/posts/{file}</loc><priority>0.8</priority></url>\n')
        f.write('</urlset>')
    
    with open("robots.txt", "w", encoding="utf-8") as f:
        f.write(f"User-agent: *\nAllow: /\nSitemap: {SITE_URL}/sitemap.xml")

if __name__ == "__main__":
    main()
