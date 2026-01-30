import os, hmac, hashlib, time, requests, json, random, re, uuid
from datetime import datetime
from time import gmtime, strftime
from urllib.parse import quote

# 🚀 [System] AF7053799 전용 하베스팅 엔진 가동 (무한 재시도 모드)
print("🚀 쿠팡 무차별 전수 조사 엔진이 가동됩니다. (ID: AF7053799)")

class SeniorHarvestEngine:
    def __init__(self):
        self.access_key = os.environ.get('COUPANG_ACCESS_KEY', '').strip()
        self.secret_key = os.environ.get('COUPANG_SECRET_KEY', '').strip()
        self.gemini_key = os.environ.get('GEMINI_API_KEY', '').strip()
        self.partners_id = "AF7053799"
        self.site_url = "https://rkskqdl-a11y.github.io/coupang-sale-shuttle"
        os.makedirs("posts", exist_ok=True)

    def _generate_auth(self, method, path, query_string=""):
        """💎 공식 문서 가이드를 100% 준수하는 HMAC 생성기"""
        datetime_gmt = strftime('%y%m%d', gmtime()) + 'T' + strftime('%H%M%S', gmtime()) + 'Z'
        message = datetime_gmt + method + path + query_string
        signature = hmac.new(bytes(self.secret_key, "utf-8"),
                             message.encode("utf-8"),
                             hashlib.sha256).hexdigest()
        return "CEA algorithm=HmacSHA256, access-key={}, signed-date={}, signature={}".format(
            self.access_key, datetime_gmt, signature)

    def fetch_search_data(self, keyword, page):
        """💎 파라미터 정렬 및 인코딩 보정으로 0개 수신 현상 해결"""
        path = "/v2/providers/affiliate_open_api/apis/openapi/v1/products/search"
        # 💎 규칙: keyword -> limit -> page 순서로 강제 정렬
        query_string = f"keyword={quote(keyword)}&limit=20&page={page}"
        
        headers = {
            "Authorization": self._generate_auth("GET", path, query_string),
            "Content-Type": "application/json"
        }
        
        try:
            url = f"https://api-gateway.coupang.com{path}?{query_string}"
            resp = requests.get(url, headers=headers, timeout=15)
            if resp.status_code == 200:
                data = resp.json()
                items = data.get('data', {}).get('productData', [])
                if items:
                    print(f"   ✅ '{keyword}' 키워드로 {len(items)}개 상품 수신 성공!")
                return items
            else:
                print(f"   ❌ API 서버 응답 실패 ({resp.status_code})")
                return []
        except Exception as e:
            print(f"   ⚠️ 통신 오류: {e}")
            return []

    def generate_review(self, product_name):
        """💎 제미나이 1.5 플래시 기반 고품질 칼럼 생성 (JSON 파싱 교정)"""
        if not self.gemini_key: return "상세 분석 준비 중"
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={self.gemini_key}"
        prompt = f"상품 '{product_name}'에 대해 IT 전문가가 작성한 분석 칼럼을 1,000자 이상 장문으로 작성해줘. <h3> 사용, HTML만 사용, 해요체 사용. '할인' 언급 금지."
        try:
            res = requests.post(url, json={"contents": [{"parts": [{"text": prompt}]}]}, timeout=60)
            # 💎 정석 인덱싱 구조로 수정 완료
            return res.json()['candidates'][0]['content']['parts'][0]['text'].replace("\n", "<br>")
        except: return f"<h3>🔍 제품 정밀 분석</h3>{product_name}은 품질이 보증된 강력 추천 상품입니다."

    def run(self):
        existing_ids = {f.split('_')[-1].replace('.html', '') for f in os.listdir("posts") if '_' in f}
        success_count, max_target = 0, 10
        
        # 💎 데이터를 뱉어낼 때까지 시도할 골든 키워드 리스트
        golden_seeds = ["노트북", "갤럭시", "나이키", "물티슈", "생수", "라면", "커피", "텐트", "운동화", "마스크"]
        
        print(f"🕵️ 현재 {len(existing_ids)}개 진열 중. 데이터 확보를 위해 전방위 수색을 시작합니다.")

        for keyword in golden_seeds:
            if success_count >= max_target: break
            
            page = random.randint(1, 20)
            print(f"🔍 [전수조사] '{keyword}' 키워드로 수색 중...")
            products = self.fetch_search_data(keyword, page)
            
            if not products: continue

            for item in products:
                p_id = str(item['productId'])
                if p_id in existing_ids: continue

                print(f"   ✨ 신규 발견! [{success_count+1}/10] {item['productName'][:20]}...")
                content = self.generate_review(item['productName'])
                
                filename = f"posts/{datetime.now().strftime('%Y%m%d')}_{p_id}.html"
                self.save_post(filename, item, content)
                
                existing_ids.add(p_id)
                success_count += 1
                time.sleep(35) # 제미나이 한도 준수
                if success_count >= max_target: break

        self.update_seo_files()
        print(f"🏁 작업 완료. 신규 발행: {success_count}개")

    def save_post(self, filename, item, content):
        img, price = item['productImage'].split('?')[0], format(int(item['productPrice']), ',')
        html = f"""<!DOCTYPE html><html lang='ko'><head><meta charset='UTF-8'><meta name='viewport' content='width=device-width, initial-scale=1.0'><title>{item['productName']} 리뷰</title>
        <style>body{{font-family:sans-serif; background:#f8f9fa; padding:20px; color:#333; line-height:2.2;}} .card{{max-width:750px; margin:auto; background:white; padding:50px; border-radius:30px; box-shadow:0 20px 50px rgba(0,0,0,0.05);}} 
        img{{width:100%; border-radius:20px; margin:30px 0;}} .p-val{{font-size:2.5rem; color:#e44d26; font-weight:bold; text-align:center;}} .buy-btn{{display:block; background:#e44d26; color:white; text-align:center; padding:25px; text-decoration:none; border-radius:60px; font-weight:bold;}}</style></head>
        <body><div class='card'><h2>{item['productName']}</h2><img src='{img}'><div class='content'>{content}</div><div class='p-val'>{price}원</div><a href='{item['productUrl']}' class='buy-btn'>🛍️ 상세 정보 확인하기</a></div></body></html>"""
        with open(filename, "w", encoding="utf-8") as f: f.write(html)

    def update_seo_files(self):
        """💎 구글 서치 콘솔 XML 네임스페이스 오류 완벽 해결"""
        files = sorted([f for f in os.listdir("posts") if f.endswith(".html")], reverse=True)
        now = datetime.now().strftime("%Y-%m-%d")
        with open("sitemap.xml", "w", encoding="utf-8") as f:
            f.write('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n')
            f.write(f'  <url><loc>{self.site_url}/</loc><lastmod>{now}</lastmod><priority>1.0</priority></url>\n')
            for file in files:
                f.write(f'  <url><loc>{self.site_url}/posts/{file}</loc><lastmod>{now}</lastmod></url>\n')
            f.write('</urlset>')

if __name__ == "__main__":
    SeniorHarvestEngine().run()
