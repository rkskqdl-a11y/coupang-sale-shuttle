import os
import hmac
import hashlib
import time
import requests
import json
from datetime import datetime
from urllib.parse import urlencode
import random

# 1. API 키 설정
ACCESS_KEY = os.environ.get('COUPANG_ACCESS_KEY')
SECRET_KEY = os.environ.get('COUPANG_SECRET_KEY')

# 2. 검색 키워드 조합 (수익률 높은 키워드)
modifiers = ["가성비", "학생용", "자취생", "사무용", "선물용", "특가", "인기", "추천", "세일", "베스트", "국민", "필수"]
brands = ["삼성", "LG", "애플", "샤오미", "나이키", "아디다스", "뉴발란스", "폴로", "타미힐피거", "지오다노", "햇반", "비비고", "다이슨", "테팔", "필립스", "파타고니아", "노스페이스", "에잇세컨즈"]
products = ["노트북", "모니터", "마우스", "키보드", "반팔티", "후드티", "슬랙스", "러닝화", "백팩", "생수", "라면", "에어프라이어", "캠핑의자", "텐트", "배변패드", "물티슈", "청소기", "영양제", "오메가3", "유산균"]
specs = ["대용량", "무라벨", "고속충전", "경량", "오버핏", "무소음", "접이식", "미니", "휴대용", "화이트", "블랙"]

def get_random_keyword():
    return f"{random.choice(modifiers)} {random.choice(brands)} {random.choice(products)} {random.choice(specs)}"

def get_authorization_header(method, path, query_string):
    datetime_gmt = time.strftime('%y%m%dT%H%M%SZ', time.gmtime())
    message = datetime_gmt + method + path + query_string
    signature = hmac.new(bytes(SECRET_KEY, 'utf-8'), msg=bytes(message, 'utf-8'), digestmod=hashlib.sha256).hexdigest()
    return f"CEA algorithm=HmacSHA256, access-key={ACCESS_KEY}, signed-date={datetime_gmt}, signature={signature}"

def fetch_data(keyword):
    DOMAIN = "https://api-gateway.coupang.com"
    path = "/v2/providers/affiliate_open_api/apis/openapi/v1/products/search"
    params = {"keyword": keyword, "limit": 20} # 상품 20개 가져오기
    query_string = urlencode(params)
    url = f"{DOMAIN}{path}?{query_string}"
    headers = {"Authorization": get_authorization_header("GET", path, query_string), "Content-Type": "application/json"}
    try:
        response = requests.get(url, headers=headers, timeout=15)
        return response.json()
    except: return None

