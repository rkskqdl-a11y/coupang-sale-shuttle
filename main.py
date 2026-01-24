import os
import hmac
import hashlib
import time
import requests
import json
from datetime import datetime

ACCESS_KEY = os.environ['COUPANG_ACCESS_KEY']
SECRET_KEY = os.environ['COUPANG_SECRET_KEY']

# 마케팅 타겟 키워드 (더 세밀하게 구성)
MARKETING_KEYWORDS = ["삼성전자노트북", "LG그램", "무선청소기", "가성비모니터", "자취생필수템", "에어프라이어", "캠핑의자"]

def get_authorization_header(method, path, query_string):
    datetime_gmt = time.strftime('%y%m%dT%H%M%SZ', time.gmtime())
    message = datetime_gmt + method + path + query_string
    signature = hmac.new(bytes(SECRET_KEY, 'utf-8'), msg=bytes(message, 'utf-8'), digestmod=hashlib.sha256).hexdigest()
    return f"CEA algorithm=HmacSHA256, access-key={ACCESS_KEY}, signed-date={datetime_gmt}, signature={signature}"

def search_products(keyword):
    DOMAIN = "https://api-gateway.coupang.com"
    # 개별 상품 노출을 위해 검색량을 적절히 조절 (최신순/베스트 10개 추출)
    URL = f"/v2/providers/affiliate_open_api/apis/opensource/v1/search?keyword={keyword}&limit=10"
    headers = {
        "Authorization": get_authorization_header("GET", URL, ""),
        "Content-Type": "application/json"
    }
    response = requests.get(DOMAIN + URL, headers=headers)
    return response.json()

def save_individual_products(products, keyword):
    os.makedirs("posts", exist_ok=True)
    product_list = products.get('data', {}).get('productData', [])
    
    for idx, item in enumerate(product_list):
        # 상품 ID를 활용해 고유한 파일명 생성 (중복 방지)
        product_id = item['productId']
        date_str = datetime.now().strftime('%Y%m%d')
        filename = f"posts/{date_str}_{product_id}.md"
        
        # 이미 올린 상품이면 건너뛰기
        if os.path.exists(filename): continue

        with open(filename, "w", encoding="utf-8") as f:
            f.write(f"# 🔥 [특가] {item['productName']}\n\n")
            f.write(f"![상품이미지]({item['productImage']})\n\n")
            f.write(f"## 📋 상품 정보\n")
            f.write(f"- **현재가:** {format(item['productPrice'], ',')}원\n")
            if item.get('discountRate'):
                f.write(f"- **할인율:** {item['discountRate']}% 적용 중\n")
            
            f.write(f"\n### 🔍 상세 정보 및 구매 평점 확인\n")
            f.write(f"쿠팡에서 실제 구매자들의 생생한 후기를 확인해 보세요!\n\n")
            f.write(f"[👉 제품 상세 페이지로 이동하기]({item['productUrl']})\n\n")
            f.write("---\n")
            f.write("*이 포스팅은 쿠팡 파트너스 활동의 일환으로 수수료를 제공받을 수 있습니다.*")

def update_readme():
    post_files = [f for f in os.listdir("posts") if f.endswith(".md")]
    post_files.sort(reverse=True)
    
    with open("README.md", "w", encoding="utf-8") as f:
        f.write("# 🚀 실시간 개별 상품 특가 정보\n")
        f.write("구매자가 많이 찾는 인기 상품의 개별 상세 페이지입니다.\n\n")
        f.write("## 📅 최신 등록 상품\n")
        for file in post_files[:20]: # 최근 등록된 20개 개별 상품 노출
            # 파일명을 읽어 가독성 있게 표시
            f.write(f"- [상세보기] {file} (posts/{file})\n")

if __name__ == "__main__":
    day_of_year = datetime.now().timetuple().tm_yday
    target_keyword = MARKETING_KEYWORDS[day_of_year % len(MARKETING_KEYWORDS)]
    data = search_products(target_keyword)
    save_individual_products(data, target_keyword)
    update_readme()
