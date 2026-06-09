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
    
    if not url: return jsonify({'error': 'กรุณาใส่ลิงก์ที่ต้องการดาวน์โหลด'}), 400

    ydl_opts = {'quiet': True, 'no_warnings': True, 'extract_flat': False}

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            media_list = []

            # ฟังก์ชันจัดการดึงลิงก์ (แก้ปัญหารูปภาพไม่มีลิงก์)
            def parse_item(item):
                is_video = item.get('ext') == 'mp4' or item.get('vcodec') != 'none'
                m_type = 'video' if is_video else 'image'
                
                # พยายามหาลิงก์ไฟล์ที่ชัดที่สุด
                dl_url = item.get('url')
                if not dl_url and item.get('formats'):
                    dl_url = item['formats'][-1].get('url')
                if not dl_url and item.get('thumbnails'):
                    dl_url = item['thumbnails'][-1].get('url')
                    
                thumb = item.get('thumbnail')
                if not thumb and item.get('thumbnails'):
                    thumb = item['thumbnails'][-1].get('url')
                    
                return {'type': m_type, 'thumbnail': thumb or dl_url, 'url': dl_url}

            # ดึงข้อมูล
            if 'entries' in info:
                for entry in info['entries']:
                    media_list.append(parse_item(entry))
            else:
                media_list.append(parse_item(info))

            # กรองอันที่หาลิงก์ไม่ได้ออก
            media_list = [m for m in media_list if m['url']]

            if not media_list:
                return jsonify({'error': 'ไม่พบสื่อ (อาจเป็น Highlight/Story หรือบัญชี Private)'}), 404

            return jsonify({'status': 'success', 'media': media_list})

    except Exception as e:
        return jsonify({'error': 'ระบบถูก IG ปิดกั้นการเข้าถึง หรือลิงก์ไม่ถูกต้อง'}), 500

# ระบบตัวกลางสำหรับบังคับให้เบราว์เซอร์ดาวน์โหลดไฟล์ลงเครื่อง
@app.route('/download-direct')
def download_direct():
    url = request.args.get('url')
    media_type = request.args.get('type', 'image')
    if not url: return "No URL", 400
    
    try:
        req = requests.get(url, stream=True)
        ext = 'mp4' if media_type == 'video' else 'jpg'
        return Response(
            req.iter_content(chunk_size=1024),
            headers={
                'Content-Disposition': f'attachment; filename="media_{os.urandom(4).hex()}.{ext}"',
                'Content-Type': req.headers.get('content-type')
            }
        )
    except Exception as e:
        return str(e), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)