def main():
    os.makedirs("posts", exist_ok=True)
    
    # 3. 상품 데이터 수집
    target = get_random_keyword()
    print(f"검색 키워드: {target}")
    res = fetch_data(target)
    
    # 4. 개별 상품 상세 페이지 생성 (.html)
    if res and 'data' in res and res['data'].get('productData'):
        clean_target = target.replace(" ", "_")
        for item in res['data']['productData']:
            p_id = item['productId']
            filename = f"posts/{datetime.now().strftime('%Y%m%d')}_{clean_target}_{p_id}.html"
            
            # 이미 있는 상품은 건너뛰기
            if os.path.exists(filename): continue 

            with open(filename, "w", encoding="utf-8") as f:
                f.write(f"""<!DOCTYPE html><html lang='ko'><head><meta charset='UTF-8'><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>{item['productName']}</title>
                <style>
                    body {{ font-family: 'Apple SD Gothic Neo', 'Malgun Gothic', sans-serif; background: #f5f6f8; margin: 0; padding: 20px; text-align: center; }}
                    .container {{ max-width: 600px; margin: auto; background: white; padding: 30px; border-radius: 20px; box-shadow: 0 4px 20px rgba(0,0,0,0.05); }}
                    h2 {{ color: #333; line-height: 1.4; font-size: 1.2rem; word-break: keep-all; }}
                    img {{ width: 100%; max-width: 400px; border-radius: 15px; margin: 20px 0; }}
                    .price {{ font-size: 1.5rem; color: #e44d26; font-weight: bold; margin-bottom: 20px; }}
                    .btn {{ background: linear-gradient(135deg, #e44d26, #f16529); color: white; padding: 18px 40px; text-decoration: none; border-radius: 50px; display: inline-block; font-weight: bold; font-size: 1.1rem; box-shadow: 0 4px 15px rgba(228, 77, 38, 0.3); transition: 0.3s; }}
                    .btn:hover {{ transform: scale(1.05); }}
                    .meta {{ color: #888; font-size: 0.8rem; margin-top: 30px; }}
                </style></head><body>
                <div class='container'>
                    <h2>{item['productName']}</h2>
                    <img src='{item['productImage']}'>
                    <div class='price'>{format(item['productPrice'], ',')}원</div>
                    <a href='{item['productUrl']}' class='btn'>👉 쿠팡에서 최저가 보기</a>
                    <div class='meta'>
                        <p>🚀 로켓배송 | ⭐️ 무료반품</p>
                        <hr style='border:0; height:1px; background:#eee;'>
                        <p>이 포스팅은 쿠팡 파트너스 활동의 일환으로,<br>이에 따른 일정액의 수수료를 제공받습니다.</p>
                    </div>
                </div></body></html>""")
    
    # 상품 파일 목록 불러오기
    files = sorted([f for f in os.listdir("posts") if f.endswith(".html")], reverse=True)
    
    # (API 오류 대비) 파일이 하나도 없으면 '임시 안내 페이지' 생성
    if not files:
        with open("posts/error.html", "w", encoding="utf-8") as f:
            f.write("<html><body><h1>상품 준비 중입니다. 잠시 후 다시 접속해주세요.</h1></body></html>")
        files = ["error.html"]

    # 5. [핵심] 메인 매장 화면 (index.html) 덮어쓰기
    # 아까 만든 검은 화면을 이 쇼핑몰 화면으로 교체합니다.
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(f"""<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>초특가 핫딜 셔틀</title>
    <style>
        body {{ font-family: 'Apple SD Gothic Neo', sans-serif; background: #f0f2f5; margin: 0; padding: 20px; max-width: 100%; }}
        .header {{ text-align: center; margin-bottom: 30px; background: white; padding: 30px 20px; border-radius: 20px; box-shadow: 0 2px 10px rgba(0,0,0,0.05); }}
        h1 {{ color: #e44d26; margin: 0 0 10px 0; font-size: 1.8rem; }}
        .desc {{ color: #666; font-size: 0.9rem; }}
        .grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 15px; max-width: 1000px; margin: auto; }}
        .card {{ background: white; padding: 20px; border-radius: 15px; text-decoration: none; color: #333; transition: 0.3s; border: 1px solid #eee; display: flex; flex-direction: column; justify-content: space-between; }}
        .card:hover {{ transform: translateY(-5px); box-shadow: 0 10px 20px rgba(0,0,0,0.1); border-color: #e44d26; }}
        .card-title {{ font-weight: bold; line-height: 1.4; margin-bottom: 10px; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }}
        .card-date {{ font-size: 0.75rem; color: #999; margin-bottom: 5px; }}
        .badge {{ display: inline-block; background: #ffeae6; color: #e44d26; padding: 4px 8px; border-radius: 5px; font-size: 0.75rem; font-weight: bold; width: fit-content; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🚀 오늘의 초특가 핫딜</h1>
        <p class="desc">실시간으로 엄선된 가성비 상품을 만나보세요.</p>
        <p class="desc" style="font-size:0.75rem; margin-top:5px;">업데이트: {datetime.now().strftime('%Y-%m-%d %H:%M')}</p>
    </div>
    <div class="grid">
""")
        for file in files[:60]: # 최신 60개 노출
            if file == "error.html": continue
            # 파일명에서 정보 추출 (날짜_키워드_상품ID)
            parts = file.replace(".html", "").split("_")
            display_name = " ".join(parts[1:-1]) if len(parts) > 2 else "추천 상품"
            
            f.write(f"""
        <a class="card" href="posts/{file}">
            <div class="card-date">{datetime.now().strftime('%Y-%m-%d')}</div>
            <div class="card-title">🔥 {display_name}</div>
            <div class="badge">최저가 확인 ></div>
        </a>
""")
        f.write("    </div></body></html>")

    # 6. .nojekyll 생성 (디자인 깨짐 방지 필수)
    with open(".nojekyll", "w", encoding="utf-8") as f: f.write("")

if __name__ == "__main__":
    main()
