import os, hmac, hashlib, time, requests, json, random, re, uuid
from datetime import datetime
from time import gmtime, strftime
from urllib.parse import urlencode
import google.generativeai as genai

# 🚀 [System] AF7053799 전용 구글 검색 기반 고품질 엔진 가동
print(f"🚀 [System] 가동 시각: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

class CoupangExpertBot:
    def __init__(self):
        self.access = os.environ.get('COUPANG_ACCESS_KEY', '').strip()
        self.secret = os.environ.get('COUPANG_SECRET_KEY', '').strip()
        self.gemini_key = os.environ.get('GEMINI_API_KEY', '').strip()
        self.partners_id = "AF7053799"
        self.site_url = "https://rkskqdl-a11y.github.io/coupang-sale-shuttle"
        self.posts_dir = "posts"
        os.makedirs(self.posts_dir, exist_ok=True)
        
        # 💎 제미나이 구글 검색(Grounding) 설정
        if self.gemini_key:
            genai.configure(api_key=self.gemini_key)
            # 'google_search' 도구를 사용하여 실시간 정보를 수집하게 합니다.
            self.model = genai.GenerativeModel(
                model_name='gemini-1.5-flash',
                tools=[{'google_search': {}}] 
            )

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

    def generate_research_content(self, p_name):
        """💎 구글 검색을 활용해 상품 정보를 수집하고 풍성한 글을 작성합니다."""
        if not self.gemini_key: return "상세 분석 준비 중"
        
        prompt = (
            f"상품명 '{p_name}'에 대해 구글 검색을 통해 정보를 수집하고 전문 리뷰를 작성해줘.\n\n"
            f"1. 제품의 핵심 스펙(사양)을 데이터 기반으로 상세히 적어줘.\n"
            f"2. 실제 사용자들의 긍정적인 평가와 아쉬운 점을 분석해줘.\n"
            f"3. 경쟁 모델과 비교했을 때 이 제품만의 강점을 설명해줘.\n"
            f"4. <h3> 태그를 사용해 문단을 나누고 1,500자 이상의 장문으로 작성해.\n"
            f"5. 제목을 그대로 반복하지 말고, 전문 칼럼니스트처럼 친절한 해요체로 HTML 태그만 출력해."
        )
        
        try:
            # 💎 제미나이가 실제로 '검색'을 수행하여 글을 씁니다.
            response = self.model.generate_content(prompt)
            return response.text.replace("\n", "<br>")
        except Exception as e:
            print(f"   ⚠️ AI 생성 오류: {e}")
            return f"<h3>🔍 제품 정밀 분석</h3>'{p_name}'은 신뢰할 수 있는 브랜드의 검증된 모델입니다."

    def get_real_title(self, path):
        try:
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
                match = re.search(r'<h2>(.*?)</h2>', content)
                if match:
                    title = match.group(1).replace(" 리뷰", "")
                    return title[:40] + "..." if len(title) > 40 else title
        except: pass
        return "최신 추천 상품"

    def run(self):
        existing_ids = {f.split('_')[-1].replace('.html', '') for f in os.listdir(self.posts_dir) if '_' in f}
        success_count, max_target = 0, 10
        
        # 💎 중복 방지를 위한 키워드 및 페이지 랜덤화
        seeds = ["게이밍 모니터", "캠핑 웨건", "무선 이어폰", "단백질 쉐이크", "아이폰 16 케이스", "로봇 청소기"]
        target = random.choice(seeds)
        start_page = random.randint(1, 15) # 1~15페이지 사이에서 무작위 수색 시작
        
        print(f"🕵️ 현재 {len(existing_ids)}개 노출 중. '{target}' {start_page}p부터 수집 시작!")

        for page in range(start_page, start_page + 5):
            if success_count >= max_target: break
            items = self.fetch_data(target, page)
            if not items: continue

            for item in items:
                p_id = str(item['productId'])
                if p_id in existing_ids: continue # 💎 중복 상품은 과감히 패스

                print(f"   ✨ 신규 발견! [{success_count+1}/{max_target}] {item['productName'][:20]}...")
                content = self.generate_research_content(item['productName'])
                img, price = item['productImage'].split('?')[0], format(int(item['productPrice']), ',')
                
                disclosure = "<p style='color:#888; font-size:0.8rem; text-align:center; margin-top:50px;'>이 포스팅은 쿠팡 파트너스 활동의 일환으로, 이에 따른 일정액의 수수료를 제공받습니다.</p>"
                
                filename = f"{self.posts_dir}/{datetime.now().strftime('%Y%m%d')}_{p_id}.html"
                with open(filename, "w", encoding="utf-8") as f:
                    f.write(f"<!DOCTYPE html><html lang='ko'><head><meta charset='UTF-8'><meta name='viewport' content='width=device-width, initial-scale=1.0'><title>{item['productName']} 리뷰</title><style>body{{font-family:sans-serif; background:#f8f9fa; padding:20px; line-height:2.4; color:#333;}} .card{{max-width:850px; margin:auto; background:white; padding:60px; border-radius:40px; box-shadow:0 30px 60px rgba(0,0,0,0.05);}} h3{{color:#e44d26; margin-top:50px; border-left:8px solid #e44d26; padding-left:25px;}} img{{width:100%; border-radius:25px; margin:40px 0;}} .p-val{{font-size:3rem; color:#e44d26; font-weight:bold; text-align:center; margin:40px 0;}} .buy-btn{{display:block; background:#e44d26; color:white; text-align:center; padding:30px; text-decoration:none; border-radius:70px; font-weight:bold; font-size:1.5rem;}}</style></head><body><div class='card'><h2>{item['productName']}</h2><img src='{img}'><div class='content'>{content}</div><div class='p-val'>{price}원</div><a href='{item['productUrl']}' class='buy-btn'>🛍️ 상세 정보 확인하기</a>{disclosure}</div></body></html>")
                
                existing_ids.add(p_id)
                success_count += 1
                time.sleep(35)
                if success_count >= max_target: break

        self.update_web()

    def update_web(self):
        """💎 robots.txt, sitemap, index를 완벽하게 동기화합니다."""
        files = sorted([f for f in os.listdir(self.posts_dir) if f.endswith(".html")], reverse=True)
        now = datetime.now().strftime("%Y-%m-%d")
        
        # 1. robots.txt 강제 갱신
        with open("robots.txt", "w", encoding="utf-8") as f:
            f.write(f"# Updated: {datetime.now().isoformat()}\n")
            f.write(f"User-agent: *\nAllow: /\nSitemap: {self.site_url}/sitemap.xml")

        # 2. Sitemap 갱신
        with open("sitemap.xml", "w", encoding="utf-8") as f:
            f.write('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n')
            f.write(f'  <url><loc>{self.site_url}/</loc><lastmod>{now}</lastmod><priority>1.0</priority></url>\n')
            for file in files:
                f.write(f'  <url><loc>{self.site_url}/posts/{file}</loc><lastmod>{now}</lastmod></url>\n')
            f.write('</urlset>')

        # 3. Index.html 갱신
        with open("index.html", "w", encoding="utf-8") as f:
            f.write(f"<!DOCTYPE html><html lang='ko'><head><meta charset='UTF-8'><title>쿠팡 고품질 매거진</title><style>body{{font-family:sans-serif; background:#f0f2f5; padding:20px;}} .grid{{display:grid; grid-template-columns:repeat(auto-fill, minmax(350px, 1fr)); gap:25px;}} .card{{background:white; padding:30px; border-radius:25px; text-decoration:none; color:#333; box-shadow:0 10px 20px rgba(0,0,0,0.05); transition:0.3s;}} .card:hover{{transform:translateY(-10px);}}</style></head><body><h1 style='text-align:center; color:#e44d26;'>🚀 실시간 쿠팡 고품질 매거진</h1><div class='grid'>")
            for file in files[:100]:
                title = self.get_real_title(f"{self.posts_dir}/{file}")
                f.write(f"<a class='card' href='posts/{file}'><div>{title}</div><div style='color:#e44d26; font-weight:bold; margin-top:15px;'>전문 칼럼 읽기 ></div></a>")
            f.write("</div></body></html>")
        print(f"🏁 모든 파일 동기화 완료! 현재 총 {len(files)}개 포스팅.")

if __name__ == "__main__":
    CoupangExpertBot().run()
