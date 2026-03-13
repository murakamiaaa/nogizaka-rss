import requests
from bs4 import BeautifulSoup
from feedgen.feed import FeedGenerator
import datetime
import time
import os
import sys
from urllib.parse import urljoin # 相対URLを絶対URLに翻訳する魔法

def get_blog_detail(session, url):
    """個別記事から本文を抽出"""
    try:
        time.sleep(1)
        res = session.get(url, timeout=20)
        res.raise_for_status()
        soup = BeautifulSoup(res.text, 'html.parser')
        
        # 本文が入っている箱
        article_box = soup.find('div', class_='bd--edit')
        
        if article_box:
            for img in article_box.find_all('img'):
                src = img.get('src')
                if src:
                    # 画像URLも省略形から完全なURLに自動変換
                    img['src'] = urljoin(url, src)
            return str(article_box)
        return "<p>本文の抽出に失敗しました。（本文のタグが異なる可能性があります）</p>"
    except Exception as e:
        return f"<p>記事取得エラー: {e}</p>"

def create_rss():
    # 💡 修正：/list は不要でした！これが全員分の最新ブログ一覧ページです。
    list_url = "https://www.nogizaka46.com/s/n46/diary/MEMBER"
    
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
        print(f"ブログ一覧にアクセス中: {list_url}")
        res = session.get(list_url, timeout=20)
        res.raise_for_status()
        soup = BeautifulSoup(res.text, 'html.parser')
        
        article_links = []
        
        # 碧さんが見つけた「タイトル」のタグから直接探し出す！
        title_tags = soup.find_all('p', class_='m--postone__ttl')
        
        if title_tags:
            print(f"ページ内から {len(title_tags)} 件のブログ記事を発見しました！")
            for title_tag in title_tags:
                # タイトルを囲んでいる <a> タグを親要素から探し出す
                a_tag = title_tag.find_parent('a')
                if a_tag and a_tag.has_attr('href'):
                    # 魔法の関数 urljoin で ../detail/123 等を完全なURLに翻訳する
                    full_url = urljoin(res.url, a_tag['href'])
                    
                    if not any(link['url'] == full_url for link in article_links):
                        article_links.append({'url': full_url, 'element': a_tag})
        else:
            print("❌ タイトルタグ（m--postone__ttl）が見つかりません。")

        print(f"処理対象の記事数: {len(article_links)}件")

        if not article_links:
            sys.exit(1)

        for item in article_links[:12]:
            url = item['url']
            element = item['element']
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
        print(f"✅ 成功: {output_file} を書き出しました！")

    except Exception as e:
        print(f"💥 エラー内容: {e}")
        sys.exit(1)

if __name__ == "__main__":
    create_rss()