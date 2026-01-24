import os
import hmac
import hashlib
import time
import requests
import json
from datetime import datetime
from urllib.parse import urlencode

ACCESS_KEY = os.environ.get('COUPANG_ACCESS_KEY')
SECRET_KEY = os.environ.get('COUPANG_SECRET_KEY')

# [디테일 롱테일 키워드 리스트]
KEYWORDS = ["햇반", "생수", "라면", "휴지", "물티슈", "노트북", "아이폰케이스", "캠핑의자", "왼손마우스", "베이컨"]

def get_authorization_header(method, path, query_string):
    datetime_gmt = time.strftime('%y%m%dT%H%M%SZ', time.gmtime())
    message = datetime_gmt + method + path + query_string
    signature = hmac.new(bytes(SECRET_KEY, 'utf-8'), msg=bytes(message, 'utf-8'), digestmod=hashlib.sha256).hexdigest()
    return f"CEA algorithm=HmacSHA256, access-key={ACCESS_KEY}, signed-date={datetime_gmt}, signature={signature}"

def fetch_data(keyword):
    DOMAIN = "https://api-gateway.coupang.com"
    path = "/v2/providers/affiliate_open_api/apis/openapi/v1/products/search"
    
    # limit을 안정적인 10으로 하향 조정
    params = {
        "keyword": keyword,
        "limit": 10
    }
    query_string = urlencode(params)
    url = f"{DOMAIN}{path}?{query_string}"
    
    headers = {
        "Authorization": get_authorization_header("GET", path, query_string),
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        return response.json()
    except Exception as e:
        print(f"DEBUG: 에러 발생 - {e}")
        return None

def save_products():
    os.makedirs("posts", exist_ok=True)
    target = KEYWORDS[int(time.time()) % len(KEYWORDS)]
    res = fetch_data(target)
    
    # 쿠팡 API는 성공 시 rCode가 '0'이거나 '200'이 아닐 수 있으므로 데이터 존재 여부로 판단
    if not res or 'data' not in res or not res['data'].get('productData'):
        print(f"DEBUG: 상품 데이터를 찾을 수 없습니다. 응답: {res}")
        return

    items = res['data']['productData']
    print(f"DEBUG: [{target}] 상품 {len(items)}개 생성 시작!")

    for item in items:
        p_id = item['productId']
        date_str = datetime.now().strftime('%Y%m%d')
        filename = f"posts/{date_str}_{p_id}.md"
        
        with open(filename, "w", encoding="utf-8") as f:
            f.write(f"# 🔥 [추천] {item['productName']}\n\n")
            f.write(f"![상품이미지]({item['productImage']})\n\n")
            f.write(f"## 💰 가격: {format(item['productPrice'], ',')}원\n\n")
            f.write(f"### 🔗 [제품 상세정보 확인하기]({item['productUrl']})\n\n")
            f.write("---\n*이 포스팅은 쿠팡 파트너스 활동의 일환으로 수수료를 제공받을 수 있습니다.*")
    
    update_index()

def update_index():
    if not os.path.exists("posts"): return
    files = sorted([f for f in os.listdir("posts") if f.endswith(".md")], reverse=True)
    with open("README.md", "w", encoding="utf-8") as f:
        f.write("# 🚀 실시간 초정밀 핫딜 리스트\n\n## 📅 최신 등록 상품\n")
        for file in files[:30]:
            f.write(f"- [상세보기] {file} (posts/{file})\n")

if __name__ == "__main__":
    save_products()
