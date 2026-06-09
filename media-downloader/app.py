from flask import Flask, render_template, request, jsonify
import yt_dlp
import os

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

    # ตั้งค่าตัวเจาะข้อมูล (ดึงแค่ลิงก์ ไม่โหลดลงเครื่อง)
    ydl_opts = {
        'quiet': True,
        'no_warnings': True,
        'extract_flat': False,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            media_list = []

            # ถ้าเป็นโพสต์ที่มีหลายรูป/วิดีโอ (อัลบั้ม IG)
            if 'entries' in info:
                for entry in info['entries']:
                    media_list.append({
                        'type': 'video' if entry.get('ext') == 'mp4' else 'image',
                        'thumbnail': entry.get('thumbnail'),
                        'url': entry.get('url') # ลิงก์ตรงสำหรับดาวน์โหลด
                    })
            else:
                # ถ้าเป็นไฟล์เดียว (TikTok หรือ IG โพสต์เดี่ยว)
                media_list.append({
                    'type': 'video' if info.get('ext') == 'mp4' else 'image',
                    'thumbnail': info.get('thumbnail'),
                    'url': info.get('url')
                })

            if not media_list:
                return jsonify({'error': 'ไม่พบสื่อ หรือบัญชีนี้ถูกตั้งเป็นส่วนตัว (Private)'}), 404

            return jsonify({'status': 'success', 'media': media_list})

    except Exception as e:
        return jsonify({'error': 'ดึงข้อมูลไม่สำเร็จ (บัญชีอาจเป็น Private หรือเซิร์ฟเวอร์ IG ปิดกั้น)'}), 500

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)