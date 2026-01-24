import os
import hmac
import hashlib
import time
import requests
import json
from datetime import datetime

ACCESS_KEY = os.environ['COUPANG_ACCESS_KEY']
SECRET_KEY = os.environ['COUPANG_SECRET_KEY']

# 마케팅 전문가 추천: 검색 실패 확률이 적은 '검색어'와 '카테고리' 혼합 전략
KEYWORDS = ["노트북", "아이폰", "캠핑", "생수", "기저귀", "단백질쉐이크"]

def get_authorization_header(method, path, query_string):
    datetime_gmt = time.strftime('%y%m%dT%H%M%SZ', time.gmtime())
    message = datetime_gmt + method + path + query_string
    signature = hmac.new(bytes(SECRET_KEY, 'utf-8'), msg=bytes(message, 'utf-8'), digestmod=hashlib.sha256).hexdigest()
    return f"CEA algorithm=HmacSHA256, access-key={ACCESS_KEY}, signed-date={datetime_gmt}, signature={signature}"

def fetch_data(keyword):
    DOMAIN = "https://api-gateway.coupang.com"
    # 검색 API 호출
    URL = f"/v2/providers/affiliate_open_api/apis/opensource/v1/search?keyword={keyword}&limit=10"
    
    headers = {
        "Authorization": get_authorization_header("GET", URL, ""),
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.get(DOMAIN + URL, headers=headers, timeout=10)
        return response.json()
    except:
        return None

def save_products():
    os.makedirs("posts", exist_ok=True)
    target = KEYWORDS[datetime.now().day % len(KEYWORDS)]
    res = fetch_data(target)
    
    items = res.get('data', {}).get('productData', [])
    
    if not items:
        print(f"{target}에 대한 상품 결과가 없습니다.")
        return

    for item in items:
        p_id = item['productId']
        filename = f"posts/{datetime.now().strftime('%Y%m%d')}_{p_id}.md"
        
        with open(filename, "w", encoding="utf-8") as f:
            # 1페이지 1상품: 구매 집중도 극대화 레이아웃
            f.write(f"# 🔥 [오늘의 픽] {item['productName']}\n\n")
            f.write(f"![상품이미지]({item['productImage']})\n\n")
            f.write(f"## 💰 특가 정보\n")
            f.write(f"- **판매가격:** {format(item['productPrice'], ',')}원\n")
            f.write(f"- **배송정보:** 쿠팡 무료배송/로켓배송 가능 여부 확인 필요\n\n")
            f.write(f"### 🔗 구매 및 상세정보 확인\n")
            f.write(f"[👉 지금 바로 확인하기 (클릭)]({item['productUrl']})\n\n")
            f.write("---\n")
            f.write("이 포스팅은 쿠팡 파트너스 활동의 일환으로 수수료를 제공받을 수 있습니다.")
    
    # README 업데이트
    update_index()

def update_index():
    files = sorted([f for f in os.listdir("posts") if f.endswith(".md")], reverse=True)
    with open("README.md", "w", encoding="utf-8") as f:
        f.write("# 🚀 실시간 핫딜 개별 상품 정보\n\n")
        for file in files[:15]:
            f.write(f"- [상세보기] {file} (posts/{file})\n")

if __name__ == "__main__":
    save_products()
