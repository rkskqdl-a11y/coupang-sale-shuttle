import os, hmac, hashlib, time, requests, json, random, re
from datetime import datetime
from urllib.parse import urlencode, quote
import google.generativeai as genai

# [1. 설정 정보]
ACCESS_KEY = os.environ.get('COUPANG_ACCESS_KEY', '').strip()
SECRET_KEY = os.environ.get('COUPANG_SECRET_KEY', '').strip()
GEMINI_KEY = os.environ.get('GEMINI_API_KEY', '').strip()
SITE_URL = "https://rkskqdl-a11y.github.io/coupang-sale-shuttle"

if GEMINI_KEY:
    genai.configure(api_key=GEMINI_KEY)

def get_authorization_header(method, path, query_string):
    """💎 사용자님이 성공했던 인증 로직을 100% 유지합니다."""
    datetime_gmt = time.strftime('%y%m%dT%H%M%SZ', time.gmtime())
    message = datetime_gmt + method + path + query_string
    signature = hmac.new(bytes(SECRET_KEY, 'utf-8'), msg=bytes(message, 'utf-8'), digestmod=hashlib.sha256).hexdigest()
    return f"CEA algorithm=HmacSHA256, access-key={ACCESS_KEY}, signed-date={datetime_gmt}, signature={signature}"

def fetch_data(keyword, page=1):
    """💎 파라미터 정렬 및 페이지 이동 기능을 포함한 데이터 수집"""
    try:
        DOMAIN = "https://api-gateway.coupang.com"
        path = "/v2/providers/affiliate_open_api/apis/openapi/v1/products/search"
        params = {"keyword": keyword, "limit": 20, "page": page}
        query_string = urlencode(params)
        url = f"{DOMAIN}{path}?{query_string}"
        headers = {"Authorization": get_authorization_header("GET", path, query_string), "Content-Type": "application/json"}
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code == 200:
            return response.json().get('data', {}).get('productData', [])
        return []
    except: return []

def generate_ai_content(product_name):
    """💎 1,000자 이상의 장문 칼럼 생성 (응답 파싱 오류 해결)"""
    if not GEMINI_KEY: return "상품 분석 중입니다."
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        prompt = f"상품 '{product_name}'에 대해 IT/라이프스타일 전문가가 작성한 분석 칼럼을 1,000자 이상 장문으로 작성해줘. <h3> 섹션으로 디자인, 기능, 실용성을 나누고 HTML 태그만 사용. 친절한 '해요체' 사용. '할인', '구매' 단어 언급 금지."
        response = model.generate_content(prompt)
        # 💎 딥서치 코드의 리스트 인덱싱 오류를 수정했습니다.
        return response.text.replace("\n", "<br>")
    except: return f"<h3>🔍 제품 상세 분석</h3>{product_name}은 완성도가 높은 추천 모델입니다."

