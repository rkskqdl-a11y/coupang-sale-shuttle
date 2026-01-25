import os
import hmac
import hashlib
import time
import requests
import json
from datetime import datetime
from urllib.parse import urlencode
import random
import re

# 1. API 키 설정
ACCESS_KEY = os.environ.get('COUPANG_ACCESS_KEY')
SECRET_KEY = os.environ.get('COUPANG_SECRET_KEY')

def get_authorization_header(method, path, query_string):
    datetime_gmt = time.strftime('%y%m%dT%H%M%SZ', time.gmtime())
    message = datetime_gmt + method + path + query_string
    signature = hmac.new(bytes(SECRET_KEY, 'utf-8'), msg=bytes(message, 'utf-8'), digestmod=hashlib.sha256).hexdigest()
    return f"CEA algorithm=HmacSHA256, access-key={ACCESS_KEY}, signed-date={datetime_gmt}, signature={signature}"

def fetch_data(keyword):
    try:
        DOMAIN = "https://api-gateway.coupang.com"
        path = "/v2/providers/affiliate_open_api/apis/openapi/v1/products/search"
        params = {"keyword": keyword, "limit": 20}
        query_string = urlencode(params)
        url = f"{DOMAIN}{path}?{query_string}"
        headers = {"Authorization": get_authorization_header("GET", path, query_string), "Content-Type": "application/json"}
        response = requests.get(url, headers=headers, timeout=15)
        return response.json()
    except: return None

