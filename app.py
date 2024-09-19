from flask import Flask, render_template, request, send_file, jsonify
import yt_dlp
import qrcode
import os
from io import BytesIO
from PyPDF2 import PdfMerger
from PIL import Image
import barcode
from barcode.writer import ImageWriter
import instaloader

app = Flask(__name__)

# Path where videos will be temporarily saved
DOWNLOAD_FOLDER = os.path.join(os.path.expanduser("~"), "Downloads")
download_progress = 0  # Global variable to store download progress percentage

# Specify the path to FFmpeg
FFMPEG_LOCATION = 'C:/ffmpeg/'  # Ensure this is the correct path to your FFmpeg installation


# YouTube Downloader (MP4 and MP3)
@app.route('/')
def index():
    return render_template('index.html')


@app.route('/download', methods=['POST'])
def download_video():
    global download_progress
    url = request.form['url']
    download_progress = 0  # Reset progress at the start of the download

    def progress_hook(d):
        global download_progress
        if d['status'] == 'downloading':
            total_bytes = d.get('total_bytes', 0)
            downloaded_bytes = d.get('downloaded_bytes', 0)
            if total_bytes > 0:
                download_progress = int(downloaded_bytes / total_bytes * 100)

    try:
        ydl_opts = {
            'outtmpl': os.path.join(DOWNLOAD_FOLDER, '%(title)s.%(ext)s'),
            'progress_hooks': [progress_hook],
            'ffmpeg_location': FFMPEG_LOCATION  # Set the correct FFmpeg location
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(url, download=True)
            video_title = info_dict.get('title', None)
            video_ext = info_dict.get('ext', None)
            file_path = os.path.join(DOWNLOAD_FOLDER, f"{video_title}.{video_ext}")
        
        return send_file(file_path, as_attachment=True)

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/progress')
def get_progress():
    global download_progress
    return jsonify({'progress': download_progress})


@app.route('/download-mp3', methods=['POST'])
def download_mp3():
    url = request.form['url']
    
    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'outtmpl': os.path.join(DOWNLOAD_FOLDER, '%(title)s.%(ext)s'),
        'ffmpeg_location': FFMPEG_LOCATION  # Set the correct FFmpeg location
    }
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
            info_dict = ydl.extract_info(url, download=True)
            file_path = os.path.join(DOWNLOAD_FOLDER, f"{info_dict['title']}.mp3")

        return send_file(file_path, as_attachment=True)

    except Exception as e:
        return jsonify({'error': str(e)}), 500


# QR Code Generator
@app.route('/qr-scanner')
def qr_scanner():
    return render_template('qr_scanner.html')


@app.route('/generate-qr', methods=['POST'])
def generate_qr():
    data = request.form['data']
    qr_img = qrcode.make(data)
    
    img_io = BytesIO()
    qr_img.save(img_io, 'PNG')
    img_io.seek(0)

    return send_file(img_io, mimetype='image/png', as_attachment=True, download_name='qrcode.png')


# PDF Merger
@app.route('/pdf-merger')
def pdf_merger():
    return render_template('pdf_merger.html')


@app.route('/merge-pdfs', methods=['POST'])
def merge_pdfs():
    pdf_files = request.files.getlist('pdfs')
    merger = PdfMerger()

    for pdf in pdf_files:
        merger.append(pdf)

    merged_pdf = BytesIO()
    merger.write(merged_pdf)
    merged_pdf.seek(0)
    
    return send_file(merged_pdf, as_attachment=True, download_name='merged.pdf', mimetype='application/pdf')


# Image Compressor
@app.route('/image-compressor')
def image_compressor():
    return render_template('image_compressor.html')


@app.route('/compress-image', methods=['POST'])
def compress_image():
    image = Image.open(request.files['image'])
    img_io = BytesIO()

    # Compress image to reduce quality
    image.save(img_io, format='JPEG', quality=20)
    img_io.seek(0)

    return send_file(img_io, as_attachment=True, download_name='compressed_image.jpg', mimetype='image/jpeg')


# Barcode Generator
@app.route('/barcode-generator')
def barcode_generator():
    return render_template('barcode_generator.html')


@app.route('/generate-barcode', methods=['POST'])
def generate_barcode():
    code = request.form['code']
    barcode_format = request.form.get('format', 'ean13')  # You can use different barcode formats

    BARCODE_CLASS = barcode.get_barcode_class(barcode_format)
    barcode_obj = BARCODE_CLASS(code, writer=ImageWriter())

    img_io = BytesIO()
    barcode_obj.write(img_io)
    img_io.seek(0)

    return send_file(img_io, as_attachment=True, download_name='barcode.png', mimetype='image/png')


# Instagram Reel Downloader
@app.route('/instagram-downloader')
def instagram_downloader():
    return render_template('instagram_downloader.html')


@app.route('/download-instagram', methods=['POST'])
def download_instagram():
    url = request.form['url']
    
    loader = instaloader.Instaloader()
    shortcode = url.split("/")[-2]
    
    try:
        loader.download_post(instaloader.Post.from_shortcode(loader.context, shortcode), target="downloads")
        return "Reel downloaded successfully!"
    except Exception as e:
        return str(e)


# Images to PDF Converter
@app.route('/images-to-pdf')
def images_to_pdf():
    return render_template('images_to_pdf.html')


@app.route('/convert-images-to-pdf', methods=['POST'])
def convert_images_to_pdf():
    image_files = request.files.getlist('images')
    img_list = [Image.open(img) for img in image_files]

    pdf_io = BytesIO()
    img_list[0].save(pdf_io, save_all=True, append_images=img_list[1:], format='PDF')
    pdf_io.seek(0)

    return send_file(pdf_io, as_attachment=True, download_name='images_to_pdf.pdf', mimetype='application/pdf')


if __name__ == '__main__':
    app.run(debug=True)
