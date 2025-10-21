import cv2
from aiohttp import web
import asyncio


async def index(request):
    """
    Serve the HTML page.
    """
    content = """
<!DOCTYPE html>
<html>
<head>
    <title>OpenCV Camera Stream</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            display: flex;
            flex-direction: column;
            align-items: center;
            padding: 20px;
            background-color: #f0f0f0;
        }
        h1 {
            color: #333;
        }
        img {
            width: 640px;
            height: 480px;
            background-color: #000;
            border: 2px solid #333;
            border-radius: 8px;
        }
        .info {
            margin: 10px;
            padding: 10px;
            background-color: #d4edda;
            color: #155724;
            border-radius: 4px;
        }
    </style>
</head>
<body>
    <h1>OpenCV Camera Stream</h1>
    <div class="info">Streaming live from camera...</div>
    <img src="/video_feed" alt="Camera Stream">
</body>
</html>
    """
    return web.Response(content_type="text/html", text=content)


async def video_feed(request):
    """
    Stream video frames as MJPEG.
    """
    # Open camera
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    cap.set(cv2.CAP_PROP_FPS, 30)
    
    response = web.StreamResponse()
    response.content_type = 'multipart/x-mixed-replace; boundary=frame'
    await response.prepare(request)
    
    try:
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            # Encode frame as JPEG
            ret, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
            if not ret:
                continue
            
            frame_bytes = buffer.tobytes()
            
            # Write frame to response
            try:
                await response.write(
                    b'--frame\r\n'
                    b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n'
                )
            except ConnectionResetError:
                break
            
            # Small delay to control frame rate
            await asyncio.sleep(0.033)  # ~30 fps
            
    finally:
        cap.release()
    
    return response


def main():
    app = web.Application()
    app.router.add_get("/", index)
    app.router.add_get("/video_feed", video_feed)
    
    print("=" * 50)
    print("OpenCV Camera Stream Server")
    print("=" * 50)
    print("Server starting on http://localhost:8080")
    print("Open this URL in your browser to view the stream")
    print("=" * 50)
    
    web.run_app(app, host="0.0.0.0", port=8080)


if __name__ == "__main__":
    main()
