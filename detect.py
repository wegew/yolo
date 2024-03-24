# YOLOv5 🚀 by Ultralytics, AGPL-3.0 license
"""
Run YOLOv5 detection inference on images, videos, directories, globs, YouTube, webcam, streams, etc.

Usage - sources:
    $ python detect.py --weights yolov5s.pt --source 0                               # webcam
                                                     img.jpg                         # image
                                                     vid.mp4                         # video
                                                     screen                          # screenshot
                                                     path/                           # directory
                                                     list.txt                        # list of images
                                                     list.streams                    # list of streams
                                                     'path/*.jpg'                    # glob
                                                     'https://youtu.be/Zgi9g1ksQHc'  # YouTube
                                                     'rtsp://example.com/media.mp4'  # RTSP, RTMP, HTTP stream

Usage - formats:
    $ python detect.py --weights yolov5s.pt                 # PyTorch
                                 yolov5s.torchscript        # TorchScript
                                 yolov5s.onnx               # ONNX Runtime or OpenCV DNN with --dnn
                                 yolov5s_openvino_model     # OpenVINO
                                 yolov5s.engine             # TensorRT
                                 yolov5s.mlmodel            # CoreML (macOS-only)
                                 yolov5s_saved_model        # TensorFlow SavedModel
                                 yolov5s.pb                 # TensorFlow GraphDef
                                 yolov5s.tflite             # TensorFlow Lite
                                 yolov5s_edgetpu.tflite     # TensorFlow Edge TPU
                                 yolov5s_paddle_model       # PaddlePaddle
"""

import argparse
import os
import platform
import sys
from pathlib import Path
import torch
import pymysql
import numpy as np
from flask import Flask, render_template, Response
FILE = Path(__file__).resolve()
ROOT = FILE.parents[0]  # YOLOv5 root directory
if str(ROOT) not in sys.path:
    sys.path.append(str(ROOT))  # add ROOT to PATH
ROOT = Path(os.path.relpath(ROOT, Path.cwd()))  # relative

from models.common import DetectMultiBackend
from utils.dataloaders import IMG_FORMATS, VID_FORMATS, LoadImages, LoadScreenshots, LoadStreams
from utils.general import (LOGGER, Profile, check_file, check_img_size, check_imshow, check_requirements, colorstr, cv2,
                           increment_path, non_max_suppression, print_args, scale_boxes, strip_optimizer, xyxy2xywh)
from utils.plots import Annotator, colors, save_one_box
from utils.torch_utils import select_device, smart_inference_mode
import requests
frame_info_list = []
# app = Flask(__name__)
def crurl(sss):
    return "https://192.168.233.158/obix/config/Drivers/ObixNetwork/exports/" + sss + "/writePoint/"
def posting(url, real_value):
    payload = "<real val=\"" + real_value + "\"/>"
    response = requests.request("POST", url, data=payload, auth=('obix', 'Obix123456'), verify=False)
@smart_inference_mode()
# 在循环外面添加一个用于绘制网格线的函数
def draw_quadrant_lines(image, rows, cols):
    # 计算水平和垂直线的间隔
    row_step = image.shape[0] // rows
    col_step = image.shape[1] // cols

    # 在图像上绘制水平线
    for i in range(1, rows):
        cv2.line(image, (0, i * row_step), (image.shape[1], i * row_step), (0, 255, 0), 2)

    # 在图像上绘制垂直线
    for j in range(1, cols):
        cv2.line(image, (j * col_step, 0), (j * col_step, image.shape[0]), (0, 255, 0), 2)
