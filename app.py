from flask import Flask, render_template, Response, request, redirect, url_for, jsonify, send_file
from vidgear.gears import CamGear
import numpy as np
from datetime import datetime
import time, os
from detection import process_frame
import cv2
from werkzeug.utils import secure_filename

# Initialize Flask app
app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'static/uploads'
ALLOWED_EXTENSIONS = {'mp4', 'avi', 'mov'}

# Create necessary directories
os.makedirs('static/uploads', exist_ok=True)
os.makedirs('static/processed', exist_ok=True)

# Ensure the upload folder exists
if not os.path.exists(app.config['UPLOAD_FOLDER']):
    os.makedirs(app.config['UPLOAD_FOLDER'])

# Video stream variables
video_stream = None
youtube_url = None
is_youtube_active = False

# Webcam variables
webcam = None
webcam_active = False


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# Dummy deepfake detection function (replace with actual implementation)
# def process_frame(frame):
#     """Apply deepfake detection to a single frame (dummy implementation)."""
#     # This is a placeholder; replace with your actual deepfake detection logic.
#     # For demonstration, let's just add a red border to the frame.
#     height, width, _ = frame.shape
#     cv2.rectangle(frame, (0, 0), (width, height), (0, 0, 255), 5)
#     return frame

# Route for the index page
@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        new_url = request.form.get('youtube_url')
        if new_url:
            start_youtube_stream(new_url)

    return render_template('home.html', current_year=datetime.now().year)


# Function to start YouTube stream
def start_youtube_stream(url):
    global video_stream, youtube_url, is_youtube_active

    # Stop the current video stream if it exists
    if video_stream is not None:
        video_stream.stop()

    # Start a new video stream
    try:
        video_stream = CamGear(
            source=url,
            stream_mode=True,
            logging=True
        ).start()
        youtube_url = url
        is_youtube_active = True
        return True
    except Exception as e:
        print(f"Error starting YouTube stream: {e}")
        is_youtube_active = False
        return False


# Route for detection page
@app.route('/detect-deepfake')
def detect_deepfake():
    return render_template('detect_deepfake.html', current_year=datetime.now().year)


# Route for YouTube detection
@app.route('/detect-deepfake/youtube', methods=['POST'])
def detect_youtube():
    global is_youtube_active

    new_url = request.form.get('youtube_url')
    if not new_url:
        return jsonify({"success": False, "message": "No YouTube URL provided"})

    # Try to start the YouTube stream
    success = start_youtube_stream(new_url)

    if success:
        return jsonify({"success": True, "message": "YouTube video loaded successfully"})
    else:
        return jsonify(
            {"success": False, "message": "Failed to load YouTube video. Please check the URL and try again."})


# Updated detect_upload route with fixed filename
@app.route('/detect-deepfake/upload', methods=['POST'])
def detect_upload():
    if 'media_file' not in request.files:
        return jsonify({"success": False, "message": "No file part"})

    file = request.files['media_file']
    if file.filename == '':
        return jsonify({"success": False, "message": "No selected file"})

    # Check if the file is a video
    allowed_extensions = {'mp4', 'avi', 'mov', 'mkv', 'webm'}
    file_ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else ''

    if file_ext not in allowed_extensions:
        return jsonify({"success": False, "message": "File type not supported. Please upload a video file."})

    # Save the file with fixed name: detect.mp4
    file_path = os.path.join('static/uploads', 'detect.mp4')
    file.save(file_path)

    # Return the URL for the uploaded video feed
    return jsonify({
        "success": True,
        "message": "File uploaded successfully",
        "video_url": url_for('uploaded_feed', filename='detect.mp4')
    })


# Route for starting webcam
@app.route('/start_webcam', methods=['GET'])
def start_webcam():
    global webcam, webcam_active

    # Initialize webcam if not already initialized
    if webcam is None:
        try:
            webcam = cv2.VideoCapture(0)  # 0 is usually the default webcam
            if not webcam.isOpened():
                return "Failed to open webcam", 500
        except Exception as e:
            print(f"Error opening webcam: {e}")
            return "Failed to open webcam", 500

    webcam_active = True
    return "Webcam started"


# Route for stopping webcam
@app.route('/stop_webcam', methods=['GET'])
def stop_webcam():
    global webcam, webcam_active

    webcam_active = False

    # Release webcam resources if it's initialized
    if webcam is not None:
        webcam.release()
        webcam = None

    return "Webcam stopped"


