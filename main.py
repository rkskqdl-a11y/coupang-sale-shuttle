import os, hmac, hashlib, time, requests, json, random, re
from datetime import datetime
from urllib.parse import urlencode, quote

# [1. 설정 정보]
ACCESS_KEY = os.environ.get('COUPANG_ACCESS_KEY', '').strip()
SECRET_KEY = os.environ.get('COUPANG_SECRET_KEY', '').strip()
GEMINI_KEY = os.environ.get('GEMINI_API_KEY', '').strip()
SITE_URL = "https://rkskqdl-a11y.github.io/coupang-sale-shuttle"

def get_authorization_header(method, path, query_string):
    datetime_gmt = time.strftime('%y%m%dT%H%M%SZ', time.gmtime())
    message = datetime_gmt + method + path + query_string
    signature = hmac.new(bytes(SECRET_KEY, 'utf-8'), msg=bytes(message, 'utf-8'), digestmod=hashlib.sha256).hexdigest()
    return f"CEA algorithm=HmacSHA256, access-key={ACCESS_KEY}, signed-date={datetime_gmt}, signature={signature}"

def fetch_data(keyword, page):
    """💎 파라미터를 알파벳 순서(k-l-p)로 정렬하여 인증 성공률을 100%로 유지합니다."""
    try:
        DOMAIN = "https://api-gateway.coupang.com"
        path = "/v2/providers/affiliate_open_api/apis/openapi/v1/products/search"
        # 인증을 위해 반드시 정렬된 리스트 형태 사용
        params = [('keyword', keyword), ('limit', 20), ('page', page)]
        query_string = urlencode(params)
        url = f"{DOMAIN}{path}?{query_string}"
        
        headers = {
            "Authorization": get_authorization_header("GET", path, query_string),
            "Content-Type": "application/json"
        }
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code == 200:
            return response.json().get('data', {}).get('productData',)
        return
    except: return

def get_infinite_keyword():
    """💎 쿠팡의 모든 상품을 건드리기 위해 무작위 조합 키워드를 생성합니다."""
    prefix = ["가성비", "인기", "추천", "세일", "필수", "북유럽", "럭셔리", "국산", "정품", "특가"]
    mid = ["생활", "주방", "캠핑", "사무용", "욕실", "차량용", "반려동물", "인테리어", "운동", "패션"]
    suffix = ["용품", "아이템", "장비", "세트", "소품", "거치대", "정리함", "의류", "잡화", "가전"]
    # 수만 가지 조합 중 하나 선택
    return f"{random.choice(prefix)} {random.choice(mid)} {random.choice(suffix)}"

def generate_ai_content(product_name):
    """💎 1,000자 이상의 장문 칼럼 생성"""
    if not GEMINI_KEY: return "상품 분석 중입니다."
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_KEY}"
    prompt = f"상품 '{product_name}'에 대해 IT/라이프스타일 전문가가 작성한 분석 칼럼을 1,000자 이상 장문으로 작성해줘. <h3> 섹션으로 디자인, 기능, 실용성을 나누고 HTML 태그만 사용. 친절한 해요체 사용. '할인', '구매' 단어 언급 금지."
    try:
        payload = {"contents": [{"parts": [{"text": prompt}]}]}
        response = requests.post(url, json=payload, timeout=60)
        return response.json()['candidates']['content']['parts']['text'].replace("\n", "<br>")
    except: return f"<h3>🔍 제품 상세 분석</h3>{product_name}은 모든 면에서 완성도가 높은 추천 모델입니다."

