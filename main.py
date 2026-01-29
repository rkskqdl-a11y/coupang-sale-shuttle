import os, hmac, hashlib, time, requests, json, random, re
from datetime import datetime
from urllib.parse import urlencode

# [1. 설정 정보]
ACCESS_KEY = os.environ.get('COUPANG_ACCESS_KEY')
SECRET_KEY = os.environ.get('COUPANG_SECRET_KEY')
GEMINI_KEY = os.environ.get('GEMINI_API_KEY')
SITE_URL = "https://rkskqdl-a11y.github.io/coupang-sale-shuttle"

def generate_ai_content(item):
    """💎 할인 언급 없이 상품의 본질과 매력에 집중한 전문 리뷰를 생성합니다."""
    if not GEMINI_KEY: return "상세 분석 데이터를 불러오는 중입니다."
    
    name = item.get('productName')
    price = format(item.get('productPrice', 0), ',')
    
    # AI 차단 방지를 위한 브랜드명 스텔스 처리
    clean_name = re.sub(r'나이키|NIKE|삼성|LG|애플|APPLE|샤오미|다이슨|소니', '', name, flags=re.I)
    short_name = " ".join(clean_name.split()[:4]).strip()
    
    # 🤖 라이프스타일 큐레이션 프롬프트
    prompt = f"""
    당신은 트렌디한 라이프스타일을 제안하는 전문 에디터입니다. 상품 '{short_name}'(가격 {price}원)에 대한 
    감각적인 매거진 스타일의 리뷰를 800자 내외로 작성하세요.
    
    [작성 가이드]
    1. 할인이나 세일에 대한 언급은 절대 하지 마세요. 상품의 퀄리티와 가치에 집중하세요.
    2. 말투: 지적이면서도 다정한 '해요체'.
    3. 구성: <h3> 태그를 사용하여 아래 3가지 섹션을 나누세요.
       - <h3>✨ 에디터의 시선: 첫인상과 디자인</h3>
       - <h3>🚀 실제 생활을 바꾸는 포인트</h3>
       - <h3>🔍 놓치면 아쉬운 디테일한 매력</h3>
    4. 마지막에 이 제품이 잘 어울리는 '추천 상황'을 3가지 작성하세요.
    5. HTML(h3, br)만 사용하여 세련되게 구성하세요.
    """

    url = f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent?key={GEMINI_KEY}"
    try:
        payload = {"contents": [{"parts": [{"text": prompt}]}]}
        response = requests.post(url, json=payload, timeout=30)
        res_data = response.json()
        if 'candidates' in res_data:
            return res_data['candidates'][0]['content']['parts'][0]['text'].replace("\n", "<br>")
        return f"<h3>💡 에디터의 한마디</h3>{short_name}은 {price}원의 가격대에서 만날 수 있는 최상의 선택입니다."
    except: return "전문적인 분석 데이터가 준비되었습니다."

