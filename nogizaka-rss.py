import requests
from bs4 import BeautifulSoup
from feedgen.feed import FeedGenerator
import datetime
import time
import os
import sys

def get_blog_detail(session, url):
    """個別記事から本文と画像URLを抽出する"""
    try:
        time.sleep(1) # サーバーへの負荷軽減
        # 404を避けるため、個別ページにも ?ima=0000 を付与
        detail_url = url + "?ima=0000" if "?" not in url else url + "&ima=0000"
        res = session.get(detail_url, timeout=15)
        res.raise_for_status()
        soup = BeautifulSoup(res.text, 'html.parser')
        
        # 乃木坂の本文が入っているエリア
        article_box = soup.find('div', class_='bd--edit')
        
        if article_box:
            # 画像URLを絶対パスに変換
            for img in article_box.find_all('img'):
                src = img.get('src')
                if src and src.startswith('/'):
                    img['src'] = f"https://www.nogizaka46.com{src}"
            return str(article_box)
        else:
            return "<p>本文の抽出に失敗しました（bd--editが見つかりません）。</p>"
    except Exception as e:
        return f"<p>記事取得エラー: {e}</p>"

def create_rss():
    # 💡 404対策：?ima=0000 を追加
    list_url = "https://www.nogizaka46.com/s/n46/diary/blog/list?ima=0000"
    
    fg = FeedGenerator()
    fg.id(list_url)
    fg.title("乃木坂46 公式ブログ RSS")
    fg.link(href=list_url, rel='alternate')
    fg.description("乃木坂46メンバーの公式ブログを全文でお届けします")
    fg.language('ja')

    icon_url = "https://www.nogizaka46.com/images/46/common/logo_01.png"
    fg.logo(icon_url)
    fg.icon(icon_url)

    session = requests.Session()
    # 💡 404対策：より本物のブラウザに近いヘッダーを設定
    session.headers.update({
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
        "Accept-Language": "ja,en-US;q=0.9,en;q=0.8",
        "Referer": "https://www.nogizaka46.com/"
    })

    print("--- 乃木坂46ブログ 解析開始 ---")

    try:
        print(f"URLにアクセス中: {list_url}")
        res = session.get(list_url, timeout=15)
        res.raise_for_status()
        soup = BeautifulSoup(res.text, 'html.parser')
        
        article_links = []
        for a in soup.find_all('a', href=True):
            href = a['href']
            if '/s/n46/diary/detail/' in href:
                full_url = f"https://www.nogizaka46.com{href}" if href.startswith('/') else href
                if not any(link['url'] == full_url for link in article_links):
                    article_links.append({'url': full_url, 'element': a})

        print(f"候補記事数: {len(article_links)}件見つかりました")

        if not article_links:
            print("❌ 記事が見つかりません。タグ構造が変わった可能性があります。")
            sys.exit(1)

        for item in article_links[:12]:
            url = item['url']
            element = item['element']
            
            # 碧さんの調査結果を反映
            title_tag = element.find('p', class_='m--postone__ttl')
            name_tag = element.find('p', class_='m--postone__name')
            
            blog_title = title_tag.get_text(strip=True) if title_tag else "タイトルなし"
            member_name = name_tag.get_text(strip=True) if name_tag else "メンバー不明"
            final_title = f"[{member_name}] {blog_title}"

            print(f"解析中: {final_title}")
            
            content = get_blog_detail(session, url)
            
            fe = fg.add_entry()
            fe.id(url)
            fe.title(final_title)
            fe.link(href=url)
            fe.description(content)
            fe.pubDate(datetime.datetime.now(datetime.timezone.utc))

        output_file = 'feed.xml'
        fg.rss_file(output_file)
        
        if os.path.exists(output_file):
            print(f"✅ 成功: {output_file} を書き出しました！")
        else:
            print("❌ ファイル生成失敗")
            sys.exit(1)

    except Exception as e:
        print(f"💥 重大なエラーが発生しました: {e}")
        sys.exit(1)

if __name__ == "__main__":
    create_rss()