import os
import hmac
import hashlib
import time
import requests
import json
from datetime import datetime

ACCESS_KEY = os.environ.get('COUPANG_ACCESS_KEY')
SECRET_KEY = os.environ.get('COUPANG_SECRET_KEY')

KEYWORDS = ["햇반", "생수", "라면", "휴지", "물티슈", "노트북", "아이폰케이스", "캠핑의자", "왼손마우스", "베이컨"]

def get_authorization_header(method, path, query_string):
    # 쿠팡 공식 규격에 맞춘 타임스탬프 생성
    datetime_gmt = time.strftime('%y%m%dT%H%M%SZ', time.gmtime())
    message = datetime_gmt + method + path + query_string
    signature = hmac.new(bytes(SECRET_KEY, 'utf-8'), msg=bytes(message, 'utf-8'), digestmod=hashlib.sha256).hexdigest()
    return f"CEA algorithm=HmacSHA256, access-key={ACCESS_KEY}, signed-date={datetime_gmt}, signature={signature}"

def fetch_data(keyword):
    DOMAIN = "https://api-gateway.coupang.com"
    # [최종수정] 경로에 /products/ 가 반드시 포함되어야 합니다.
    path = "/v2/providers/affiliate_open_api/apis/openapi/v1/products/search"
    query_string = f"keyword={keyword}&limit=20"
    url = f"{DOMAIN}{path}?{query_string}"
    
    headers = {
        "Authorization": get_authorization_header("GET", path, query_string),
        "Content-Type": "application/json"
    }
    
    try:
        print(f"DEBUG: [{keyword}] 최신 경로로 검색 시도 중...")
        response = requests.get(url, headers=headers, timeout=15)
        return response.json()
    except Exception as e:
        print(f"DEBUG: 에러 발생 - {e}")
        return None

def save_products():
    os.makedirs("posts", exist_ok=True)
    target = KEYWORDS[int(time.time()) % len(KEYWORDS)]
    res = fetch_data(target)
    
    if not res or res.get('data') is None:
        print(f"DEBUG: API 응답 오류 - {res}")
        return

    items = res['data']['productData']
    print(f"DEBUG: [{target}] 상품 {len(items)}개 발견!")

    for item in items:
        p_id = item['productId']
        filename = f"posts/{datetime.now().strftime('%Y%m%d')}_{p_id}.md"
        with open(filename, "w", encoding="utf-8") as f:
            f.write(f"# 🔥 [추천] {item['productName']}\n\n")
            f.write(f"![상품이미지]({item['productImage']})\n\n")
            f.write(f"## 💰 가격: {format(item['productPrice'], ',')}원\n\n")
            f.write(f"### 🔗 [제품 상세정보 확인하기]({item['productUrl']})\n\n")
            f.write("---\n*이 포스팅은 쿠팡 파트너스 활동의 일환으로 수수료를 제공받을 수 있습니다.*")
    
    update_index()

def update_index():
    files = sorted([f for f in os.listdir("posts") if f.endswith(".md")], reverse=True)
    with open("README.md", "w", encoding="utf-8") as f:
        f.write("# 🚀 실시간 핫딜 리스트\n\n## 📅 최신 등록 상품\n")
        for file in files[:30]:
            f.write(f"- [상세보기] {file} (posts/{file})\n")

if __name__ == "__main__":
    save_products()
