from __future__ import annotations

import csv
import io
from collections import Counter
from pathlib import Path
from urllib.error import URLError
from urllib.request import urlopen

from flask import Flask, flash, redirect, render_template, request, url_for

DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)

DEFAULT_SOURCE_URL = "https://raw.githubusercontent.com/mirror-media/politicalcontribution/master/legislators/2016/A05_basic_all.csv"
LOCAL_CSV_PATH = DATA_DIR / "A05_basic_all.csv"

app = Flask(__name__)
app.secret_key = "dev-secret-key"


def _normalize_url(url: str) -> str:
    """Accept GitHub blob URL and convert to raw URL."""
    url = url.strip()
    if "github.com" in url and "/blob/" in url:
        return url.replace("https://github.com/", "https://raw.githubusercontent.com/").replace("/blob/", "/")
    return url


def refresh_csv(source_url: str = DEFAULT_SOURCE_URL) -> str:
    """Try to download latest CSV to local path; return status message."""
    source_url = _normalize_url(source_url)
    try:
        with urlopen(source_url, timeout=20) as response:
            content = response.read()
        LOCAL_CSV_PATH.write_bytes(content)
        return f"已自動下載最新 CSV：{source_url}"
    except (URLError, OSError) as exc:
        if LOCAL_CSV_PATH.exists():
            return f"無法下載最新 CSV，改用本機檔案：{LOCAL_CSV_PATH}（{exc}）"
        raise RuntimeError(f"下載 CSV 失敗，且本機無備份檔案：{exc}") from exc


def load_rows() -> list[dict[str, str]]:
    if not LOCAL_CSV_PATH.exists():
        refresh_csv()

    text = LOCAL_CSV_PATH.read_text(encoding="utf-8-sig")
    reader = csv.DictReader(io.StringIO(text))
    return [dict(row) for row in reader]


def _first_existing_key(row: dict[str, str], keys: list[str]) -> str:
    for key in keys:
        if key in row and row.get(key):
            return str(row.get(key, "")).strip()
    return "未知"


def compute_statistics(rows: list[dict[str, str]]) -> tuple[list[tuple[str, int]], list[tuple[str, int]]]:
    party_counter: Counter[str] = Counter()
    city_counter: Counter[str] = Counter()

    for row in rows:
        party = _first_existing_key(row, ["party", "所屬政黨", "政黨"])
        city = _first_existing_key(row, ["city", "縣市", "選區"])
        party_counter[party] += 1
        city_counter[city] += 1

    return party_counter.most_common(), city_counter.most_common()


@app.route("/", methods=["GET", "POST"])
def index():
    status_message = refresh_csv(DEFAULT_SOURCE_URL)
    rows = load_rows()

    query = request.values.get("q", "").strip()
    results: list[dict[str, str]] = []

    if query:
        q_lower = query.lower()
        for row in rows:
            searchable = " ".join(str(value) for value in row.values()).lower()
            if q_lower in searchable:
                results.append(row)

    party_stats, city_stats = compute_statistics(rows)

    return render_template(
        "index.html",
        csv_status=status_message,
        total=len(rows),
        query=query,
        search_results=results[:100],
        party_stats=party_stats,
        city_stats=city_stats,
    )


@app.route("/stats")
def stats():
    status_message = refresh_csv(DEFAULT_SOURCE_URL)
    rows = load_rows()
    party_stats, city_stats = compute_statistics(rows)
    return render_template(
        "stats.html",
        csv_status=status_message,
        total=len(rows),
        party_stats=party_stats,
        city_stats=city_stats,
    )


@app.route("/upload", methods=["POST"])
def upload_csv():
    uploaded = request.files.get("csv_file")
    if not uploaded or uploaded.filename == "":
        flash("請先選擇 CSV 檔案", "error")
        return redirect(url_for("index"))

    if not uploaded.filename.lower().endswith(".csv"):
        flash("只接受 .csv 檔案", "error")
        return redirect(url_for("index"))

    LOCAL_CSV_PATH.write_bytes(uploaded.read())
    flash(f"上傳成功：{uploaded.filename}", "success")
    return redirect(url_for("index"))


if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
