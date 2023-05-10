# softmax 모델


import dlib
import cv2
import numpy as np
import tensorflow as tf
import matplotlib.pyplot as plt
import pandas as pd

    # 얼굴 감지기와 랜드마크 감지기 초기화
face_detector = dlib.get_frontal_face_detector()
landmark_detector = dlib.shape_predictor('model/shape_predictor_68_face_landmarks.dat')  # 랜드마크 모델 파일 경로

    # 눈 감은/뜬 모델 초기화
model = tf.keras.models.load_model('model/eye_closed_open_tf_0503_C1_1.h5')
cnt=0 
cnt_s=0
# left_eye_close=[]
# left_eye_open=[]
# right_eye_close=[]
# right_eye_open=[]
# result_l=[]
# result_r=[]


    # 비디오 캡처 초기화
cap = cv2.VideoCapture(0)  

while True:
    ret, frame = cap.read()  # 비디오 프레임 읽기
    #     frame = cv2.flip(frame,1)
    if not ret:
        break
 
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # 얼굴 감지
    faces = face_detector(gray,0)
        #print(faces)

    for rect in faces:
            # 얼굴 랜드마크 감지
            #shapes = face_utils.shape_to_np(rect)
            #shapes = face_utils.shape_to_np(shapes)

            # 눈 랜드마크
        landmarks = landmark_detector(gray, rect)
        landmarks = [(landmarks.part(i).x, landmarks.part(i).y) for i in range(68)]  # 랜드마크 좌표 추출

            # 눈의 좌표 추출
        left_eye = landmarks[36:42]
        right_eye = landmarks[42:48]

            # 눈 인식 결과 시각화
#             for (x, y) in left_eye:
#                 cv2.circle(frame, (x, y), 2, (0, 255, 0), -1)
#             for (x, y) in right_eye:
#                 cv2.circle(frame, (x, y), 2, (0, 255, 0), -1)

            # 눈 감은/뜬 모델에 입력으로 사용할 데이터 생성

        le_margin = int((landmarks[39][0]-landmarks[36][0])*0.5)
        re_margin = int((landmarks[45][0]-landmarks[42][0])*0.5)
        left_eye_img = gray[landmarks[37][1]-le_margin:landmarks[41][1]+le_margin, landmarks[36][0]-le_margin:landmarks[39][0]+le_margin]
            
            # 눈 주위 사각형 그리기
        cv2.rectangle(frame, (landmarks[37][0]-20,landmarks[41][1]+20), (landmarks[40][0]+10, landmarks[39][1]-20), (255, 255, 255), 2)
        cv2.rectangle(frame, (landmarks[43][0]-20,landmarks[47][1]+20), (landmarks[46][0]+10, landmarks[45][1]-20), (255, 255, 255), 2)


            # 64x64 크기 변환
        left_eye_img = cv2.resize(left_eye_img, (64, 64))   
            # 이미지 4차원 배열로 수정
        left_eye_img = left_eye_img.reshape((1, 64, 64, 1))
            # 원-핫 인코딩
        left_eye_img = left_eye_img / 255.0

            # 오른쪽눈 감은/뜬 모델에 입력으로 사용할 데이터 생성
        right_eye_img = gray[landmarks[43][1]-re_margin:landmarks[47][1]+re_margin, landmarks[42][0]-re_margin:landmarks[45][0]+re_margin]
             # 64x64 크기 변환
        right_eye_img = cv2.resize(right_eye_img, (64, 64))
            # 이미지 4차원 배열로 수정
        right_eye_img = right_eye_img.reshape((1, 64, 64, 1))
             # 원-핫 인코딩
        right_eye_img = right_eye_img / 255.0


            # 눈 감은/뜬 모델로 예측
        left_eye_pred = model.predict(left_eye_img)
        right_eye_pred = model.predict(right_eye_img)

#             ## 테스트: 오른쪽 눈 이미지 가져오기 
            ## 왼쪽 눈
        plt.subplot(1, 2, 1)
        plt.imshow(left_eye_img[0])
        ## 오른 쪽 눈
        plt.subplot(1, 2, 2)
        plt.imshow(right_eye_img[0])
        plt.show()
    
        print(f'왼쪽눈:{left_eye_pred}')
        print(f'오른쪽눈:{right_eye_pred}')
#         left_eye_close.append(left_eye_pred[0][0])
#         left_eye_open.append(left_eye_pred[0][1])
#         right_eye_close.append(right_eye_pred[0][0])
#         right_eye_open.append(right_eye_pred[0][1])
#         left_img.append(left_eye_img[0])
#         right_img.append(right_eye_img[0])
        
        # 눈 감은/뜬 눈 판별하기
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
#         result_l.append(label_l)
#         result_r.append(label_r)
        
            
         
        if (left_eye_pred[0][0])>(left_eye_pred[0][1]) or (right_eye_pred[0][0])>(right_eye_pred[0][1]):
            cnt_s+=1
        else: 
            cnt_s=0
            
        # case 1: 감긴눈이 0.5초 이상 지속되면 졸음운전이라고 판별
        if cnt> 10:
            #cv2.putText(frame,"Wake up_1", (landmarks[41][0]-50, landmarks[41][1]-50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0),2)
            result="true"
            cnt=0
        else:
            result="false"
            

         # 프레임이 일정 수 이상이면 졸음운전이라고 판별(case2 : 1분 동안 한 쪽눈당 400프레임 이상 눈을 감는다면)
        if len(frame) > 600:
            if cnt_s >=400:
                #cv2.putText(frame,"Wake up_2", (x-90, y - 70), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0),2)
                print(cnt)
                cnt_s=0
            result="true"
        else:
            result="false"

            # 눈의 상태 화면 표시
            # 왼쪽눈 ->화면상으로 오른쪽
        state_l= '{:.2f}'.format(left_eye_pred[0][0])
        state_r= '{:.20f}'.format(right_eye_pred[0][0])
            #print(state_l)
        cv2.putText(frame, state_l, (landmarks[37][0]-50, landmarks[37][1]-50), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        #cv2.putText(frame, state_r, (x+30, y - 20), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2
        cv2.putText(frame, label_l, (landmarks[37][0]-20, landmarks[37][1]-20), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        cv2.putText(frame, label_r, (landmarks[43][0]-20, landmarks[43][1]-20), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        print(label_l)
        print(label_r)
        
         

             # 결과 비디오 출력
    cv2.imshow("Eyes Detection", frame)

    k = cv2.waitKey(33) # 종료하는 키 만들기

    if k ==49:
        cap.release()# 동영상 연결 종료
        cv2.destroyAllWindows() # 윈도우창 닫기

        break
        

 

  
