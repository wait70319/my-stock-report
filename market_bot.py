import yfinance as yf
import feedparser
import pandas as pd
from datetime import datetime
import os

# --- 設定設定 ---
HTML_FILENAME = "index.html"

# 定義追蹤資產 (Yahoo Finance 代碼)
ASSETS = {
    'S&P 500': '^GSPC',
    '台灣加權': '^TWII',
    '日經 225': '^N225',
    '美金/台幣': 'TWD=X',
    '美金/日圓': 'JPY=X'
}

# RSS 新聞來源 (Google News)
RSS_FEEDS = {
    'TW': 'https://news.google.com/rss/search?q=台股+when:1d&hl=zh-TW&gl=TW&ceid=TW:zh-Hant',
    'US': 'https://news.google.com/rss/search?q=US+Stock+Market+when:1d&hl=en-US&gl=US&ceid=US:en',
    'JP': 'https://news.google.com/rss/search?q=Nikkei+Stock+when:1d&hl=en-US&gl=US&ceid=US:en'
}

def get_market_data():
    print("正在抓取市場數據...")
    data = []
    for name, ticker in ASSETS.items():
        try:
            stock = yf.Ticker(ticker)
            # 抓取近 5 天數據以確保有前後兩天的收盤價
            hist = stock.history(period="5d")
            
            if len(hist) < 2:
                print(f"警告: {name} 數據不足")
                continue

            current_price = hist['Close'].iloc[-1]
            prev_close = hist['Close'].iloc[-2]
            change_pct = ((current_price - prev_close) / prev_close) * 100
            
            # 判斷漲跌顏色 (台股習慣：紅漲綠跌)
            # 匯率部分：美金/台幣 跌代表台幣升值(好)，但這裡單純顯示數字變化
            if change_pct >= 0:
                arrow = "▲"
                color_class = "up"
                sign = "+"
            else:
                arrow = "▼"
                color_class = "down"
                sign = ""

            data.append({
                "name": name,
                "price": f"{current_price:,.2f}",
                "change_text": f"{arrow} {sign}{change_pct:.2f}%",
                "color_class": color_class
            })
        except Exception as e:
            print(f"抓取 {name} 失敗: {e}")
            data.append({"name": name, "price": "Error", "change_text": "-", "color_class": ""})
    return data

def get_news(region):
    print(f"正在抓取 {region} 新聞...")
    try:
        feed = feedparser.parse(RSS_FEEDS[region])
        news_items = []
        for entry in feed.entries[:5]: # 只取前 5 則
            news_items.append({
                "title": entry.title,
                "link": entry.link,
                "date": datetime(*entry.published_parsed[:6]).strftime('%H:%M') if entry.published_parsed else ""
            })
        return news_items
    except Exception as e:
        print(f"抓取新聞失敗: {e}")
        return []

def generate_html(market_data, news_tw, news_us, news_jp):
    # 這裡使用 Python f-string 直接生成 HTML，不需要額外的 template 檔案
    
    # 生成市場卡片 HTML
    cards_html = ""
    for item in market_data:
        cards_html += f"""
            <div class="card">
                <div class="asset-name">{item['name']}</div>
                <div class="asset-price">{item['price']}</div>
                <div class="asset-change {item['color_class']}">{item['change_text']}</div>
            </div>
        """

    # 生成新聞列表 HTML helper
    def make_news_list(news_items):
        html = ""
        for n in news_items:
            html += f"""
            <div class="news-item">
                <a href="{n['link']}" target="_blank">{n['title']}</a>
                <div class="news-meta">{n['date']}</div>
            </div>"""
        return html

    full_html = f"""
    <!DOCTYPE html>
    <html lang="zh-TW">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>全球市場日報</title>
        <style>
            :root {{ --bg: #f4f7f6; --card-bg: #ffffff; --text: #333; --red: #e74c3c; --green: #27ae60; }}
            body {{ font-family: 'Segoe UI', sans-serif; background: var(--bg); color: var(--text); margin: 0; padding: 20px; }}
            .container {{ max-width: 1000px; margin: 0 auto; }}
            header {{ text-align: center; margin-bottom: 30px; }}
            .update-time {{ font-size: 0.9em; color: #666; }}
            .market-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 15px; margin-bottom: 30px; }}
            .card {{ background: var(--card-bg); padding: 20px; border-radius: 10px; box-shadow: 0 2px 5px rgba(0,0,0,0.05); text-align: center; }}
            .asset-name {{ font-size: 0.9em; color: #777; margin-bottom: 5px; }}
            .asset-price {{ font-size: 1.5em; font-weight: bold; }}
            .asset-change {{ font-size: 1em; margin-top: 5px; }}
            .up {{ color: var(--red); }}
            .down {{ color: var(--green); }}
            .news-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; }}
            .news-col {{ background: var(--card-bg); padding: 20px; border-radius: 10px; }}
            .news-col h3 {{ border-bottom: 2px solid #eee; padding-bottom: 10px; margin-top: 0; }}
            .news-item {{ margin-bottom: 15px; padding-bottom: 15px; border-bottom: 1px dashed #eee; }}
            .news-item:last-child {{ border: none; }}
            .news-item a {{ text-decoration: none; color: #2c3e50; font-weight: 500; display: block; margin-bottom: 5px; }}
            .news-item a:hover {{ color: #3498db; }}
            .news-meta {{ font-size: 0.8em; color: #999; }}
        </style>
    </head>
    <body>
        <div class="container">
            <header>
                <h1>📈 全球股市匯市自動日報</h1>
                <p class="update-time">更新時間: {datetime.now().strftime('%Y-%m-%d %H:%M')}</p>
            </header>

            <div class="market-grid">
                {cards_html}
            </div>

            <div class="news-grid">
                <div class="news-col">
                    <h3>🇹🇼 台灣焦點</h3>
                    {make_news_list(news_tw)}
                </div>
                <div class="news-col">
                    <h3>🇺🇸 美國焦點</h3>
                    {make_news_list(news_us)}
                </div>
                <div class="news-col">
                    <h3>🇯🇵 日本焦點</h3>
                    {make_news_list(news_jp)}
                </div>
            </div>
        </div>
    </body>
    </html>
    """
    
    with open(HTML_FILENAME, "w", encoding="utf-8") as f:
        f.write(full_html)
    print(f"成功！已生成網頁：{os.path.abspath(HTML_FILENAME)}")

if __name__ == "__main__":
    market_data = get_market_data()
    news_tw = get_news('TW')
    news_us = get_news('US')
    news_jp = get_news('JP')
    generate_html(market_data, news_tw, news_us, news_jp)