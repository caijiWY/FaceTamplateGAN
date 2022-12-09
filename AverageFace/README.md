前提条件
=========
(1) 安装Python 2.7

(2) 安装pip

(3) 安装dlib,cv2等所需library

构造平均脸
===========

第一步：将要平均的照片放入${AverageFace_root}\input_data\${sub_dir_name}文档，确保图片为jpg格式。
    例如： input_data\president

第二步：在终端运行 face_landmark_detection.py
${AverageFace_root}> python scripts\face_landmark_detection.py input_data\president

第三步：在终端运行 faceAverage.py

${AverageFace_root}> python scripts\average_face_generation.py input_data\president output_data\president.jpg

这样就能看到制作成功的平均脸了！
