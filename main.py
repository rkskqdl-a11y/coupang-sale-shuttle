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

MARKETING_CATEGORIES = [
    "가전디지털", "컴퓨터주변기기", "주방가전", "생활가전",
    "홈인테리어", "가구", "생활용품", "주방용품",
    "스포츠레저", "캠핑용품", "골프", "낚시",
    "뷰티", "화장품", "향수",
    "출산유아동", "장난감", "기저귀",
    "반려동물용품", "강아지사료", "고양이간식",
    "자동차용품", "공구", "정원",
    "식품", "신선식품", "간편조리식품", "건강식품"
]

def get_authorization_header(method, path, query_string):
    datetime_gmt = time.strftime('%y%m%dT%H%M%SZ', time.gmtime())
    message = datetime_gmt + method + path + query_string
    signature = hmac.new(bytes(SECRET_KEY, 'utf-8'), msg=bytes(message, 'utf-8'), digestmod=hashlib.sha256).hexdigest()
    return f"CEA algorithm=HmacSHA256, access-key={ACCESS_KEY}, signed-date={datetime_gmt}, signature={signature}"

def search_products(keyword):
    DOMAIN = "https://api-gateway.coupang.com"
    URL = f"/v2/providers/affiliate_open_api/apis/opensource/v1/search?keyword={keyword}&limit=50"
    headers = {
        "Authorization": get_authorization_header("GET", URL, ""),
        "Content-Type": "application/json"
    }
    response = requests.get(DOMAIN + URL, headers=headers)
    return response.json()

def update_readme():
    # posts 폴더 내의 모든 마크다운 파일을 가져와 최신순으로 정렬
    post_files = [f for f in os.listdir("posts") if f.endswith(".md")]
    post_files.sort(reverse=True)
    
    with open("README.md", "w", encoding="utf-8") as f:
        f.write("# 🚀 실시간 가성비 핫딜 셔틀\n")
        f.write("> 매일 업데이트되는 쿠팡 최저가 상품 리스트입니다.\n\n")
        f.write("## 📅 최신 업데이트 리스트\n")
        for file in post_files[:10]: # 최근 10개 포스팅만 노출
            date = file.split("-deal.md")[0]
            f.write(f"- [{date} 오늘의 특가 정보 보러가기](posts/{file})\n")
        f.write("\n\n---\n*이 채널은 쿠팡 파트너스 활동을 통해 소정의 수수료를 제공받을 수 있습니다.*")

def save_to_markdown(products, keyword):
    date_str = datetime.now().strftime('%Y-%m-%d')
    filename = f"posts/{date_str}-deal.md"
    os.makedirs("posts", exist_ok=True)
    
    with open(filename, "w", encoding="utf-8") as f:
        f.write(f"# 🏷️ 오늘의 {keyword} 베스트 가성비 추천\n")
        product_list = products.get('data', {}).get('productData', [])
        for item in product_list:
            f.write(f"## {item['productName']}\n")
            f.write(f"![{item['productName']}]({item['productImage']})\n\n")
            f.write(f"- **판매 가격:** {format(item['productPrice'], ',')}원\n")
            f.write(f"\n#### [▶ 상세정보 및 구매 후기 확인하기]({item['productUrl']})\n\n---\n")
        f.write("\n*이 포스팅은 쿠팡 파트너스 활동의 일환으로 수수료를 제공받을 수 있습니다.*")

if __name__ == "__main__":
    day_of_year = datetime.now().timetuple().tm_yday
    target_keyword = MARKETING_CATEGORIES[day_of_year % len(MARKETING_CATEGORIES)]
    data = search_products(target_keyword)
    save_to_markdown(data, target_keyword)
    update_readme() # README 업데이트 함수 실행
