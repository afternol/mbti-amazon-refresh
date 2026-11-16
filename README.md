# mbti-amazon-refresh

MBTIキャリア（career-kentaro.com/mbti/）のAmazon商品ボックスに表示する画像データを、GitHub Actions で12時間ごとに更新する。

- `asins.json` … 掲載中の全ASIN（`mbti-career/affiliate/sync_asins.py` が更新して push）
- `refresh.py` … Creators API で画像URLを取得 → `public/amazon_products.json` を書き出し、GitHub Pages で公開
- 公開URL: https://afternol.github.io/mbti-amazon-refresh/amazon_products.json（サイトの `assets/amz.js` が読む）
- 秘密情報（Creators APIのキー）は GitHub Secrets にのみ保存。このリポジトリのファイルには含まれない
- 価格は扱わない（画像のみ）。画像は保存せずURL参照。24時間を超えたデータはサイト側（`assets/amz.js`）で無視する
