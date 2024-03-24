import cv2
from flask import Flask, render_template, Response, request

app = Flask(__name__)

# 全局变量用于存储当前打开的摄像头对象
current_camera = None

# 打开摄像头的函数
def open_camera(url):
    global current_camera
    if current_camera is not None:
        current_camera.release()  # 释放之前的摄像头对象
    current_camera = cv2.VideoCapture(url)
    current_camera.set(cv2.CAP_PROP_FPS, 30)

# 关闭当前摄像头的函数
def close_camera():
    global current_camera
    if current_camera is not None:
        current_camera.release()
        current_camera = None

# 生成视频流帧的函数
def generate_frames():
    global current_camera
    while True:
        if current_camera is None:
            break
        success, frame = current_camera.read()
        if not success:
            break
        else:
            ret, buffer = cv2.imencode('.jpg', frame, [cv2.IMWRITE_JPEG_QUALITY, 80])
            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')

@app.route('/')
def index():
    return render_template('open_stream.html')

@app.route('/open_stream', methods=['POST'])
def open_stream():
    global current_camera
    camera_url = request.form.get('camera_url')  # 获取前端传递的摄像头 URL
    open_camera(camera_url)  # 调用打开摄像头函数
    return 'Camera opened successfully!'  # 返回成功信息

@app.route('/display_camera')
def display_camera():
    return render_template('index.html')  # 返回用于显示摄像头画面的模板

@app.route('/video_feed')
def video_feed():
    return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')

if __name__ == "__main__":
    app.run(debug=True, host='192.168.233.66', threaded=True)


