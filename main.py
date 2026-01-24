import os
from datetime import datetime

def main():
    # 1. 무조건 폴더 생성
    os.makedirs("posts", exist_ok=True)

    # 2. [강제 생성] index.html (검은색 배경의 확실한 웹사이트 화면)
    with open("index.html", "w", encoding="utf-8") as f:
        f.write(f"""<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>접속 성공!</title>
    <style>
        body {{ 
            background-color: black; 
            color: yellow; 
            text-align: center; 
            padding-top: 100px; 
            font-family: sans-serif; 
        }}
        h1 {{ font-size: 3em; }}
        .box {{ border: 5px solid red; padding: 20px; display: inline-block; }}
    </style>
</head>
<body>
    <div class="box">
        <h1>🎉 접속 성공! 🎉</h1>
        <p>이 검은 화면이 보이면 웹사이트가 100% 동작하는 것입니다.</p>
        <p>확인 시간: {datetime.now().strftime('%H:%M:%S')}</p>
    </div>
</body>
</html>""")

    # 3. README.md 생성 (웹사이트 주소 안내용)
    with open("README.md", "w", encoding="utf-8") as f:
        f.write(f"# 확인 완료\n\n")
        f.write(f"웹사이트가 정상적으로 생성되었습니다.\n\n")
        f.write(f"👉 [여기를 클릭해서 검은 화면을 확인하세요](https://rkskqdl-a11y.github.io/coupang-sale-shuttle/)")

    # 4. .nojekyll 생성 (필수)
    with open(".nojekyll", "w", encoding="utf-8") as f: 
        f.write("")

    print("모든 파일 강제 생성 완료!")

if __name__ == "__main__":
    main()
