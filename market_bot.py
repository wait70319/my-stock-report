import yfinance as yf
import feedparser
import pandas as pd
import numpy as np
from datetime import datetime
import os

HTML_FILENAME = "index.html"

# 1. 核心追蹤清單 (已加入日圓換美元)
ASSETS = {
    '🇺🇸 標普 500': '^GSPC',
    '🇹🇼 台灣加權': '^TWII',
    '🇯🇵 日經 225': '^N225',
    '💴 日圓換美元 (JPY/USD)': 'JPYUSD=X',  # 新增這一行
    '💵 美元指數 (DXY)': 'DX-Y.NYB',
    '📉 美債10年殖利率': '^TNX',
    '😨 恐慌指數 (VIX)': '^VIX',
    '🔥 台積電 (TSM)': 'TSM',
    '⚡ 核能龍頭 (CEG)': 'CEG',
    '💊 禮來製藥 (LLY)': 'LLY'
}

# 2. 定義新聞關鍵字
NEWS_RSS = {
    '📈 宏觀市場': 'https://news.google.com/rss/search?q=Federal+Reserve+OR+Inflation+when:1d&hl=en-US&gl=US&ceid=US:en',
    '🤖 AI 與半導體': 'https://news.google.com/rss/search?q=TSMC+OR+NVIDIA+OR+ASML+when:1d&hl=en-US&gl=US&ceid=US:en',
    '🇹🇼 台股焦點': 'https://news.google.com/rss/search?q=台股+OR+外資+when:1d&hl=zh-TW&gl=TW&ceid=TW:zh-Hant'
}

# 計算 RSI 指標
def calculate_rsi(series, period=14):
    delta = series.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def get_market_data():
    data = []
    print("正在進行深度數據分析...")
    
    for name, ticker in ASSETS.items():
        try:
            stock = yf.Ticker(ticker)
            hist = stock.history(period="1mo")
            
            if len(hist) < 20: continue

            price = hist['Close'].iloc[-1]
            prev = hist['Close'].iloc[-2]
            change = ((price - prev) / prev) * 100
            
            ma20 = hist['Close'].tail(20).mean()
            rsi = calculate_rsi(hist['Close']).iloc[-1]
            
            trend = "多頭排列 🐂" if price > ma20 else "跌破月線 🐻"
            rsi_signal = "過熱 🔥" if rsi > 70 else "超賣 🧊" if rsi < 30 else "中性 😐"
            
            # 顏色設定 (漲紅跌綠)
            color = "red" if change > 0 else "green"
            if name in ['😨 恐慌指數 (VIX)', '📉 美債10年殖利率']:
                color = "green" if change > 0 else "red" 

            data.append({
                "name": name,
                "price": f"{price:,.4f}" if "USD" in name else f"{price:,.2f}", # 匯率顯示多一點小數點
                "change": f"{change:+.2f}%",
                "color": color,
                "ma20_diff": f"{(price - ma20)/ma20*100:+.1f}%",
                "trend": trend,
                "rsi": f"{rsi:.1f} ({rsi_signal})"
            })
        except Exception as e:
            print(f"Error {name}: {e}")
    return data

def get_news():
    news_data = {}
    for category, url in NEWS_RSS.items():
        try:
            feed = feedparser.parse(url)
            news_data[category] = feed.entries[:4]
        except:
            continue
    return news_data

def generate_html(market_data, news_data):
    html = f"""
    <!DOCTYPE html>
    <html lang="zh-TW">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>深度投資日報</title>
        <style>
            body {{ font-family: 'Segoe UI', sans-serif; background: #1a1a1a; color: #e0e0e0; padding: 20px; }}
            .container {{ max-width: 1200px; margin: 0 auto; }}
            h1, h2 {{ color: #ffffff; border-bottom: 2px solid #333; padding-bottom: 10px; }}
            table {{ width: 100%; border-collapse: collapse; margin-bottom: 30px; background: #252525; }}
            th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #333; }}
            th {{ background: #333; color: #aaa; }}
            .red {{ color: #ff6b6b; font-weight: bold; }}
            .green {{ color: #4ecdc4; font-weight: bold; }}
            .news-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(350px, 1fr)); gap: 20px; }}
            .news-card {{ background: #252525; padding: 15px; border-radius: 8px; border: 1px solid #333; }}
            .news-card h3 {{ margin-top: 0; color: #4dabf7; }}
            .news-item a {{ color: #e0e0e0; text-decoration: none; display: block; margin-bottom: 10px; border-bottom: 1px dashed #444; padding-bottom: 5px; }}
            .news-item a:hover {{ color: #ffeb3b; }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>📊 深度市場量化日報 (Pro)</h1>
            <p>更新時間: {datetime.now().strftime('%Y-%m-%d %H:%M')}</p>
            
            <h2>⚡ 市場核心數據</h2>
            <table>
                <tr>
                    <th>資產</th>
                    <th>價格</th>
                    <th>漲跌幅</th>
                    <th>RSI 強度</th>
                    <th>趨勢</th>
                    <th>乖離率</th>
                </tr>
                {"".join([f'''
                <tr>
                    <td>{d['name']}</td>
                    <td>{d['price']}</td>
                    <td class="{d['color']}">{d['change']}</td>
                    <td>{d['rsi']}</td>
                    <td>{d['trend']}</td>
                    <td>{d['ma20_diff']}</td>
                </tr>
                ''' for d in market_data])}
            </table>

            <h2>📰 深度情報掃描</h2>
            <div class="news-grid">
                {"".join([f'''
                <div class="news-card">
                    <h3>{cat}</h3>
                    {"".join([f'<div class="news-item"><a href="{n.link}" target="_blank">{n.title}</a></div>' for n in news_list])}
                </div>
                ''' for cat, news_list in news_data.items()])}
            </div>
        </div>
    </body>
    </html>
    """
    with open(HTML_FILENAME, "w", encoding="utf-8") as f:
        f.write(html)

if __name__ == "__main__":
    data = get_market_data()
    news = get_news()
    generate_html(data, news)
