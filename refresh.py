"""MBTIキャリア: Amazon商品画像データの定期更新（GitHub Actions から12時間ごとに実行）

asins.json の全ASINについて Creators API の GetItems で画像URL・商品ページURLを取得し、
public/amazon_products.json を書き出す（ワークフローが GitHub Pages に公開する）。
サイト側の assets/amz.js が https://afternol.github.io/mbti-amazon-refresh/amazon_products.json を読む。

- 価格は取得・表示しない（画像のみ）
- 規約: 画像は保存せずURL参照のみ。URLは24時間以内に再取得（amz.js は24hを超えたデータを使わない）
必要な環境変数（GitHub Secrets）:
  AMAZON_CREATORS_CLIENT_ID / AMAZON_CREATORS_CLIENT_SECRET / AMAZON_CREATORS_VERSION / AMAZON_PARTNER_TAG
"""
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import requests

TOKEN_URL = {"3.1": "https://api.amazon.com/auth/o2/token",
             "3.2": "https://api.amazon.co.uk/auth/o2/token",
             "3.3": "https://api.amazon.co.jp/auth/o2/token"}
API = "https://creatorsapi.amazon/catalog/v1/getItems"
MARKET = "www.amazon.co.jp"
HERE = Path(__file__).parent


def token(ver):
    r = requests.post(TOKEN_URL[ver], timeout=30, json={
        "grant_type": "client_credentials", "scope": "creatorsapi::default",
        "client_id": os.environ["AMAZON_CREATORS_CLIENT_ID"],
        "client_secret": os.environ["AMAZON_CREATORS_CLIENT_SECRET"]})
    r.raise_for_status()
    return r.json()["access_token"]


def fetch(asins):
    ver = os.environ["AMAZON_CREATORS_VERSION"].lstrip("v")
    tok = token(ver)
    items, errors = {}, []
    for i in range(0, len(asins), 10):
        batch = asins[i:i + 10]
        for attempt in range(3):
            r = requests.post(API, timeout=30, json={
                "itemIds": batch, "partnerTag": os.environ["AMAZON_PARTNER_TAG"], "marketplace": MARKET,
                "resources": ["images.primary.medium"]},
                headers={"Authorization": f"Bearer {tok}, Version {ver}", "x-marketplace": MARKET})
            if r.status_code == 429:
                time.sleep(2 ** attempt * 2)
                continue
            break
        if r.status_code != 200:
            errors.append(f"{r.status_code} {batch}: {r.text[:200]}")
            continue
        for it in r.json().get("itemsResult", {}).get("items", []):
            img = ((it.get("images", {}).get("primary") or {}).get("medium") or {}).get("url")
            items[it["asin"]] = {"url": it["detailPageURL"], "image": img}
        time.sleep(1.1)   # 1 TPS
    return items, errors


def main():
    asins = json.loads((HERE / "asins.json").read_text(encoding="utf-8"))
    items, errors = fetch(asins)
    print(f"asins {len(asins)} / fetched {len(items)} / errors {len(errors)}")
    for e in errors:
        print("  ", e)
    if not items:
        sys.exit("no items fetched")
    out = HERE / "public"
    out.mkdir(exist_ok=True)
    (out / "amazon_products.json").write_text(json.dumps(
        {"fetched_at": datetime.now(timezone.utc).isoformat(), "items": items},
        ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
    (out / "index.html").write_text("<!doctype html><meta charset=utf-8><title>data</title>", encoding="utf-8")
    print("written", out / "amazon_products.json")
    if len(items) < len(asins) * 0.9:
        print(f"::warning::取得率が低い: {len(items)}/{len(asins)}")


if __name__ == "__main__":
    main()
