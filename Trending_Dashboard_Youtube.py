import os
import requests
import webbrowser
import json
import xml.etree.ElementTree as ET
import pandas as pd
from pytrends.request import TrendReq
from datetime import datetime

# ==========================================
# CONFIGURATION
# ==========================================
YOUTUBE_API_KEY = "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
COUNTRY_CODE = "US" 
TIMEZONE_OFFSET = 330  

def get_realtime_searches():
    print("Fetching real-time Google search trends...")
    try:
        # 1. Attempt using PyTrends with Browser Headers to bypass Bot Detection
        browser_headers = {
            'headers': {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/108.0.0.0 Safari/537.36'
            }
        }
        pytrends = TrendReq(hl='en-US', tz=TIMEZONE_OFFSET, requests_args=browser_headers)
        df = pytrends.realtime_trending_searches(pn=COUNTRY_CODE)
        
        trends = []
        for index, row in df.head(10).iterrows():
            entities = row.get('entityNames', [])
            entity_str = ", ".join(entities) if isinstance(entities, list) else str(entities)
            
            urls = row.get('articleUrls', ['#'])
            target_url = urls[0] if isinstance(urls, list) and len(urls) > 0 else '#'
            
            trends.append({
                "title": row.get('title', 'Unknown Topic'),
                "desc": f"Keywords: {entity_str}",
                "url": target_url
            })
        return trends
    except Exception as e:
        print(f"PyTrends limit reached. Engaging RSS Failsafe...")
        # 2. Failsafe: Use Google Trends RSS if PyTrends throws a 429 Too Many Requests error
        try:
            rss_url = f"https://trends.google.com/trending/rss?geo={COUNTRY_CODE}"
            response = requests.get(rss_url, headers={'User-Agent': 'Mozilla/5.0'})
            root = ET.fromstring(response.content)
            
            trends = []
            for item in root.findall('./channel/item')[:10]:
                title = item.find('title').text
                link = item.find('link').text
                
                # Extract approximate search volume traffic from RSS
                traffic_elem = item.find('{https://trends.google.com/rss/namespace}approx_traffic')
                traffic = traffic_elem.text if traffic_elem is not None else "High Traffic"
                
                trends.append({
                    "title": title,
                    "desc": f"Search Volume: {traffic}",
                    "url": link
                })
            return trends
        except Exception as ex:
            print(f"Error fetching RSS: {ex}")
            return []

def get_youtube_trending():
    print("Fetching top 20 YouTube trending videos...")
    if YOUTUBE_API_KEY == "YOUR_API_KEY_HERE":
        print("No YouTube API Key detected. Please insert your key.")
        return []

    # maxResults changed to 20
    url = f"https://www.googleapis.com/youtube/v3/videos?part=snippet,statistics&chart=mostPopular&regionCode={COUNTRY_CODE}&maxResults=20&key={YOUTUBE_API_KEY}"
    try:
        response = requests.get(url)
        data = response.json()
        videos = []
        for item in data.get('items', []):
            # Fetching a smaller medium-sized thumbnail for the grid layout
            thumbnails = item['snippet']['thumbnails']
            thumb_url = thumbnails.get('medium', thumbnails.get('default'))['url']
            
            raw_views = int(item['statistics'].get('viewCount', 0))
            
            videos.append({
                "title": item['snippet']['title'],
                "channel": item['snippet']['channelTitle'],
                "raw_views": raw_views, 
                "views": f"{raw_views:,}",
                "thumbnail": thumb_url,
                "link": f"https://www.youtube.com/watch?v={item['id']}"
            })
        return videos
    except Exception as e:
        print(f"Error fetching YouTube videos: {e}")
        return []