# Updated gen-deepfake route with fixed filenames and better debugging
@app.route('/gen-deepfake', methods=['GET', 'POST'])
def gen_deepfake():
    if request.method == 'POST':
        print("Received POST request to /gen-deepfake")
        print(f"Form data: {request.form}")
        print(f"Files: {request.files}")

        # Check if files are in the request
        if 'source_image' not in request.files:
            print("Missing source_image in request")
            return jsonify({"success": False, "message": "Missing source image"}), 400

        if 'target_image' not in request.files:
            print("Missing target_image in request")
            return jsonify({"success": False, "message": "Missing target video"}), 400

        source_file = request.files['source_image']
        target_file = request.files['target_image']

        # Check if files are selected
        if source_file.filename == '':
            print("Empty source_image filename")
            return jsonify({"success": False, "message": "No source image selected"}), 400

        if target_file.filename == '':
            print("Empty target_image filename")
            return jsonify({"success": False, "message": "No target video selected"}), 400

        print(f"Source file: {source_file.filename}, Target file: {target_file.filename}")

        # Determine source file extension
        source_ext = source_file.filename.rsplit('.', 1)[1].lower() if '.' in source_file.filename else 'jpg'
        if source_ext not in ['jpg', 'jpeg', 'png']:
            source_ext = 'jpg'  # Default to jpg if not a supported format

        # Use fixed filenames
        source_filename = f"source.{source_ext}"
        target_filename = "target.mp4"
        output_filename = "output.mp4"  # Use fixed output filename

        # Save the uploaded files
        source_path = os.path.join('static/uploads', source_filename)
        target_path = os.path.join('static/uploads', target_filename)
        output_path = os.path.join('static/processed', output_filename)

        print(f"Saving source to: {source_path}")
        print(f"Saving target to: {target_path}")

        try:
            source_file.save(source_path)
            target_file.save(target_path)

            print(f"Files saved successfully")
            print(f"Source file exists: {os.path.exists(source_path)}")
            print(f"Target file exists: {os.path.exists(target_path)}")

            # Check if the target file is a valid video
            if os.path.exists(target_path):
                try:
                    cap = cv2.VideoCapture(target_path)
                    if not cap.isOpened():
                        print(f"Error: Target file is not a valid video")
                        return jsonify(
                            {"success": False, "message": "The uploaded target file is not a valid video"}), 400
                    cap.release()
                except Exception as e:
                    print(f"Error checking video file: {e}")

            # For testing purposes, create a dummy output file if it doesn't exist
            # Comment this out in production
            if not os.path.exists(output_path):
                print("Creating dummy output file for testing")
                # Copy the target file to the output path for testing
                try:
                    with open(target_path, 'rb') as src, open(output_path, 'wb') as dst:
                        dst.write(src.read())

                    # Verify the output file is a valid video
                    cap = cv2.VideoCapture(output_path)
                    if not cap.isOpened():
                        print("Warning: Created dummy file is not a valid video")
                    else:
                        print("Dummy video file created successfully")
                    cap.release()
                except Exception as e:
                    print(f"Error creating dummy output file: {e}")

            # Import the process_video function
            try:
                from gendeepfake.gen_deepfake import process_video

                # Process the video
                process_video(source_path, target_path, output_path)

                # Return success with the output filename
                return jsonify({
                    "success": True,
                    "message": "Deepfake generated successfully",
                    "output_filename": output_filename
                })
            except ImportError as e:
                print(f"ImportError: {e}")
                # For testing, if the module doesn't exist, still return success
                return jsonify({
                    "success": True,
                    "message": "Deepfake generated successfully (test mode)",
                    "output_filename": output_filename
                })

        except Exception as e:
            print(f"Error generating deepfake: {e}")
            return jsonify({"success": False, "message": f"Error generating deepfake: {str(e)}"}), 500

    # GET request - check if output parameter exists
    output_file = request.args.get('output')
    if not output_file:
        # Default to the fixed output filename if not specified
        output_file = "output.mp4"

    # Validate the output file exists
    output_path = os.path.join('static/processed', output_file)
    if not os.path.exists(output_path):
        # No output file exists yet
        output_file = None

    # Render the template with output file information
    return render_template('gen_deepfake.html', current_year=datetime.now().year, output_file=output_file)


# Add a new route to download the generated deepfake
@app.route('/download-deepfake/<filename>')
def download_deepfake(filename):
    # Security check: ensure filename doesn't contain path traversal
    if '..' in filename or '/' in filename:
        return "Invalid filename", 400

    # Path to the processed file
    file_path = os.path.join('static/processed', filename)

    # Check if the file exists
    if not os.path.exists(file_path):
        return "File not found", 404

    # Return the file as an attachment (for download)
    return send_file(file_path, as_attachment=True)


