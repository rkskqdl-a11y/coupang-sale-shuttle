import os, hmac, hashlib, time, requests, json, random, re
from datetime import datetime
from urllib.parse import urlencode
from google import genai

# [1. 설정]
ACCESS_KEY = os.environ.get('COUPANG_ACCESS_KEY')
SECRET_KEY = os.environ.get('COUPANG_SECRET_KEY')
GEMINI_KEY = os.environ.get('GEMINI_API_KEY')
SITE_URL = "https://rkskqdl-a11y.github.io/coupang-sale-shuttle"

# 💎 가장 안정적인 클라이언트 설정 (버전 수동 지정 제거)
client = None
if GEMINI_KEY:
    client = genai.Client(api_key=GEMINI_KEY)

def get_title_from_html(filepath):
    """파일 내용에서 실제 상품명을 추출하여 메인에 표시합니다."""
    try:
        if not os.path.exists(filepath): return "상세 리뷰"
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            match = re.search(r'<title>(.*?)</title>', content)
            if match:
                # '리뷰' 글자를 떼고 깔끔하게 제목만 반환
                return match.group(1).replace(" 리뷰", "").strip()
    except: pass
    return "상품 상세 정보"

def generate_ai_content(product_name, price):
    """중복 방지 및 404 에러를 피하기 위한 견고한 호출"""
    if not client: return "리뷰를 준비 중입니다."
    
    # AI가 헷갈리지 않게 핵심 명사만 추출
    short_name = " ".join(re.sub(r'[^\w\s]', '', product_name).split()[:3])
    
    try:
        # 🤖 모델 이름을 'gemini-1.5-flash'로 단순화하여 호출
        response = client.models.generate_content(
            model='gemini-1.5-flash',
            contents=f"상품 '{short_name}'({price}원)의 상세 리뷰를 블로그 스타일로 써줘. 인사말이나 제목은 생략하고 <h3> 태그를 사용해 장점과 특징만 바로 시작해줘. HTML(h3, br)만 사용."
        )
        if response.text:
            return response.text.replace("\n", "<br>")
        raise ValueError("Empty Response")
    except Exception as e:
        print(f"❌ AI 에러 발생: {e}")
        # 💎 에러 발생 시에도 상품마다 문구가 다르게 조합되도록 수정
        comments = [
            f"{short_name}은 성능과 디자인을 모두 갖춘 모델입니다.",
            f"실제 사용자들 사이에서 만족도가 매우 높은 {short_name}입니다.",
            f"현재 {price}원이라는 가격이 믿기지 않는 고퀄리티 제품입니다."
        ]
        return f"<h3>🔍 에디터의 한줄 평</h3>{random.choice(comments)} 탄탄한 기본기로 후회 없는 선택이 될 것입니다."

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
    target = f"{random.choice(['인기', '추천'])} {random.choice(['삼성', '나이키', '애플'])} {random.choice(['노트북', '운동화', '태블릿'])}"
    print(f"🚀 안정화 엔진 가동: {target}")
    products = fetch_data(target)
    
    for item in products:
        try:
            p_id = item['productId']
            clean_img_url = item['productImage'].split('?')[0]
            price_str = format(item['productPrice'], ',')
            
            # 파일명을 단순하게 유지하여 중복 방지
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
                    <img src='{clean_img_url}' alt='{item['productName']}'>
                    <div class='content'>{ai_content}</div>
                    <div class='price'>{price_str}원</div>
                    <a href='{item['productUrl']}' class='buy-btn'>🛒 최저가 확인 및 구매하기</a>
                    <p style='font-size: 0.75rem; color: #999; margin-top: 30px; text-align: center;'>본 포스팅은 쿠팡 파트너스 활동의 일환으로 수수료를 제공받을 수 있습니다.</p>
                </div></body></html>""")
            time.sleep(35)
        except: continue

    # [인덱스 업데이트 로직 강화]
    files = sorted([f for f in os.listdir("posts") if f.endswith(".html")], reverse=True)
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(f"<!DOCTYPE html><html><head><meta charset='UTF-8'><title>핫딜 셔틀</title><style>body{{font-family:sans-serif; background:#f0f2f5; padding:20px;}} .grid{{display:grid; grid-template-columns:repeat(auto-fill, minmax(280px, 1fr)); gap:20px;}} .card{{background:white; padding:25px; border-radius:15px; text-decoration:none; color:#333; box-shadow:0 2px 10px rgba(0,0,0,0.05); height: 140px; display: flex; flex-direction: column; justify-content: space-between;}} .title{{font-weight: bold; font-size: 0.9rem; overflow: hidden; text-overflow: ellipsis; display: -webkit-box; -webkit-line-clamp: 3; -webkit-box-orient: vertical;}}</style></head><body><h1 style='text-align:center;'>🚀 실시간 핫딜 쇼핑몰</h1><div class='grid'>")
        for file in files[:100]:
            # 💎 파일 내부의 <title>에서 진짜 상품명을 가져옵니다.
            real_product_name = get_title_from_html(f"posts/{file}")
            f.write(f"<a class='card' href='posts/{file}'><div class='title'>{real_product_name}</div><div style='color:#e44d26; font-size:0.8rem;'>상세 리뷰 보기 ></div></a>")
        f.write("</div></body></html>")
    
    # 사이트맵/로봇 파일 업데이트 유지
    with open("sitemap.xml", "w", encoding="utf-8") as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n')
        f.write(f'<url><loc>{SITE_URL}/</loc><priority>1.0</priority></url>\n')
        for file in files: f.write(f'<url><loc>{SITE_URL}/posts/{file}</loc><priority>0.8</priority></url>\n')
        f.write('</urlset>')
    with open("robots.txt", "w", encoding="utf-8") as f:
        f.write(f"User-agent: *\nAllow: /\nSitemap: {SITE_URL}/sitemap.xml")

if __name__ == "__main__":
    main()
