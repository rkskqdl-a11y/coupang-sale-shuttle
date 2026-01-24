import os
import hmac
import hashlib
import time
import requests
import json
from datetime import datetime

# 1. API 키 불러오기
ACCESS_KEY = os.environ.get('COUPANG_ACCESS_KEY')
SECRET_KEY = os.environ.get('COUPANG_SECRET_KEY')

# API가 가장 잘 반응하는 롱테일 키워드
KEYWORDS = ["햇반", "생수", "라면", "두루마리휴지", "물티슈", "샴푸", "바디워시", "노트북", "아이폰케이스", "캠핑의자"]

def get_authorization_header(method, path, query_string):
    datetime_gmt = time.strftime('%y%m%dT%H%M%SZ', time.gmtime())
    message = datetime_gmt + method + path + query_string
    signature = hmac.new(bytes(SECRET_KEY, 'utf-8'), msg=bytes(message, 'utf-8'), digestmod=hashlib.sha256).hexdigest()
    return f"CEA algorithm=HmacSHA256, access-key={ACCESS_KEY}, signed-date={datetime_gmt}, signature={signature}"

def fetch_data(keyword):
    DOMAIN = "https://api-gateway.coupang.com"
    # [수정됨] opensource -> openapi 로 경로 변경
    URL = f"/v2/providers/affiliate_open_api/apis/openapi/v1/search?keyword={keyword}&limit=20"
    
    headers = {
        "Authorization": get_authorization_header("GET", URL, ""),
        "Content-Type": "application/json"
    }
    
    try:
        print(f"DEBUG: [{keyword}] 검색 시도 중 (경로 수정 버전)...")
        response = requests.get(DOMAIN + URL, headers=headers, timeout=15)
        print(f"DEBUG: API 응답 코드: {response.status_code}")
        return response.json()
    except Exception as e:
        print(f"DEBUG: API 호출 에러 발생: {e}")
        return None

def save_products():
    os.makedirs("posts", exist_ok=True)
    target = KEYWORDS[int(time.time()) % len(KEYWORDS)]
    res = fetch_data(target)
    
    if not res or 'data' not in res or 'productData' not in res['data']:
        print(f"DEBUG: 데이터 구조 오류 또는 결과 없음: {res}")
        return

    items = res['data']['productData']
    print(f"DEBUG: 찾은 상품 개수: {len(items)}")

    for item in items:
        p_id = item['productId']
        date_str = datetime.now().strftime('%Y%m%d')
        filename = f"posts/{date_str}_{p_id}.md"
        
        with open(filename, "w", encoding="utf-8") as f:
            f.write(f"# 🔥 [초특가] {item['productName']}\n\n")
            f.write(f"![상품이미지]({item['productImage']})\n\n")
            f.write(f"## 💰 가격 정보\n")
            f.write(f"- **현재 판매가:** {format(item['productPrice'], ',')}원\n\n")
            f.write(f"### 🔗 상세 확인 및 구매\n")
            f.write(f"[👉 쿠팡에서 자세히 보기 및 후기확인]({item['productUrl']})\n\n")
            f.write("---\n")
            f.write("이 포스팅은 쿠팡 파트너스 활동의 일환으로 수수료를 제공받을 수 있습니다.")
    
    update_index()

def update_index():
    if not os.path.exists("posts"): return
    files = sorted([f for f in os.listdir("posts") if f.endswith(".md")], reverse=True)
    with open("README.md", "w", encoding="utf-8") as f:
        f.write("# 🚀 실시간 초정밀 핫딜 리스트\n\n")
        f.write("## 📅 최신 등록 상품\n")
        for file in files[:30]:
            f.write(f"- [상세보기] {file} (posts/{file})\n")

if __name__ == "__main__":
    save_products()