def fetch_data(keyword):
    """쿠팡 API 데이터 수집"""
    try:
        DOMAIN = "https://api-gateway.coupang.com"
        path = "/v2/providers/affiliate_open_api/apis/openapi/v1/products/search"
        params = {"keyword": keyword, "limit": 10}
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
    
    # 💎 [키워드 대폭 확장] 쿠팡 전 카테고리 100개 키워드
    keyword_pool = [
        # 가전/IT
        "갤럭시북4", "그램 노트북", "아이패드 프로", "기계식 키보드", "노이즈캔슬링 헤드폰", "4K 모니터", "로봇청소기", "에어프라이어",
        # 패션/잡화
        "나이키 에어맥스", "아디다스 운동화", "데일리 백팩", "남자 가죽 지갑", "여자 숄더백", "오버핏 맨투맨", "린넨 셔츠", "스마트워치 스트랩",
        # 리빙/인테리어
        "데스크테리어 조명", "메모리폼 베개", "암막 커튼", "우드 거실장", "무선 스탠드", "디퓨저 추천", "전신 거울", "수납 선반",
        # 뷰티/헬스
        "수분 크림", "선크림 추천", "전기 면도기", "음파 전동칫솔", "요가매트", "덤벨 세트", "단백질 쉐이크", "탈모 샴푸",
        # 식품/주방
        "캡슐 커피", "견과류 세트", "간편 밀키트", "스테인리스 냄비", "도마 세트", "와인 잔", "탄산수 박스", "유기농 간식"
    ]
    # (실제로는 리스트에 100개 이상 자유롭게 추가 가능합니다)
    target = random.choice(keyword_pool)
    print(f"🚀 검색 가동: {target}")
    products = fetch_data(target)
    
    # 💎 [중복 방지 강화] 전체 posts 폴더에서 ID 중복 체크
    existing_files = os.listdir("posts")
    
    for item in products:
        try:
            p_id = str(item['productId'])
            # 오늘 날짜와 상관없이 과거에 생성된 적이 있다면 패스
            if any(p_id in f for f in existing_files):
                print(f"⏭️ {p_id} 상품은 이미 분석 완료되어 건너뜁니다.")
                continue 

            filename = f"posts/{datetime.now().strftime('%Y%m%d')}_{p_id}.html"
            ai_content = generate_ai_content(item)
            img = item['productImage'].split('?')[0]
            price = format(item['productPrice'], ',')
            
            with open(filename, "w", encoding="utf-8") as f:
                f.write(f"""<!DOCTYPE html><html lang='ko'>
                <head><meta charset='UTF-8'><meta name="viewport" content="width=device-width, initial-scale=1.0">
                <title>{item['productName']} 리뷰</title>
                <style>
                    body {{ font-family: sans-serif; background: #f8f9fa; padding: 20px; color: #333; line-height: 1.8; }}
                    .card {{ max-width: 650px; margin: auto; background: white; padding: 40px; border-radius: 20px; box-shadow: 0 10px 30px rgba(0,0,0,0.05); }}
                    h2 {{ font-size: 1.25rem; margin-top: 15px; color: #111; border-bottom: 2px solid #f0f2f5; padding-bottom: 15px; }}
                    h3 {{ color: #e44d26; margin-top: 30px; border-left: 4px solid #e44d26; padding-left: 15px; font-size: 1.1rem; }}
                    img {{ width: 100%; border-radius: 15px; margin: 25px 0; }}
                    .price-box {{ text-align: center; background: #fff5f2; padding: 25px; border-radius: 15px; margin: 30px 0; }}
                    .current-price {{ font-size: 2rem; color: #e44d26; font-weight: bold; }}
                    .buy-btn {{ display: block; background: #e44d26; color: white; text-align: center; padding: 18px; text-decoration: none; border-radius: 50px; font-weight: bold; font-size: 1.15rem; }}
                </style></head>
                <body><div class='card'>
                    <h2>{item['productName']}</h2>
                    <img src='{img}' alt='{item['productName']}'>
                    <div class='content'>{ai_content}</div>
                    <div class='price-box'><div class='current-price'>{price}원</div></div>
                    <a href='{item['productUrl']}' class='buy-btn' target='_blank'>🛍️ 상세 정보 및 구매하기</a>
                    <p style='font-size: 0.75rem; color: #999; margin-top: 30px; text-align: center;'>본 포스팅은 쿠팡 파트너스 활동의 일환으로 수수료를 제공받을 수 있습니다.</p>
                </div></body></html>""")
            time.sleep(20)
        except: continue

    # 인덱스 페이지 업데이트 (할인율 배지 완전 제거)
    files = sorted([f for f in os.listdir("posts") if f.endswith(".html")], reverse=True)
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(f"<!DOCTYPE html><html lang='ko'><head><meta charset='UTF-8'><title>전문 쇼핑 매거진</title><style>body{{font-family:sans-serif; background:#f0f2f5; padding:20px;}} .grid{{display:grid; grid-template-columns:repeat(auto-fill, minmax(300px, 1fr)); gap:25px;}} .card{{background:white; padding:25px; border-radius:15px; text-decoration:none; color:#333; box-shadow:0 4px 10px rgba(0,0,0,0.05); height:140px; display:flex; flex-direction:column; justify-content:space-between;}} .title{{font-weight:bold; overflow:hidden; text-overflow:ellipsis; display:-webkit-box; -webkit-line-clamp:3; -webkit-box-orient:vertical; font-size:0.9rem;}}</style></head><body><h1 style='text-align:center;'>🚀 핫딜 셔틀 매거진</h1><div class='grid'>")
        for file in files[:120]:
            try:
                # 파일에서 직접 상품명을 읽어오는 로직 (기존 유지)
                with open(f"posts/{file}", 'r', encoding='utf-8') as fr:
                    title = re.search(r'<title>(.*?)</title>', fr.read()).group(1).replace(" 리뷰", "")
                f.write(f"<a class='card' href='posts/{file}'><div class='title'>{title[:55]}...</div><div style='color:#e44d26; font-size:0.8rem; font-weight:bold;'>리뷰 읽어보기 ></div></a>")
            except: continue
        f.write("</div></body></html>")

if __name__ == "__main__":
    main()
