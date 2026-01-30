import os, hmac, hashlib, time, requests, json, random, re
from datetime import datetime
from time import gmtime, strftime
from urllib.parse import urlencode, quote

# 🚀 [System] 무한 하베스팅 엔진 가동...
print("🚀 쿠팡 전 상품 무차별 수집 엔진이 가동됩니다.")

# [1. 설정 정보]
ACCESS_KEY = os.environ.get('COUPANG_ACCESS_KEY', '').strip()
SECRET_KEY = os.environ.get('COUPANG_SECRET_KEY', '').strip()
GEMINI_KEY = os.environ.get('GEMINI_API_KEY', '').strip()
SITE_URL = "https://rkskqdl-a11y.github.io/coupang-sale-shuttle"

def generate_hmac_official(method, path, query_string):
    """💎 공식 가이드 100% 준수 인증 서명 생성"""
    datetime_gmt = strftime('%y%m%d', gmtime()) + 'T' + strftime('%H%M%S', gmtime()) + 'Z'
    message = datetime_gmt + method + path + query_string
    signature = hmac.new(bytes(SECRET_KEY, "utf-8"), message.encode("utf-8"), hashlib.sha256).hexdigest()
    return "CEA algorithm=HmacSHA256, access-key={}, signed-date={}, signature={}".format(ACCESS_KEY, datetime_gmt, signature)

def fetch_data(keyword, page):
    """💎 무한 키워드와 페이지를 조합하여 데이터를 가져옵니다."""
    try:
        DOMAIN = "https://api-gateway.coupang.com"
        path = "/v2/providers/affiliate_open_api/apis/openapi/v1/products/search"
        
        # 💎 알파벳 순서 정렬 필수 (keyword -> limit -> page)
        params = [('keyword', keyword), ('limit', 20), ('page', page)]
        query_string = urlencode(params)
        
        headers = {
            "Authorization": generate_hmac_official("GET", path, query_string),
            "Content-Type": "application/json"
        }
        
        url = f"{DOMAIN}{path}?{query_string}"
        response = requests.get(url, headers=headers, timeout=15)
        
        if response.status_code != 200:
            print(f"   ⚠️ API 응답 실패: {response.status_code}")
            return []
            
        data = response.json()
        return data.get('data', {}).get('productData', [])
    except: return []

def get_random_keyword():
    """💎 쿠팡의 모든 상품을 건드리기 위한 무작위 조합기"""
    prefix = ["가성비", "인기", "추천", "필수", "북유럽", "럭셔리", "국산", "정품", "실생활"]
    mid = ["가전", "주방", "캠핑", "욕실", "차량", "반려동물", "인테리어", "운동", "사무", "생활"]
    suffix = ["용품", "아이템", "장비", "세트", "소품", "거치대", "정리함", "의류", "잡화", "가구"]
    return f"{random.choice(prefix)} {random.choice(mid)} {random.choice(suffix)}"

def generate_ai_content(product_name):
    """💎 1,000자 이상 전문가 칼럼 생성 (안정적 파싱)"""
    if not GEMINI_KEY: return "상품 분석 중입니다."
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_KEY}"
    prompt = f"상품 '{product_name}'에 대해 IT/라이프스타일 전문가가 작성한 분석 칼럼을 1,000자 이상 장문으로 작성해줘. <h3> 섹션으로 디자인, 기능, 실용성을 나누고 HTML 태그만 사용. 친절한 해요체 사용. '할인' 언급 금지."
    try:
        res = requests.post(url, json={"contents": [{"parts": [{"text": prompt}]}]}, timeout=60)
        return res.json()['candidates'][0]['content']['parts'][0]['text'].replace("\n", "<br>")
    except:
        return f"<h3>🔍 제품 상세 분석</h3>{product_name}은 품질과 디자인을 모두 잡은 모델입니다."