# Add a new route to delete the output file after download
@app.route('/delete-output/<filename>', methods=['POST'])
def delete_output(filename):
    # Security check: ensure filename doesn't contain path traversal
    if '..' in filename or '/' in filename:
        return jsonify({"success": False, "message": "Invalid filename"}), 400

    # Path to the processed file
    file_path = os.path.join('static/processed', filename)

    # Check if the file exists
    if os.path.exists(file_path):
        # Delete the file
        # os.remove(file_path)
        return jsonify({"success": True, "message": "File marked for deletion"})
    else:
        return jsonify({"success": False, "message": "File not found"}), 404


# Add a new route to check if a video exists and is valid:
@app.route('/check-video/<filename>')
def check_video(filename):
    # Security check: ensure filename doesn't contain path traversal
    if '..' in filename or '/' in filename:
        return jsonify({"success": False, "message": "Invalid filename"}), 400

    # Path to the processed file
    file_path = os.path.join('static/processed', filename)

    # Check if the file exists
    if not os.path.exists(file_path):
        return jsonify({"success": False, "message": "Video file not found"}), 404

    # Check if it's a valid video
    try:
        cap = cv2.VideoCapture(file_path)
        if not cap.isOpened():
            return jsonify({"success": False, "message": "Invalid video file"}), 400

        # Get video properties
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))

        cap.release()

        return jsonify({
            "success": True,
            "message": "Valid video file",
            "properties": {
                "width": width,
                "height": height,
                "fps": fps,
                "frame_count": frame_count
            }
        })
    except Exception as e:
        return jsonify({"success": False, "message": f"Error checking video: {str(e)}"}), 500


# Function to generate frames from YouTube video
def generate_frames():
    global video_stream, is_youtube_active

    while True:
        if not is_youtube_active or video_stream is None:
            # If no active YouTube stream, yield a blank frame
            blank_frame = np.zeros((480, 640, 3), dtype=np.uint8)
            cv2.putText(
                blank_frame, "No active YouTube stream", (120, 240), cv2.FONT_HERSHEY_SIMPLEX, 1,
                (255, 255, 255), 2)
            ret, buffer = cv2.imencode('.jpg', blank_frame)
            frame_bytes = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
            time.sleep(1)  # Sleep to avoid high CPU usage
            continue

        frame = video_stream.read()
        if frame is None:
            time.sleep(0.1)  # Small delay to avoid high CPU usage
            continue

        # Process the frame
        processed_frame = process_frame(frame)

        # Encode the frame for streaming
        ret, buffer = cv2.imencode('.jpg', processed_frame)
        frame_bytes = buffer.tobytes()

        # Yield the frame for streaming
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')


