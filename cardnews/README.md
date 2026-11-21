# 카드뉴스 자동 생성 (1단계)

문안 CSV → 인스타그램 세로형 PNG(1080×1350) 자동 생성.

```bash
sudo apt-get install -y fonts-nanum   # 한글 글꼴 (OFL, 상업 이용 가능)
python3 cardnews/render.py cardnews/content/fruit_v1.csv --out cardnews/out
python3 -m unittest discover -s cardnews/tests -v
```

- CSV 열: `세트, 장, 역할(표지/본문/CTA), 큰 제목, 본문` — 본문의 ` / ` 는 줄바꿈
- 글자가 이미지 밖으로 넘치면 오류로 멈춤 (조용히 잘리지 않음)
- 범위 밖(승인 전): 사진 합성, 인스타 자동 게시, DM 자동화
