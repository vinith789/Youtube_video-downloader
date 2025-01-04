from flask import Flask, request, jsonify, render_template
import yt_dlp
import os

app = Flask(__name__)

# Default storage directory
DEFAULT_DIRECTORY = "My_youtube"

# Progress tracker
progress = {
    "status": "idle",
    "speed": "0 KB/s",
    "total_size": "0 MB",
    "downloaded_size": "0 MB",
    "time_remaining": "0s",
    "file_name": "unknown",
}


# Update progress during download
def progress_hook(d):
    if d['status'] == 'downloading':
        progress['status'] = "Downloading"
        progress['speed'] = d.get('_speed_str', "0 KB/s")
        total_bytes = d.get('total_bytes', d.get('total_bytes_estimate', 0))
        progress['total_size'] = f"{round(total_bytes / 1024**2, 2)} MB" if total_bytes else "Unknown size"
        progress['downloaded_size'] = f"{round(d.get('downloaded_bytes', 0) / 1024**2, 2)} MB"
        progress['time_remaining'] = f"{d.get('eta', 0)}s"

        filename = d.get('filename')
        progress['file_name'] = filename.split(os.sep)[-1] if filename else "unknown"
    elif d['status'] == 'finished':
        progress['status'] = "Finished"



# Serve the main page
@app.route('/')
def index():
    return render_template('index.html')

# Provide progress updates
@app.route('/status', methods=['GET'])
def check_status():
    return jsonify(progress)

# Handle download requests
# Reset progress to default values
def reset_progress():
    global progress
    progress = {
        "status": "idle",
        "speed": "0 KB/s",
        "total_size": "0 MB",
        "downloaded_size": "0 MB",
        "time_remaining": "0s",
        "file_name": "unknown",
    }

# Handle download requests
@app.route('/download', methods=['POST'])
def download():
    reset_progress()  # Reset progress before starting a new download

    data = request.get_json()
    video_url = data.get('videoUrl', '').strip()
    video_quality = data.get('videoQuality', '').strip()

    if not video_url or not video_quality:
        return jsonify({'message': 'Invalid input'}), 400

    try:
        if not os.path.exists(DEFAULT_DIRECTORY):
            os.makedirs(DEFAULT_DIRECTORY)

        # Temporary yt-dlp options to extract video metadata
        metadata_opts = {
            'format': video_quality,
            'simulate': True,
            'quiet': True,
            'skip_download': True,
            'force_generic_extractor': False,
        }

        # Extract video information to get the title and format_id
        with yt_dlp.YoutubeDL(metadata_opts) as ydl:
            info = ydl.extract_info(video_url, download=False)
            video_title = info.get('title', 'Unknown Title')
            video_format_id = video_quality  # The selected quality

        # Construct the expected filename
        filename = f"{video_title} [{video_format_id}].mp4"
        file_path = os.path.join(DEFAULT_DIRECTORY, filename)

        # Check if the exact file already exists
        if os.path.exists(file_path):
            return jsonify({'message': 'File with the same quality already exists'}), 409  # Conflict status

        # Configure yt-dlp options for actual download
        ydl_opts = {
            'format': video_quality,  # Selected quality from the frontend
            'outtmpl': os.path.join(DEFAULT_DIRECTORY, '%(title)s [%(format_id)s].%(ext)s'),
            'merge_output_format': 'mp4',
            'progress_hooks': [progress_hook],
            'postprocessors': [
                {'key': 'FFmpegVideoConvertor', 'preferedformat': 'mp4'},
            ],
        }

        # Start the download in a new thread to allow progress updates
        from threading import Thread

        def download_video():
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                ydl.download([video_url])

        Thread(target=download_video).start()

        return jsonify({'message': 'Download started'})

    except Exception as e:
        return jsonify({'message': f'Error during download: {str(e)}'}), 500

if __name__ == "__main__":
    app.run(debug=True)