def get_title_from_html(filepath):
    """💎 인덱스 페이지 SEO를 위해 실제 상품명을 HTML에서 추출"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            match = re.search(r'<title>(.*?)</title>', content)
            if match: return match.group(1).replace(" 리뷰", "")
    except: pass
    return "추천 상품"

def main():
    os.makedirs("posts", exist_ok=True)
    existing_posts = os.listdir("posts")
    existing_ids = {f.split('_')[-1].replace('.html', '') for f in existing_posts if '_' in f}
    
    success_count, max_target = 0, 10
    
    # 💎 무차별 수집을 위한 무작위 키워드 조합 생성
    seeds = ["가성비", "인기", "추천", "필수"]
    items = ["노트북", "주방용품", "캠핑장비", "인테리어소품", "생활가전"]
    target_keyword = f"{random.choice(seeds)} {random.choice(items)}"
    
    print(f"🕵️ 현재 {len(existing_ids)}개 노출 중. '{target_keyword}' 전수 조사 시작!")

    # 💎 10개를 채울 때까지 페이지를 넘기며 저인망식 수색
    for page in range(1, 11):
        if success_count >= max_target: break
        print(f"🔍 {page}페이지 수색 중...")
        products = fetch_data(target_keyword, page)
        
        for item in products:
            p_id = str(item['productId'])
            if p_id in existing_ids: continue

            p_name = item['productName']
            print(f"   ✨ 신규 발견! [{success_count+1}/10] {p_name[:20]}...")
            
            ai_content = generate_ai_content(p_name)
            # 💎 리스트 타입 오류를 해결했습니다.
            img = item['productImage'].split('?')[0] 
            price = format(item['productPrice'], ',')
            
            filename = f"posts/{datetime.now().strftime('%Y%m%d')}_{p_id}.html"
            with open(filename, "w", encoding="utf-8") as f:
                f.write(f"<!DOCTYPE html><html lang='ko'><head><meta charset='UTF-8'><meta name='viewport' content='width=device-width, initial-scale=1.0'><title>{p_name} 리뷰</title><style>body{{font-family:sans-serif; background:#f8f9fa; padding:20px; color:#333; line-height:2.2;}} .card{{max-width:750px; margin:auto; background:white; padding:50px; border-radius:30px; box-shadow:0 20px 50px rgba(0,0,0,0.05);}} h3{{color:#e44d26; margin-top:40px; border-left:6px solid #e44d26; padding-left:20px;}} img{{width:100%; border-radius:20px; margin:30px 0;}} .p-val{{font-size:2.5rem; color:#e44d26; font-weight:bold; text-align:center;}} .buy-btn{{display:block; background:#e44d26; color:white; text-align:center; padding:25px; text-decoration:none; border-radius:60px; font-weight:bold; font-size:1.3rem;}}</style></head><body><div class='card'><h2>{p_name}</h2><img src='{img}'><div class='content'>{ai_content}</div><div class='p-val'>{price}원</div><a href='{item['productUrl']}' class='buy-btn'>🛍️ 상세 정보 확인하기</a></div></body></html>")
            
            existing_ids.add(p_id)
            success_count += 1
            time.sleep(35) # 제미나이 무료 한도 준수
            if success_count >= max_target: break

    # [동기화] 인덱스 및 사이트맵 갱신
    files = sorted([f for f in os.listdir("posts") if f.endswith(".html")], reverse=True)
    now_iso = datetime.now().strftime("%Y-%m-%d")
    
    # 💎 index.html 갱신 (추출된 실제 상품명 사용)
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(f"<!DOCTYPE html><html lang='ko'><head><meta charset='UTF-8'><title>쿠팡 핫딜 셔틀</title><style>body{{font-family:sans-serif; background:#f0f2f5; padding:20px;}} .grid{{display:grid; grid-template-columns:repeat(auto-fill, minmax(300px, 1fr)); gap:20px;}} .card{{background:white; padding:25px; border-radius:20px; text-decoration:none; color:#333; box-shadow:0 5px 15px rgba(0,0,0,0.05);}}</style></head><body><h1 style='text-align:center; color:#e44d26;'>🚀 실시간 쿠팡 전수 조사 매거진</h1><div class='grid'>")
        for file in files[:150]:
            title = get_title_from_html(f"posts/{file}")
            f.write(f"<a class='card' href='posts/{file}'><div>{title}</div><div style='color:#e44d26; font-weight:bold; margin-top:15px;'>칼럼 읽기 ></div></a>")
        f.write("</div></body></html>")

    # 💎 sitemap.xml 갱신 (구글 표준 네임스페이스 추가)
    with open("sitemap.xml", "w", encoding="utf-8") as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n')
        f.write(f'  <url><loc>{SITE_URL}/</loc><lastmod>{now_iso}</lastmod><priority>1.0</priority></url>\n')
        for file in files:
            f.write(f'  <url><loc>{SITE_URL}/posts/{file}</loc><lastmod>{now_iso}</lastmod></url>\n')
        f.write('</urlset>')
    
    # robots.txt 자동 생성
    with open("robots.txt", "w", encoding="utf-8") as f:
        f.write(f"User-agent: *\nAllow: /\nSitemap: {SITE_URL}/sitemap.xml")

    print(f"🏁 작업 완료! 총 {len(files)}개 노출. (신규: {success_count}개)")

if __name__ == "__main__":
    main()
