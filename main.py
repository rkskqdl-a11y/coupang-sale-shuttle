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

def generate_ai_content(product_name):
    """💎 SDK를 사용하여 안정적으로 1,000자 이상의 리뷰 생성"""
    try:
        model = genai.GenerativeModel('gemini-1.5-flash')
        prompt = f"상품 '{product_name}'에 대해 전문적인 제품 분석 칼럼을 1,000자 이상 장문으로 작성해줘. <h3> 태그를 사용하여 디자인, 성능, 사용자 경험 섹션을 나누고 HTML만 사용해. '할인' 단어 절대 금지."
        response = model.generate_content(prompt)
        return response.text.replace("\n", "<br>")
    except:
        return f"<h3>🔍 전문가 분석</h3>{product_name}은 탄탄한 완성도와 세련된 디자인이 돋보이는 제품입니다."

def get_authorization_header(method, path, query_string):
    """💎 파라미터 정렬 문제를 해결한 엄격한 인증 헤더 생성"""
    datetime_gmt = time.strftime('%y%m%dT%H%M%SZ', time.gmtime())
    message = datetime_gmt + method + path + query_string
    signature = hmac.new(bytes(SECRET_KEY, 'utf-8'), msg=bytes(message, 'utf-8'), digestmod=hashlib.sha256).hexdigest()
    return f"CEA algorithm=HmacSHA256, access-key={ACCESS_KEY}, signed-date={datetime_gmt}, signature={signature}"

def fetch_data(keyword, page):
    """💎 서명 오류를 방지하기 위해 파라미터를 사전순으로 정렬하여 호출"""
    try:
        DOMAIN = "https://api-gateway.coupang.com"
        path = "/v2/providers/affiliate_open_api/apis/openapi/v1/products/search"
        
        # 💎 중요: 파라미터는 반드시 사전순(ABC순)으로 구성해야 인증 에러가 안 납니다.
        params = {
            "keyword": keyword,
            "limit": 20,
            "page": page
        }
        query_string = urlencode(params)
        
        url = f"{DOMAIN}{path}?{query_string}"
        headers = {
            "Authorization": get_authorization_header("GET", path, query_string),
            "Content-Type": "application/json"
        }
        
        response = requests.get(url, headers=headers, timeout=15)
        res_json = response.json()
        return res_json.get('data', {}).get('productData', [])
    except: return []

