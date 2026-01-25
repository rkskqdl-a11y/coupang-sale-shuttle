import os
import hmac
import hashlib
import time
import requests
import json
from datetime import datetime
from urllib.parse import urlencode

# 1. API 키 설정
ACCESS_KEY = os.environ.get('COUPANG_ACCESS_KEY')
SECRET_KEY = os.environ.get('COUPANG_SECRET_KEY')

def get_authorization_header(method, path, query_string):
    datetime_gmt = time.strftime('%y%m%dT%H%M%SZ', time.gmtime())
    message = datetime_gmt + method + path + query_string
    signature = hmac.new(bytes(SECRET_KEY, 'utf-8'), msg=bytes(message, 'utf-8'), digestmod=hashlib.sha256).hexdigest()
    return f"CEA algorithm=HmacSHA256, access-key={ACCESS_KEY}, signed-date={datetime_gmt}, signature={signature}"

def main():
    print("----- [진단 시작] -----")
    
    # 1. 키가 제대로 입력되었는지 확인 (앞 4자리만 출력)
    if not ACCESS_KEY or not SECRET_KEY:
        print("❌ 오류: GitHub Secrets에 키가 등록되지 않았습니다.")
        return
    else:
        print(f"✅ Access Key 확인됨: {ACCESS_KEY[:4]}****")
        print(f"✅ Secret Key 확인됨: (길이 {len(SECRET_KEY)}자)")

    # 2. 쿠팡 API 호출 시도
    DOMAIN = "https://api-gateway.coupang.com"
    path = "/v2/providers/affiliate_open_api/apis/openapi/v1/products/search"
    params = {"keyword": "라면", "limit": 1}
    query_string = urlencode(params)
    url = f"{DOMAIN}{path}?{query_string}"
    
    headers = {
        "Authorization": get_authorization_header("GET", path, query_string),
        "Content-Type": "application/json"
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        print(f"\n📡 응답 코드: {response.status_code}")
        print(f"📩 응답 내용: {response.text}")
        
        if response.status_code == 200:
            print("\n🎉 [성공] API 연결이 완벽합니다! 기존 코드를 다시 쓰시면 됩니다.")
        else:
            print("\n❌ [실패] 위 '응답 내용'을 복사해서 알려주세요.")
            
    except Exception as e:
        print(f"❌ 연결 오류 발생: {e}")

    # (웹사이트가 깨지지 않게 최소한의 파일 유지)
    os.makedirs("posts", exist_ok=True)
    with open("index.html", "w", encoding="utf-8") as f:
        f.write("<h1>API 진단 중... 로그를 확인하세요.</h1>")
    with open(".nojekyll", "w", encoding="utf-8") as f: f.write("")

if __name__ == "__main__":
    main()
