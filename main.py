import os, hmac, hashlib, time, requests, json, random, re
from datetime import datetime
from urllib.parse import urlencode, quote

# 💎 [System] 엔진 가동
print("🚀 쿠팡 저인망 하베스팅 엔진을 가동합니다. (인증 및 인코딩 보정 완료)")

class CoupangEngine:
    def __init__(self):
        self.access_key = os.environ.get('COUPANG_ACCESS_KEY', '').strip()
        self.secret_key = os.environ.get('COUPANG_SECRET_KEY', '').strip()
        self.gemini_key = os.environ.get('GEMINI_API_KEY', '').strip()
        self.site_url = "https://rkskqdl-a11y.github.io/coupang-sale-shuttle"
        
    def get_signature(self, method, path, query_string):
        """💎 공식 문서 기반 HMAC 서명 생성 (공백 인코딩 보정)"""
        timestamp = time.strftime('%y%m%dT%H%M%SZ', time.gmtime())
        # 쿠팡 API 서명 공식: $timestamp + $method + $path + $query_string$
        message = timestamp + method + path + query_string
        signature = hmac.new(bytes(self.secret_key, 'utf-8'), 
                             msg=bytes(message, 'utf-8'), 
                             digestmod=hashlib.sha256).hexdigest()
        return timestamp, signature

    def fetch_data(self, keyword, page=1):
        """💎 검색어 인코딩 방식을 고정하여 수집 성공률을 극대화합니다."""
        domain = "https://api-gateway.coupang.com"
        path = "/v2/providers/affiliate_open_api/apis/openapi/v1/products/search"
        
        # ⚠️ 파라미터 순서 고정 (keyword -> limit -> page)
        # quote를 사용하여 공백 문제를 해결합니다.
        query_string = f"keyword={quote(keyword)}&limit=20&page={page}"
        
        timestamp, signature = self.get_signature("GET", path, query_string)
        
        headers = {
            "Authorization": f"CEA algorithm=HmacSHA256, access-key={self.access_key}, signed-date={timestamp}, signature={signature}",
            "Content-Type": "application/json"
        }
        
        try:
            resp = requests.get(f"{domain}{path}?{query_string}", headers=headers, timeout=15)
            if resp.status_code == 200:
                return resp.json().get('data', {}).get('productData', [])
            return []
        except: return []

    def generate_content(self, product_name):
        """💎 제미나이 AI 칼럼 생성 (1,000자 이상)"""
        if not self.gemini_key: return "상세 분석 준비 중"
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={self.gemini_key}"
        try:
            prompt = f"상품 '{product_name}'에 대해 IT 쇼핑 칼럼니스트가 작성한 분석 글을 1000자 내외로 작성해줘. <h3> 사용, HTML만 사용, 해요체 사용. '할인' 언급 금지."
            res = requests.post(url, json={"contents": [{"parts": [{"text": prompt}]}]}, timeout=60)
            return res.json()['candidates'][0]['content']['parts'][0]['text'].replace("\n", "<br>")
        except: return f"<h3>🔍 제품 분석</h3>{product_name}은 품질이 검증된 추천 모델입니다."

    def run(self):
        os.makedirs("posts", exist_ok=True)
        existing_ids = {f.split('_')[-1].replace('.html', '') for f in os.listdir("posts") if '_' in f}
        
        success_count = 0
        # 💎 실패 확률이 거의 없는 범용 키워드 리스트
        seeds = ["노트북", "운동화", "생수", "라면", "갤럭시", "아이폰", "물티슈", "기저귀"]
        keyword = random.choice(seeds)
        
        print(f"🕵️ 현재 {len(existing_ids)}개 데이터 노출 중. '{keyword}' 전수 조사 시작!")

        for page in range(1, 11):
            if success_count >= 10: break
            print(f"🔍 {page}페이지 수색 중...")
            products = self.fetch_data(keyword, page)
            
            if not products:
                print(f"⚠️ {page}페이지 결과 없음. 다음 키워드로 전환합니다.")
                keyword = random.choice(seeds)
                continue

            for item in products:
                p_id = str(item['productId'])
                if p_id in existing_ids: continue

                print(f"   ✨ 발견! {item['productName'][:20]}...")
                content = self.generate_content(item['productName'])
                
                # 파일 저장
                filename = f"posts/{datetime.now().strftime('%Y%m%d')}_{p_id}.html"
                self.save_post(filename, item, content)
                
                existing_ids.add(p_id)
                success_count += 1
                time.sleep(35) # 제미나이 한도 준수
                if success_count >= 10: break

        self.update_sitemap()
        print(f"🏁 작업 완료. 신규 발행: {success_count}개")

    def save_post(self, filename, item, content):
        img = item['productImage'].split('?')[0]
        price = format(item['productPrice'], ',')
        html = f"""<!DOCTYPE html><html lang='ko'><head><meta charset='UTF-8'><title>{item['productName']} 리뷰</title>
        <style>body{{font-family:sans-serif; background:#f8f9fa; padding:20px; color:#333; line-height:2.2;}}
        .card{{max-width:700px; margin:auto; background:white; padding:40px; border-radius:25px; box-shadow:0 10px 30px rgba(0,0,0,0.05);}}
        img{{width:100%; border-radius:15px;}} .p-val{{font-size:2rem; color:#e44d26; font-weight:bold; text-align:center;}}
        .buy-btn{{display:block; background:#e44d26; color:white; text-align:center; padding:20px; text-decoration:none; border-radius:50px; font-weight:bold;}}</style></head>
        <body><div class='card'><h2>{item['productName']}</h2><img src='{img}'><div class='content'>{content}</div><div class='p-val'>{price}원</div>
        <a href='{item['productUrl']}' class='buy-btn'>🛍️ 상세 정보 확인하기</a></div></body></html>"""
        with open(filename, "w", encoding="utf-8") as f: f.write(html)

    def update_sitemap(self):
        """💎 구글 서치 콘솔 오류(Missing XML namespace) 완벽 해결"""
        files = sorted([f for f in os.listdir("posts") if f.endswith(".html")], reverse=True)
        now = datetime.now().strftime("%Y-%m-%d")
        with open("sitemap.xml", "w", encoding="utf-8") as f:
            f.write('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n')
            f.write(f'  <url><loc>{self.site_url}/</loc><lastmod>{now}</lastmod><priority>1.0</priority></url>\n')
            for file in files:
                f.write(f'  <url><loc>{self.site_url}/posts/{file}</loc><lastmod>{now}</lastmod></url>\n')
            f.write('</urlset>')

if __name__ == "__main__":
    CoupangEngine().run()