def main():
    os.makedirs("posts", exist_ok=True)
    
    # 💎 [확장된 키워드 풀] 일반적인 단어 + 속성 조합으로 중복 회피
    seeds = ["티셔츠", "운동화", "슬리퍼", "샴푸", "비타민", "충전기", "케이블", "후라이팬", "베개", "이불", "마스크", "물티슈"]
    attrs = ["가성비", "인기", "추천", "대용량", "신제품", "프리미엄"]
    
    existing_posts = os.listdir("posts")
    existing_ids = {f.split('_')[-1].replace('.html', '') for f in existing_posts if '_' in f}
    
    success_count, max_target = 0, 10
    print(f"🚀 목표: 새 상품 {max_target}개 발행 시작 (현재 {len(existing_ids)}개 노출 중)")

    # 💎 10개를 채울 때까지 멈추지 않는 루프
    attempts = 0
    while success_count < max_target and attempts < 50:
        attempts += 1
        target = f"{random.choice(attrs)} {random.choice(seeds)}"
        page = random.randint(1, 20)
        
        products = fetch_data(target, page)
        if not products:
            print(f"❓ [{attempts}차] '{target}' p.{page} 결과 없음. 다시 시도.")
            continue

        print(f"🔍 [{attempts}차] '{target}'에서 {len(products)}개 발견! 중복 체크 중...")
        random.shuffle(products)

        for item in products:
            p_id = str(item['productId'])
            if p_id in existing_ids: continue

            # 포스팅 생성
            p_name = item['productName']
            filename = f"posts/{datetime.now().strftime('%Y%m%d')}_{p_id}.html"
            ai_content = generate_ai_content(p_name)
            img = item['productImage'].split('?')[0]
            price = format(item['productPrice'], ',')
            
            with open(filename, "w", encoding="utf-8") as f:
                f.write(f"<!DOCTYPE html><html lang='ko'><head><meta charset='UTF-8'><title>{p_name} 리뷰</title><style>body{{font-family:sans-serif; background:#f8f9fa; padding:20px; color:#333; line-height:2.2;}} .card{{max-width:700px; margin:auto; background:white; padding:50px; border-radius:30px; box-shadow:0 20px 50px rgba(0,0,0,0.05);}} h3{{color:#e44d26; margin-top:40px; border-left:6px solid #e44d26; padding-left:20px;}} img{{width:100%; border-radius:20px; margin:30px 0;}} .price-box{{text-align:center; background:#fff5f2; padding:30px; border-radius:20px; margin:40px 0;}} .p-val{{font-size:2.5rem; color:#e44d26; font-weight:bold;}} .buy-btn{{display:block; background:#e44d26; color:white; text-align:center; padding:25px; text-decoration:none; border-radius:60px; font-weight:bold; font-size:1.3rem;}}</style></head><body><div class='card'><h2>{p_name}</h2><img src='{img}'><div class='content'>{ai_content}</div><div class='price-box'><div class='p-val'>{price}원</div></div><a href='{item['productUrl']}' class='buy-btn'>🛍️ 상세 정보 확인하기</a></div></body></html>")
            
            existing_ids.add(p_id)
            success_count += 1
            print(f"   ✨ 성공 ({success_count}/{max_target}): {p_name[:25]}...")
            time.sleep(35) # RPM 제한 준수
            
            if success_count >= max_target: break

    # [SEO 동기화 부분 유지]
    files = sorted([f for f in os.listdir("posts") if f.endswith(".html")], reverse=True)
    now_iso = datetime.now().strftime("%Y-%m-%d")
    sitemap = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    sitemap += f'  <url><loc>{SITE_URL}/</loc><lastmod>{now_iso}</lastmod><priority>1.0</priority></url>\n'
    for f in files: sitemap += f'  <url><loc>{SITE_URL}/posts/{f}</loc><lastmod>{now_iso}</lastmod></url>\n'
    sitemap += '</urlset>'
    with open("sitemap.xml", "w", encoding="utf-8") as f: f.write(sitemap.strip())
    with open("robots.txt", "w", encoding="utf-8") as f: f.write(f"User-agent: *\nAllow: /\nSitemap: {SITE_URL}/sitemap.xml\n")
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(f"<!DOCTYPE html><html lang='ko'><head><meta charset='UTF-8'><title>전문 쇼핑 매거진</title><style>body{{font-family:sans-serif; background:#f0f2f5; padding:20px;}} .grid{{display:grid; grid-template-columns:repeat(auto-fill, minmax(300px, 1fr)); gap:30px;}} .card{{background:white; padding:30px; border-radius:25px; text-decoration:none; color:#333; box-shadow:0 10px 20px rgba(0,0,0,0.05); height:160px; display:flex; flex-direction:column; justify-content:space-between;}} .title{{font-weight:bold; overflow:hidden; text-overflow:ellipsis; display:-webkit-box; -webkit-line-clamp:3; -webkit-box-orient:vertical; font-size:0.9rem;}}</style></head><body><h1 style='text-align:center;'>🚀 쿠팡 전 상품 노출 프로젝트</h1><div class='grid'>")
        for file in files[:120]:
            try:
                with open(f"posts/{file}", 'r', encoding='utf-8') as fr:
                    content = fr.read()
                    match = re.search(r'<title>(.*?)</title>', content)
                    title = match.group(1).replace(" 리뷰", "") if match else file
                f.write(f"<a class='card' href='posts/{file}'><div class='title'>{title}</div><div style='color:#e44d26; font-weight:bold;'>리뷰 읽기 ></div></a>")
            except: continue
        f.write("</div></body></html>")
    print(f"🏁 작업 완료! 총 {len(files)}개 노출 중.")

if __name__ == "__main__":
    main()
