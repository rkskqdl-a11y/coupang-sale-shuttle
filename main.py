import os
import hmac
import hashlib
import time
import requests
import json
from datetime import datetime
from urllib.parse import urlencode
import random

# API 키 설정
ACCESS_KEY = os.environ.get('COUPANG_ACCESS_KEY')
SECRET_KEY = os.environ.get('COUPANG_SECRET_KEY')

# [롱테일 4요소 무한 조합 박스] - 여기 단어를 추가할수록 그물망이 수만 개로 늘어납니다.
modifiers = ["가성비", "학생용", "자취생", "사무용", "선물용", "특가", "인기", "추천", "세일", "베스트", "국민", "필수"]
brands = [
    "삼성", "LG", "애플", "샤오미", "나이키", "아디다스", "뉴발란스", "폴로", "타미힐피거", "지오다노", 
    "햇반", "비비고", "다이슨", "테팔", "필립스", "파타고니아", "노스페이스", "에잇세컨즈", "탑텐", "유니클로"
]
products = [
    "노트북", "모니터", "마우스", "키보드", "반팔티", "후드티", "슬랙스", "러닝화", "백팩", 
    "생수", "라면", "에어프라이어", "캠핑의자", "텐트", "배변패드", "물티슈", "청소기", "원피스", "조거팬츠"
]
specs = ["대용량", "무라벨", "고속충전", "경량", "오버핏", "무소음", "접이식", "미니", "휴대용", "화이트", "블랙", "베스트셀러"]

def get_random_keyword():
    # 4가지 박스에서 각각 하나씩 무작위 추출하여 조합
    return f"{random.choice(modifiers)} {random.choice(brands)} {random.choice(products)} {random.choice(specs)}"

def get_authorization_header(method, path, query_string):
    datetime_gmt = time.strftime('%y%m%dT%H%M%SZ', time.gmtime())
    message = datetime_gmt + method + path + query_string
    signature = hmac.new(bytes(SECRET_KEY, 'utf-8'), msg=bytes(message, 'utf-8'), digestmod=hashlib.sha256).hexdigest()
    return f"CEA algorithm=HmacSHA256, access-key={ACCESS_KEY}, signed-date={datetime_gmt}, signature={signature}"

def fetch_data(keyword):
    DOMAIN = "https://api-gateway.coupang.com"
    path = "/v2/providers/affiliate_open_api/apis/openapi/v1/products/search"
    # 1회 실행 시 10개 상품만 가져옴
    params = {"keyword": keyword, "limit": 10}
    query_string = urlencode(params)
    url = f"{DOMAIN}{path}?{query_string}"
    headers = {"Authorization": get_authorization_header("GET", path, query_string), "Content-Type": "application/json"}
    try:
        response = requests.get(url, headers=headers, timeout=15)
        return response.json()
    except: return None

def save_products():
    os.makedirs("posts", exist_ok=True)
    
    # 랜덤 조합 키워드 1개 생성
    target = get_random_keyword()
    print(f"--- 이번 업로드 타겟 키워드: {target} ---")
    
    res = fetch_data(target)
    if not res or 'data' not in res or not res['data'].get('productData'):
        print("상품 데이터가 없습니다.")
        return

    items = res['data']['productData']
    for item in items:
        p_id = item['productId']
        filename = f"posts/{datetime.now().strftime('%Y%m%d')}_{p_id}.md"
        
        # 중복 파일 생성 방지
        if os.path.exists(filename): continue 

        with open(filename, "w", encoding="utf-8") as f:
            # 소비자용 중앙 정렬 및 디자인 레이아웃
            f.write(f"<div align='center'>\n\n")
            f.write(f"# 🚀 [오늘의 추천] {item['productName']}\n\n")
            f.write(f"![상품이미지]({item['productImage']})\n\n")
            f.write(f"## 📋 상세 정보 및 가격\n")
            f.write(f"| 항목 | 내용 |\n| :--- | :--- |\n")
            f.write(f"| **판매가** | <b style='color:red; font-size:1.2em;'>{format(item['productPrice'], ',')}원</b> |\n")
            f.write(f"| **배송** | 로켓배송 / 무료배송 지원 |\n")
            f.write(f"| **키워드** | #{target.replace(' ', ' #')} |\n\n")
            
            # 주황색 버튼 UI
            f.write(f"<a href='{item['productUrl']}' style='background-color: #ff4500; color: white; padding: 18px 30px; text-decoration: none; border-radius: 12px; font-weight: bold; font-size: 1.2em; display: inline-block;'>🛒 최저가 확인 및 구매하기 (클릭) 🛒</a>\n\n")
            f.write(f"</div>\n\n---\n<p align='center' style='font-size: 0.8em; color: gray;'>본 포스팅은 파트너스 활동의 일환으로 수수료를 제공받을 수 있습니다.</p>")

    update_index()

def update_index():
    if not os.path.exists("posts"): return
    files = sorted([f for f in os.listdir("posts") if f.endswith(".md")], reverse=True)
    with open("README.md", "w", encoding="utf-8") as f:
        f.write(f"<div align='center'>\n\n# 🏆 실시간 가성비 핫딜 정보 센터 🏆\n\n## 📅 최근 업데이트 상품\n")
        for file in files[:50]:
            f.write(f"#### [{file.replace('.md','')}](posts/{file})\n")
        f.write(f"</div>")

if __name__ == "__main__":
    save_products()
