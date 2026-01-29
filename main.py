import os, hmac, hashlib, time, requests, json, random, re
from datetime import datetime
from urllib.parse import urlencode

# [1. 설정 정보]
ACCESS_KEY = os.environ.get('COUPANG_ACCESS_KEY', '').strip()
SECRET_KEY = os.environ.get('COUPANG_SECRET_KEY', '').strip()
GEMINI_KEY = os.environ.get('GEMINI_API_KEY', '').strip()
SITE_URL = "https://rkskqdl-a11y.github.io/coupang-sale-shuttle"

def generate_ai_content(item):
    """💎 1,500자 이상의 초장문 칼럼 생성 (브랜드명 마스킹)"""
    if not GEMINI_KEY: return "상세 분석 데이터 준비 중"
    name = item.get('productName')
    price = format(item.get('productPrice', 0), ',')
    clean_name = re.sub(r'나이키|NIKE|삼성|LG|애플|APPLE|아디다스|소니', '', name, flags=re.I)
    short_name = " ".join(clean_name.split()[:4]).strip()
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_KEY}"
    prompt = f"상품 '{short_name}'(가격 {price}원)에 대해 전문 테크 칼럼을 1,500자 이상 장문으로 작성해줘. <h3> 태그를 사용하여 디자인, 성능, 실사용 후기 섹션을 나누어 작성하고 HTML만 사용해. '할인'이나 '세일' 단어는 절대 쓰지 마."

    try:
        payload = {"contents": [{"parts": [{"text": prompt}]}]}
        response = requests.post(url, json=payload, timeout=55)
        res_data = response.json()
        if 'candidates' in res_data and len(res_data['candidates']) > 0:
            text = res_data['candidates'][0]['content']['parts'][0]['text']
            return text.replace("\n", "<br>").strip()
    except: pass
    return f"<h3>🔍 전문가의 정밀 분석</h3>{short_name} 모델은 {price}원의 가격대에서 만날 수 있는 최상의 기술력이 집약된 모델입니다. 세련된 디자인과 탄탄한 기본기가 돋보이는 이 제품은 실제 환경에서도 뛰어난 안정성을 선사합니다."

