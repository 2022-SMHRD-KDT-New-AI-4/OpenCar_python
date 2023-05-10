import time
import cv2
import imutils
import tensorflow as tf
import platform
import numpy as np
from threading import Thread
from queue import Queue
import dlib


class Streamer :

    
    def __init__(self):
        
        if cv2.ocl.haveOpenCL() :
            cv2.ocl.setUseOpenCL(True)
        print('[wandlab] ', 'OpenCL : ', cv2.ocl.haveOpenCL())
            
        self.capture = None
        self.thread = None
        self.width = 360
        self.height = 360
        self.stat = False
        self.current_time = time.time()
        self.preview_time = time.time()
        self.sec = 0
        self.Q = Queue(maxsize=64)
        self.started = False
        self.frame=None

    def run(self, src = 0) :
        
        self.stop()
    
        if platform.system() == 'Windows' :        
            self.capture = cv2.VideoCapture(src , cv2.CAP_DSHOW)
        
        else :
            self.capture = cv2.VideoCapture(src)
            
        self.capture.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
        self.capture.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
        
        if self.thread is None :
            self.thread = Thread(target=self.update, args=())
            self.thread.daemon = False
            self.thread.start()
        
        self.started = True
    
    def stop(self):
        
        self.started = False
        
        if self.capture is not None :
            
            self.capture.release()
            self.clear()
            
    def update(self):

        face_detector = dlib.get_frontal_face_detector()
        landmark_detector = dlib.shape_predictor('shape_predictor_68_face_landmarks.dat')
        model = tf.keras.models.load_model('Test0429_4.h5')
        cnt=0

                    
        while True:

            if self.started :
                ret, frame = self.capture.read()  # 비디오 프레임 읽기
                # print("hello")
                if not ret:
                    print("ret.break")
                    break

            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

            faces = face_detector(gray,0)
            # print(1)
            for rect in faces:
                print(2)
                # 눈 랜드마크
                landmarks = landmark_detector(gray, rect)
                landmarks = [(landmarks.part(i).x, landmarks.part(i).y) for i in range(68)]  # 랜드마크 좌표 추출

                # 눈의 좌표 추출
                left_eye = landmarks[36:42]
                right_eye = landmarks[42:48]

                le_margin = int((landmarks[39][0]-landmarks[36][0])*0.5)
                re_margin = int((landmarks[45][0]-landmarks[42][0])*0.5)
                left_eye_img = gray[landmarks[37][1]-le_margin:landmarks[41][1]+le_margin, landmarks[36][0]-le_margin:landmarks[39][0]+le_margin]
                right_eye_img = gray[landmarks[43][1]-re_margin:landmarks[47][1]+re_margin, landmarks[42][0]-re_margin:landmarks[45][0]+re_margin]
                

                # # 눈 주위 사각형 그리기
                cv2.rectangle(frame, (landmarks[37][0]-20,landmarks[41][1]+20), (landmarks[40][0]+10, landmarks[39][1]-20), (255, 255, 255), 2)
                cv2.rectangle(frame, (landmarks[43][0]-20,landmarks[47][1]+20), (landmarks[46][0]+10, landmarks[45][1]-20), (255, 255, 255), 2)

                # # 64x64 크기 변환
                try:
                    # print(3)
                    left_eye_img = cv2.resize(left_eye_img, (64, 64))   
                    # 이미지 4차원 배열로 수정
                    left_eye_img = left_eye_img.reshape((1, 64, 64, 1))
                    # 원-핫 인코딩
                    left_eye_img = left_eye_img / 255.0

                    # 64x64 크기 변환
                    right_eye_img = cv2.resize(right_eye_img, (64, 64))
                    # 이미지 4차원 배열로 수정
                    right_eye_img = right_eye_img.reshape((1, 64, 64, 1))
                    # 원-핫 인코딩
                    right_eye_img = right_eye_img / 255.0

                    # # 눈 감은/뜬 모델로 예측
                    # print("eyes")
                    left_eye_pred = model.predict(left_eye_img)
                    right_eye_pred = model.predict(right_eye_img)
                except Exception as e:
                    print(str(e))

                # # 눈 감은/뜬 모델 예측 결과 시각화
                # print(4)
                if (left_eye_pred[0][0])>(left_eye_pred[0][1]):
                    cnt+=1
                    label_l="close"
                else:
                    label_l="open"
                if (right_eye_pred[0][0])>(right_eye_pred[0][1]):
                    cnt+=1
                    label_r="close"
                else:
                    label_r="open"

                # print(5)
                # if (left_eye_pred[0][0])>(left_eye_pred[0][1]) or (right_eye_pred[0][0])>(right_eye_pred[0][1]):
                #     cnt_s+=1
                # else: 
                #     cnt_s=0
        
                # print(6)
                cv2.putText(frame, label_l, (landmarks[37][0]-20, landmarks[37][1]-20), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
                cv2.putText(frame, label_r, (landmarks[43][0]-20, landmarks[43][1]-20), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)  

            
            self.Q.put(frame)        
            # print("여기입니다")
            return cnt
        


                          
    def clear(self):
        
        with self.Q.mutex:
            self.Q.queue.clear()
            
    def read(self):

        return self.Q.get()

    def blank(self):
        
        return np.ones(shape=[self.height, self.width, 3], dtype=np.uint8)

    def bytescode(self):
        
        if not self.capture.isOpened():
            
            frame = self.blank()

        else :
            
            frame = imutils.resize(self.read(), width=int(self.width))
            if self.stat :  
                
                cv2.rectangle(frame, (0,0), (120,30), (0,0,0), -1)
                fps = 'FPS : ' + str(self.fps())
                cv2.putText  (frame, fps, (10,20), cv2.FONT_HERSHEY_PLAIN, 1, (0,0,255), 1, cv2.LINE_AA)
            
            
        return cv2.imencode('.jpg', frame )[1].tobytes()
    
    def fps(self):
        
        self.current_time = time.time()
        self.sec = self.current_time - self.preview_time
        self.preview_time = self.current_time
        
        if self.sec > 0 :
            fps = round(1/(self.sec),1)
            
        else :
            fps = 1
            
        return fps
     
    def __exit__(self) :
        print('* streamer class exit')
        self.capture.release()