import requests
from bs4 import BeautifulSoup
from feedgen.feed import FeedGenerator
import datetime
import time
import os
import sys

def get_blog_detail(session, url):
    """個別記事から本文を抽出"""
    try:
        time.sleep(1)
        res = session.get(url, timeout=20)
        res.raise_for_status()
        soup = BeautifulSoup(res.text, 'html.parser')
        article_box = soup.find('div', class_='bd--edit')
        if article_box:
            for img in article_box.find_all('img'):
                src = img.get('src')
                if src and src.startswith('/'):
                    img['src'] = f"https://www.nogizaka46.com{src}"
            return str(article_box)
        return "<p>本文の抽出に失敗しました。</p>"
    except Exception as e:
        return f"<p>記事取得エラー: {e}</p>"

def create_rss():
    base_url = "https://www.nogizaka46.com"
    # 💡 修正箇所：乃木坂の正しいURLはこれです！
    list_url = f"{base_url}/s/n46/diary/MEMBER"
    
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
        for a in soup.find_all('a', href=True):
            href = a['href']
            if '/s/n46/diary/detail/' in href:
                full_url = f"{base_url}{href}" if href.startswith('/') else href
                if not any(link['url'] == full_url for link in article_links):
                    article_links.append({'url': full_url, 'element': a})

        print(f"候補記事数: {len(article_links)}件")

        if not article_links:
            print("❌ 記事が見つかりません。")
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