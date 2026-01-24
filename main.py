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

# [초정밀 롱테일 키워드 50개] - API가 가장 잘 반응하는 단어들로 구성
KEYWORDS = [
    "햇반", "생수", "라면", "두루마리휴지", "물티슈", "샴푸", "바디워시", "세탁세제",
    "노트북", "무선마우스", "블루투스이어폰", "보조배터리", "충전기", "아이패드케이스",
    "에어프라이어", "믹서기", "전기포트", "가습기", "제습기", "청소기",
    "단백질쉐이크", "비타민C", "유산균", "오메가3", "마스크",
    "강아지사료", "고양이모래", "배변패드", "간식", "애견샴푸",
    "캠핑의자", "캠핑테이블", "텐트", "랜턴", "침낭",
    "베이컨", "닭가슴살", "계란", "우유", "요거트",
    "양말", "반팔티", "청바지", "슬리퍼", "운동화",
    "왼손마우스", "인강용노트북", "학생용노트북", "베이킹소다", "주방세제"
]

def get_authorization_header(method, path, query_string):
    datetime_gmt = time.strftime('%y%m%dT%H%M%SZ', time.gmtime())
    message = datetime_gmt + method + path + query_string
    signature = hmac.new(bytes(SECRET_KEY, 'utf-8'), msg=bytes(message, 'utf-8'), digestmod=hashlib.sha256).hexdigest()
    return f"CEA algorithm=HmacSHA256, access-key={ACCESS_KEY}, signed-date={datetime_gmt}, signature={signature}"

def fetch_data(keyword):
    DOMAIN = "https://api-gateway.coupang.com"
    URL = f"/v2/providers/affiliate_open_api/apis/opensource/v1/search?keyword={keyword}&limit=20"
    
    headers = {
        "Authorization": get_authorization_header("GET", URL, ""),
        "Content-Type": "application/json"
    }
    
    try:
        print(f"DEBUG: [{keyword}] 검색 시도 중...")
        response = requests.get(DOMAIN + URL, headers=headers, timeout=15)
        print(f"DEBUG: API 응답 코드: {response.status_code}")
        return response.json()
    except Exception as e:
        print(f"DEBUG: API 호출 에러 발생: {e}")
        return None

def save_products():
    os.makedirs("posts", exist_ok=True)
    
    # 시간 기반으로 키워드 선택
    target = KEYWORDS[int(time.time()) % len(KEYWORDS)]
    res = fetch_data(target)
    
    if not res:
        print("DEBUG: API 응답이 비어있습니다.")
        return

    # 쿠팡 API 응답 구조 로그 출력 (문제 진단용)
    print(f"DEBUG: API 응답 본문 일부: {str(res)[:200]}")

    if 'data' not in res or 'productData' not in res['data']:
        print(f"DEBUG: [{target}] 키워드에 대한 상품 데이터가 응답에 없습니다.")
        return

    items = res['data']['productData']
    print(f"DEBUG: 찾은 상품 개수: {len(items)}")

    for item in items:
        p_id = item['productId']
        date_str = datetime.now().strftime('%Y%m%d')
        # 파일명 중복 방지 및 SEO를 위해 키워드 포함
        filename = f"posts/{date_str}_{p_id}.md"
        
        with open(filename, "w", encoding="utf-8") as f:
            f.write(f"# 🔥 [초특가] {item['productName']}\n\n")
            f.write(f"![상품이미지]({item['productImage']})\n\n")
            f.write(f"## 💰 가격 정보\n")
            f.write(f"- **현재 판매가:** {format(item['productPrice'], ',')}원\n")
            f.write(f"- **상태:** 베스트 인기 상품\n\n")
            f.write(f"### 🔗 상세 확인 및 구매\n")
            f.write(f"[👉 쿠팡에서 자세히 보기 및 후기확인]({item['productUrl']})\n\n")
            f.write("---\n")
            f.write("이 포스팅은 쿠팡 파트너스 활동의 일환으로 수수료를 제공받을 수 있습니다.")
    
    update_index()

def update_index():
    if not os.path.exists("posts"): return
    files = sorted([f for f in os.listdir("posts") if f.endswith(".md")], reverse=True)
    
    with open("README.md", "w", encoding="utf-8") as f:
        f.write("# 🚀 실시간 초정밀 핫딜 리스트\n")
        f.write(f"> 마지막 업데이트: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write("## 📅 최신 등록 상품\n")
        if not files:
            f.write("- 등록된 상품이 없습니다. 시스템 확인 중입니다.\n")
        else:
            for file in files[:30]: # 최근 30개 노출
                f.write(f"- [상세보기] {file} (posts/{file})\n")

if __name__ == "__main__":
    if not ACCESS_KEY or not SECRET_KEY:
        print("ERROR: API 키가 설정되지 않았습니다. GitHub Secrets를 확인하세요.")
    else:
        save_products()
