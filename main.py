import os, hmac, hashlib, time, requests, json, random, re
from datetime import datetime
from time import gmtime, strftime
from urllib.parse import quote

# 💎 사용자 AF7053799 전용 식별자
MY_PARTNERS_ID = "AF7053799"
SITE_URL = "https://rkskqdl-a11y.github.io/coupang-sale-shuttle"

def generate_hmac_official(method, path, query_string, secret_key, access_key):
    """💎 공식 문서 가이드 100% 준수 (오차 범위 0%)"""
    datetime_gmt = strftime('%y%m%d', gmtime()) + 'T' + strftime('%H%M%S', gmtime()) + 'Z'
    message = datetime_gmt + method + path + query_string
    signature = hmac.new(bytes(secret_key, "utf-8"), message.encode("utf-8"), hashlib.sha256).hexdigest()
    return "CEA algorithm=HmacSHA256, access-key={}, signed-date={}, signature={}".format(access_key, datetime_gmt, signature)

class CoupangDeepInspector:
    def __init__(self):
        self.access = os.environ.get('COUPANG_ACCESS_KEY', '').strip()
        self.secret = os.environ.get('COUPANG_SECRET_KEY', '').strip()
        self.gemini = os.environ.get('GEMINI_API_KEY', '').strip()
        self.posts_dir = "posts"
        os.makedirs(self.posts_dir, exist_ok=True)

    def fetch_api(self, keyword, page):
        """💎 상품을 가져오되, 실패 시 쿠팡의 응답을 낱낱이 공개합니다."""
        path = "/v2/providers/affiliate_open_api/apis/openapi/v1/products/search"
        # ⚠️ 공식 규격: keyword -> limit -> page 순서 정렬
        query_string = f"keyword={quote(keyword)}&limit=20&page={page}"
        
        auth_header = generate_hmac_official("GET", path, query_string, self.secret, self.access)
        headers = {"Authorization": auth_header, "Content-Type": "application/json"}
        
        try:
            url = f"https://api-gateway.coupang.com{path}?{query_string}"
            resp = requests.get(url, headers=headers, timeout=15)
            data = resp.json()

            if resp.status_code == 200:
                items = data.get('data', {}).get('productData', [])
                if not items:
                    # 💎 [핵심 진단] 상품이 0개일 때 쿠팡이 보낸 메시지 전체 출력
                    print(f"   🔎 [진단 데이터] rCode: {data.get('rCode')}, rMessage: {data.get('rMessage')}")
                    print(f"   🔎 [Raw Response]: {json.dumps(data)}")
                return items
            else:
                print(f"   ❌ [통신 실패] HTTP {resp.status_code}: {resp.text}")
                return []
        except Exception as e:
            print(f"   ⚠️ [시스템 오류] {e}")
            return []

    def generate_ai(self, p_name):
        """💎 1,000자 이상 전문가 칼럼 생성"""
        if not self.gemini: return "상세 분석 준비 중"
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={self.gemini}"
        try:
            prompt = f"상품 '{p_name}'에 대해 IT 칼럼니스트처럼 1000자 이상 장문 분석 글을 써줘. <h3> 사용, HTML만 사용. '해요체' 사용. '할인' 언급 금지."
            res = requests.post(url, json={"contents": [{"parts": [{"text": prompt}]}]}, timeout=60)
            return res.json()['candidates'][0]['content']['parts'][0]['text'].replace("\n", "<br>")
        except: return f"<h3>🔍 제품 분석</h3>{p_name}은 품질이 우수한 추천 모델입니다."

    def run(self):
        existing_ids = {f.split('_')[-1].replace('.html', '') for f in os.listdir(self.posts_dir) if '_' in f}
        success_count = 0
        
        # 💎 실패를 모르는 '마지막 보루' 키워드
        seeds = ["삼성전자", "생수", "라면", "갤럭시", "물티슈", "나이키"]
        
        print(f"🚀 [AF7053799] 엔진 가동. 현재 {len(existing_ids)}개 노출 중.")

        for keyword in seeds:
            if success_count >= 10: break
            print(f"🔄 '{keyword}' 키워드로 심층 수색 중...")
            products = self.fetch_api(keyword, 1)
            
            if not products: continue

            for item in products:
                p_id = str(item['productId'])
                if p_id in existing_ids: continue

                print(f"   ✨ 발견! [{success_count+1}/10] {item['productName'][:20]}...")
                content = self.generate_ai(item['productName'])
                
                # HTML 저장 로직
                filename = f"{self.posts_dir}/{datetime.now().strftime('%Y%m%d')}_{p_id}.html"
                self.save_post(filename, item, content)
                
                existing_ids.add(p_id)
                success_count += 1
                time.sleep(35) # 제미나이 안전 장치
                if success_count >= 10: break

        self.sync_seo()
        print(f"🏁 작업 완료. 신규 발행: {success_count}개")

    def save_post(self, filename, item, content):
        img, price = item['productImage'].split('?')[0], format(int(item['productPrice']), ',')
        html = f"""<!DOCTYPE html><html lang='ko'><head><meta charset='UTF-8'><title>{item['productName']} 리뷰</title>
        <style>body{{font-family:sans-serif; background:#f8f9fa; padding:20px; line-height:2.2;}} .card{{max-width:750px; margin:auto; background:white; padding:50px; border-radius:30px; box-shadow:0 20px 50px rgba(0,0,0,0.05);}} 
        img{{width:100%; border-radius:20px; margin:30px 0;}} .p-val{{font-size:2.5rem; color:#e44d26; font-weight:bold; text-align:center;}} .buy-btn{{display:block; background:#e44d26; color:white; text-align:center; padding:25px; text-decoration:none; border-radius:60px; font-weight:bold;}}</style></head>
        <body><div class='card'><h2>{item['productName']}</h2><img src='{img}'><div class='content'>{content}</div><div class='p-val'>{price}원</div><a href='{item['productUrl']}' class='buy-btn'>🛍️ 상세 정보 확인하기</a></div></body></html>"""
        with open(filename, "w", encoding="utf-8") as f: f.write(html)

    def sync_seo(self):
        """💎 사이트맵 XML 네임스페이스 오류 영구 해결"""
        files = sorted([f for f in os.listdir(self.posts_dir) if f.endswith(".html")], reverse=True)
        now = datetime.now().strftime("%Y-%m-%d")
        with open("sitemap.xml", "w", encoding="utf-8") as f:
            f.write('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n')
            f.write(f'  <url><loc>{SITE_URL}/</loc><lastmod>{now}</lastmod><priority>1.0</priority></url>\n')
            for file in files:
                f.write(f'  <url><loc>{SITE_URL}/posts/{file}</loc><lastmod>{now}</lastmod></url>\n')
            f.write('</urlset>')

if __name__ == "__main__":
    CoupangDeepInspector().run()
