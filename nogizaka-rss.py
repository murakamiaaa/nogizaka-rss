import requests
from bs4 import BeautifulSoup
from feedgen.feed import FeedGenerator
import datetime
import time

def get_blog_detail(session, url):
    """乃木坂46の個別記事から本文と画像を抜き出す"""
    try:
        time.sleep(1)
        res = session.get(url, timeout=10)
        res.raise_for_status()
        soup = BeautifulSoup(res.text, 'html.parser')
        
        # 💡 乃木坂の本文が入っている一般的な箱（bd--edit）
        article_box = soup.find('div', class_='bd--edit')
        
        if article_box:
            for img in article_box.find_all('img'):
                src = img.get('src')
                if src and src.startswith('/'):
                    img['src'] = f"https://www.nogizaka46.com{src}"
            return str(article_box)
        else:
            return "<p>本文の抽出に失敗しました。</p>"
    except Exception as e:
        return f"<p>記事取得エラー: {e}</p>"

def create_rss():
    list_url = "https://www.nogizaka46.com/s/n46/diary/blog/list"
    
    fg = FeedGenerator()
    fg.id(list_url)
    fg.title("乃木坂46 公式ブログ (全文・画像あり)")
    fg.link(href=list_url, rel='alternate')
    fg.description("乃木坂46メンバーの公式ブログを全文でお届けします")
    fg.language('ja')

    # アイコンも乃木坂仕様に（公式サイトのロゴ等）
    icon_url = "https://www.nogizaka46.com/images/46/common/logo_01.png"
    fg.logo(icon_url)
    fg.icon(icon_url)

    session = requests.Session()
    session.headers.update({"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"})

    try:
        res = session.get(list_url, timeout=10)
        res.raise_for_status()
        soup = BeautifulSoup(res.text, 'html.parser')
        
        # 乃木坂の記事リンクを抽出
        article_links = soup.find_all('a', href=True)
        blog_posts = []
        for a in article_links:
            href = a['href']
            if '/s/n46/diary/detail/' in href:
                full_url = f"https://www.nogizaka46.com{href}" if href.startswith('/') else href
                if not any(post['url'] == full_url for post in blog_posts):
                    blog_posts.append({'url': full_url, 'element': a})

        print(f"--- 乃木坂46ブログ 解析開始: {len(blog_posts)}件 ---")

        for post in blog_posts[:15]:
            url = post['url']
            element = post['element']
            
            # 💡 碧さんが見つけてくれたクラス名で抽出！
            title_tag = element.find('p', class_='m--postone__ttl')
            name_tag = element.find('p', class_='m--postone__name')
            
            blog_title = title_tag.get_text(strip=True) if title_tag else "タイトルなし"
            member_name = name_tag.get_text(strip=True) if name_tag else "メンバー"
            final_title = f"[{member_name}] {blog_title}"

            print(f"解析中: {final_title}")
            full_html_content = get_blog_detail(session, url)
            
            fe = fg.add_entry()
            fe.id(url)
            fe.title(final_title)
            fe.link(href=url)
            fe.description(full_html_content)
            fe.pubDate(datetime.datetime.now(datetime.timezone.utc))

        fg.rss_file('nogizaka-rss/nogizaka.xml')
        print("🎉 nogizaka.xml の生成が完了しました！")

    except Exception as e:
        print(f"エラー発生: {e}")

if __name__ == "__main__":
    create_rss()
