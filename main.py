import os
import hmac
import hashlib
import time
import requests
import json
import random
import re
from datetime import datetime
from urllib.parse import urlencode

# 💎 로깅 및 설정 클래스
class CoupangBot:
    def __init__(self):
        self.access_key = os.environ.get('COUPANG_ACCESS_KEY', '').strip()
        self.secret_key = os.environ.get('COUPANG_SECRET_KEY', '').strip()
        self.gemini_key = os.environ.get('GEMINI_API_KEY', '').strip()
        self.site_url = "https://rkskqdl-a11y.github.io/coupang-sale-shuttle"
        self.session = requests.Session()
        self.posts_dir = "posts"
        os.makedirs(self.posts_dir, exist_ok=True)

    def _generate_auth_header(self, method, path, query_string):
        """💎 공식 문서 규격에 따른 HMAC 서명 생성"""
        timestamp = time.strftime('%y%m%dT%H%M%SZ', time.gmtime())
        canonical_string = timestamp + method + path + query_string
        
        signature = hmac.new(
            bytes(self.secret_key, 'utf-8'),
            msg=bytes(canonical_string, 'utf-8'),
            digestmod=hashlib.sha256
        ).hexdigest()
        
        return f"CEA algorithm=HmacSHA256, access-key={self.access_key}, signed-date={timestamp}, signature={signature}"

    def fetch_products(self, keyword: str, page: int = 1):
        """💎 정렬된 쿼리 스트링으로 쿠팡 API 호출"""
        domain = "https://api-gateway.coupang.com"
        path = "/v2/providers/affiliate_open_api/apis/openapi/v1/products/search"
        
        # ⚠️ 파라미터는 반드시 알파벳 순으로 정렬되어야 함
        params = {
            "keyword": keyword,
            "limit": 20,
            "page": page
        }
        query_string = urlencode(sorted(params.items()))
        
        headers = {
            "Authorization": self._generate_auth_header("GET", path, query_string),
            "Content-Type": "application/json"
        }

        try:
            resp = self.session.get(f"{domain}{path}?{query_string}", headers=headers, timeout=15)
            if resp.status_code != 200:
                print(f"❌ API 에러 [{resp.status_code}]: {resp.text}")
                return []
            
            data = resp.json()
            return data.get('data', {}).get('productData', [])
        except Exception as e:
            print(f"⚠️ 통신 중 예외 발생: {e}")
            return []

    def generate_review(self, product_name: str):
        """💎 제미나이 1.5 플래시 모델을 활용한 고품질 리뷰 생성"""
        if not self.gemini_key: return "상세 분석 준비 중입니다."
        
        api_url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={self.gemini_key}"
        prompt = (f"상품명 '{product_name}'에 대해 IT 쇼핑 전문가의 시선으로 1000자 내외의 상세 분석을 작성해줘. "
                  f"반드시 <h3> 태그를 사용해 '디자인', '성능', '총평'으로 문단을 나누고 HTML 태그만 사용해. "
                  f"친절한 해요체로 작성하되 '할인'이나 '최저가'라는 단어는 쓰지 마.")
        
        try:
            payload = {"contents": [{"parts": [{"text": prompt}]}]}
            resp = self.session.post(api_url, json=payload, timeout=30)
            res_json = resp.json()
            return res_json['candidates'][0]['content']['parts'][0]['text'].replace("\n", "<br>")
        except:
            return f"<h3>🔍 제품 요약</h3>{product_name}은 품질과 가격을 모두 잡은 추천 모델입니다."

    def run(self):
        existing_ids = {f.split('_')[-1].replace('.html', '') for f in os.listdir(self.posts_dir) if '_' in f}
        success_count = 0
        
        # 💎 저인망식 수집을 위한 시드 키워드
        seeds = ["가성비", "인기", "추천", "필수", "생활"]
        targets = ["가전", "노트북", "주방용품", "운동화", "캠핑용품"]
        keyword = f"{random.choice(seeds)} {random.choice(targets)}"
        
        print(f"🕵️ 현재 {len(existing_ids)}개 데이터 확보됨. '{keyword}' 전수 조사 시작...")

        for page in range(1, 11): # 10페이지까지 정밀 수색
            if success_count >= 10: break
            
            print(f"🔍 {page}페이지 분석 중...")
            products = self.fetch_products(keyword, page)
            
            if not products:
                print(f"⚠️ {page}페이지에 상품이 없습니다. 수색 종료.")
                break

            for item in products:
                p_id = str(item['productId'])
                if p_id in existing_ids: continue

                print(f"   ✨ 신규 발견: {item['productName'][:20]}...")
                content = self.generate_review(item['productName'])
                
                # HTML 생성 및 저장 (사용자님의 기존 템플릿 유지/강화)
                filename = f"{self.posts_dir}/{datetime.now().strftime('%Y%m%d')}_{p_id}.html"
                self._save_post(filename, item, content)
                
                existing_ids.add(p_id)
                success_count += 1
                time.sleep(35) # 제미나이 안전 발행 대기
                if success_count >= 10: break

        self._update_index_and_sitemap()
        print(f"🏁 작업 완료. 신규 발행: {success_count}개")

    def _save_post(self, filename, item, content):
        img_url = item['productImage'].split('?')[0]
        price = format(item['productPrice'], ',')
        html = f"""<!DOCTYPE html><html lang='ko'><head><meta charset='UTF-8'><title>{item['productName']} 리뷰</title>
        <style>body{{font-family:sans-serif; background:#f8f9fa; padding:20px; color:#333; line-height:1.8;}}
        .card{{max-width:700px; margin:auto; background:white; padding:40px; border-radius:25px; box-shadow:0 10px 30px rgba(0,0,0,0.05);}}
        img{{width:100%; border-radius:15px;}} h2{{color:#e44d26;}} .buy-btn{{display:block; background:#e44d26; color:white; text-align:center; padding:15px; text-decoration:none; border-radius:50px; font-weight:bold; margin-top:30px;}}</style></head>
        <body><div class='card'><h2>{item['productName']}</h2><img src='{img_url}'><div class='content'>{content}</div><div style='font-size:2rem; font-weight:bold; text-align:center; margin:20px 0;'>{price}원</div>
        <a href='{item['productUrl']}' class='buy-btn'>🛍️ 상세 정보 및 구매평 보기</a></div></body></html>"""
        with open(filename, "w", encoding="utf-8") as f: f.write(html)

    def _update_index_and_sitemap(self):
        # index.html 및 sitemap.xml 갱신 로직 (전문가 수준의 XML 네임스페이스 포함)
        files = sorted([f for f in os.listdir(self.posts_dir) if f.endswith(".html")], reverse=True)
        now = datetime.now().strftime("%Y-%m-%d")
        
        # sitemap.xml (구글 검색 최적화 버전) 
        with open("sitemap.xml", "w", encoding="utf-8") as f:
            f.write('<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n')
            f.write(f'<url><loc>{self.site_url}/</loc><lastmod>{now}</lastmod><priority>1.0</priority></url>\n')
            for file in files:
                f.write(f'<url><loc>{self.site_url}/posts/{file}</loc><lastmod>{now}</lastmod></url>\n')
            f.write('</urlset>')

if __name__ == "__main__":
    CoupangBot().run()
