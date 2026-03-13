import requests
from bs4 import BeautifulSoup
from feedgen.feed import FeedGenerator
import datetime
import time
import os
import sys
from urllib.parse import urljoin

def create_rss():
    # ブログ一覧ページのURL
    list_url = "https://www.nogizaka46.com/s/n46/diary/MEMBER/list"
    
    fg = FeedGenerator()
    fg.id(list_url)
    fg.title("乃木坂46 公式ブログ RSS")
    fg.link(href=list_url, rel='alternate')
    fg.description("乃木坂46メンバーの公式ブログ全文配信")
    fg.language('ja')

    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
    })

    print("--- 乃木坂46ブログ 解析開始 ---")

    try:
        print(f"一覧ページからURLを収集します: {list_url}")
        res = session.get(list_url, timeout=20)
        res.raise_for_status()
        soup = BeautifulSoup(res.text, 'html.parser')
        
        # 💡 作戦変更：一覧ページからは「リンク（URL）」だけを回収する！
        article_urls = []
        for a in soup.find_all('a', href=True):
            href = a['href']
            # detail（個別記事）へのリンクだけを拾う
            if '/s/n46/diary/detail/' in href:
                full_url = urljoin(res.url, href)
                if full_url not in article_urls:
                    article_urls.append(full_url)

        print(f"発見した記事リンク数: {len(article_urls)}件")

        if not article_urls:
            print("❌ 記事のリンクが見つかりません。")
            sys.exit(1)

        # 💡 収集したURL（最新12件）に直接アクセスして中身を引っこ抜く！
        for url in article_urls[:12]:
            print(f"記事を取得中: {url}")
            time.sleep(1) # サーバーに優しく
            
            detail_res = session.get(url, timeout=20)
            detail_res.raise_for_status()
            detail_soup = BeautifulSoup(detail_res.text, 'html.parser')
            
            # 碧さんが見つけた「個別ページ用のタグ」をここで使う！
            title_tag = detail_soup.find(class_='m--postone__ttl')
            name_tag = detail_soup.find(class_='m--postone__name')
            article_box = detail_soup.find('div', class_='bd--edit')
            
            blog_title = title_tag.get_text(strip=True) if title_tag else "タイトルなし"
            member_name = name_tag.get_text(strip=True) if name_tag else "メンバー不明"
            final_title = f"[{member_name}] {blog_title}"
            
            print(f"  -> 解析成功: {final_title}")
            
            # 本文と画像の処理
            content_html = "<p>本文の抽出に失敗しました。</p>"
            if article_box:
                for img in article_box.find_all('img'):
                    src = img.get('src')
                    if src:
                        img['src'] = urljoin(url, src) # 画像も絶対URLに変換
                content_html = str(article_box)
            
            # RSSに追加
            fe = fg.add_entry()
            fe.id(url)
            fe.title(final_title)
            fe.link(href=url)
            fe.description(content_html)
            fe.pubDate(datetime.datetime.now(datetime.timezone.utc))

        output_file = 'feed.xml'
        fg.rss_file(output_file)
        print(f"✅ 成功: {output_file} を書き出しました！")

    except Exception as e:
        print(f"💥 エラー内容: {e}")
        sys.exit(1)

if __name__ == "__main__":
    create_rss()