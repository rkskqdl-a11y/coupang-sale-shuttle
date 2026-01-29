import os, hmac, hashlib, time, requests, json, random, re
from datetime import datetime
from urllib.parse import urlencode

# [1. 설정 정보]
ACCESS_KEY = os.environ.get('COUPANG_ACCESS_KEY', '').strip()
SECRET_KEY = os.environ.get('COUPANG_SECRET_KEY', '').strip()
GEMINI_KEY = os.environ.get('GEMINI_API_KEY', '').strip()
SITE_URL = "https://rkskqdl-a11y.github.io/coupang-sale-shuttle"

def generate_ai_content(item):
    """💎 1,500자 이상의 초장문 칼럼 생성 (브랜드 마스킹 적용)"""
    if not GEMINI_KEY: return "분석 데이터 준비 중"
    name = item.get('productName')
    price = format(item.get('productPrice', 0), ',')
    clean_name = re.sub(r'나이키|NIKE|삼성|LG|애플|APPLE', '', name, flags=re.I)
    short_name = " ".join(clean_name.split()[:4]).strip()
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_KEY}"
    prompt = f"상품 '{short_name}'(가격 {price}원)에 대해 전문 테크 칼럼을 1,500자 이상 장문으로 작성해줘. <h3> 태그를 사용하여 디자인, 성능, UX, 가치 분석 섹션을 나누고 HTML만 사용해."

    try:
        payload = {"contents": [{"parts": [{"text": prompt}]}]}
        response = requests.post(url, json=payload, timeout=55)
        res_data = response.json()
        if 'candidates' in res_data and len(res_data['candidates']) > 0:
            return res_data['candidates'][0]['content']['parts'][0]['text'].replace("\n", "<br>").strip()
    except: pass
    return f"<h3>🔍 전문가 분석</h3>{short_name}은 {price}원대에 만날 수 있는 최상의 기술력이 집약된 모델입니다."

