import os, hmac, hashlib, time, requests, json, random, re
from datetime import datetime
from urllib.parse import urlencode

# [1. 설정 정보]
ACCESS_KEY = os.environ.get('COUPANG_ACCESS_KEY', '').strip()
SECRET_KEY = os.environ.get('COUPANG_SECRET_KEY', '').strip()
GEMINI_KEY = os.environ.get('GEMINI_API_KEY', '').strip()
SITE_URL = "https://rkskqdl-a11y.github.io/coupang-sale-shuttle"

def generate_ai_content(item):
    """💎 제미나이 Pro를 활용한 1,500자 이상의 초장문 칼럼 생성"""
    if not GEMINI_KEY: return "상세 분석 데이터 준비 중"
    name = item.get('productName')
    price = format(item.get('productPrice', 0), ',')
    clean_name = re.sub(r'나이키|NIKE|삼성|LG|애플|APPLE', '', name, flags=re.I)
    short_name = " ".join(clean_name.split()[:4]).strip()
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_KEY}"
    prompt = f"상품 '{short_name}'(가격 {price}원)에 대해 전문 테크 칼럼을 1,500자 이상 장문으로 작성해줘. <h3> 태그를 사용하고 HTML만 사용해. '할인'이나 '세일' 단어는 절대 금지."

    try:
        payload = {"contents": [{"parts": [{"text": prompt}]}]}
        response = requests.post(url, json=payload, timeout=55)
        res_data = response.json()
        if 'candidates' in res_data and len(res_data['candidates']) > 0:
            return res_data['candidates'][0]['content']['parts'][0]['text'].replace("\n", "<br>").strip()
    except: pass
    return f"<h3>🔍 전문가의 정밀 분석</h3>{short_name} 모델은 사용자의 일상을 바꾸는 뛰어난 완성도를 갖춘 제품입니다. 세련된 디자인과 견고한 하드웨어 성능이 조화를 이루어 최상의 경험을 제공합니다."

