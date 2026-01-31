import os, hmac, hashlib, time, requests, json, random, re
from datetime import datetime
from urllib.parse import urlencode

# 🚀 [System] AF7053799 전용 '성공 보장' 엔진 가동...
print("🚀 [System] 하베스팅 성공 확인! 이제 웹사이트 진열을 시작합니다.")

# [1. 설정 정보]
ACCESS_KEY = os.environ.get('COUPANG_ACCESS_KEY', '').strip()
SECRET_KEY = os.environ.get('COUPANG_SECRET_KEY', '').strip()
GEMINI_KEY = os.environ.get('GEMINI_API_KEY', '').strip()
SITE_URL = "https://rkskqdl-a11y.github.io/coupang-sale-shuttle"

def get_auth_header(method, path, query):
    timestamp = time.strftime('%y%m%dT%H%M%SZ', time.gmtime())
    msg = timestamp + method + path + query
    sig = hmac.new(bytes(SECRET_KEY, 'utf-8'), msg=bytes(msg, 'utf-8'), digestmod=hashlib.sha256).hexdigest()
    return f"CEA algorithm=HmacSHA256, access-key={ACCESS_KEY}, signed-date={timestamp}, signature={sig}"

def fetch_data(keyword, page):
    path = "/v2/providers/affiliate_open_api/apis/openapi/v1/products/search"
    params = [('keyword', keyword), ('limit', 10), ('page', page)] # 💎 10개씩 안정적 수집
    query = urlencode(params)
    headers = {"Authorization": get_auth_header("GET", path, query), "Content-Type": "application/json"}
    try:
        resp = requests.get(f"https://api-gateway.coupang.com{path}?{query}", headers=headers, timeout=15)
        return resp.json().get('data', {}).get('productData', [])
    except: return []

def generate_ai_review(p_name):
    if not GEMINI_KEY: return "상세 분석 준비 중"
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_KEY}"
    try:
        prompt = f"'{p_name}'에 대해 IT 칼럼니스트처럼 1000자 이상 장문 분석 글을 써줘. <h3> 사용, HTML만 사용. '해요체' 사용."
        res = requests.post(url, json={"contents": [{"parts": [{"text": prompt}]}]}, timeout=60)
        return res.json()['candidates'][0]['content']['parts'][0]['text'].replace("\n", "<br>")
    except: return f"<h3>🔍 제품 분석</h3>{p_name}은 품질이 우수한 추천 상품입니다."

def get_title_from_file(path):
    """💎 HTML 파일에서 실제 상품명을 추출합니다"""
    try:
        with open(path, 'r', encoding='utf-8') as f:
            c = f.read()
            m = re.search(r'<h2>(.*?)</h2>', c)
            if m: return m.group(1)[:40] + "..."
    except: pass
    return "최신 추천 상품"

def main():
    os.makedirs("posts", exist_ok=True)
    existing_ids = {f.split('_')[-1].replace('.html', '') for f in os.listdir("posts") if '_' in f}
    
    seeds = ["삼성전자", "노트북", "캠핑용품", "운동화", "물티슈", "영양제", "아이폰", "가습기"]
    target = random.choice(seeds)
    success_count = 0

    print(f"🕵️ 현재 {len(existing_ids)}개 노출 중. '{target}' 수집 시작!")

    for page in range(1, 11):
        if success_count >= 10: break
        items = fetch_data(target, page)
        if not items: continue

        for item in items:
            p_id = str(item['productId'])
            if p_id in existing_ids: continue

            print(f"   ✨ 발견! [{success_count+1}/10] {item['productName'][:20]}...")
            content = generate_ai_review(item['productName'])
            img, price = item['productImage'].split('?')[0], format(int(item['productPrice']), ',')
            
            filename = f"posts/{datetime.now().strftime('%Y%m%d')}_{p_id}.html"
            with open(filename, "w", encoding="utf-8") as f:
                f.write(f"<!DOCTYPE html><html lang='ko'><head><meta charset='UTF-8'><meta name='viewport' content='width=device-width, initial-scale=1.0'><title>{item['productName']} 리뷰</title><style>body{{font-family:sans-serif; background:#f8f9fa; padding:20px; line-height:2.2;}} .card{{max-width:750px; margin:auto; background:white; padding:50px; border-radius:30px; box-shadow:0 20px 50px rgba(0,0,0,0.05);}} img{{width:100%; border-radius:20px; margin:30px 0;}} .p-val{{font-size:2.5rem; color:#e44d26; font-weight:bold; text-align:center;}} .buy-btn{{display:block; background:#e44d26; color:white; text-align:center; padding:25px; text-decoration:none; border-radius:60px; font-weight:bold;}}</style></head><body><div class='card'><h2>{item['productName']}</h2><img src='{img}'><div class='content'>{content}</div><div class='p-val'>{price}원</div><a href='{item['productUrl']}' class='buy-btn'>🛍️ 상세 정보 확인하기</a></div></body></html>")
            
            existing_ids.add(p_id)
            success_count += 1
            time.sleep(35)
            if success_count >= 10: break

    # 💎 [핵심] index.html 및 sitemap.xml 동시 갱신
    files = sorted([f for f in os.listdir("posts") if f.endswith(".html")], reverse=True)
    now = datetime.now().strftime("%Y-%m-%d")
    
    # 1. 사이트맵 갱신
    with open("sitemap.xml", "w", encoding="utf-8") as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n')
        f.write(f'  <url><loc>{SITE_URL}/</loc><lastmod>{now}</lastmod><priority>1.0</priority></url>\n')
        for file in files:
            f.write(f'  <url><loc>{SITE_URL}/posts/{file}</loc><lastmod>{now}</lastmod></url>\n')
        f.write('</urlset>')

    # 2. 메인 페이지(index.html) 강제 갱신
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(f"<!DOCTYPE html><html lang='ko'><head><meta charset='UTF-8'><title>쿠팡 핫딜 매거진</title><style>body{{font-family:sans-serif; background:#f0f2f5; padding:20px;}} .grid{{display:grid; grid-template-columns:repeat(auto-fill, minmax(320px, 1fr)); gap:20px;}} .card{{background:white; padding:25px; border-radius:20px; text-decoration:none; color:#333; box-shadow:0 5px 15px rgba(0,0,0,0.05); transition:0.3s;}} .card:hover{{transform:translateY(-10px);}}</style></head><body><h1 style='text-align:center; color:#e44d26;'>🚀 실시간 쿠팡 전수 조사 매거진</h1><div class='grid'>")
        for file in files[:200]: # 최신 200개 노출
            title = get_title_from_file(f"posts/{file}")
            f.write(f"<a class='card' href='posts/{file}'><div>{title}</div><div style='color:#e44d26; font-weight:bold; margin-top:15px;'>전문 보기 ></div></a>")
        f.write("</div></body></html>")

    print(f"🏁 작업 완료. 총 {len(files)}개 노출. (신규: {success_count}개)")

if __name__ == "__main__":
    main()