def get_title_from_html(filepath):
    """💎 인덱스 SEO를 위한 타이틀 추출"""
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
    attempts = 0
    
    print(f"🕵️ 현재 {len(existing_ids)}개 노출 중. 무한 키워드 수색 시작!")

    while success_count < max_target and attempts < 15:
        target_keyword = get_random_keyword()
        # 1~30페이지 중 랜덤 타격하여 데이터 다양성 확보
        target_page = random.randint(1, 30)
        print(f"🔄 [{attempts+1}차] '{target_keyword}' p.{target_page} 분석 중...")
        
        products = fetch_data(target_keyword, target_page)
        attempts += 1
        if not products: continue

        print(f"   📦 {len(products)}개 상품 수신 성공. 신규 상품 찾는 중...")

        for item in products:
            p_id = str(item['productId'])
            if p_id in existing_ids: continue # 중복 건너뛰기

            p_name = item['productName']
            print(f"   ✨ 발견! [{success_count+1}/10] {p_name[:20]}...")
            
            ai_content = generate_ai_content(p_name)
            img = item['productImage'].split('?')[0] # 💎 이미지 깨짐 방지
            price = format(item['productPrice'], ',')
            
            filename = f"posts/{datetime.now().strftime('%Y%m%d')}_{p_id}.html"
            with open(filename, "w", encoding="utf-8") as f:
                f.write(f"<!DOCTYPE html><html lang='ko'><head><meta charset='UTF-8'><meta name='viewport' content='width=device-width, initial-scale=1.0'><title>{p_name} 리뷰</title><style>body{{font-family:sans-serif; background:#f8f9fa; padding:20px; color:#333; line-height:2.2;}} .card{{max-width:750px; margin:auto; background:white; padding:50px; border-radius:30px; box-shadow:0 20px 50px rgba(0,0,0,0.05);}} h3{{color:#e44d26; margin-top:40px; border-left:6px solid #e44d26; padding-left:20px;}} img{{width:100%; border-radius:20px; margin:30px 0;}} .p-val{{font-size:2.5rem; color:#e44d26; font-weight:bold; text-align:center;}} .buy-btn{{display:block; background:#e44d26; color:white; text-align:center; padding:25px; text-decoration:none; border-radius:60px; font-weight:bold; font-size:1.3rem;}}</style></head><body><div class='card'><h2>{p_name}</h2><img src='{img}'><div class='content'>{ai_content}</div><div class='p-val'>{price}원</div><a href='{item['productUrl']}' class='buy-btn'>🛍️ 상세 정보 확인하기</a></div></body></html>")
            
            existing_ids.add(p_id)
            success_count += 1
            time.sleep(35) # 안전 대기
            if success_count >= max_target: break

    # [동기화] 인덱스 및 사이트맵 갱신
    files = sorted([f for f in os.listdir("posts") if f.endswith(".html")], reverse=True)
    now_iso = datetime.now().strftime("%Y-%m-%d")
    
    with open("sitemap.xml", "w", encoding="utf-8") as f:
        # 💎 구글 서치 콘솔 오류 해결을 위한 네임스페이스 삽입
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n')
        f.write(f'  <url><loc>{SITE_URL}/</loc><lastmod>{now_iso}</lastmod><priority>1.0</priority></url>\n')
        for file in files:
            f.write(f'  <url><loc>{SITE_URL}/posts/{file}</loc><lastmod>{now_iso}</lastmod></url>\n')
        f.write('</urlset>')

    with open("index.html", "w", encoding="utf-8") as f:
        f.write(f"<!DOCTYPE html><html lang='ko'><head><meta charset='UTF-8'><title>쿠팡 핫딜 셔틀</title><style>body{{font-family:sans-serif; background:#f0f2f5; padding:20px;}} .grid{{display:grid; grid-template-columns:repeat(auto-fill, minmax(300px, 1fr)); gap:20px;}} .card{{background:white; padding:25px; border-radius:20px; text-decoration:none; color:#333; box-shadow:0 5px 15px rgba(0,0,0,0.05);}}</style></head><body><h1 style='text-align:center; color:#e44d26;'>🚀 실시간 쿠팡 전수 조사 매거진</h1><div class='grid'>")
        for file in files[:150]:
            title = get_title_from_html(f"posts/{file}")
            f.write(f"<a class='card' href='posts/{file}'><div>{title}</div><div style='color:#e44d26; font-weight:bold; margin-top:15px;'>칼럼 읽기 ></div></a>")
        f.write("</div></body></html>")

    print(f"🏁 작업 완료! 총 {len(files)}개 노출. (신규: {success_count}개)")

if __name__ == "__main__":
    main()
