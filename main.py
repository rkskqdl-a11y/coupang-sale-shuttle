import os, hmac, hashlib, time, requests, json, random, re
from datetime import datetime
from urllib.parse import urlencode
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

def fetch_data(keyword):
    """💎 1페이지에서 확실하게 상품 데이터를 가져옵니다."""
    try:
        DOMAIN = "https://api-gateway.coupang.com"
        path = "/v2/providers/affiliate_open_api/apis/openapi/v1/products/search"
        # 1페이지 상단 20개 상품을 모두 가져옵니다.
        params = {"keyword": keyword, "limit": 20}
        query_string = urlencode(params)
        url = f"{DOMAIN}{path}?{query_string}"
        headers = {"Authorization": get_authorization_header("GET", path, query_string), "Content-Type": "application/json"}
        response = requests.get(url, headers=headers, timeout=15)
        return response.json().get('data', {}).get('productData', [])
    except: return []

def get_title_from_html(filepath):
    """💎 [에러 해결] 누락되었던 HTML 타이틀 추출 함수를 복구했습니다."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            match = re.search(r'<title>(.*?)</title>', content)
            if match: return match.group(1).replace(" 리뷰", "")
    except: pass
    return "추천 상품"

def generate_ai_content(product_name):
    """💎 제미나이 AI로 800자 내외 상세 리뷰 생성."""
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        prompt = f"상품명 '{product_name}'에 대해 쇼핑 전문가처럼 친절한 해요체로 800자 내외 상세 분석 리뷰를 작성해줘. <h3> 태그를 활용하고 HTML만 사용해. '할인' 언급 금지."
        response = model.generate_content(prompt)
        return response.text.replace("\n", "<br>")
    except:
        return f"<h3>🔍 제품 분석</h3>{product_name}은 품질과 가격 모두 만족스러운 최고의 선택입니다."

def main():
    os.makedirs("posts", exist_ok=True)
    
    # 💎 무조건 결과가 쏟아지는 씨앗 단어들
    seeds = ["노트북", "운동화", "세탁기", "건조기", "린넨셔츠", "가습기", "커피머신", "모니터", "비타민", "물티슈", "기저귀", "양말"]
    target = random.choice(seeds)
    
    existing_posts = os.listdir("posts")
    existing_ids = {f.split('_')[-1].replace('.html', '') for f in existing_posts if '_' in f}
    
    print(f"🕵️ 현재 {len(existing_ids)}개 노출 중. '{target}' 1페이지 전수 조사 시작!")
    products = fetch_data(target)
    
    success_count = 0
    for item in products:
        try:
            p_id = str(item['productId'])
            if p_id in existing_ids: continue # 중복 건너뛰기

            p_name = item['productName']
            print(f"   ✨ 신규 발견! [{success_count+1}/10] {p_name[:20]}... 발행 중")
            
            ai_content = generate_ai_content(p_name)
            clean_img_url = item['productImage'].split('?')[0]
            
            # 파일명을 날짜_ID 형태로 고정하여 관리 편의성을 높였습니다.
            filename = f"posts/{datetime.now().strftime('%Y%m%d')}_{p_id}.html"
            
            with open(filename, "w", encoding="utf-8") as f:
                f.write(f"<!DOCTYPE html><html><head><meta charset='UTF-8'><meta name='viewport' content='width=device-width, initial-scale=1.0'><title>{p_name} 리뷰</title><style>body{{font-family:sans-serif; background:#f5f6f8; padding:20px; color:#333; line-height:1.8;}} .container{{max-width:700px; margin:auto; background:white; padding:40px; border-radius:30px; box-shadow:0 10px 30px rgba(0,0,0,0.05);}} img{{width:100%; border-radius:20px; margin:20px 0;}} h3{{color:#e44d26; border-left:5px solid #e44d26; padding-left:15px; margin-top:30px;}}</style></head><body><div class='container'><h2>{p_name}</h2><img src='{clean_img_url}'><div class='content'>{ai_content}</div><div style='font-size:2rem; color:#e44d26; font-weight:bold; text-align:center; margin:30px 0;'>{format(item['productPrice'], ',')}원</div><a href='{item['productUrl']}' style='display:block; background:#e44d26; color:white; padding:20px; text-align:center; text-decoration:none; border-radius:50px; font-weight:bold; font-size:1.2rem;'>🛍️ 상세 정보 확인하기</a><p style='font-size:0.75rem; color:#999; margin-top:40px; text-align:center;'>본 포스팅은 쿠팡 파트너스 활동의 일환으로 수수료를 제공받을 수 있습니다.</p></div></body></html>")
            
            existing_ids.add(p_id)
            success_count += 1
            time.sleep(30) # 안전 발행을 위한 대기
            if success_count >= 10: break
        except: continue

    # 💎 [동기화] 인덱스, 사이트맵, robots.txt 갱신
    files = sorted([f for f in os.listdir("posts") if f.endswith(".html")], reverse=True)
    now_iso = datetime.now().strftime("%Y-%m-%d")
    
    # 1. index.html 갱신
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(f"<!DOCTYPE html><html lang='ko'><head><meta charset='UTF-8'><title>쿠팡 핫딜 셔틀</title><style>body{{font-family:sans-serif; background:#f0f2f5; padding:20px;}} .grid{{display:grid; grid-template-columns:repeat(auto-fill, minmax(300px, 1fr)); gap:20px;}} .card{{background:white; padding:25px; border-radius:20px; text-decoration:none; color:#333; box-shadow:0 5px 15px rgba(0,0,0,0.05);}}</style></head><body><h1 style='text-align:center; color:#e44d26;'>🚀 실시간 쿠팡 핫딜 매거진</h1><div class='grid'>")
        for file in files[:100]:
            title = get_title_from_html(f"posts/{file}")
            f.write(f"<a class='card' href='posts/{file}'><div>{title}</div><div style='color:#e44d26; font-weight:bold; margin-top:15px;'>칼럼 읽기 ></div></a>")
        f.write("</div></body></html>")

    # 2. sitemap.xml 갱신 (네임스페이스 오류 해결)
    with open("sitemap.xml", "w", encoding="utf-8") as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n')
        f.write(f'  <url><loc>{SITE_URL}/</loc><lastmod>{now_iso}</lastmod><priority>1.0</priority></url>\n')
        for file in files:
            f.write(f'  <url><loc>{SITE_URL}/posts/{file}</loc><lastmod>{now_iso}</lastmod></url>\n')
        f.write('</urlset>')

    # 3. robots.txt 갱신
    with open("robots.txt", "w", encoding="utf-8") as f:
        f.write(f"User-agent: *\nAllow: /\nSitemap: {SITE_URL}/sitemap.xml")

    print(f"🏁 작업 종료! 총 {len(files)}개 노출 중. (신규 발행: {success_count}개)")

if __name__ == "__main__":
    main()
