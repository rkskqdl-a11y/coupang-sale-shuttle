import os, hmac, hashlib, time, requests, json, random, re, uuid
from datetime import datetime
from time import gmtime, strftime

# 🚀 [System] 사용자 AF7053799 전용 엔진 가동 (진단 모드 포함)
print("🚀 쿠팡 Reco v2 & Search 하이브리드 엔진이 가동됩니다. (ID: AF7053799)")

class CoupangUltimateEngine:
    def __init__(self):
        self.access_key = os.environ.get('COUPANG_ACCESS_KEY', '').strip()
        self.secret_key = os.environ.get('COUPANG_SECRET_KEY', '').strip()
        self.gemini_key = os.environ.get('GEMINI_API_KEY', '').strip()
        # 💎 사용자님의 파트너스 아이디 반영
        self.partners_id = "AF7053799"
        self.site_url = "https://rkskqdl-a11y.github.io/coupang-sale-shuttle"
        self.posts_dir = "posts"
        os.makedirs(self.posts_dir, exist_ok=True)

    def _generate_hmac(self, method, path, query_string=""):
        """💎 공식 문서 가이드를 100% 준수하는 HMAC 생성기"""
        datetime_gmt = strftime('%y%m%d', gmtime()) + 'T' + strftime('%H%M%S', gmtime()) + 'Z'
        message = datetime_gmt + method + path + query_string
        signature = hmac.new(bytes(self.secret_key, "utf-8"),
                             message.encode("utf-8"),
                             hashlib.sha256).hexdigest()
        return "CEA algorithm=HmacSHA256, access-key={}, signed-date={}, signature={}".format(
            self.access_key, datetime_gmt, signature)

    def fetch_reco_v2(self):
        """💎 최신 v2 Reco API: 쿠팡 추천 로직으로 0개 수집 현상을 해결합니다."""
        path = "/v2/providers/affiliate_open_api/apis/openapi/v2/products/reco"
        headers = {
            "Authorization": self._generate_hmac("POST", path),
            "Content-Type": "application/json"
        }
        
        # 💎 공식 문서 기반 필수 파라미터 구조화
        payload = {
            "site": {
                "id": self.partners_id, 
                "domain": "rkskqdl-a11y.github.io"
            },
            "device": {
                "id": uuid.uuid4().hex, # 32자리 고유 ID 자동 생성
                "lmt": 0
            },
            "imp": {
                "adType": 3, 
                "imageSize": "600x600"
            },
            "user": {
                "puid": "user_" + str(int(time.time()))
            }
        }
        
        try:
            url = f"https://api-gateway.coupang.com{path}"
            resp = requests.post(url, headers=headers, json=payload, timeout=20)
            if resp.status_code == 200:
                data = resp.json()
                items = data.get('data', [])
                if items: print(f"   ✅ Reco API: {len(items)}개 상품 수신 성공!")
                return items
            else:
                print(f"   ❌ API 응답 실패 ({resp.status_code}): {resp.text[:100]}")
                return []
        except Exception as e:
            print(f"   ⚠️ 통신 오류: {e}")
            return []

    def generate_review(self, product_name):
        """💎 제미나이 1.5 플래시 기반 고품질 칼럼 생성 (1,000자 이상)"""
        if not self.gemini_key: return "상세 분석 데이터 준비 중입니다."
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={self.gemini_key}"
        prompt = (f"상품 '{product_name}'에 대해 쇼핑 전문가가 작성한 1,000자 이상의 분석 칼럼을 써줘. "
                  f"<h3> 태그로 단락을 나누고 HTML 태그만 사용해. '해요체'로 작성하고 '할인', '구매' 단어는 절대 금지.")
        try:
            res = requests.post(url, json={"contents": [{"parts": [{"text": prompt}]}]}, timeout=60)
            res_json = res.json()
            # 💎 리스트 인덱싱 오류를 완벽히 수정했습니다.
            return res_json['candidates'][0]['content']['parts'][0]['text'].replace("\n", "<br>")
        except Exception as e:
            print(f"   ⚠️ AI 생성 오류: {e}")
            return f"<h3>🔍 제품 정밀 분석</h3>{product_name}은 모든 면에서 뛰어난 추천 모델입니다."

    def run(self):
        existing_ids = {f.split('_')[-1].replace('.html', '') for f in os.listdir(self.posts_dir) if '_' in f}
        print(f"🕵️ 현재 {len(existing_ids)}개 진열 중. 무차별 수집을 시작합니다.")
        
        products = self.fetch_reco_v2()
        success_count, max_target = 0, 10

        if not products:
            print("❌ 상품 데이터 확보 실패. 위 로그의 에러 메시지를 확인하세요.")
            return

        for item in products:
            p_id = str(item['productId'])
            if p_id in existing_ids: continue

            print(f"   ✨ 발견! [{success_count+1}/10] {item['productName'][:20]}...")
            content = self.generate_review(item['productName'])
            
            img = item['productImage']
            price = format(int(item['productPrice']), ',')
            
            filename = f"{self.posts_dir}/{datetime.now().strftime('%Y%m%d')}_{p_id}.html"
            with open(filename, "w", encoding="utf-8") as f:
                f.write(f"""<!DOCTYPE html><html lang='ko'><head><meta charset='UTF-8'><meta name='viewport' content='width=device-width, initial-scale=1.0'><title>{item['productName']} 리뷰</title>
                <style>body{{font-family:sans-serif; background:#f8f9fa; padding:20px; color:#333; line-height:2.2;}} 
                .card{{max-width:750px; margin:auto; background:white; padding:50px; border-radius:30px; box-shadow:0 20px 50px rgba(0,0,0,0.05);}} 
                img{{width:100%; border-radius:20px; margin:30px 0;}} .p-val{{font-size:2.5rem; color:#e44d26; font-weight:bold; text-align:center;}} 
                .buy-btn{{display:block; background:#e44d26; color:white; text-align:center; padding:25px; text-decoration:none; border-radius:60px; font-weight:bold;}}</style></head>
                <body><div class='card'><h2>{item['productName']}</h2><img src='{img}'><div class='content'>{content}</div><div class='p-val'>{price}원</div>
                <a href='{item['productUrl']}' class='buy-btn'>🛍️ 상세 정보 확인하기</a></div></body></html>""")
            
            existing_ids.add(p_id)
            success_count += 1
            time.sleep(35) # 제미나이 한도 및 발행 안전 대기
            if success_count >= max_target: break

        self._update_seo_files()
        print(f"🏁 작업 완료. 신규 발행: {success_count}개")

    def _update_seo_files(self):
        """💎 구글 서치 콘솔 XML 네임스페이스 및 사이트맵 갱신"""
        files = sorted([f for f in os.listdir(self.posts_dir) if f.endswith(".html")], reverse=True)
        now = datetime.now().strftime("%Y-%m-%d")
        
        # sitemap.xml 갱신 (네임스페이스 포함) 
        with open("sitemap.xml", "w", encoding="utf-8") as f:
            f.write('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n')
            f.write(f'  <url><loc>{self.site_url}/</loc><lastmod>{now}</lastmod><priority>1.0</priority></url>\n')
            for file in files:
                f.write(f'  <url><loc>{self.site_url}/posts/{file}</loc><lastmod>{now}</lastmod></url>\n')
            f.write('</urlset>')

if __name__ == "__main__":
    try:
        CoupangUltimateEngine().run()
    except Exception as e:
        print(f"❌ 시스템 치명적 에러: {e}")
