import os
import hmac
import hashlib
import time
import requests
import json
from datetime import datetime
from urllib.parse import urlencode

# 1. API 키 불러오기
ACCESS_KEY = os.environ.get('COUPANG_ACCESS_KEY')
SECRET_KEY = os.environ.get('COUPANG_SECRET_KEY')

KEYWORDS = ["햇반", "생수", "라면", "휴지", "물티슈", "노트북", "아이폰케이스", "캠핑의자", "왼손마우스", "베이컨"]

def get_authorization_header(method, path, query_string):
    # 쿠팡 규격: 날짜 + 메서드 + 경로 + 쿼리스트링 (물음표 제외)
    datetime_gmt = time.strftime('%y%m%dT%H%M%SZ', time.gmtime())
    message = datetime_gmt + method + path + query_string
    
    signature = hmac.new(
        bytes(SECRET_KEY, 'utf-8'), 
        msg=bytes(message, 'utf-8'), 
        digestmod=hashlib.sha256
    ).hexdigest()
    
    return f"CEA algorithm=HmacSHA256, access-key={ACCESS_KEY}, signed-date={datetime_gmt}, signature={signature}"

def fetch_data(keyword):
    DOMAIN = "https://api-gateway.coupang.com"
    path = "/v2/providers/affiliate_open_api/apis/openapi/v1/products/search"
    
    # 쿼리 스트링을 딕셔너리로 관리하여 서명 생성 시 일관성 유지
    params = {
        "keyword": keyword,
        "limit": 20
    }
    query_string = urlencode(params)
    url = f"{DOMAIN}{path}?{query_string}"
    
    headers = {
        "Authorization": get_authorization_header("GET", path, query_string),
        "Content-Type": "application/json"
    }
    
    try:
        print(f"DEBUG: [{keyword}] 서명 재검증 버전 실행 중...")
        response = requests.get(url, headers=headers, timeout=15)
        print(f"DEBUG: 응답 코드: {response.status_code}")
        return response.json()
    except Exception as e:
        print(f"DEBUG: 에러 발생 - {e}")
        return None

def save_products():
    os.makedirs("posts", exist_ok=True)
    # 중복 방지를 위해 시간 대신 날짜와 초 단위를 섞어 키워드 선택
    target = KEYWORDS[int(time.time()) % len(KEYWORDS)]
    res = fetch_data(target)
    
    if not res or res.get('data') is None:
        print(f"DEBUG: API 응답 본문: {res}")
        return

    items = res['data']['productData']
    print(f"DEBUG: [{target}] 상품 {len(items)}개 성공적으로 가져옴!")

    for item in items:
        p_id = item['productId']
        date_str = datetime.now().strftime('%Y%m%d')
        filename = f"posts/{date_str}_{p_id}.md"
        
        with open(filename, "w", encoding="utf-8") as f:
            f.write(f"# 🔥 [추천] {item['productName']}\n\n")
            f.write(f"![상품이미지]({item['productImage']})\n\n")
            f.write(f"## 💰 가격: {format(item['productPrice'], ',')}원\n\n")
            f.write(f"### 🔗 [상세정보 및 구매평 확인하기]({item['productUrl']})\n\n")
            f.write("---\n*이 포스팅은 쿠팡 파트너스 활동의 일환으로 수수료를 제공받을 수 있습니다.*")
    
    update_index()

def update_index():
    files = sorted([f for f in os.listdir("posts") if f.endswith(".md")], reverse=True)
    with open("README.md", "w", encoding="utf-8") as f:
        f.write("# 🚀 실시간 핫딜 리스트\n\n## 📅 최신 등록 상품\n")
        for file in files[:30]:
            f.write(f"- [상세보기] {file} (posts/{file})\n")

if __name__ == "__main__":
    if not ACCESS_KEY or not SECRET_KEY:
        print("ERROR: GitHub Secrets에 API 키가 설정되어 있지 않습니다.")
    else:
        save_products()