def fetch_data(keyword):
    """쿠팡 API로 상품 수집"""
    try:
        DOMAIN = "https://api-gateway.coupang.com"
        path = "/v2/providers/affiliate_open_api/apis/openapi/v1/products/search"
        params = {"keyword": keyword, "limit": 20} # 검색량을 늘림
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
    
    # 💎 [대폭 확장] 쿠팡 전 카테고리 150개 이상 키워드 풀
    categories = {
        "디지털/가전": ["게이밍 노트북", "4K 모니터", "기계식 키보드", "무선 헤드셋", "캡슐 커피머신", "로봇청소기", "전동 칫솔", "아이패드 프로", "갤럭시탭", "가습기 추천", "블루투스 스피커", "보조배터리", "C타입 허브"],
        "주방/생활": ["에어프라이어", "멀티압력쿠커", "인덕션 냄비세트", "칼블럭 세트", "밀폐용기 세트", "식기건조대", "빨래건조대", "분리수거함", "핸디 청소기"],
        "패션/잡화": ["나이키 운동화", "아디다스 스니커즈", "데일리 백팩", "스마트워치 스트랩", "남자 가죽지갑", "여자 숄더백", "오버핏 맨투맨", "린넨 셔츠", "등산화 추천"],
        "뷰티/식품": ["수분 크림", "탈모 샴푸", "선크림 추천", "전기 면도기", "단백질 보충제", "멀티비타민", "견과류 박스", "탄산수 박스", "간편 밀키트"],
        "캠핑/스포츠": ["캠핑 의자", "롤테이블", "감성 랜턴", "자차 도킹텐트", "요가매트", "덤벨 세트", "폼롤러", "자전거 헬멧", "골프 거리측정기"]
    }
    
    # 랜덤 카테고리 -> 랜덤 키워드 선택
    cat_name = random.choice(list(categories.keys()))
    target = random.choice(categories[cat_name])
    print(f"🚀 [{cat_name}] 큐레이션 시작: {target}")
    
    products = fetch_data(target)
    existing_files = "".join(os.listdir("posts")) # 모든 파일명을 하나의 문자열로 합쳐 중복 체크
    
    success_count = 0
    for item in products:
        try:
            p_id = str(item['productId'])
            # 💎 중복 원천 봉쇄: 과거 파일명 어디든 이 ID가 포함되어 있으면 패스
            if p_id in existing_files: continue 

            filename = f"posts/{datetime.now().strftime('%Y%m%d')}_{p_id}.html"
            ai_content = generate_ai_content(item)
            img = item['productImage'].split('?')[0]
            price = format(item['productPrice'], ',')
            
            with open(filename, "w", encoding="utf-8") as f:
                f.write(f"<!DOCTYPE html><html lang='ko'><head><meta charset='UTF-8'><meta name='viewport' content='width=device-width, initial-scale=1.0'><title>{item['productName']} 리뷰</title><style>body{{font-family:sans-serif; background:#f8f9fa; padding:20px; color:#333; line-height:2.2;}} .card{{max-width:700px; margin:auto; background:white; padding:50px; border-radius:30px; box-shadow:0 20px 50px rgba(0,0,0,0.05);}} h3{{color:#e44d26; margin-top:40px; border-left:6px solid #e44d26; padding-left:20px;}} img{{width:100%; border-radius:20px; margin:30px 0;}} .price-box{{text-align:center; background:#fff5f2; padding:30px; border-radius:20px; margin:40px 0;}} .p-val{{font-size:2.5rem; color:#e44d26; font-weight:bold;}} .buy-btn{{display:block; background:#e44d26; color:white; text-align:center; padding:25px; text-decoration:none; border-radius:60px; font-weight:bold; font-size:1.3rem;}}</style></head><body><div class='card'><h2>{item['productName']}</h2><img src='{img}'><div class='content'>{ai_content}</div><div class='price-box'><div class='p-val'>{price}원</div></div><a href='{item['productUrl']}' class='buy-btn'>🛍️ 상세 정보 확인하기</a></div></body></html>")
            
            success_count += 1
            print(f"✅ 생성 완료 ({success_count}/10): {p_id}")
            time.sleep(30)
            if success_count >= 10: break # 한 번 실행에 10개로 제한하여 안정성 확보
        except: continue

    # 💎 3. [SEO 파일 강제 업데이트] 413개의 모든 파일 시간을 동기화합니다.
    files = sorted([f for f in os.listdir("posts") if f.endswith(".html")], reverse=True)
    now_iso = datetime.now().strftime("%Y-%m-%d")

    # 사이트맵 네임스페이스 오류 해결
    sitemap_xml = '<?xml version="1.0" encoding="UTF-8"?>\n'
    sitemap_xml += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    sitemap_xml += f'  <url><loc>{SITE_URL}/</loc><lastmod>{now_iso}</lastmod><priority>1.0</priority></url>\n'
    for file in files:
        sitemap_xml += f'  <url><loc>{SITE_URL}/posts/{file}</loc><lastmod>{now_iso}</lastmod></url>\n'
    sitemap_xml += '</urlset>'
    with open("sitemap.xml", "w", encoding="utf-8") as f: f.write(sitemap_xml.strip())

    # robots.txt 갱신
    with open("robots.txt", "w", encoding="utf-8") as f:
        f.write(f"User-agent: *\nAllow: /\nSitemap: {SITE_URL}/sitemap.xml\n")

    # index.html (ID가 아닌 진짜 상품명 추출)
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(f"<!DOCTYPE html><html lang='ko'><head><meta charset='UTF-8'><title>전문 쇼핑 매거진</title><style>body{{font-family:sans-serif; background:#f0f2f5; padding:20px;}} .grid{{display:grid; grid-template-columns:repeat(auto-fill, minmax(300px, 1fr)); gap:30px;}} .card{{background:white; padding:30px; border-radius:25px; text-decoration:none; color:#333; box-shadow:0 10px 20px rgba(0,0,0,0.05); height:160px; display:flex; flex-direction:column; justify-content:space-between;}} .title{{font-weight:bold; overflow:hidden; text-overflow:ellipsis; display:-webkit-box; -webkit-line-clamp:3; -webkit-box-orient:vertical; font-size:0.9rem;}}</style></head><body><h1 style='text-align:center;'>🚀 실시간 큐레이션 매거진</h1><div class='grid'>")
        for file in files[:120]:
            try:
                # 💎 파일 내부의 <title> 태그에서 진짜 상품명을 추출합니다.
                with open(f"posts/{file}", 'r', encoding='utf-8') as fr:
                    content = fr.read()
                    match = re.search(r'<title>(.*?)</title>', content)
                    title = match.group(1).replace(" 리뷰", "") if match else file
                f.write(f"<a class='card' href='posts/{file}'><div class='title'>{title}</div><div style='color:#e44d26; font-weight:bold; font-size:0.85rem;'>칼럼 보기 ></div></a>")
            except: continue
        f.write("</div></body></html>")
    
    print(f"✨ 전체 동기화 완료! 현재 포스팅 수: {len(files)}")

if __name__ == "__main__":
    main()
