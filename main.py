import os
import hmac
import hashlib
import time
import requests
import json
from datetime import datetime

# 1. API 키 불러오기
ACCESS_KEY = os.environ['COUPANG_ACCESS_KEY']
SECRET_KEY = os.environ['COUPANG_SECRET_KEY']

# 2. 전 품목을 커버하는 마케팅 카테고리 사전 (전문가가 구성함)
# 매일 다른 카테고리를 공략하여 쿠팡 전체 상품을 타겟팅합니다.
MARKETING_CATEGORIES = [
    "가전디지털", "컴퓨터주변기기", "주방가전", "생활가전", # 가전 라인
    "홈인테리어", "가구", "생활용품", "주방용품", # 리빙 라인
    "스포츠레저", "캠핑용품", "골프", "낚시", # 레저 라인
    "뷰티", "화장품", "향수", # 뷰티 라인
    "출산유아동", "장난감", "기저귀", # 육아 라인
    "반려동물용품", "강아지사료", "고양이간식", # 펫 라인
    "자동차용품", "공구", "정원", # 기타 전문 라인
    "식품", "신선식품", "간편조리식품", "건강식품" # 식품 라인
]

def get_authorization_header(method, path, query_string):
    datetime_gmt = time.strftime('%y%m%dT%H%M%SZ', time.gmtime())
    message = datetime_gmt + method + path + query_string
    signature = hmac.new(bytes(SECRET_KEY, 'utf-8'), msg=bytes(message, 'utf-8'), digestmod=hashlib.sha256).hexdigest()
    return f"CEA algorithm=HmacSHA256, access-key={ACCESS_KEY}, signed-date={datetime_gmt}, signature={signature}"

def search_products(keyword):
    DOMAIN = "https://api-gateway.coupang.com"
    # 마케팅 효과를 위해 상품 정보를 최대한 많이 가져오도록 limit을 50으로 상향
    URL = f"/v2/providers/affiliate_open_api/apis/opensource/v1/search?keyword={keyword}&limit=50"
    
    headers = {
        "Authorization": get_authorization_header("GET", URL, ""),
        "Content-Type": "application/json"
    }
    
    response = requests.get(DOMAIN + URL, headers=headers)
    return response.json()

def save_to_markdown(products, keyword):
    # 파일 이름에 한글이 들어가면 오류가 날 수 있어 날짜 기반으로 생성
    date_str = datetime.now().strftime('%Y-%m-%d')
    filename = f"posts/{date_str}-deal.md"
    os.makedirs("posts", exist_ok=True)
    
    with open(filename, "w", encoding="utf-8") as f:
        f.write(f"# 🏷️ 오늘의 {keyword} 베스트 가성비 추천\n")
        f.write(f"> **작성일:** {date_str} | 실시간으로 업데이트되는 최저가 정보입니다.\n\n")
        
        product_list = products.get('data', {}).get('productData', [])
        
        if not product_list:
            f.write("현재 업데이트된 특가 상품이 없습니다. 잠시 후 다시 확인해 주세요.")
        else:
            for item in product_list:
                # 검색 최적화(SEO)를 위해 상품명과 스펙 정보를 풍성하게 구성
                f.write(f"## {item['productName']}\n")
                f.write(f"![{item['productName']}]({item['productImage']})\n\n")
                f.write(f"### 💰 혜택 정보\n")
                f.write(f"- **판매 가격:** {format(item['productPrice'], ',')}원\n")
                if item['discountRate'] > 0:
                    f.write(f"- **할인율:** {item['discountRate']}% 적용 중\n")
                
                # 가독성 높은 클릭 유도 버튼(마케팅 기법)
                f.write(f"\n#### [▶ 상세정보 및 구매 후기 확인하기]({item['productUrl']})\n\n")
                f.write("---\n")
            
        f.write("\n\n---\n")
        f.write("### 📢 안내사항\n")
        f.write("이 포스팅은 쿠팡 파트너스 활동의 일환으로, 이에 따른 일정액의 수수료를 제공받습니다. ")
        f.write("구매 가격에는 영향을 주지 않으며 채널 운영에 큰 도움이 됩니다. 감사합니다.\n")

if __name__ == "__main__":
    # 매일 다른 카테고리를 순환 선택 (전 품목 대상)
    day_of_year = datetime.now().timetuple().tm_yday
    target_keyword = MARKETING_CATEGORIES[day_of_year % len(MARKETING_CATEGORIES)]
    
    print(f"오늘의 타겟 키워드: {target_keyword}")
    data = search_products(target_keyword)
    save_to_markdown(data, target_keyword)
