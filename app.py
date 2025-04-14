from flask import Flask, render_template, request
import requests
import re
import os
from collections import defaultdict

app = Flask(__name__)

def get_file_type(url):
    ext = os.path.splitext(url.split('?')[0])[1].lower()
    if ext in ['.mp4', '.mkv', '.webm', '.m4v', '.mov', '.flv']:
        return '视频'
    elif ext in ['.mp3', '.wav', '.m4a', '.aac', '.ogg', '.flac']:
        return '音频'
    elif ext in ['.srt']:
        return '字幕'
    elif ext in ['.json']:
        return 'JSON'
    else:
        return '其他'

def count_files_by_type(urls):
    counts = defaultdict(int)
    for url in urls:
        file_type = get_file_type(url)
        counts[file_type] += 1
    return counts

def format_group_count(urls):
    counts = count_files_by_type(urls)
    # 按特定顺序显示文件类型
    order = ['音频', '视频', 'JSON', '字幕', '其他']
    parts = []
    
    for file_type in order:
        if counts[file_type] > 0:
            parts.append(f"{counts[file_type]}{file_type}")
    
    return '/'.join(parts) if parts else "0个链接"

def extract_urls_from_page(url):
    try:
        response = requests.get(url, timeout=10)
        return re.findall(r'(https?://[^\s<>"\']+)', response.text)
    except Exception as e:
        return []

def extract_and_group_urls(url, groups, key):
    """提取URL并按组分类"""
    if not url:
        return
        
    found_urls = extract_urls_from_page(url)
    for found_url in found_urls:
        match = re.search(r'/(\d+_\d+)/', found_url)
        group_name = match.group(1) if match else '其他'
        groups[group_name][key].append(found_url)

@app.route('/', methods=['GET', 'POST'])
def index():
    file_types = {}
    selected_group = request.form.get('group_select') if request.method == 'POST' else None
    url1 = request.form.get('url1') if request.method == 'POST' else ""
    url2 = request.form.get('url2') if request.method == 'POST' else ""
    is_group_select = request.form.get('is_group_select') == 'true'
    
    groups = defaultdict(lambda: {'url1': [], 'url2': []})
    
    if url1 or url2:
        # 处理两个URL的提取和分组
        extract_and_group_urls(url1, groups, 'url1')
        extract_and_group_urls(url2, groups, 'url2')
        
        all_groups = sorted(groups.keys())
        if all_groups:
            selected_group = selected_group or all_groups[0]
            
            # 处理所选组的文件类型
            all_urls = groups[selected_group]['url1'] + groups[selected_group]['url2']
            for url in all_urls:
                file_type = get_file_type(url)
                if file_type not in file_types:
                    file_types[file_type] = []
                file_types[file_type].append(url)
    
    # 定义标签顺序
    tab_order = ['视频', 'JSON', '字幕', '音频']
    
    # 确定默认活动标签
    # 如果是组选择请求，优先选择"视频"标签
    active_tab = request.form.get('active_tab')
    if is_group_select:
        # 组选择后优先选择"视频"标签
        active_tab = '视频' if '视频' in file_types and file_types['视频'] else None
    
    # 如果没有活动标签或组选择请求重置标签
    if not active_tab:
        if url1 or url2:
            # 按指定顺序查找第一个有内容的标签
            for tab in tab_order:
                if tab in file_types and file_types[tab]:
                    active_tab = tab
                    break
        # 如果没有找到有内容的标签或没有URL，使用第一个标签
        active_tab = active_tab or tab_order[0]
    
    return render_template('index.html', 
                         grouped_links=groups,
                         all_groups=sorted(groups.keys()),
                         selected_group=selected_group,
                         file_types=file_types,
                         active_tab=active_tab,
                         tab_order=tab_order,
                         url1=url1,
                         url2=url2,
                         format_group_count=format_group_count)

@app.route('/proxy')
def proxy():
    url = request.args.get('url')
    if not url:
        return "缺少URL参数"
        
    try:
        response = requests.get(url, timeout=10)
        
        # 获取内容类型
        content_type = response.headers.get('Content-Type', '')
        
        # 如果是字幕文件(srt)或文本文件，返回二进制内容，让前端处理编码
        if url.lower().endswith('.srt') or 'text/' in content_type:
            return response.content, 200, {
                'Content-Type': 'application/octet-stream',
                'Access-Control-Allow-Origin': '*'
            }
        
        # 其他文件类型直接返回文本内容
        return response.text
    except Exception as e:
        return f"获取内容失败: {str(e)}"

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=8080)