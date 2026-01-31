import os, hmac, hashlib, time, requests, json, random, re, sys
from datetime import datetime
from time import gmtime, strftime
from urllib.parse import urlencode

# 🚀 [System] AF7053799 전용 고품질 하베스팅 & 로봇 동기화 가동
print("🚀 [System] 로봇(robots.txt) 동기화 및 고품질 칼럼 생성 모드 가동 중...")

class CoupangMasterBot:
    def __init__(self):
        self.access = os.environ.get('COUPANG_ACCESS_KEY', '').strip()
        self.secret = os.environ.get('COUPANG_SECRET_KEY', '').strip()
        self.gemini = os.environ.get('GEMINI_API_KEY', '').strip()
        self.partners_id = "AF7053799" #
        self.site_url = "https://rkskqdl-a11y.github.io/coupang-sale-shuttle" #
        os.makedirs("posts", exist_ok=True)

    def _generate_auth(self, method, path, query=""):
        datetime_gmt = strftime('%y%m%d', gmtime()) + 'T' + strftime('%H%M%S', gmtime()) + 'Z'
        message = datetime_gmt + method + path + query
        signature = hmac.new(bytes(self.secret, "utf-8"), message.encode("utf-8"), hashlib.sha256).hexdigest()
        return f"CEA algorithm=HmacSHA256, access-key={self.access}, signed-date={datetime_gmt}, signature={signature}"

    def fetch_data(self, keyword, page):
        path = "/v2/providers/affiliate_open_api/apis/openapi/v1/products/search"
        params = [('keyword', keyword), ('limit', 10), ('page', page)]
        query = urlencode(params)
        headers = {"Authorization": self._generate_auth("GET", path, query), "Content-Type": "application/json"}
        try:
            resp = requests.get(f"https://api-gateway.coupang.com{path}?{query}", headers=headers, timeout=15)
            return resp.json().get('data', {}).get('productData', [])
        except: return []

    def generate_rich_content(self, item):
        """💎 상품 정보를 결합하여 제미나이가 풍성한 글을 쓰도록 유도합니다."""
        if not self.gemini: return "상세 분석 준비 중입니다."
        
        p_name = item['productName']
        price = format(int(item['productPrice']), ',')
        rocket = "로켓배송 가능" if item.get('isRocket') else "일반배송"
        
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={self.gemini}"
        
        # 💎 고품질 프롬프트 설계
        prompt = (
            f"상품 '{p_name}'(가격: {price}원, {rocket})에 대해 전문 쇼핑 칼럼니스트가 작성한 1,500자 이상의 분석 글을 써줘. "
            f"1. 제목의 키워드를 본문에 그대로 반복해서 나열하지 말 것.\n"
            f"2. '디자인의 특징', '성능 및 스펙 분석', '사용자 평점 및 실사용 후기 요약', '이런 분들께 강력 추천'의 4개 섹션으로 구성할 것.\n"
            f"3. 반드시 <h3> 태그를 사용해 문단을 나누고 HTML 태그만 사용할 것.\n"
            f"4. 친절한 해요체로 작성하되, '할인'이나 '최저가'라는 단어는 쓰지 마."
        )
        
        try:
            res = requests.post(url, json={"contents": [{"parts": [{"text": prompt}]}]}, timeout=60)
            return res.json()['candidates'][0]['content']['parts'][0]['text'].replace("\n", "<br>")
        except:
            return f"<h3>🔍 제품 정밀 분석</h3>'{p_name}'은 {price}원대에 만나볼 수 있는 고품질 추천 모델입니다."

    def run(self):
        existing_ids = {f.split('_')[-1].replace('.html', '') for f in os.listdir("posts") if '_' in f}
        success_count = 0
        seeds = ["게이밍 노트북", "캠핑 텐트", "무선 청소기", "영양제세트", "아이폰 케이스", "사무용 의자"]
        target = random.choice(seeds)
        
        print(f"🕵️ 현재 {len(existing_ids)}개 노출 중. '{target}' 고품질 수집 시작!")

        for page in range(1, 4): # 고품질 생성을 위해 수집 범위를 압축
            if success_count >= 10: break
            items = self.fetch_data(target, page)
            if not items: continue

            for item in items:
                p_id = str(item['productId'])
                if p_id in existing_ids: continue

                print(f"   ✨ 발견! [{success_count+1}/10] {item['productName'][:20]}...")
                content = self.generate_rich_content(item)
                img, price = item['productImage'].split('?')[0], format(int(item['productPrice']), ',')
                
                filename = f"posts/{datetime.now().strftime('%Y%m%d')}_{p_id}.html"
                with open(filename, "w", encoding="utf-8") as f:
                    f.write(f"<!DOCTYPE html><html lang='ko'><head><meta charset='UTF-8'><meta name='viewport' content='width=device-width, initial-scale=1.0'><title>{item['productName']} 리뷰</title><style>body{{font-family:sans-serif; background:#f8f9fa; padding:20px; line-height:2.4; color:#333;}} .card{{max-width:800px; margin:auto; background:white; padding:60px; border-radius:40px; box-shadow:0 30px 60px rgba(0,0,0,0.05);}} h3{{color:#e44d26; margin-top:50px; border-left:8px solid #e44d26; padding-left:25px;}} img{{width:100%; border-radius:25px; margin:40px 0;}} .p-val{{font-size:3rem; color:#e44d26; font-weight:bold; text-align:center; margin:40px 0;}} .buy-btn{{display:block; background:#e44d26; color:white; text-align:center; padding:30px; text-decoration:none; border-radius:70px; font-weight:bold; font-size:1.5rem;}}</style></head><body><div class='card'><h2>{item['productName']}</h2><img src='{img}'><div class='content'>{content}</div><div class='p-val'>{price}원</div><a href='{item['productUrl']}' class='buy-btn'>🛍️ 상세 정보 확인하기</a></div></body></html>")
                
                existing_ids.add(p_id)
                success_count += 1
                time.sleep(35) # 제미나이 한도 준수
                if success_count >= 10: break

        self.update_web()

    def update_web(self):
        """💎 robots, index, sitemap을 완벽히 동기화합니다."""
        files = sorted([f for f in os.listdir("posts") if f.endswith(".html")], reverse=True)
        now = datetime.now().strftime("%Y-%m-%d")
        
        # 1. robots.txt (💎 어제 날짜 갱신 문제를 해결합니다)
        with open("robots.txt", "w", encoding="utf-8") as f:
            f.write(f"User-agent: *\nAllow: /\nSitemap: {self.site_url}/sitemap.xml")

        # 2. Sitemap (💎 구글 색인용)
        with open("sitemap.xml", "w", encoding="utf-8") as f:
            f.write('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n')
            f.write(f'  <url><loc>{self.site_url}/</loc><lastmod>{now}</lastmod><priority>1.0</priority></url>\n')
            for file in files:
                f.write(f'  <url><loc>{self.site_url}/posts/{file}</loc><lastmod>{now}</lastmod></url>\n')
            f.write('</urlset>')

        # 3. Index.html (💎 메인 대문)
        with open("index.html", "w", encoding="utf-8") as f:
            f.write(f"<!DOCTYPE html><html lang='ko'><head><meta charset='UTF-8'><title>쿠팡 고품질 매거진</title><style>body{{font-family:sans-serif; background:#f0f2f5; padding:20px;}} .grid{{display:grid; grid-template-columns:repeat(auto-fill, minmax(350px, 1fr)); gap:25px;}} .card{{background:white; padding:30px; border-radius:25px; text-decoration:none; color:#333; box-shadow:0 10px 20px rgba(0,0,0,0.05); transition:0.3s;}} .card:hover{{transform:translateY(-10px);}}</style></head><body><h1 style='text-align:center; color:#e44d26;'>🚀 실시간 쿠팡 고품질 매거진</h1><div class='grid'>")
            for file in files[:100]:
                p_id = file.split('_')[-1].replace('.html', '')
                f.write(f"<a class='card' href='posts/{file}'><div>📦 추천 상품 (ID: {p_id})</div><div style='color:#e44d26; font-weight:bold; margin-top:15px;'>전문 분석 칼럼 읽기 ></div></a>")
            f.write("</div></body></html>")
        print(f"🏁 작업 완료. 로봇 파일 및 {len(files)}개 포스팅 최신화 완료!")

if __name__ == "__main__":
    CoupangMasterBot().run()