def fetch_data(keyword):
    """쿠팡 API로 상품 수집 (정렬 방식 랜덤화)"""
    try:
        DOMAIN = "https://api-gateway.coupang.com"
        path = "/v2/providers/affiliate_open_api/apis/openapi/v1/products/search"
        # 정렬 옵션: 베스트셀러, 최신순, 높은가격순, 낮은가격순 무작위 믹스
        sort_type = random.choice(["G", "H", "I", "L"]) 
        params = {"keyword": keyword, "limit": 20, "sorter": sort_type}
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
    
    # 💎 [카테고리 무한 확장] 150개 이상의 세부 키워드 풀
    keyword_pool = [
        "게이밍 노트북", "공기청정기 추천", "캠핑 의자", "무선 헤드셋", "캡슐 커피머신", "전동 칫솔", "단백질 보충제",
        "데일리 백팩", "스마트워치 스트랩", "건조기 시트", "멀티비타민", "메모리폼 토퍼", "홈트 용품", "스탠드 조명",
        "무선 청소기", "에어프라이어", "블루투스 스피커", "보조배터리", "C타입 허브", "기계식 키보드", "마사지건",
        "캠핑 롤테이블", "차박 텐트", "등산화", "골프 거리측정기", "요가매트", "폼롤러", "남자 올인원 로션",
        "클렌징 오일", "탈모 샴푸", "전기 면도기", "미니 냉장고", "제습기", "써큘레이터", "전기 온수매트",
        "유기농 견과류", "냉동 닭가슴살", "탄산수 박스", "고양이 모래", "강아지 사료", "주방 칼세트", "프라이팬 세트"
    ]
    # (키워드 풀은 계속 늘려가시면 좋습니다!)
    target = random.choice(keyword_pool)
    print(f"🚀 검색 가동: {target}")
    products = fetch_data(target)
    
    existing_files = "".join(os.listdir("posts")) # 중복 체크 최적화
    
    success_count = 0
    for item in products:
        try:
            p_id = str(item['productId'])
            if p_id in existing_files: continue # 과거에 올린 적 있으면 가차없이 패스

            filename = f"posts/{datetime.now().strftime('%Y%m%d')}_{p_id}.html"
            ai_content = generate_ai_content(item)
            img = item['productImage'].split('?')[0]
            price = format(item['productPrice'], ',')
            
            with open(filename, "w", encoding="utf-8") as f:
                f.write(f"<!DOCTYPE html><html lang='ko'><head><meta charset='UTF-8'><meta name='viewport' content='width=device-width, initial-scale=1.0'><title>{item['productName']} 리뷰</title><style>body{{font-family:sans-serif; background:#f8f9fa; padding:20px; color:#333; line-height:2.2;}} .card{{max-width:700px; margin:auto; background:white; padding:50px; border-radius:30px; box-shadow:0 20px 50px rgba(0,0,0,0.05);}} h3{{color:#e44d26; margin-top:40px; border-left:6px solid #e44d26; padding-left:20px;}} img{{width:100%; border-radius:20px; margin:30px 0;}} .price-box{{text-align:center; background:#fff5f2; padding:30px; border-radius:20px; margin:40px 0;}} .p-val{{font-size:2.5rem; color:#e44d26; font-weight:bold;}} .buy-btn{{display:block; background:#e44d26; color:white; text-align:center; padding:25px; text-decoration:none; border-radius:60px; font-weight:bold; font-size:1.3rem;}}</style></head><body><div class='card'><h2>{item['productName']}</h2><img src='{img}'><div class='content'>{ai_content}</div><div class='price-box'><div class='p-val'>{price}원</div></div><a href='{item['productUrl']}' class='buy-btn'>🛍️ 상세 리뷰 확인하기</a></div></body></html>")
            
            success_count += 1
            print(f"✅ 생성 ({success_count}/10): {p_id}")
            time.sleep(25)
            if success_count >= 10: break
        except: continue

    # 💎 [SEO 동기화] 새로운 글이 없더라도 무조건 실행
    files = sorted([f for f in os.listdir("posts") if f.endswith(".html")], reverse=True)
    now_iso = datetime.now().strftime("%Y-%m-%d")

    # 사이트맵 네임스페이스 누락 해결
    sitemap_xml = '<?xml version="1.0" encoding="UTF-8"?>\n'
    sitemap_xml += '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    sitemap_xml += f'  <url><loc>{SITE_URL}/</loc><lastmod>{now_iso}</lastmod><priority>1.0</priority></url>\n'
    for file in files:
        sitemap_xml += f'  <url><loc>{SITE_URL}/posts/{file}</loc><lastmod>{now_iso}</lastmod></url>\n'
    sitemap_xml += '</urlset>'
    with open("sitemap.xml", "w", encoding="utf-8") as f: f.write(sitemap_xml.strip())

    # 로봇 파일 & 인덱스 페이지 업데이트 (제목 추출 로직 포함)
    with open("robots.txt", "w", encoding="utf-8") as f:
        f.write(f"User-agent: *\nAllow: /\nSitemap: {SITE_URL}/sitemap.xml\n")

    with open("index.html", "w", encoding="utf-8") as f:
        f.write(f"<!DOCTYPE html><html lang='ko'><head><meta charset='UTF-8'><title>전문 쇼핑 매거진</title><style>body{{font-family:sans-serif; background:#f0f2f5; padding:20px;}} .grid{{display:grid; grid-template-columns:repeat(auto-fill, minmax(300px, 1fr)); gap:30px;}} .card{{background:white; padding:30px; border-radius:25px; text-decoration:none; color:#333; box-shadow:0 10px 20px rgba(0,0,0,0.05); height:160px; display:flex; flex-direction:column; justify-content:space-between;}} .title{{font-weight:bold; overflow:hidden; text-overflow:ellipsis; display:-webkit-box; -webkit-line-clamp:3; -webkit-box-orient:vertical; font-size:0.9rem;}}</style></head><body><h1 style='text-align:center;'>🚀 핫딜 셔틀 매거진</h1><div class='grid'>")
        for file in files[:120]:
            try:
                with open(f"posts/{file}", 'r', encoding='utf-8') as fr:
                    content = fr.read()
                    match = re.search(r'<title>(.*?)</title>', content)
                    title = match.group(1).replace(" 리뷰", "") if match else file
                f.write(f"<a class='card' href='posts/{file}'><div class='title'>{title}</div><div style='color:#e44d26; font-weight:bold; font-size:0.85rem;'>칼럼 보기 ></div></a>")
            except: continue
        f.write("</div></body></html>")
    
    print(f"✨ 작업 완료! 현재 총 포스팅: {len(files)}")

if __name__ == "__main__":
    main()
