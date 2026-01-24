import os
import hmac
import hashlib
import time
import requests
import json
from datetime import datetime

# 1. GitHub Secrets에서 API 키 불러오기
ACCESS_KEY = os.environ['COUPANG_ACCESS_KEY']
SECRET_KEY = os.environ['COUPANG_SECRET_KEY']

# 2. 마케팅 전략 키워드 (여기에 원하는 검색어를 계속 추가하세요)
KEYWORDS = ["가성비 노트북", "자취생 필수템", "부모님 선물 추천", "캠핑 용품", "주방 꿀템"]

def get_authorization_header(method, path, query_string):
    datetime_gmt = time.strftime('%y%m%dT%H%M%SZ', time.gmtime())
    message = datetime_gmt + method + path + query_string
    signature = hmac.new(bytes(SECRET_KEY, 'utf-8'), msg=bytes(message, 'utf-8'), digestmod=hashlib.sha256).hexdigest()
    return f"CEA algorithm=HmacSHA256, access-key={ACCESS_KEY}, signed-date={datetime_gmt}, signature={signature}"

def search_products(keyword):
    DOMAIN = "https://api-gateway.coupang.com"
    URL = f"/v2/providers/affiliate_open_api/apis/opensource/v1/search?keyword={keyword}&limit=20"
    
    headers = {
        "Authorization": get_authorization_header("GET", URL, ""),
        "Content-Type": "application/json"
    }
    
    response = requests.get(DOMAIN + URL, headers=headers)
    return response.json()

def save_to_markdown(products, keyword):
    filename = f"posts/{datetime.now().strftime('%Y-%m-%d')}-{keyword}.md"
    os.makedirs("posts", exist_ok=True)
    
    with open(filename, "w", encoding="utf-8") as f:
        f.write(f"# 🚀 오늘의 {keyword} 추천 리스트\n\n")
        
        for item in products.get('data', {}).get('productData', []):
            f.write(f"### {item['productName']}\n")
            f.write(f"![상품이미지]({item['productImage']})\n\n")
            f.write(f"- **가격**: {item['productPrice']}원\n")
            f.write(f"- **할인율**: {item['discountRate']}%\n")
            f.write(f"- [👉 상품 자세히 보기 및 구매하기]({item['productUrl']})\n\n")
            f.write("---\n")
            
        f.write("\n\n*이 포스팅은 쿠팡 파트너스 활동의 일환으로, 이에 따른 일정액의 수수료를 제공받습니다.*")

# 실행 로직
if __name__ == "__main__":
    # 매일 다른 키워드로 검색 (날짜를 기준으로 인덱스 순환)
    target_keyword = KEYWORDS[datetime.now().day % len(KEYWORDS)]
    data = search_products(target_keyword)
    save_to_markdown(data, target_keyword)