def main():
    os.makedirs("posts", exist_ok=True)
    existing_posts = os.listdir("posts")
    existing_ids = {f.split('_')[-1].replace('.html', '') for f in existing_posts if '_' in f}
    
    success_count, max_target = 0, 10
    attempts = 0
    
    print(f"🕵️ 현재 {len(existing_ids)}개 데이터 확보 중. 전수 조사 엔진 가동!")

    # 💎 10개를 채울 때까지 검색어를 바꿔가며 무한 루프
    while success_count < max_target and attempts < 20:
        target = get_infinite_keyword()
        # 1~50페이지 중 랜덤하게 접근하여 데이터 신선도 유지
        page = random.randint(1, 50)
        print(f"🔍 시도 {attempts+1}: '{target}' 키워드로 {page}페이지 수색 중...")
        
        products = fetch_data(target, page)
        attempts += 1
        
        if not products: continue

        for item in products:
            p_id = str(item['productId'])
            if p_id in existing_ids: continue # 중복 제거 로직

            p_name = item['productName']
            print(f"   ✨ 신규 발견! [{success_count+1}/10] {p_name[:20]}...")
            
            ai_content = generate_ai_content(p_name)
            img = item['productImage'].split('?')
            price = format(item['productPrice'], ',')
            
            filename = f"posts/{datetime.now().strftime('%Y%m%d')}_{p_id}.html"
            with open(filename, "w", encoding="utf-8") as f:
                f.write(f"<!DOCTYPE html><html lang='ko'><head><meta charset='UTF-8'><meta name='viewport' content='width=device-width, initial-scale=1.0'><title>{p_name} 리뷰</title><style>body{{font-family:sans-serif; background:#f8f9fa; padding:20px; color:#333; line-height:2.2;}}.card{{max-width:750px; margin:auto; background:white; padding:50px; border-radius:30px; box-shadow:0 20px 50px rgba(0,0,0,0.05);}} h3{{color:#e44d26; margin-top:40px; border-left:6px solid #e44d26; padding-left:20px;}} img{{width:100%; border-radius:20px; margin:30px 0;}}.p-val{{font-size:2.5rem; color:#e44d26; font-weight:bold; text-align:center;}}.buy-btn{{display:block; background:#e44d26; color:white; text-align:center; padding:25px; text-decoration:none; border-radius:60px; font-weight:bold; font-size:1.3rem;}}</style></head><body><div class='card'><h2>{p_name}</h2><img src='{img}'><div class='content'>{ai_content}</div><div class='p-val'>{price}원</div><a href='{item['productUrl']}' class='buy-btn'>🛍️ 상세 정보 확인하기</a></div></body></html>")
            
            existing_ids.add(p_id)
            success_count += 1
            time.sleep(35) # 제미나이 무료 한도 및 발행 안전성 확보
            if success_count >= max_target: break

    # [동기화] 인덱스 및 사이트맵 갱신
    files = sorted([f for f in os.listdir("posts") if f.endswith(".html")], reverse=True)
    now_iso = datetime.now().strftime("%Y-%m-%d")
    
    # index.html (최신 150개)
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(f"<!DOCTYPE html><html lang='ko'><head><meta charset='UTF-8'><title>쿠팡 핫딜 셔틀</title><style>body{{font-family:sans-serif; background:#f0f2f5; padding:20px;}}.grid{{display:grid; grid-template-columns:repeat(auto-fill, minmax(300px, 1fr)); gap:20px;}}.card{{background:white; padding:25px; border-radius:20px; text-decoration:none; color:#333; box-shadow:0 5px 15px rgba(0,0,0,0.05);}}</style></head><body><h1 style='text-align:center; color:#e44d26;'>🚀 실시간 쿠팡 전수 조사 매거진</h1><div class='grid'>")
        for file in files[:150]:
            f.write(f"<a class='card' href='posts/{file}'><div>{file[9:25]}...</div><div style='color:#e44d26; font-weight:bold; margin-top:15px;'>칼럼 읽기 ></div></a>")
        f.write("</div></body></html>")

    # sitemap.xml
    with open("sitemap.xml", "w", encoding="utf-8") as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n')
        f.write(f'  <url><loc>{SITE_URL}/</loc><lastmod>{now_iso}</lastmod><priority>1.0</priority></url>\n')
        for file in files:
            f.write(f'  <url><loc>{SITE_URL}/posts/{file}</loc><lastmod>{now_iso}</lastmod></url>\n')
        f.write('</urlset>')

    print(f"🏁 작업 완료! 총 {len(files)}개 노출. (신규: {success_count}개)")

if __name__ == "__main__":
    main()
