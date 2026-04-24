# teach2025

政治獻金資料網站（Flask 範例）：

- 入口頁 `/`：
  - 人名 / 關鍵字搜尋
  - 政黨統計（前 10）
  - 縣市統計（前 10）
  - CSV 上傳
- 統計結果頁 `/stats`
- 每次進入頁面會嘗試自動下載最新 CSV（失敗則用本機備份）

## 使用方式

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

預設 CSV 來源：

- <https://github.com/mirror-media/politicalcontribution/blob/master/legislators/2016/A05_basic_all.csv>

程式會自動轉換 GitHub `blob` 連結為 `raw` 連結下載。
