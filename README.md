# pass_gene_lambda

pass_gene は、パスワードの自動生成・管理用の web アプリケーションです。
本ソースコードは、pass_gene のバック側の処理を記述したものです。

# DEMO

デモサイトはこちらからご確認ください。
http://matsuda-portfolio.s3-website.ap-northeast-3.amazonaws.com/pass_gene

# Description

本プログラムは、フロントとバックの処理が分かれており、
フロントは HTML/CSS/JS(JQuery)にて記述されています。
バック側の処理は AWS を利用し、
APIGateway / Lambda / DynamoDB の構成となっています。

フロントから送られたデータに応じて、DynamoDB に対してデータの取得、登録、削除を行います。

# Caution

本アプリは、作者のポートフォリオ用に制作いたしました。
パスワードの暗号化処理などは行っておりますが、ソースコードを公開しているため、セキュリティ的に脆弱である可能性が高いと考えられます。
そのため、本アプリを正規の目的で使用することは推奨いたしません。
本アプリを使用する上で生じたいかなる不利益につきましても、作者は責任を負いかねますのでご了承ください。

# Author

- 松田涼佑
- 創造社デザイン専門学校
- mtd.931129@gmail.com