def get_title_from_html(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            match = re.search(r'<title>(.*?)</title>', content)
            if match: return match.group(1)
    except: pass
    return "추천 상품"

# [업그레이드] 키워드 창고 대개방 (수백 가지 조합 가능)
def get_random_keyword():
    modifiers = [
        "가성비", "인기", "추천", "세일", "베스트", "특가", "국민", "필수", "요즘 뜨는", "대박",
        "자취생", "학생용", "사무용", "선물용", "부모님", "아이들", "캠핑용", "여행용", "집들이",
        "봄", "여름", "가을", "겨울", "장마철", "폭염", "한파"
    ]
    
    brands = [
        "삼성", "LG", "애플", "샤오미", "다이슨", "테팔", "필립스", "브라운", "쿠쿠", "쿠첸", # 가전
        "나이키", "아디다스", "뉴발란스", "휠라", "언더아머", "노스페이스", "파타고니아", # 의류
        "농심", "오뚜기", "CJ", "비비고", "햇반", "동원", "서울우유", "종근당", "정관장", # 식품
        "크리넥스", "코디", "다우니", "피죤", "페브리즈", "유한킴벌리", "3M" # 생필품
    ]
    
    products = [
        "노트북", "모니터", "마우스", "키보드", "아이패드", "갤럭시탭", "에어팟", "버즈", "스마트워치", # 디지털
        "라면", "생수", "햇반", "김치", "통조림", "커피", "우유", "두유", "영양제", "유산균", "오메가3", # 식품
        "물티슈", "휴지", "세제", "섬유유연제", "샴푸", "바디워시", "치약", "칫솔", "마스크", # 생필품
        "청소기", "로봇청소기", "공기청정기", "제습기", "선풍기", "에어프라이어", "전자레인지", "건조기", # 가전
        "반팔티", "후드티", "슬랙스", "청바지", "패딩", "바람막이", "운동화", "슬리퍼", "양말" # 의류
    ]
    
    specs = [
        "대용량", "1+1", "세트", "번들", "무료배송", "로켓배송", "새벽배송", 
        "고속충전", "무선", "저소음", "게이밍", "미니", "휴대용", 
        "화이트", "블랙", "네이비", "그레이", "파스텔", "신상"
    ]
    
    # 4가지를 다 섞으면 너무 길어서 검색 결과가 없을 수도 있으니, 
    # 랜덤으로 2~3개만 조합해서 더 정확한 검색어를 만듭니다.
    strategy = random.choice([1, 2, 3])
    if strategy == 1:
        return f"{random.choice(modifiers)} {random.choice(products)}"
    elif strategy == 2:
        return f"{random.choice(brands)} {random.choice(products)}"
    else:
        return f"{random.choice(brands)} {random.choice(products)} {random.choice(specs)}"

def main():
    os.makedirs("posts", exist_ok=True)
    
    # 2. 상품 데이터 수집
    target = get_random_keyword()
    print(f"오늘의 검색어: {target}")
    
    res = fetch_data(target)
    
    # 3. 상품 파일 생성
    if res and 'data' in res and res['data'].get('productData'):
        clean_target = target.replace(" ", "_")
        for item in res['data']['productData']:
            try:
                p_id = item['productId']
                filename = f"posts/{datetime.now().strftime('%Y%m%d')}_{clean_target}_{p_id}.html"
                if os.path.exists(filename): continue 
                
                with open(filename, "w", encoding="utf-8") as f:
                    f.write(f"""<!DOCTYPE html><html><head><meta charset='UTF-8'><meta name="viewport" content="width=device-width, initial-scale=1.0"><title>{item['productName']}</title>
                    <style>
                        body {{ font-family: sans-serif; background: #f5f6f8; padding: 20px; text-align: center; }}
                        .container {{ max-width: 600px; margin: auto; background: white; padding: 20px; border-radius: 15px; box-shadow: 0 2px 10px rgba(0,0,0,0.05); }}
                        img {{ width: 100%; border-radius: 10px; }}
                        .btn {{ background: #e44d26; color: white; padding: 15px 30px; text-decoration: none; border-radius: 30px; display: inline-block; margin-top: 20px; font-weight: bold; transition: 0.3s; }}
                        .btn:hover {{ transform: scale(1.05); }}
                    </style></head><body>
                    <div class='container'>
                        <h2>{item['productName']}</h2>
                        <img src='{item['productImage']}'>
                        <h3 style='color:#e44d26;'>{format(item['productPrice'], ',')}원</h3>
                        <a href='{item['productUrl']}' class='btn'>👉 쿠팡 최저가 보기</a>
                        <p style='font-size:0.8rem; color:#888; margin-top:20px;'>수수료를 제공받을 수 있음</p>
                    </div></body></html>""")
            except: continue

    # 4. 메인 화면(index.html) 업데이트
    files = sorted([f for f in os.listdir("posts") if f.endswith(".html")], reverse=True)
    
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(f"""<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>핫딜 셔틀</title>
    <style>
        body {{ font-family: 'Apple SD Gothic Neo', sans-serif; background: #f0f2f5; margin: 0; padding: 20px; }}
        .header {{ text-align: center; background: white; padding: 30px; border-radius: 20px; margin-bottom: 20px; box-shadow: 0 4px 10px rgba(0,0,0,0.05); }}
        h1 {{ color: #e44d26; margin: 0; font-size: 1.8rem; }}
        .grid {{ display: grid; grid-template-columns: repeat(auto-fill, minmax(250px, 1fr)); gap: 15px; max-width: 1000px; margin: auto; }}
        .card {{ background: white; padding: 20px; border-radius: 15px; text-decoration: none; color: #333; display: flex; flex-direction: column; justify-content: space-between; min-height: 120px; border: 1px solid #eee; transition: 0.3s; }}
        .card:hover {{ border-color: #e44d26; transform: translateY(-3px); box-shadow: 0 5px 15px rgba(0,0,0,0.1); }} 
        .title {{ font-weight: bold; font-size: 1rem; margin-bottom: 10px; line-height: 1.4; overflow: hidden; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; }}
        .badge {{ color: #e44d26; font-size: 0.8rem; font-weight: bold; text-align: right; margin-top: auto; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🚀 실시간 핫딜 쇼핑몰</h1>
        <p style="color:#666;">매일 업데이트되는 최저가 상품</p>
        <p style="font-size:0.8rem; color:#999;">최근 업데이트: {datetime.now().strftime('%Y-%m-%d %H:%M')}</p>
        <p style="font-size:0.8rem; color:#aaa;">검색어: {target}</p>
    </div>
    <div class="grid">
""")
        if files:
            for file in files[:60]:
                real_name = get_title_from_html(f"posts/{file}")
                f.write(f"""
        <a class="card" href="posts/{file}">
            <div class="title">{real_name}</div>
            <div class="badge">최저가 확인하기 ></div>
        </a>""")
        else:
            f.write("<div class='card'><h3>상품 수집 중...</h3><p>잠시 후 다시 접속해주세요.</p></div>")
            
        f.write("    </div></body></html>")

    # 5. 마무리
    with open("README.md", "w", encoding="utf-8") as f:
        f.write("# 🛒 쇼핑몰 가동 중\n\n[웹사이트 바로가기](https://rkskqdl-a11y.github.io/coupang-sale-shuttle/)")
    with open(".nojekyll", "w", encoding="utf-8") as f: f.write("")

if __name__ == "__main__":
    main()