def run(
        weights=ROOT / 'yolov5s.pt',  # model path or triton URL
        source=ROOT / 'data/video',  # file/dir/URL/glob/screen/0(webcam)
        data=ROOT / 'data/coco128.yaml',  # dataset.yaml path
        imgsz=(640, 640),  # inference size (height, width)
        conf_thres=0.25,  # confidence threshold
        iou_thres=0.45,  # NMS IOU threshold
        max_det=1000,  # maximum detections per image
        device='',  # cuda device, i.e. 0 or 0,1,2,3 or cpu
        view_img=True,  # show results
        save_txt=False,  # save results to *.txt
        save_conf=False,  # save confidences in --save-txt labels
        save_crop=False,  # save cropped prediction boxes
        nosave=False,  # do not save images/videos
        classes=None,  # filter by class: --class 0, or --class 0 2 3
        agnostic_nms=False,  # class-agnostic NMS
        augment=False,  # augmented inference
        visualize=False,  # visualize features
        update=False,  # update all models
        project=ROOT / 'runs/detect',  # save results to project/name
        name='exp',  # save results to project/name
        exist_ok=False,  # existing project/name ok, do not increment
        line_thickness=3,  # bounding box thickness (pixels)
        hide_labels=False,  # hide labels
        hide_conf=False,  # hide confidences
        half=False,  # use FP16 half-precision inference
        dnn=False,  # use OpenCV DNN for ONNX inference
        vid_stride=1,  # video frame-rate stride
):
    DBHOST = "localhost"
    # DBHOST = "192.168.1.11"
    DBUSER = "root"
    DBPASS = "12138"
    DBNAME = "er"

    try:
        conn = pymysql.connect(host=DBHOST, user=DBUSER, password=DBPASS, database=DBNAME)
        print("数据库成功连接")
    except pymysql.Error as e:
        print("数据库连接失败")
        exit()

    source = str(source)
    save_img = not nosave and not source.endswith('.txt')  # save inference images
    is_file = Path(source).suffix[1:] in (IMG_FORMATS + VID_FORMATS)
    is_url = source.lower().startswith(('rtsp://', 'rtmp://', 'http://', 'https://'))
    webcam = source.isnumeric() or source.endswith('.streams') or (is_url and not is_file)or(source.endswith('.txt'))
    screenshot = source.lower().startswith('screen')
    if is_url and is_file:
        # Check if the content of the file starts with a URL
        with open(source, 'r') as file:
            file_content = file.read().strip()
        if any(content.lower().startswith(('rtsp://', 'rtmp://', 'http://', 'https://')) for content in
               file_content.splitlines()):
            source = check_file(source)  # download

    # Directories
    save_dir = increment_path(Path(project) / name, exist_ok=exist_ok)  # increment run
    (save_dir / 'labels' if save_txt else save_dir).mkdir(parents=True, exist_ok=True)  # make dir

    # Load model
    device = select_device(device)
    model = DetectMultiBackend(weights, device=device, dnn=dnn, data=data, fp16=half)
    stride, names, pt = model.stride, model.names, model.pt
    imgsz = check_img_size(imgsz, s=stride)  # check image size

    # Dataloader
    bs = 1  # batch_size
    s1=''
    if webcam:
        view_img = check_imshow(warn=True)
        dataset = LoadStreams(source, img_size=imgsz, stride=stride, auto=pt, vid_stride=vid_stride)

        bs = len(dataset)
    elif screenshot:
        dataset = LoadScreenshots(source, img_size=imgsz, stride=stride, auto=pt)
    else:
        dataset = LoadImages(source, img_size=imgsz, stride=stride, auto=pt, vid_stride=vid_stride)
    vid_path, vid_writer = [None] * bs, [None] * bs
    # Run inference
    model.warmup(imgsz=(1 if pt or model.triton else bs, 3, *imgsz))  # warmup
    seen, windows, dt = 0, [], (Profile(), Profile(), Profile())
    prev_person_count = -1
    frame_index = 0
    for path, im, im0s, vid_cap, s in dataset:
        # Initialize frame number
        with dt[0]:
            im = torch.from_numpy(im).to(model.device)
            im = im.half() if model.fp16 else im.float()  # uint8 to fp16/32
            im /= 255  # 0 - 255 to 0.0 - 1.0
            if len(im.shape) == 3:
                im = im[None]  # expand for batch dim

        # Inference
        with dt[1]:
            visualize = increment_path(save_dir / Path(path).stem, mkdir=True) if visualize else False
            pred = model(im, augment=augment, visualize=visualize)

        # NMS
        with dt[2]:
            pred = non_max_suppression(pred, conf_thres, iou_thres, classes, agnostic_nms, max_det=max_det)

        # Second-stage classifier (optional)
        # pred = utils.general.apply_classifier(pred, classifier_model, im, im0s)

        # Process predictions
        for i, det in enumerate(pred):
            if frame_index%2 == 0:
                s1 = 'F101light'
            elif frame_index%1 == 1:
                s1 = 'F102light'
            # per image
            seen += 1
            if webcam:  # batch_size >= 1
                p, im0, frame = path[i], im0s[i].copy(), dataset.count
                s += f'{i}: '
            else:
                p, im0, frame = path, im0s.copy(), getattr(dataset, 'frame', 0)

            p = Path(p)  # to Path
            save_path = str(save_dir / p.name)  # im.jpg
            txt_path = str(save_dir / 'labels' / p.stem) + ('' if dataset.mode == 'image' else f'_{frame}')  # im.txt
            s += '%gx%g ' % im.shape[2:]  # print string
            gn = torch.tensor(im0.shape)[[1, 0, 1, 0]]  # normalization gain whwh
            imc = im0.copy() if save_crop else im0  # for save_crop
            annotator = Annotator(im0, line_width=line_thickness, example=str(names))
            person_count = 0
            rows, cols, _ = im0.shape
            draw_quadrant_lines(imc, 3,3)
            grid_rows, grid_cols = 3, 3
            grid_height, grid_width = rows // grid_rows, cols // grid_cols

            # 计数器数组，用于每个网格的人数
            person_counts_grid = np.zeros((grid_rows, grid_cols), dtype=int)
            if len(det):
                # Rescale boxes from img_size to im0 size
                det[:, :4] = scale_boxes(im.shape[2:], det[:, :4], im0.shape).round()

                # Print results
                for c in det[:, 5].unique():
                    n = (det[:, 5] == c).sum()  # detections per class
                    s += f"{n} {names[int(c)]}{'s' * (n > 1)}, "  # add to string

                # Write results
                for *xyxy, conf, cls in reversed(det):
                    c = int(cls)  # integer class
                    if c == 0:  # Person class index is 0
                        person_count += 1
                        center_x = (xyxy[0] + xyxy[2]) / 2
                        center_y = (xyxy[1] + xyxy[3]) / 2
                        grid_row = int(center_y // grid_height)
                        grid_col = int(center_x // grid_width)
                        # 增加相应网格的人数计数
                        person_counts_grid[grid_row, grid_col] += 1
                    if save_txt:  # Write to file
                        xywh = (xyxy2xywh(torch.tensor(xyxy).view(1, 4)) / gn).view(-1).tolist()  # normalized xywh
                        line = (cls, *xywh, conf) if save_conf else (cls, *xywh)  # label format
                        with open(f'{txt_path}.txt', 'a') as f:
                            f.write(('%g ' * len(line)).rstrip() % line + '\n')
                    if save_img or save_crop or view_img:  # Add bbox to image
                        c = int(cls)  # integer class
                        label = None if hide_labels else (names[c] if hide_conf else f'{names[c]} {conf:.2f}')
                        annotator.box_label(xyxy, label, color=colors(c, True))
                    if save_crop:
                        save_one_box(xyxy, imc, file=save_dir / 'crops' / names[c] / f'{p.stem}.jpg', BGR=True)
            cv2.putText(im0, f'Persons: {person_count}', (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 0, 0), 2)
            for k in range(grid_rows):
                for j in range(grid_cols):
                    grid_person_count = person_counts_grid[k, j]

                    sr = s1+str(k+j+1)
                    print(f'Grid [{k + 1}, {j + 1}]: Persons: {grid_person_count}')
                    payload = "<real val=\"" +str(grid_person_count) + "\"/>"
                    cur = crurl(sr)
                    posting(cur,str(grid_person_count))
                    # response = requests.request("POST", url, data=payload, auth=('obix', 'Obix123456'), verify=False)
                    # print(response.text)
                    # 在网格上绘制人数
                    font = cv2.FONT_HERSHEY_SIMPLEX
                    font_scale = 1
                    font_thickness = 2
                    font_color = (255, 255, 255)
                    cv2.putText(im0, f'Persons: {grid_person_count}',
                                (j * grid_width + 10, k * grid_height + 30),
                                font, font_scale, font_color, font_thickness)

            print(person_count)
            if person_count != prev_person_count:
                # Save the person count data into the database
                # Increment the frame number
                frame_number = 1
                try:
                    with conn.cursor() as cursor:
                        # Insert the data into the 'person_counts' table
                        sql = "UPDATE person_counts SET person_count = %s WHERE frame_number = %s;"
                        cursor.execute(sql, (person_count, frame_number))
                        conn.commit()  # Commit the changes to the database
                except pymysql.Error as e:
                    print("Error inserting data into the database:", e)

            # Update the previous person count
            prev_person_count = person_count
            # Stream results
            im0 = annotator.result()
            im0_resized = cv2.resize(im0, (640, 480))
            if view_img:
                if platform.system() == 'Linux' and p not in windows:
                    windows.append(p)
                    cv2.namedWindow(str(p), cv2.WINDOW_NORMAL | cv2.WINDOW_KEEPRATIO)  # allow window resize (Linux)
                    cv2.resizeWindow(str(p), 640, 480)
                    # 固定宽度和高度
                cv2.imshow(str(p), im0_resized)
                frame_info_list.append({
                    'path': p,
                    'im0': im0.copy(),
                    'frame_number': frame,
                    'person_count': person_count,
                    # 其他你需要的信息
                })
                cv2.waitKey(1)  # 1 millisecond
            frame_index = frame_index+1;
            # Save results (image with detections)
            if save_img:
                if dataset.mode == 'image':
                    cv2.imwrite(save_path, im0)
                else:  # 'video' or 'stream'
                    if i < len(vid_path):
                        if vid_path[i] != save_path:  # new video
                            if i < len(vid_path):
                                vid_path[i] = save_path
                            else:
                                print(
                                    f"Warning: Index {i} is out of range for vid_path list with length {len(vid_path)}")
                            if isinstance(vid_writer[i], cv2.VideoWriter):
                                vid_writer[i].release()  # release previous video writer
                            if vid_cap:  # video
                                fps = vid_cap.get(cv2.CAP_PROP_FPS)
                                w = int(vid_cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                                h = int(vid_cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                            else:  # stream
                                fps, w, h = 30, im0.shape[1], im0.shape[0]
                            save_path = str(Path(save_path).with_suffix('.mp4'))  # force *.mp4 suffix on results videos
                            vid_writer[i] = cv2.VideoWriter(save_path, cv2.VideoWriter_fourcc(*'mp4v'), fps, (w, h))
                    # 处理新的视频
                    else:
                        print(f"Warning: Index {i} is out of range for vid_path list with length {len(vid_path)}")

                    vid_writer[i].write(im0)

        # Print time (inference-only)
        LOGGER.info(f"{s}{'' if len(det) else '(no detections), '}{dt[1].dt * 1E3:.1f}ms")

    # Print results
    t = tuple(x.t / seen * 1E3 for x in dt)  # speeds per image
    LOGGER.info(f'Speed: %.1fms pre-process, %.1fms inference, %.1fms NMS per image at shape {(1, 3, *imgsz)}' % t)
    if save_txt or save_img:
        s = f"\n{len(list(save_dir.glob('labels/*.txt')))} labels saved to {save_dir / 'labels'}" if save_txt else ''
        LOGGER.info(f"Results saved to {colorstr('bold', save_dir)}{s}")
    if update:
        strip_optimizer(weights[0])  # update model (to fix SourceChangeWarning)


def parse_opt():
    parser = argparse.ArgumentParser()
    parser.add_argument('--weights', nargs='+', type=str, default=ROOT / 'yolov5s.pt', help='model path or triton URL')
    # parser.add_argument('--source', type=str, default=ROOT / 'data/video', help='file/dir/URL/glob/screen/0(webcam)')
    parser.add_argument('--source', type=str, default='streams.txt', help='camera source URL')  # 单网络多线程 实时检测
    # parser.add_argument('--source', type=str, default='rtsp://admin:dhbiss12138@192.168.1.108/cam/realmonitor?channel=1&subtype=0', help='camera source URL')
    # parser.add_argument('--
    # ', type=str, default='http://admin:dhbiss12138@192.168.1.108/cgi-bin/snapshot.cgi', help='camera source URL')
    parser.add_argument('--data', type=str, default=ROOT / 'data/coco128.yaml', help='(optional) dataset.yaml path')
    parser.add_argument('--imgsz', '--img', '--img-size', nargs='+', type=int, default=[640], help='inference size h,w')
    parser.add_argument('--conf-thres', type=float, default=0.25, help='confidence threshold')
    parser.add_argument('--iou-thres', type=float, default=0.45, help='NMS IoU threshold')
    parser.add_argument('--max-det', type=int, default=1000, help='maximum detections per image')
    parser.add_argument('--device', default='', help='cuda device, i.e. 0 or 0,1,2,3 or cpu')
    parser.add_argument('--view-img', action='store_true', help='show results')
    parser.add_argument('--save-txt', action='store_true', help='save results to *.txt')
    parser.add_argument('--save-conf', action='store_true', help='save confidences in --save-txt labels')
    parser.add_argument('--save-crop', action='store_true', help='save cropped prediction boxes')
    parser.add_argument('--nosave', action='store_true', help='do not save images/videos')
    parser.add_argument('--classes', nargs='+', type=int, help='filter by class: --classes 0, or --classes 0 2 3')
    parser.add_argument('--agnostic-nms', action='store_true', help='class-agnostic NMS')
    parser.add_argument('--augment', action='store_true', help='augmented inference')
    parser.add_argument('--visualize', action='store_true', help='visualize features')
    parser.add_argument('--update', action='store_true', help='update all models')
    parser.add_argument('--project', default=ROOT / 'runs/detect', help='save results to project/name')
    parser.add_argument('--name', default='exp', help='save results to project/name')
    parser.add_argument('--exist-ok', action='store_true', help='existing project/name ok, do not increment')
    parser.add_argument('--line-thickness', default=3, type=int, help='bounding box thickness (pixels)')
    parser.add_argument('--hide-labels', default=False, action='store_true', help='hide labels')
    parser.add_argument('--hide-conf', default=False, action='store_true', help='hide confidences')
    parser.add_argument('--half', action='store_true', help='use FP16 half-precision inference')
    parser.add_argument('--dnn', action='store_true', help='use OpenCV DNN for ONNX inference')
    parser.add_argument('--vid-stride', type=int, default=1, help='video frame-rate stride')
    opt = parser.parse_args()
    opt.view_img = True
    opt.imgsz *= 2 if len(opt.imgsz) == 1 else 1  # expand
    print_args(vars(opt))
    return opt

# def generate_frames():
#     global frame_info_list
#     while True:
#         check_requirements(ROOT / 'requirements.txt', exclude=('tensorboard', 'thop'))
#         opt = parse_opt()
#         opt.classes = [0]
#
#         success, frame = run(**vars(opt))# 读取摄像头帧
#         if not success:
#             break
#         else:
#             ret, buffer = cv2.imencode('.jpg', frame)
#             frame = buffer.tobytes()
#             yield (b'--frame\r\n'
#                    b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')  # 将每一帧编码并传输到浏览器
#
# @app.route('/')
# def index():
#     return render_template('index.html')  # 渲染HTML模板
# @app.route('/video_feed/<feed_type>')
# def video_feed(feed_type):
#     check_requirements(ROOT / 'requirements.txt', exclude=('tensorboard', 'thop'))
#     opt.classes = [0]
#     """Video streaming route. Put this in the src attribute of an img tag."""
#     if feed_type == 'Camera_0':
#         return Response(generate_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')
#
#     # elif feed_type == 'Camera_1':
#     #     return Response(run(**vars(opt)),
#     #                     mimetype='multipart/x-mixed-replace; boundary=frame')
def main(opt):
    check_requirements(ROOT / 'requirements.txt', exclude=('tensorboard', 'thop'))
    opt.classes = [0]
    run(**vars(opt))
if __name__ == '__main__':
    opt = parse_opt()
    main(opt)
    # app.run(host='0.0.0.0', port="5000", threaded=True)
