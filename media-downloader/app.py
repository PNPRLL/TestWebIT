from flask import Flask, render_template, request, jsonify, Response
import yt_dlp
import os
import requests

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/extract', methods=['POST'])
def extract_media():
    data = request.json
    url = data.get('url')
    
    if not url:
        return jsonify({'error': 'กรุณาใส่ลิงก์ที่ต้องการดาวน์โหลด'}), 400

    # 🕵️‍♂️ ตั้งค่าพรางตัวเป็นเบราว์เซอร์ทั่วไป เพื่อแก้ปัญหา Login Wall ของ IG บนเซิร์ฟเวอร์ Cloud
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'extract_flat': False,
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Sec-Fetch-Mode': 'navigate',
        }
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            media_list = []

            # ฟังก์ชันช่วยแกะลิงก์รูปภาพและวิดีโอให้แม่นยำ
            def parse_item(item):
                is_video = item.get('ext') == 'mp4' or item.get('vcodec') != 'none'
                m_type = 'video' if is_video else 'image'
                
                # ค้นหาลิงก์ตรงสำหรับดาวน์โหลดไฟล์ดิบ
                dl_url = item.get('url')
                if not dl_url and item.get('formats'):
                    dl_url = item['formats'][-1].get('url')
                if not dl_url and item.get('thumbnails'):
                    dl_url = item['thumbnails'][-1].get('url')
                    
                # ค้นหารูปภาพพรีวิว (Thumbnail)
                thumb = item.get('thumbnail')
                if not thumb and item.get('thumbnails'):
                    thumb = item['thumbnails'][-1].get('url')
                    
                return {'type': m_type, 'thumbnail': thumb or dl_url, 'url': dl_url}

            # ตรวจสอบว่าเป็นอัลบั้มภาพกลุ่ม (entries) หรือโพสต์เดี่ยว
            if 'entries' in info:
                for entry in info['entries']:
                    parsed = parse_item(entry)
                    if parsed['url']:
                        media_list.append(parsed)
            else:
                parsed = parse_item(info)
                if parsed['url']:
                    media_list.append(parsed)

            if not media_list:
                return jsonify({'error': 'ไม่พบสื่อ หรือระบบถูกปิดกั้นการเข้าถึง'}), 404

            return jsonify({'status': 'success', 'media': media_list})

    except Exception as e:
        return jsonify({'error': 'ดึงข้อมูลไม่สำเร็จ (IG ปิดกั้น IP ของเซิร์ฟเวอร์ หรือลิงก์ไม่ถูกต้อง)'}), 500

# 📥 ระบบตัวกลางดาวน์โหลดตรง (แก้ปัญหาลิ้งก์ภาพหาย/ช่วยบังคับเซฟลงเครื่องทันที)
@app.route('/download-direct')
def download_direct():
    url = request.args.get('url')
    media_type = request.args.get('type', 'image')
    if not url:
        return "No URL provided", 400
    
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36'
        }
        req = requests.get(url, headers=headers, stream=True)
        ext = 'mp4' if media_type == 'video' else 'jpg'
        
        return Response(
            req.iter_content(chunk_size=1024),
            headers={
                'Content-Disposition': f'attachment; filename="download_{os.urandom(4).hex()}.{ext}"',
                'Content-Type': req.headers.get('content-type')
            }
        )
    except Exception as e:
        return f"Error: {str(e)}", 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)