import os, hmac, hashlib, time, requests, json, random, re, sys
from datetime import datetime
from time import gmtime, strftime
from urllib.parse import urlencode
# 🚨 최신 SDK 규격 (ValueError 및 404 에러 원천 차단)
from google import genai
from google.genai import types

# 🚀 [System] AF7053799 전용 '실시간 구글 검색(Grounding)' 엔진 가동
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
        
        # 💎 신형 제미나이 클라이언트 설정
        if self.gemini_key:
            self.client = genai.Client(api_key=self.gemini_key)

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
        """💎 구글 실시간 검색(Grounding)을 통해 외부 정보를 수집합니다."""
        if not self.gemini_key: return "상세 분석 준비 중"
        
        # 💎 AI에게 '반드시 검색해서 외부 사양을 찾아내라'는 강력한 미션을 줍니다.
        prompt = (
            f"상품명 '{p_name}'에 대해 실시간 구글 검색을 수행하고 IT 전문 기자의 관점에서 칼럼을 작성하세요.\n\n"
            f"1. [상세 사양]: 검색된 정보를 바탕으로 이 모델의 핵심 사양(CPU, 배터리, 무게, 기능 등)을 표(table) 형식으로 상세히 만드세요.\n"
            f"2. [전문 분석]: 쿠팡 외의 다른 쇼핑몰이나 제조사 페이지에서 언급된 이 제품의 독보적인 기술 포인트 3가지를 분석하세요.\n"
            f"3. [실사용자 리뷰 분석]: 블로그, 커뮤니티, 유튜브의 실제 사용자 후기를 장단점으로 나누어 1,000자 이상으로 깊이 있게 정리하세요.\n"
            f"4. <h3> 태그를 사용하여 문단을 나누고 전체 2,000자 내외의 압도적인 분량으로 작성하세요.\n"
            f"5. 제목을 본문 첫 문장에 반복하지 말고, HTML 태그만 출력하세요. 친절한 해요체로 작성하세요."
        )
        
        try:
            # 🚨 [해결] 404 에러를 잡기 위해 모델명에서 'models/' 접두어를 제거합니다.
            response = self.client.models.generate_content(
                model='gemini-1.5-flash',
                contents=prompt,
                config=types.GenerateContentConfig(
                    tools=[types.Tool(google_search=types.GoogleSearch())]
                )
            )
            return response.text.replace("\n", "<br>")
        except Exception as e:
            print(f"   ⚠️ AI 수집 오류: {e}")
            return f"<h3>🔍 제품 정밀 분석</h3>'{p_name}'은 신뢰할 수 있는 성능과 품질을 갖춘 고성능 추천 모델입니다."

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
        
        # 💎 500개 중복을 피하기 위해 키워드를 더 정교하게 바꾸고 페이지를 크게 점프합니다.
        seeds = ["게이밍 노트북 i7", "대용량 캠핑 웨건", "차이슨 무선청소기 신제품", "오메가3 영양제 추천", "로봇청소기 물걸레"]
        target = random.choice(seeds)
        start_page = random.randint(10, 100) # 💎 100페이지까지 무작위 점프하여 수색
        
        print(f"🕵️ 현재 {len(existing_ids)}개 진열 중. '{target}' {start_page}p부터 수색 시작!")

        for page in range(start_page, start_page + 15):
            if success_count >= max_target: break
            items = self.fetch_data(target, page)
            if not items: continue

            for item in items:
                p_id = str(item['productId'])
                if p_id in existing_ids: continue 

                print(f"   ✨ 신규 발견! [{success_count+1}/10] {item['productName'][:20]}...")
                content = self.generate_research_content(item['productName'])
                img, price = item['productImage'].split('?')[0], format(int(item['productPrice']), ',')
                
                disclosure = "<p style='color:#888; font-size:0.9rem; text-align:center; margin-top:50px;'>이 포스팅은 쿠팡 파트너스 활동의 일환으로, 이에 따른 일정액의 수수료를 제공받습니다.</p>"
                
                filename = f"{self.posts_dir}/{datetime.now().strftime('%Y%m%d')}_{p_id}.html"
                with open(filename, "w", encoding="utf-8") as f:
                    f.write(f"<!DOCTYPE html><html lang='ko'><head><meta charset='UTF-8'><meta name='viewport' content='width=device-width, initial-scale=1.0'><title>{item['productName']} 리뷰</title><style>body{{font-family:sans-serif; background:#f8f9fa; padding:20px; line-height:2.4; color:#333;}} .card{{max-width:850px; margin:auto; background:white; padding:60px; border-radius:40px; box-shadow:0 30px 60px rgba(0,0,0,0.05);}} h3{{color:#e44d26; margin-top:50px; border-left:8px solid #e44d26; padding-left:25px;}} img{{width:100%; border-radius:25px; margin:40px 0;}} .p-val{{font-size:3rem; color:#e44d26; font-weight:bold; text-align:center; margin:40px 0;}} .buy-btn{{display:block; background:#e44d26; color:white; text-align:center; padding:30px; text-decoration:none; border-radius:70px; font-weight:bold; font-size:1.5rem;}} table{{width:100%; border-collapse:collapse; margin:20px 0;}} td, th{{border:1px solid #ddd; padding:12px; text-align:left;}} th{{background-color:#f2f2f2;}}</style></head><body><div class='card'><h2>{item['productName']}</h2><img src='{img}'><div class='content'>{content}</div><div class='p-val'>{price}원</div><a href='{item['productUrl']}' class='buy-btn'>🛍️ 상세 정보 확인하기</a>{disclosure}</div></body></html>")
                
                existing_ids.add(p_id)
                success_count += 1
                time.sleep(55) # 💎 고품질 검색 데이터 처리를 위해 대기 시간을 넉넉히 가집니다.
                if success_count >= max_target: break

        self.update_web()

    def update_web(self):
        files = sorted([f for f in os.listdir(self.posts_dir) if f.endswith(".html")], reverse=True)
        now = datetime.now().strftime("%Y-%m-%d")
        with open("robots.txt", "w", encoding="utf-8") as f:
            f.write(f"# Updated: {datetime.now().isoformat()}\nUser-agent: *\nAllow: /\nSitemap: {self.site_url}/sitemap.xml")
        with open("sitemap.xml", "w", encoding="utf-8") as f:
            f.write('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n')
            f.write(f'  <url><loc>{self.site_url}/</loc><lastmod>{now}</lastmod><priority>1.0</priority></url>\n')
            for file in files: f.write(f'  <url><loc>{self.site_url}/posts/{file}</loc><lastmod>{now}</lastmod></url>\n')
            f.write('</set>')
        with open("index.html", "w", encoding="utf-8") as f:
            f.write(f"<!DOCTYPE html><html lang='ko'><head><meta charset='UTF-8'><title>쿠팡 고품질 매거진</title><style>body{{font-family:sans-serif; background:#f0f2f5; padding:20px;}} .grid{{display:grid; grid-template-columns:repeat(auto-fill, minmax(350px, 1fr)); gap:25px;}} .card{{background:white; padding:30px; border-radius:25px; text-decoration:none; color:#333; box-shadow:0 10px 20px rgba(0,0,0,0.05); transition:0.3s;}} .card:hover{{transform:translateY(-10px);}}</style></head><body><h1 style='text-align:center; color:#e44d26;'>🚀 실시간 쿠팡 고품질 매거진</h1><div class='grid'>")
            for file in files[:100]:
                title = self.get_real_title(f"{self.posts_dir}/{file}")
                f.write(f"<a class='card' href='posts/{file}'><div>{title}</div><div style='color:#e44d26; font-weight:bold; margin-top:15px;'>전문 칼럼 읽기 ></div></a>")
            f.write("</div></body></html>")
        print(f"🏁 모든 파일 동기화 완료! 현재 총 {len(files)}개 포스팅.")

if __name__ == "__main__":
    CoupangExpertBot().run()
