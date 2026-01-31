import os, hmac, hashlib, time, requests, json, random, re, sys, uuid
from datetime import datetime
from time import gmtime, strftime
from urllib.parse import urlencode

# 🚀 [System] AF7053799 전용 고품질 & 파일 동기화 엔진 가동
print("🚀 [System] 로봇(robots.txt) 동기화 및 고품질 칼럼 생성 모드 시작...")

class CoupangUltimateBot:
    def __init__(self):
        self.access = os.environ.get('COUPANG_ACCESS_KEY', '').strip()
        self.secret = os.environ.get('COUPANG_SECRET_KEY', '').strip()
        self.gemini = os.environ.get('GEMINI_API_KEY', '').strip()
        self.partners_id = "AF7053799"
        self.site_url = "https://rkskqdl-a11y.github.io/coupang-sale-shuttle"
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
        """💎 상품 정보를 결합해 제미나이가 전문적인 글을 쓰도록 유도합니다."""
        if not self.gemini: return "상세 분석 준비 중"
        p_name = item['productName']
        price = format(int(item['productPrice']), ',')
        rocket = "로켓배송 가능" if item.get('isRocket') else "안전 배송"
        
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={self.gemini}"
        # 💎 부실한 내용을 방지하기 위한 정밀 프롬프트
        prompt = (
            f"상품 '{p_name}'(가격: {price}원, {rocket})에 대해 IT 가전 전문 칼럼니스트가 작성한 1,500자 이상의 정밀 분석 글을 써줘.\n\n"
            f"⚠️ 주의사항: 제목에 있는 텍스트를 본문에 그대로 반복해서 나열하지 마세요.\n"
            f"<h3> 태그를 사용하여 아래 4가지 섹션으로 작성하세요.\n"
            f"1. 디자인과 소재의 특징 (외관 분석)\n"
            f"2. 성능 및 실사용 경험 (주요 기능 포인트)\n"
            f"3. 가성비 및 경쟁사 대비 장단점\n"
            f"4. 이런 분들에게 최고의 선택 (최종 추천 결론)\n\n"
            f"친절한 해요체로 작성하고 '할인', '구매' 단어는 절대 쓰지 마세요. 오직 HTML 태그만 출력하세요."
        )
        try:
            res = requests.post(url, json={"contents": [{"parts": [{"text": prompt}]}]}, timeout=60)
            return res.json()['candidates'][0]['content']['parts'][0]['text'].replace("\n", "<br>")
        except: return f"<h3>🔍 제품 분석</h3>'{p_name}'은 품질이 검증된 최고의 추천 모델입니다."

    def get_real_title(self, path):
        """💎 인덱스 페이지 노출을 위해 실제 상품명을 추출합니다."""
        try:
            with open(path, 'r', encoding='utf-8') as f:
                c = f.read()
                m = re.search(r'<h2>(.*?)</h2>', c)
                return m.group(1)[:35] + "..." if m else "추천 상품"
        except: return "최신 핫딜 상품"

    def run(self):
        existing_ids = {f.split('_')[-1].replace('.html', '') for f in os.listdir("posts") if '_' in f}
        success_count = 0
        seeds = ["게이밍 노트북", "캠핑 텐트", "무선 청소기", "영양제세트", "아이폰 케이스", "사무용 의자"]
        target = random.choice(seeds)
        
        print(f"🕵️ 현재 {len(existing_ids)}개 진열 중. '{target}' 수집 시작!")

        for page in range(1, 4):
            if success_count >= 10: break
            items = self.fetch_data(target, page)
            if not items: continue

            for item in items:
                p_id = str(item['productId'])
                if p_id in existing_ids: continue

                print(f"   ✨ 발견! [{success_count+1}/10] {item['productName'][:20]}...")
                content = self.generate_rich_content(item)
                img = item['productImage'].split('?')[0]
                price = format(int(item['productPrice']), ',')
                
                filename = f"posts/{datetime.now().strftime('%Y%m%d')}_{p_id}.html"
                with open(filename, "w", encoding="utf-8") as f:
                    f.write(f"<!DOCTYPE html><html lang='ko'><head><meta charset='UTF-8'><meta name='viewport' content='width=device-width, initial-scale=1.0'><title>{item['productName']} 리뷰</title><style>body{{font-family:sans-serif; background:#f8f9fa; padding:20px; line-height:2.4; color:#333;}} .card{{max-width:800px; margin:auto; background:white; padding:60px; border-radius:40px; box-shadow:0 30px 60px rgba(0,0,0,0.05);}} h3{{color:#e44d26; margin-top:50px; border-left:8px solid #e44d26; padding-left:25px;}} img{{width:100%; border-radius:25px; margin:40px 0;}} .p-val{{font-size:3rem; color:#e44d26; font-weight:bold; text-align:center; margin:40px 0;}} .buy-btn{{display:block; background:#e44d26; color:white; text-align:center; padding:30px; text-decoration:none; border-radius:70px; font-weight:bold; font-size:1.5rem;}}</style></head><body><div class='card'><h2>{item['productName']}</h2><img src='{img}'><div class='content'>{content}</div><div class='p-val'>{price}원</div><a href='{item['productUrl']}' class='buy-btn'>🛍️ 상세 정보 확인하기</a></div></body></html>")
                
                existing_ids.add(p_id)
                success_count += 1
                time.sleep(35)
                if success_count >= 10: break

        self.update_web()

    def update_web(self):
        """💎 robots.txt, sitemap, index를 완벽하게 동기화합니다."""
        files = sorted([f for f in os.listdir("posts") if f.endswith(".html")], reverse=True)
        now = datetime.now().strftime("%Y-%m-%d")
        
        # 1. robots.txt 강제 갱신 (💎 불일치 문제 해결)
        with open("robots.txt", "w", encoding="utf-8") as f:
            f.write(f"User-agent: *\nAllow: /\nSitemap: {self.site_url}/sitemap.xml")

        # 2. Sitemap 갱신
        with open("sitemap.xml", "w", encoding="utf-8") as f:
            f.write('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n')
            f.write(f'  <url><loc>{self.site_url}/</loc><lastmod>{now}</lastmod><priority>1.0</priority></url>\n')
            for file in files:
                f.write(f'  <url><loc>{self.site_url}/posts/{file}</loc><lastmod>{now}</lastmod></url>\n')
            f.write('</urlset>')

        # 3. Index.html 갱신 (💎 상품명 노출 강화)
        with open("index.html", "w", encoding="utf-8") as f:
            f.write(f"<!DOCTYPE html><html lang='ko'><head><meta charset='UTF-8'><title>쿠팡 고품질 매거진</title><style>body{{font-family:sans-serif; background:#f0f2f5; padding:20px;}} .grid{{display:grid; grid-template-columns:repeat(auto-fill, minmax(350px, 1fr)); gap:25px;}} .card{{background:white; padding:30px; border-radius:25px; text-decoration:none; color:#333; box-shadow:0 10px 20px rgba(0,0,0,0.05); transition:0.3s;}} .card:hover{{transform:translateY(-10px);}}</style></head><body><h1 style='text-align:center; color:#e44d26;'>🚀 실시간 쿠팡 고품질 매거진</h1><div class='grid'>")
            for file in files[:100]:
                title = self.get_real_title(f"posts/{file}")
                f.write(f"<a class='card' href='posts/{file}'><div>{title}</div><div style='color:#e44d26; font-weight:bold; margin-top:15px;'>전문 칼럼 읽기 ></div></a>")
            f.write("</div></body></html>")
        print(f"🏁 모든 파일(robots, sitemap, index) 동기화 완료!")

if __name__ == "__main__":
    CoupangUltimateBot().run()
