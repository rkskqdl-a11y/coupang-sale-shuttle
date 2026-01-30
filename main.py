import os, hmac, hashlib, time, requests, json, random, re
from datetime import datetime
from urllib.parse import urlencode, quote

# [1. 설정 정보]
ACCESS_KEY = os.environ.get('COUPANG_ACCESS_KEY', '').strip()
SECRET_KEY = os.environ.get('COUPANG_SECRET_KEY', '').strip()
GEMINI_KEY = os.environ.get('GEMINI_API_KEY', '').strip()
SITE_URL = "https://rkskqdl-a11y.github.io/coupang-sale-shuttle"

def get_authorization_header(method, path, query_string):
    """💎 사용자님이 성공했던 인증 로직을 100% 유지합니다."""
    datetime_gmt = time.strftime('%y%m%dT%H%M%SZ', time.gmtime())
    message = datetime_gmt + method + path + query_string
    signature = hmac.new(bytes(SECRET_KEY, 'utf-8'), msg=bytes(message, 'utf-8'), digestmod=hashlib.sha256).hexdigest()
    return f"CEA algorithm=HmacSHA256, access-key={ACCESS_KEY}, signed-date={datetime_gmt}, signature={signature}"

def fetch_data(keyword, page):
    """💎 콤마 버그와 파라미터 정렬 문제를 해결했습니다."""
    try:
        DOMAIN = "https://api-gateway.coupang.com"
        path = "/v2/providers/affiliate_open_api/apis/openapi/v1/products/search"
        # 💎 알파벳 순서(k-l-p) 정렬로 인증 성공 보장
        params = [('keyword', keyword), ('limit', 20), ('page', page)]
        query_string = urlencode(params)
        url = f"{DOMAIN}{path}?{query_string}"
        headers = {"Authorization": get_authorization_header("GET", path, query_string), "Content-Type": "application/json"}
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code == 200:
            return response.json().get('data', {}).get('productData', []) # 💎 콤마 제거 완료
        return []
    except: return []

def generate_ai_content(product_name):
    """💎 1,000자 이상 장문 생성 및 파싱 오류 해결."""
    if not GEMINI_KEY: return "상품 분석 중입니다."
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_KEY}"
    prompt = f"상품 '{product_name}'에 대해 전문가용 분석 칼럼을 1,000자 이상 장문으로 작성해줘. <h3> 섹션 구분, HTML 태그만 사용, 친절한 해요체 사용. '할인' 언급 금지."
    try:
        response = requests.post(url, json={"contents": [{"parts": [{"text": prompt}]}]}, timeout=60)
        # 💎 딥서치의 잘못된 파싱 경로를 수정했습니다.
        return response.json()['candidates'][0]['content']['parts'][0]['text'].replace("\n", "<br>")
    except: return f"<h3>🔍 제품 상세 분석</h3>{product_name}은 완성도가 뛰어난 추천 모델입니다."

def main():
    os.makedirs("posts", exist_ok=True)
    existing_posts = os.listdir("posts")
    existing_ids = {f.split('_')[-1].replace('.html', '') for f in existing_posts if '_' in f}
    
    success_count, max_target = 0, 10
    attempts = 0
    
    # 💎 무차별 수집을 위한 시드 키워드
    seeds = ["가성비", "인기", "추천", "세일", "필수"]
    items = ["노트북", "주방용품", "캠핑장비", "인테리어", "생활가전", "운동기구", "반려동물용품"]
    
    print(f"🕵️ 현재 {len(existing_ids)}개 데이터 확보 중. 저인망 수색 시작!")

    while success_count < max_target and attempts < 20:
        target = f"{random.choice(seeds)} {random.choice(items)}"
        page = random.randint(1, 30)
        print(f"🔄 시도 {attempts+1}: '{target}' {page}페이지 수색 중...")
        
        products = fetch_data(target, page)
        attempts += 1
        if not products: continue

        for item in products:
            p_id = str(item['productId'])
            if p_id in existing_ids: continue

            p_name = item['productName']
            print(f"   ✨ 신규 발견! [{success_count+1}/10] {p_name[:20]}...")
            
            ai_content = generate_ai_content(p_name)
            img = item['productImage'].split('?')[0] # 💎 이미지 주소 깨짐 해결
            price = format(item['productPrice'], ',')
            
            filename = f"posts/{datetime.now().strftime('%Y%m%d')}_{p_id}.html"
            with open(filename, "w", encoding="utf-8") as f:
                f.write(f"<!DOCTYPE html><html lang='ko'><head><meta charset='UTF-8'><meta name='viewport' content='width=device-width, initial-scale=1.0'><title>{p_name} 리뷰</title><style>body{{font-family:sans-serif; background:#f8f9fa; padding:20px; color:#333; line-height:2.2;}} .card{{max-width:750px; margin:auto; background:white; padding:50px; border-radius:30px; box-shadow:0 20px 50px rgba(0,0,0,0.05);}} h3{{color:#e44d26; margin-top:40px; border-left:6px solid #e44d26; padding-left:20px;}} img{{width:100%; border-radius:20px; margin:30px 0;}} .p-val{{font-size:2.5rem; color:#e44d26; font-weight:bold; text-align:center;}} .buy-btn{{display:block; background:#e44d26; color:white; text-align:center; padding:25px; text-decoration:none; border-radius:60px; font-weight:bold; font-size:1.3rem;}}</style></head><body><div class='card'><h2>{p_name}</h2><img src='{img}'><div class='content'>{ai_content}</div><div class='p-val'>{price}원</div><a href='{item['productUrl']}' class='buy-btn'>🛍️ 상세 정보 확인하기</a></div></body></html>")
            
            existing_ids.add(p_id)
            success_count += 1
            time.sleep(35)
            if success_count >= max_target: break

    # [동기화] 사이트맵 네임스페이스 및 인덱스 갱신
    files = sorted([f for f in os.listdir("posts") if f.endswith(".html")], reverse=True)
    now_iso = datetime.now().strftime("%Y-%m-%d")
    
    with open("sitemap.xml", "w", encoding="utf-8") as f:
        # 💎 구글 서치 콘솔 오류를 해결하기 위한 네임스페이스 명시
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n')
        f.write(f'  <url><loc>{SITE_URL}/</loc><lastmod>{now_iso}</lastmod><priority>1.0</priority></url>\n')
        for file in files:
            f.write(f'  <url><loc>{SITE_URL}/posts/{file}</loc><lastmod>{now_iso}</lastmod></url>\n')
        f.write('</urlset>')

    print(f"🏁 작업 완료! 총 {len(files)}개 노출. (신규: {success_count}개)")

if __name__ == "__main__":
    main()
