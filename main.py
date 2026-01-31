import os, hmac, hashlib, time, requests, json, random, re, sys, uuid
from datetime import datetime
from time import gmtime, strftime
from urllib.parse import urlencode

# 🚀 [Security] 사용자 AF7053799 보호 및 웹 자동화 엔진
print("🚀 [System] 웹사이트 진열 및 계정 보호 엔진 가동 중...")

class CoupangMasterBot:
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
        """💎 400 에러 방지를 위해 limit=10으로 고정합니다."""
        path = "/v2/providers/affiliate_open_api/apis/openapi/v1/products/search"
        params = [('keyword', keyword), ('limit', 10), ('page', page)]
        query = urlencode(params)
        headers = {"Authorization": self._generate_auth("GET", path, query), "Content-Type": "application/json"}
        try:
            resp = requests.get(f"https://api-gateway.coupang.com{path}?{query}", headers=headers, timeout=15)
            if resp.status_code == 403:
                print("🚨 [Alert] 시간당 호출 한도 초과! 계정 보호를 위해 즉시 중단합니다."); sys.exit(0)
            return resp.json().get('data', {}).get('productData', [])
        except: return []

    def generate_content(self, p_name):
        if not self.gemini: return "상세 분석 준비 중"
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={self.gemini}"
        try:
            prompt = f"'{p_name}'에 대해 IT 칼럼니스트처럼 1000자 이상 장문 분석 글을 써줘. <h3> 사용, HTML만 사용. '해요체' 사용."
            res = requests.post(url, json={"contents": [{"parts": [{"text": prompt}]}]}, timeout=60)
            return res.json()['candidates'][0]['content']['parts'][0]['text'].replace("\n", "<br>")
        except: return f"<h3>🔍 제품 분석</h3>{p_name}은 품질이 우수한 추천 모델입니다."

    def get_title(self, path):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
                match = re.search(r'<h2>(.*?)</h2>', content)
                return match.group(1)[:40] + "..." if match else "추천 상품"
        except: return "최신 추천 상품"

    def run(self):
        existing_ids = {f.split('_')[-1].replace('.html', '') for f in os.listdir("posts") if '_' in f}
        success_count = 0
        
        # 💎 신규 상품 확보를 위해 키워드를 무작위로 섞습니다.
        seeds = ["게이밍 노트북", "사무용 모니터", "캠핑 텐트", "나이키 운동화", "영양제세트", "아이폰 케이스"]
        target = random.choice(seeds)
        
        print(f"🕵️ 현재 {len(existing_ids)}개 노출 중. '{target}' 수집 시작!")

        for page in range(1, 11):
            if success_count >= 10: break
            items = self.fetch_data(target, page)
            if not items: continue

            for item in items:
                p_id = str(item['productId'])
                if p_id in existing_ids: continue

                print(f"   ✨ 발견! {item['productName'][:20]}...")
                content = self.generate_content(item['productName'])
                img, price = item['productImage'].split('?')[0], format(int(item['productPrice']), ',')
                
                filename = f"posts/{datetime.now().strftime('%Y%m%d')}_{p_id}.html"
                with open(filename, "w", encoding="utf-8") as f:
                    f.write(f"<!DOCTYPE html><html lang='ko'><head><meta charset='UTF-8'><meta name='viewport' content='width=device-width, initial-scale=1.0'><title>{item['productName']} 리뷰</title><style>body{{font-family:sans-serif; background:#f8f9fa; padding:20px; line-height:2.2;}} .card{{max-width:750px; margin:auto; background:white; padding:50px; border-radius:30px; box-shadow:0 20px 50px rgba(0,0,0,0.05);}} img{{width:100%; border-radius:20px; margin:30px 0;}} .p-val{{font-size:2.5rem; color:#e44d26; font-weight:bold; text-align:center;}} .buy-btn{{display:block; background:#e44d26; color:white; text-align:center; padding:25px; text-decoration:none; border-radius:60px; font-weight:bold;}}</style></head><body><div class='card'><h2>{item['productName']}</h2><img src='{img}'><div class='content'>{content}</div><div class='p-val'>{price}원</div><a href='{item['productUrl']}' class='buy-btn'>🛍️ 상세 정보 확인하기</a></div></body></html>")
                
                existing_ids.add(p_id)
                success_count += 1
                time.sleep(35)
                if success_count >= 10: break

        # 💎 [핵심] index.html 및 sitemap.xml을 무조건 새로 씁니다.
        self.update_web()

    def update_web(self):
        files = sorted([f for f in os.listdir("posts") if f.endswith(".html")], reverse=True)
        now = datetime.now().strftime("%Y-%m-%d")
        
        # 1. Sitemap
        with open("sitemap.xml", "w", encoding="utf-8") as f:
            f.write('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n')
            f.write(f'  <url><loc>{self.site_url}/</loc><lastmod>{now}</lastmod><priority>1.0</priority></url>\n')
            for file in files:
                f.write(f'  <url><loc>{self.site_url}/posts/{file}</loc><lastmod>{now}</lastmod></url>\n')
            f.write('</urlset>')

        # 2. Index.html (메인 대문)
        with open("index.html", "w", encoding="utf-8") as f:
            f.write(f"<!DOCTYPE html><html lang='ko'><head><meta charset='UTF-8'><title>쿠팡 전수조사 매거진</title><style>body{{font-family:sans-serif; background:#f0f2f5; padding:20px;}} .grid{{display:grid; grid-template-columns:repeat(auto-fill, minmax(320px, 1fr)); gap:20px;}} .card{{background:white; padding:25px; border-radius:20px; text-decoration:none; color:#333; box-shadow:0 5px 15px rgba(0,0,0,0.05); transition:0.3s;}} .card:hover{{transform:translateY(-10px);}}</style></head><body><h1 style='text-align:center; color:#e44d26;'>🚀 실시간 쿠팡 전수 조사 매거진</h1><div class='grid'>")
            for file in files[:100]:
                title = self.get_title(f"posts/{file}")
                f.write(f"<a class='card' href='posts/{file}'><div>{title}</div><div style='color:#e44d26; font-weight:bold; margin-top:15px;'>전문 읽기 ></div></a>")
            f.write("</div></body></html>")
        print(f"🏁 작업 완료. 총 {len(files)}개 진열 완료!")

if __name__ == "__main__":
    CoupangMasterBot().run()
