import dlib
import cv2
import numpy as np
import math
from scipy.spatial import distance

def calculate_EAR(eye): # 눈 거리 계산 !
	A = distance.euclidean(eye[1], eye[5])
	B = distance.euclidean(eye[2], eye[4])
	C = distance.euclidean(eye[0], eye[3])
	ear = (A+B)/(2.0*C)
	return ear

# 얼굴 감지기와 랜드마크 감지기 초기화
face_detector = dlib.get_frontal_face_detector()
landmark_detector = dlib.shape_predictor("shape_predictor_68_face_landmarks.dat")  # 랜드마크 모델 파일 경로

# 비디오 캡처 초기화
cap = cv2.VideoCapture(0)  # 카메라 인덱스 (0은 기본 카메라)

while True:
    ret, frame = cap.read()  # 비디오 프레임 읽기
    if not ret:
        break

    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

    # 얼굴 감지
    faces = face_detector(gray,0)
    for rect in faces:
        # 얼굴 랜드마크 감지
        landmarks = landmark_detector(gray, rect)
        landmarks = [(landmarks.part(i).x, landmarks.part(i).y) for i in range(68)]  # 랜드마크 좌표 추출

        # 눈의 좌표 추출
        left_eye = landmarks[36:42]
        right_eye = landmarks[42:48]
        print(left_eye)

        # 눈 인식 결과 시각화
        for (x, y) in left_eye:
            cv2.circle(frame, (x, y), 2, (0, 255, 0), -1)
        for (x, y) in right_eye:
            cv2.circle(frame, (x, y), 2, (0, 255, 0), -1)
            
        # 눈 사이의 거리 구하기
        left_ear = calculate_EAR(left_eye)
        right_ear = calculate_EAR(right_eye)
        
        EAR = (left_ear+right_ear)/2
        EAR = round(EAR,2)

        # 눈 감지 성공 시 "eyes"라는 글자 표시
        if len(left_eye) > 0 and len(right_eye) > 0:
            cv2.putText(frame, "eyes", (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
         # 눈 사이의 거리 출력
            cv2.putText(frame, f"Eye Distance: {EAR}", (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2)
        
        if EAR<0.19:
           cv2.putText(frame, "WAKE UP!!", (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 0, 255), 2) 

        

    # 결과 비디오 출력
    cv2.imshow("Eyes Detection", frame)

    k = cv2.waitKey(33) # 종료하는 키 만들기
    
    if k ==49:
        cap.release()# 동영상 연결 종료
        cv2.destroyAllWindows() # 윈도우창 닫기
        break
