import os
import hmac
import hashlib
import time
import requests
import json
from datetime import datetime

ACCESS_KEY = os.environ['COUPANG_ACCESS_KEY']
SECRET_KEY = os.environ['COUPANG_SECRET_KEY']

# [마케팅 전문가의 초정밀 키워드 리스트]
# 구매 의도가 확실한 디테일한 키워드들입니다. 계속 추가 가능합니다.
KEYWORDS = [
    "베이컨", "학생노트북", "인강용노트북", "왼손마우스", "무소음키보드", 
    "자취생침대", "캠핑용의자", "단백질보충제", "강아지배변패드", "고양이모래",
    "독서대", "블루투스이어폰", "보조배터리", "가습기", "전기포트",
    "에어프라이어", "물티슈", "세탁세제", "샴푸", "바디워시",
    "게이밍모니터", "데스크패드", "아이패드케이스", "맥북파우치", "거치대",
    "스탠딩책상", "목마사지기", "폼롤러", "요가매트", "손목보호대",
    "비타민D", "오메가3", "루테인", "밀크씨슬", "유산균",
    "햇반", "컵라면", "생수2L", "탄산수", "제로콜라",
    "에어팟프로", "갤럭시버즈", "스마트워치스트랩", "차량용거치대", "방향제"
    # 여기에 생각나시는 디테일한 키워드를 따옴표와 쉼표 사이에 계속 추가하시면 됩니다.
]

def get_authorization_header(method, path, query_string):
    datetime_gmt = time.strftime('%y%m%dT%H%M%SZ', time.gmtime())
    message = datetime_gmt + method + path + query_string
    signature = hmac.new(bytes(SECRET_KEY, 'utf-8'), msg=bytes(message, 'utf-8'), digestmod=hashlib.sha256).hexdigest()
    return f"CEA algorithm=HmacSHA256, access-key={ACCESS_KEY}, signed-date={datetime_gmt}, signature={signature}"

def fetch_data(keyword):
    DOMAIN = "https://api-gateway.coupang.com"
    # 실제 구매자가 검색할 법한 키워드로 검색
    URL = f"/v2/providers/affiliate_open_api/apis/opensource/v1/search?keyword={keyword}&limit=10"
    
    headers = {
        "Authorization": get_authorization_header("GET", URL, ""),
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.get(DOMAIN + URL, headers=headers, timeout=15)
        return response.json()
    except Exception as e:
        print(f"Error fetching data: {e}")
        return None

def save_products():
    os.makedirs("posts", exist_ok=True)
    
    # 날짜와 시간을 조합해 리스트에서 키워드를 순환 선택
    # 1000개가 넘어도 중복 없이 매번 다른 키워드를 잡습니다.
    seed = int(datetime.now().strftime('%Y%m%d%H%M'))
    target = KEYWORDS[seed % len(KEYWORDS)]
    
    print(f"--- 오늘의 정밀 타겟 키워드: {target} ---")
    res = fetch_data(target)
    
    if not res or 'data' not in res:
        print(f"[{target}] 결과가 없습니다. API 응답 확인 필요.")
        return

    items = res.get('data', {}).get('productData', [])
    
    if not items:
        print(f"[{target}] 상품 리스트가 비어있습니다.")
        return

    for item in items:
        p_id = item['productId']
        # 파일명에 키워드를 포함해 SEO(검색엔진최적화) 강화
        date_str = datetime.now().strftime('%Y%m%d')
        filename = f"posts/{date_str}_{target}_{p_id}.md"
        
        with open(filename, "w", encoding="utf-8") as f:
            f.write(f"# 🔥 [추천] {item['productName']}\n\n")
            f.write(f"![상품이미지]({item['productImage']})\n\n")
            f.write(f"## 💰 가격 및 혜택\n")
            f.write(f"- **판매가:** {format(item['productPrice'], ',')}원\n")
            f.write(f"- **특징:** {target} 관련 베스트 인기 상품\n\n")
            f.write(f"### 🔗 구매 링크\n")
            f.write(f"**실제 사용 후기와 상세 정보를 확인하세요!**\n\n")
            f.write(f"[👉 제품 상세페이지 바로가기]({item['productUrl']})\n\n")
            f.write("---\n")
            f.write("이 포스팅은 쿠팡 파트너스 활동의 일환으로 소정의 수수료를 제공받을 수 있습니다.")
    
    update_index()

def update_index():
    # 최신 등록 순으로 README 업데이트
    files = sorted([f for f in os.listdir("posts") if f.endswith(".md")], reverse=True)
    with open("README.md", "w", encoding="utf-8") as f:
        f.write("# 🚀 실시간 초정밀 핫딜 정보\n")
        f.write("> 구매 의사가 확실한 세부 품목별 베스트 상품입니다.\n\n")
        f.write("## 📅 최신 업데이트 상품\n")
        for file in files[:20]:
            # 파일명에서 키워드와 날짜 추출하여 가독성 있게 노출
            display_name = file.replace(".md", "").replace("_", " ")
            f.write(f"- [{display_name}](posts/{file})\n")

if __name__ == "__main__":
    save_products()