def generate_dashboard():
    searches = get_realtime_searches()
    videos = get_youtube_trending()
    
    current_time = datetime.now().strftime("%A, %B %d, %Y at %I:%M %p")

    # Data Preparation for Chart.js (Top 10 out of 20 videos for visual clarity)
    chart_labels = [v['title'][:25] + "..." for v in videos[:10]]
    chart_data = [v['raw_views'] for v in videos[:10]]

    # Search Trends HTML
    search_html = ""
    for s in searches:
        search_html += f"""
        <div class="bg-gray-800/50 backdrop-blur-sm p-4 rounded-xl border border-gray-700/50 hover:bg-gray-700/50 transition-colors">
            <h3 class="font-bold text-md text-blue-400 mb-1 truncate">
                <a href="{s['url']}" target="_blank">{s['title']}</a>
            </h3>
            <p class="text-xs text-gray-400 truncate">{s['desc']}</p>
        </div>
        """

    # 20 YouTube Videos HTML (Smaller Thumbnails Layout)
    video_html = ""
    for v in videos:
        video_html += f"""
        <a href="{v['link']}" target="_blank" class="block bg-gray-800/80 rounded-lg overflow-hidden border border-gray-700 hover:border-red-500/50 transition-all transform hover:-translate-y-1 hover:shadow-[0_0_15px_rgba(239,68,68,0.3)]">
            <img src="{v['thumbnail']}" alt="Thumbnail" class="w-full h-32 object-cover">
            <div class="p-3">
                <h3 class="font-semibold text-sm mb-1 truncate text-gray-100" title="{v['title']}">{v['title']}</h3>
                <p class="text-xs text-gray-400 truncate">{v['channel']}</p>
                <p class="text-[10px] text-red-400 font-bold mt-1 tracking-wider">{v['views']} VIEWS</p>
            </div>
        </a>
        """

    # Assemble final HTML Document
    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Real-Time Live Dashboard</title>
        <script src="https://cdn.tailwindcss.com"></script>
        <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
        <style>
            body {{ background-color: #0f172a; color: #f8fafc; }}
            ::-webkit-scrollbar {{ width: 8px; }}
            ::-webkit-scrollbar-track {{ background: #0f172a; }}
            ::-webkit-scrollbar-thumb {{ background: #334155; border-radius: 4px; }}
        </style>
    </head>
    <body class="p-4 md:p-8 font-sans antialiased bg-[radial-gradient(ellipse_at_top_right,_var(--tw-gradient-stops))] from-slate-900 via-[#0f172a] to-slate-900 min-h-screen">
        
        <!-- Header -->
        <header class="mb-8 flex flex-col md:flex-row justify-between items-center border-b border-gray-700/50 pb-6">
            <div>
                <h1 class="text-3xl md:text-4xl font-black text-transparent bg-clip-text bg-gradient-to-r from-cyan-400 to-purple-500 mb-1">
                    LIVE TRENDS PULSE
                </h1>
                <p class="text-gray-400 text-xs md:text-sm">Real-time data synchronized for {COUNTRY_CODE} • Last updated: {current_time}</p>
            </div>
            <div class="mt-4 md:mt-0 flex items-center space-x-2 bg-gray-800/50 px-4 py-2 rounded-full border border-gray-700/50">
                <div class="w-2 h-2 rounded-full bg-green-500 animate-pulse"></div>
                <span class="text-xs font-semibold text-green-400 tracking-widest uppercase">System Online</span>
            </div>
        </header>

        <!-- Main Dashboard Grid -->
        <main class="grid grid-cols-1 lg:grid-cols-12 gap-8">
            
            <!-- Left Column: Search Trends & Chart -->
            <section class="lg:col-span-4 flex flex-col gap-8">
                
                <!-- Chart Section -->
                <div class="bg-gray-800/30 rounded-2xl p-6 border border-gray-700/50 shadow-xl relative overflow-hidden">
                    <div class="absolute top-0 right-0 w-32 h-32 bg-purple-500/10 rounded-full blur-3xl"></div>
                    <h2 class="text-lg font-bold text-gray-200 mb-4 flex items-center">
                        <svg class="w-5 h-5 mr-2 text-purple-400" fill="currentColor" viewBox="0 0 20 20"><path d="M2 10a8 8 0 018-8v8h8a8 8 0 11-16 0z"></path><path d="M12 2.252A8.014 8.014 0 0117.748 8H12V2.252z"></path></svg>
                        Top 10 Video Views Share
                    </h2>
                    <div class="w-full h-64 flex justify-center">
                        <canvas id="viewsChart"></canvas>
                    </div>
                </div>

                <!-- Real-Time Searches List -->
                <div>
                    <h2 class="text-xl font-bold text-gray-200 mb-4 flex items-center">
                        <svg class="w-5 h-5 mr-2 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"></path></svg>
                        Trending Keywords
                    </h2>
                    <div class="space-y-3">
                        {search_html if searches else "<p class='text-gray-500 text-sm italic'>Unable to fetch search data.</p>"}
                    </div>
                </div>
            </section>

            <!-- Right Column: Top 20 YouTube Videos -->
            <section class="lg:col-span-8">
                <div class="flex items-center mb-6">
                    <svg class="w-6 h-6 mr-2 text-red-500" fill="currentColor" viewBox="0 0 24 24"><path d="M19.615 3.184c-3.604-.246-11.631-.245-15.23 0-3.897.266-4.356 2.62-4.385 8.816.029 6.185.484 8.549 4.385 8.816 3.6.245 11.626.246 15.23 0 3.897-.266 4.356-2.62 4.385-8.816-.029-6.185-.484-8.549-4.385-8.816zm-10.615 12.816v-8l8 3.993-8 4.007z"/></svg>
                    <h2 class="text-2xl font-bold text-gray-200">Top 20 Trending Videos</h2>
                </div>
                <!-- 4 Columns on large screens, 2 on small screens -->
                <div class="grid grid-cols-2 md:grid-cols-3 xl:grid-cols-4 gap-4">
                    {video_html if videos else "<p class='text-gray-500 text-sm italic col-span-full'>No video data available. Did you add your API key?</p>"}
                </div>
            </section>
        </main>

        <!-- Chart.js Injection -->
        <script>
            const ctx = document.getElementById('viewsChart').getContext('2d');
            const data = {{
                labels: {json.dumps(chart_labels)},
                datasets: [{{
                    data: {json.dumps(chart_data)},
                    backgroundColor: [
                        '#ef4444', '#3b82f6', '#10b981', '#f59e0b', '#8b5cf6', 
                        '#ec4899', '#14b8a6', '#f97316', '#6366f1', '#84cc16'
                    ],
                    borderWidth: 0,
                    hoverOffset: 10
                }}]
            }};
            
            new Chart(ctx, {{
                type: 'doughnut',
                data: data,
                options: {{
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {{
                        legend: {{ display: false }},
                        tooltip: {{
                            backgroundColor: 'rgba(15, 23, 42, 0.9)',
                            titleFont: {{ size: 13 }},
                            bodyFont: {{ size: 12 }},
                            padding: 10,
                            callbacks: {{
                                label: function(context) {{
                                    let value = context.raw;
                                    return ' ' + value.toLocaleString() + ' Views';
                                }}
                            }}
                        }}
                    }},
                    cutout: '70%'
                }}
            }});
        </script>
    </body>
    </html>
    """

    filename = "trending_dashboard.html"
    with open(filename, "w", encoding="utf-8") as f:
        f.write(html_content)
    
    print("Dashboard generated successfully! Opening in browser...")
    webbrowser.open('file://' + os.path.realpath(filename))

if __name__ == "__main__":
    generate_dashboard()