def fetch_data(keyword):
    """💎 정렬 옵션을 삭제하고 오로지 키워드로만 검색합니다."""
    try:
        DOMAIN = "https://api-gateway.coupang.com"
        path = "/v2/providers/affiliate_open_api/apis/openapi/v1/products/search"
        # 정렬(sorter) 파라미터를 제거했습니다.
        params = {"keyword": keyword, "limit": 20}
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
    
    # 💎 [롱테일 키워드 대폭 확장] 중복을 피하기 위한 초세분화 키워드 셋
    keyword_pool = [
        # 디지털/가전 롱테일
        "원룸용 저소음 미니 제습기", "노트북 거치대 알루미늄", "맥북 투명 하드 케이스", "기계식 키보드 저소음 적축", "무선 게이밍 마우스 경량", "고속 충전 C타입 멀티허브", "아이패드 드로잉 종이질감 필름", "모니터 조명 데스크테리어", "휴대용 음파 전동칫솔",
        # 리빙/생활 롱테일
        "메모리폼 경추베개 목디스크", "안방 암막 커튼 베이지", "거실용 대형 러그 카페트", "화장실 미끄럼방지 욕실매트", "원목 전신거울 대형", "데스크탑 모니터 받침대 수납형", "접이식 캠핑 의자 경량", "무선 센서등 현관용", "옷장 수납 정리함",
        # 패션/뷰티 롱테일
        "데일리 캔버스 백팩 대학생", "가죽 카드지갑 슬림형", "여성 숄더백 비건레더", "남성 오버핏 린넨 셔츠", "발편한 워킹화 런닝화", "수분부족지성 수분크림", "민감성 피부 선크림 추천", "탈모 완화 기능성 샴푸", "전기 면도기 세정 스테이션",
        # 식품/반려동물 롱테일
        "무설탕 견과류 하루한봉", "고단백 냉동 닭가슴살 도시락", "무라벨 탄산수 500ml", "강아지 눈건강 영양제", "고양이 벤토나이트 모래", "스테인리스 주방 칼세트", "인덕션용 코팅 프라이팬", "캡슐 커피 머신 호환 캡슐", "유기농 어린이 간식 세트"
    ]
    
    target = random.choice(keyword_pool)
    print(f"🚀 무한 큐레이션 가동: {target}")
    products = fetch_data(target)
    
    existing_files = "".join(os.listdir("posts"))
    
    success_count = 0
    for item in products:
        try:
            p_id = str(item['productId'])
            if p_id in existing_files: continue # 중복 원천 차단

            filename = f"posts/{datetime.now().strftime('%Y%m%d')}_{p_id}.html"
            ai_content = generate_ai_content(item)
            img = item['productImage'].split('?')[0]
            price = format(item['productPrice'], ',')
            
            with open(filename, "w", encoding="utf-8") as f:
                f.write(f"<!DOCTYPE html><html lang='ko'><head><meta charset='UTF-8'><meta name='viewport' content='width=device-width, initial-scale=1.0'><title>{item['productName']} 리뷰</title><style>body{{font-family:sans-serif; background:#f8f9fa; padding:20px; color:#333; line-height:2.2;}} .card{{max-width:700px; margin:auto; background:white; padding:50px; border-radius:30px; box-shadow:0 20px 50px rgba(0,0,0,0.05);}} h3{{color:#e44d26; margin-top:40px; border-left:6px solid #e44d26; padding-left:20px;}} img{{width:100%; border-radius:20px; margin:30px 0;}} .price-box{{text-align:center; background:#fff5f2; padding:30px; border-radius:20px; margin:40px 0;}} .p-val{{font-size:2.5rem; color:#e44d26; font-weight:bold;}} .buy-btn{{display:block; background:#e44d26; color:white; text-align:center; padding:25px; text-decoration:none; border-radius:60px; font-weight:bold; font-size:1.3rem;}}</style></head><body><div class='card'><h2>{item['productName']}</h2><img src='{img}' alt='{item['productName']}'><div class='content'>{ai_content}</div><div class='price-box'><div class='p-val'>{price}원</div></div><a href='{item['productUrl']}' class='buy-btn'>🛍️ 상세 정보 확인하기</a></div></body></html>")
            
            success_count += 1
            print(f"✅ 생성 ({success_count}/10): {p_id}")
            time.sleep(30)
            if success_count >= 10: break
        except: continue

    # 💎 [SEO 최적화] 사이트맵 네임스페이스 및 구조 최적화 (필수 유지)
    files = sorted([f for f in os.listdir("posts") if f.endswith(".html")], reverse=True)
    now_iso = datetime.now().strftime("%Y-%m-%d")

    sitemap_xml = '<?xml version="1.0" encoding="UTF-8"?>\n'
    sitemap_xml += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    sitemap_xml += f'  <url><loc>{SITE_URL}/</loc><lastmod>{now_iso}</lastmod><priority>1.0</priority></url>\n'
    for file in files:
        sitemap_xml += f'  <url><loc>{SITE_URL}/posts/{file}</loc><lastmod>{now_iso}</lastmod></url>\n'
    sitemap_xml += '</urlset>'
    with open("sitemap.xml", "w", encoding="utf-8") as f: f.write(sitemap_xml.strip())

    with open("robots.txt", "w", encoding="utf-8") as f:
        f.write(f"User-agent: *\nAllow: /\nSitemap: {SITE_URL}/sitemap.xml\n")

    # index.html (진짜 상품명 추출 로직)
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(f"<!DOCTYPE html><html lang='ko'><head><meta charset='UTF-8'><title>전문 쇼핑 매거진</title><style>body{{font-family:sans-serif; background:#f0f2f5; padding:20px;}} .grid{{display:grid; grid-template-columns:repeat(auto-fill, minmax(300px, 1fr)); gap:30px;}} .card{{background:white; padding:30px; border-radius:25px; text-decoration:none; color:#333; box-shadow:0 10px 20px rgba(0,0,0,0.05); height:150px; display:flex; flex-direction:column; justify-content:space-between;}} .title{{font-weight:bold; overflow:hidden; text-overflow:ellipsis; display:-webkit-box; -webkit-line-clamp:3; -webkit-box-orient:vertical; font-size:0.9rem;}}</style></head><body><h1 style='text-align:center;'>🚀 실시간 쇼핑 큐레이션</h1><div class='grid'>")
        for file in files[:120]:
            try:
                with open(f"posts/{file}", 'r', encoding='utf-8') as fr:
                    content = fr.read()
                    match = re.search(r'<title>(.*?)</title>', content)
                    title = match.group(1).replace(" 리뷰", "") if match else file
                f.write(f"<a class='card' href='posts/{file}'><div class='title'>{title}</div><div style='color:#e44d26; font-weight:bold; font-size:0.85rem;'>칼럼 읽기 ></div></a>")
            except: continue
        f.write("</div></body></html>")
    
    print(f"✨ 전체 동기화 완료! 현재 포스팅 수: {len(files)}")

if __name__ == "__main__":
    main()