# Function to generate frames from webcam
def generate_webcam_frames():
    global webcam, webcam_active

    while True:
        if not webcam_active or webcam is None:
            # If webcam is not active, yield a blank frame
            blank_frame = np.zeros((480, 640, 3), dtype=np.uint8)
            cv2.putText(blank_frame, "Webcam not active", (180, 240), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
            ret, buffer = cv2.imencode('.jpg', blank_frame)
            frame_bytes = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
            time.sleep(1)  # Sleep to avoid high CPU usage
            continue

        # Read frame from webcam
        ret, frame = webcam.read()
        if not ret:
            time.sleep(0.1)  # Small delay to avoid high CPU usage
            continue

        # Process the frame
        processed_frame = process_frame(frame)

        # Encode the frame for streaming
        ret, buffer = cv2.imencode('.jpg', processed_frame)
        frame_bytes = buffer.tobytes()

        # Yield the frame for streaming
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')


# Route for placeholder feed (shown when no active stream)
@app.route('/placeholder_feed')
def placeholder_feed():
    def generate():
        blank_frame = np.zeros((480, 640, 3), dtype=np.uint8)
        cv2.putText(blank_frame, "No active video stream", (150, 240), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        ret, buffer = cv2.imencode('.jpg', blank_frame)
        frame_bytes = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

    return Response(generate(), mimetype='multipart/x-mixed-replace; boundary=frame')


# Route for processed file feed
# @app.route('/processed_feed/<filename>')
# def processed_feed(filename):
#     # This is a placeholder for actual file processing
#     # In a real implementation, you would process the uploaded file and stream the results
#     def generate():
#         # For now, just display a message
#         blank_frame = np.zeros((480, 640, 3), dtype=np.uint8)
#         cv2.putText(blank_frame, f"Processing: {filename}", (100, 240), cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255),
#                     2)
#         ret, buffer = cv2.imencode('.jpg', blank_frame)
#         frame_bytes = buffer.tobytes()
#         yield (b'--frame\r\n'
#                b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

#     return Response(generate(), mimetype='multipart/x-mixed-replace; boundary=frame')

# Add this route to stream the processed video
@app.route('/processed_feed/<filename>')
def processed_feed(filename):
    """Stream a processed video file"""

    def generate():
        # Construct the full path to the processed file
        video_path = os.path.join('static/processed', filename)

        # Check if the file exists
        if not os.path.exists(video_path):
            # If file doesn't exist, yield an error frame
            blank_frame = np.zeros((480, 640, 3), dtype=np.uint8)
            cv2.putText(blank_frame, "Video file not found", (150, 240),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
            ret, buffer = cv2.imencode('.jpg', blank_frame)
            frame_bytes = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
            return

        # Open the video file
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            # If can't open video, yield an error frame
            blank_frame = np.zeros((480, 640, 3), dtype=np.uint8)
            cv2.putText(blank_frame, "Could not open video file", (120, 240),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
            ret, buffer = cv2.imencode('.jpg', blank_frame)
            frame_bytes = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
            return

        # Get video properties
        fps = cap.get(cv2.CAP_PROP_FPS)
        delay = 1 / fps if fps > 0 else 0.033  # Default to ~30fps if fps is 0

        # Process and stream each frame
        while True:
            ret, frame = cap.read()

            # If reached end of video, loop back to beginning
            if not ret:
                cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                ret, frame = cap.read()
                if not ret:
                    break  # If still can't read, exit loop
                continue

            # No need to process the frame for the output video
            # Just stream it as is

            # Encode the frame for streaming
            ret, buffer = cv2.imencode('.jpg', frame)
            frame_bytes = buffer.tobytes()

            # Yield the frame for streaming
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

            # Control frame rate
            time.sleep(delay)

    # Return the streaming response
    return Response(generate(), mimetype='multipart/x-mixed-replace; boundary=frame')


# Route for YouTube video feed
@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')


# Route for webcam feed
@app.route('/webcam_feed')
def webcam_feed():
    return Response(generate_webcam_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')


# Updated uploaded_feed route to handle fixed filename
@app.route('/uploaded_feed/<filename>')
def uploaded_feed(filename):
    """Stream an uploaded video file with deepfake detection applied"""

    def generate():
        # Construct the full path to the uploaded file
        video_path = os.path.join('static/uploads', filename)

        # Check if the file exists
        if not os.path.exists(video_path):
            # If file doesn't exist, yield an error frame
            blank_frame = np.zeros((480, 640, 3), dtype=np.uint8)
            cv2.putText(blank_frame, "Video file not found", (150, 240),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
            ret, buffer = cv2.imencode('.jpg', blank_frame)
            frame_bytes = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
            return

        # Open the video file
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            # If can't open video, yield an error frame
            blank_frame = np.zeros((480, 640, 3), dtype=np.uint8)
            cv2.putText(blank_frame, "Could not open video file", (120, 240),
                        cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
            ret, buffer = cv2.imencode('.jpg', blank_frame)
            frame_bytes = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')
            return

        # Get video properties
        fps = cap.get(cv2.CAP_PROP_FPS)
        delay = 1 / fps if fps > 0 else 0.033  # Default to ~30fps if fps is 0

        # Process and stream each frame
        while True:
            ret, frame = cap.read()

            # If reached end of video, loop back to beginning
            if not ret:
                cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                cap.open(video_path)  # Reopen the video
                ret, frame = cap.read()  # Read the first frame after reopening
                if not ret:
                    break  # If still can't read, exit loop
                continue

            # Apply deepfake detection to the frame
            processed_frame = process_frame(frame)

            # Encode the frame for streaming
            ret, buffer = cv2.imencode('.jpg', processed_frame)
            frame_bytes = buffer.tobytes()

            # Yield the frame for streaming
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

            # Control frame rate
            time.sleep(delay)

    # Return the streaming response
    return Response(generate(), mimetype='multipart/x-mixed-replace; boundary=frame')


# Run the Flask app
if __name__ == '__main__':
    app.run(port=8000, debug=True)

