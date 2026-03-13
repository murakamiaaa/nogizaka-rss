import requests
from bs4 import BeautifulSoup
from feedgen.feed import FeedGenerator
import datetime
import time
import os

def get_blog_detail(session, url):
    """個別記事から本文と画像URLを抽出する"""
    try:
        time.sleep(1) # サーバー負荷軽減
        res = session.get(url, timeout=10)
        res.raise_for_status()
        soup = BeautifulSoup(res.text, 'html.parser')
        
        # 乃木坂の本文が入っている一般的な箱
        article_box = soup.find('div', class_='bd--edit')
        
        if article_box:
            # 画像URLを絶対パスに変換
            for img in article_box.find_all('img'):
                src = img.get('src')
                if src and src.startswith('/'):
                    img['src'] = f"https://www.nogizaka46.com{src}"
            return str(article_box)
        else:
            return "<p>本文の抽出に失敗しました（タグが見つかりません）。</p>"
    except Exception as e:
        return f"<p>記事取得エラー: {e}</p>"

def create_rss():
    list_url = "https://www.nogizaka46.com/s/n46/diary/blog/list"
    
    # RSSフィードの基本設定
    fg = FeedGenerator()
    fg.id(list_url)
    fg.title("乃木坂46 公式ブログ RSS")
    fg.link(href=list_url, rel='alternate')
    fg.description("乃木坂46メンバーの公式ブログを全文でお届けします")
    fg.language('ja')

    # アイコン設定
    icon_url = "https://www.nogizaka46.com/images/46/common/logo_01.png"
    fg.logo(icon_url)
    fg.icon(icon_url)

    session = requests.Session()
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"
    })

    print(f"--- 乃木坂46ブログ 解析開始 ---")

    try:
        res = session.get(list_url, timeout=10)
        res.raise_for_status()
        soup = BeautifulSoup(res.text, 'html.parser')
        
        # 記事へのリンク（aタグ）をすべて取得
        article_links = []
        for a in soup.find_all('a', href=True):
            if '/s/n46/diary/detail/' in a['href']:
                href = a['href']
                full_url = f"https://www.nogizaka46.com{href}" if href.startswith('/') else href
                # 重複チェック
                if full_url not in [link['url'] for link in article_links]:
                    article_links.append({'url': full_url, 'element': a})

        print(f"候補記事数: {len(article_links)}件")

        # 最新の12件（1ページ分）を処理
        for item in article_links[:12]:
            url = item['url']
            element = item['element']
            
            # 碧さんが調査したクラス名を使用
            title_tag = element.find('p', class_='m--postone__ttl')
            name_tag = element.find('p', class_='m--postone__name')
            
            blog_title = title_tag.get_text(strip=True) if title_tag else "タイトルなし"
            member_name = name_tag.get_text(strip=True) if name_tag else "メンバー不明"
            final_title = f"[{member_name}] {blog_title}"

            print(f"解析中: {final_title}")
            
            # 本文を取得
            full_html_content = get_blog_detail(session, url)
            
            fe = fg.add_entry()
            fe.id(url)
            fe.title(final_title)
            fe.link(href=url)
            fe.description(full_html_content)
            # 現在時刻を公開日として設定
            fe.pubDate(datetime.datetime.now(datetime.timezone.utc))

        # 保存実行
        output_file = 'feed.xml'
        fg.rss_file(output_file)
        
        if os.path.exists(output_file):
            print(f"✅ 成功: {output_file} を生成しました！")
        else:
            print(f"❌ 失敗: ファイルが生成されませんでした。")

    except Exception as e:
        print(f"エラー発生: {e}")

if __name__ == "__main__":
    create_rss()