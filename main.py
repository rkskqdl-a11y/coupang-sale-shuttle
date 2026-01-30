import os, hmac, hashlib, time, requests, json, random, re, uuid
from datetime import datetime
from time import gmtime, strftime

# 🚀 [System] Reco API v2 하베스팅 엔진 가동
print("🚀 쿠팡 Reco v2 엔진으로 전환합니다. (무차별 수집 모드)")

class CoupangRecoV2Engine:
    def __init__(self):
        self.access_key = os.environ.get('COUPANG_ACCESS_KEY', '').strip()
        self.secret_key = os.environ.get('COUPANG_SECRET_KEY', '').strip()
        self.gemini_key = os.environ.get('GEMINI_API_KEY', '').strip()
        self.site_url = "https://rkskqdl-a11y.github.io/coupang-sale-shuttle"
        self.endpoint = "/v2/providers/affiliate_open_api/apis/openapi/v2/products/reco"
        self.domain = "https://api-gateway.coupang.com"
        
    def generate_auth_header(self, method, path):
        """💎 공식 문서의 HMAC 생성 로직을 POST 방식에 맞춰 구현"""
        # POST 방식이므로 query_string은 빈 문자열("")입니다.
        datetime_gmt = strftime('%y%m%d', gmtime()) + 'T' + strftime('%H%M%S', gmtime()) + 'Z'
        message = datetime_gmt + method + path + "" # query는 없음
        
        signature = hmac.new(bytes(self.secret_key, "utf-8"),
                             message.encode("utf-8"),
                             hashlib.sha256).hexdigest()

        return "CEA algorithm=HmacSHA256, access-key={}, signed-date={}, signature={}".format(
            self.access_key, datetime_gmt, signature)

    def fetch_reco_products(self):
        """💎 JSON Body 구조를 공식 가이드와 100% 일치시켰습니다."""
        headers = {
            "Authorization": self.generate_auth_header("POST", self.endpoint),
            "Content-Type": "application/json"
        }
        
        # 💎 필수 파라미터 구성 (사용자 식별 및 노출 최적화)
        payload = {
            "site": {
                "id": "reco_site_01", # 사용자님의 사이트 고유 ID
                "domain": "rkskqdl-a11y.github.io"
            },
            "device": {
                "id": uuid.uuid4().hex, # 💎 필수: 32자리 고유 디바이스 ID 자동생성
                "lmt": 0
            },
            "imp": {
                "adType": 3, # 네이티브 광고 형태
                "imageSize": "500x500" # 💎 필수: 이미지 크기 지정
            },
            "user": {
                "puid": str(int(time.time())) # 💎 필수: 퍼블리셔 정의 사용자 ID
            }
        }
        
        try:
            url = self.domain + self.endpoint
            resp = requests.post(url, headers=headers, json=payload, timeout=15)
            
            if resp.status_code == 200:
                data = resp.json()
                items = data.get('data', [])
                if items: print(f"   ✅ Reco API로부터 {len(items)}개 상품 수신 성공!")
                return items
            else:
                print(f"   ❌ API 실패: {resp.status_code} | {resp.text[:100]}")
                return []
        except Exception as e:
            print(f"   ⚠️ 연결 오류: {e}")
            return []

    # --- (중략: generate_review, save_post, update_sitemap 함수는 시니어급 로직 유지) ---

    def generate_review(self, product_name):
        if not self.gemini_key: return "상세 분석 준비 중"
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={self.gemini_key}"
        try:
            prompt = f"상품 '{product_name}'에 대해 IT 칼럼니스트처럼 1000자 이상 전문적인 분석 글을 작성해줘. <h3> 사용, HTML만 사용, 해요체 사용. '할인' 언급 금지."
            res = requests.post(url, json={"contents": [{"parts": [{"text": prompt}]}]}, timeout=60)
            return res.json()['candidates'][0]['content']['parts'][0]['text'].replace("\n", "<br>")
        except: return f"<h3>🔍 제품 정밀 분석</h3>{product_name}은 품질이 보증된 강력 추천 상품입니다."

    def run(self):
        os.makedirs("posts", exist_ok=True)
        existing_ids = {f.split('_')[-1].replace('.html', '') for f in os.listdir("posts") if '_' in f}
        
        print(f"🕵️ 현재 {len(existing_ids)}개 진열 중. 무차별 수집 시작!")
        
        # 💎 Reco API는 한 번의 호출로 신선한 추천 리스트를 줍니다.
        products = self.fetch_reco_products()
        success_count = 0

        for item in products:
            p_id = str(item['productId'])
            if p_id in existing_ids: continue # 중복 필터링

            print(f"   ✨ 발견! [{success_count+1}] {item['productName'][:20]}...")
            content = self.generate_review(item['productName'])
            
            filename = f"posts/{datetime.now().strftime('%Y%m%d')}_{p_id}.html"
            self.save_post(filename, item, content)
            
            existing_ids.add(p_id)
            success_count += 1
            time.sleep(35) # 제미나이 한도 준수
            if success_count >= 10: break

        self.update_seo_files()
        print(f"🏁 작업 완료. 신규 발행: {success_count}개")

    def save_post(self, filename, item, content):
        img, price = item['productImage'], format(int(item['productPrice']), ',')
        html = f"""<!DOCTYPE html><html lang='ko'><head><meta charset='UTF-8'><title>{item['productName']} 리뷰</title>
        <style>body{{font-family:sans-serif; background:#f8f9fa; padding:20px; color:#333; line-height:2.2;}}
        .card{{max-width:750px; margin:auto; background:white; padding:50px; border-radius:30px; box-shadow:0 20px 50px rgba(0,0,0,0.05);}}
        img{{width:100%; border-radius:20px; margin:30px 0;}} .p-val{{font-size:2.5rem; color:#e44d26; font-weight:bold; text-align:center;}}
        .buy-btn{{display:block; background:#e44d26; color:white; text-align:center; padding:25px; text-decoration:none; border-radius:60px; font-weight:bold;}}</style></head>
        <body><div class='card'><h2>{item['productName']}</h2><img src='{img}'><div class='content'>{content}</div><div class='p-val'>{price}원</div>
        <a href='{item['productUrl']}' class='buy-btn'>🛍️ 상세 정보 확인하기</a></div></body></html>"""
        with open(filename, "w", encoding="utf-8") as f: f.write(html)

    def update_seo_files(self):
        files = sorted([f for f in os.listdir("posts") if f.endswith(".html")], reverse=True)
        now = datetime.now().strftime("%Y-%m-%d")
        with open("sitemap.xml", "w", encoding="utf-8") as f:
            f.write('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n')
            f.write(f'  <url><loc>{self.site_url}/</loc><lastmod>{now}</lastmod><priority>1.0</priority></url>\n')
            for file in files:
                f.write(f'  <url><loc>{self.site_url}/posts/{file}</loc><lastmod>{now}</lastmod></url>\n')
            f.write('</urlset>')

if __name__ == "__main__":
    CoupangRecoV2Engine().run()
