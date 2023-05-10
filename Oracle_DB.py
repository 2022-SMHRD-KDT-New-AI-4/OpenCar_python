import os
import cx_Oracle as oci
from flask import Flask, request, redirect



app = Flask(__name__)
app.config['JSON_AS_ASCII'] = False

sleepCheck = ""  # 졸음 여부

def connenct ():
    # oracle DB 연결
    dsn = oci.makedsn("project-db-stu.ddns.net", 1524, service_name="xe") # DB 접속 정보 설정
    conn = oci.connect(user="smhrd_e_2", password="smhrde2", dsn=dsn) # DB 연결
    cursor = conn.cursor() # Cursor 객체 생성
    return cursor, conn


"""  tb_user(회원정보) """
# 로그인 기능 
# 아이디 비번 일치x 리턴값 x
@app.route('/login/', methods=['GET','POST'])
def login():        
    cursor, conn = connenct()
    if request.method == 'POST':
        id = request.form["User_id"]
        pw = request.form["User_pw"]

        cursor.execute(f"select * from tb_user where user_id = '{id}' and user_pw ='{pw}'")
        userInfo = cursor.fetchall() # SQL 쿼리 실행 및 결과 가져오기
        

        userInfo = {"user_id":userInfo[0][0], "user_pw":userInfo[0][1],
                    "user_name":userInfo[0][2], "user_birthdate":userInfo[0][3],
                    "user_model":userInfo[0][4]}
    #결과값 리턴하면 안드로이드 스튜디오 StringRequest 안에 있는 onResponse()로 값 전달


    return userInfo
           

# 회원가입
@app.route('/join/',methods=['GET','POST'])
def join():
    cursor, conn = connenct()

    if request.method == 'GET':
        #cursor.execute(f"INSERT INTO tb_user VALUES ('{user_id}','{user_pw}','{user_name}','{user_birthdate}')")
        #conn.commit() # 변경사항을 데이터베이스에 반영
        return 'false'
     
    elif request.method == 'POST':
        User_id = request.form["User_id"]
        User_pw = request.form["User_pw"]
        User_name = request.form["User_name"]
        User_birthdate = request.form["User_birthdate"]
        user_model = request.form["User_model"]

        if User_birthdate == '': # 생일이 ''이라면 

            cursor.execute(f"INSERT INTO tb_user (user_id, user_pw, user_name, user_model) VALUES ('{User_id}','{User_pw}','{User_name}','{user_model}')")
            conn.commit() # 변경사항을 데이터베이스에 반영
        else :
            cursor.execute(f"INSERT INTO tb_user VALUES ('{User_id}','{User_pw}','{User_name}',to_date('{User_birthdate}','YYYYMMDDHH24MISS'),'{user_model}')")
            conn.commit() # 변경사항을 데이터베이스에 반영
        return 'true'
     
    return 'false'

# 나의 나이, 차종
@app.route('/my_info/<string:id>/',methods=['GET','POST'])
def my_info(id):
    cursor, conn = connenct()

    if request.method == 'GET':
        sql = f"""-- 나의 나이, 차종(my_info)
select  user_model,
        case
        when to_char(user_birthdate, 'YYYY') between '1994' and '2004' then '20대'
        when to_char(user_birthdate, 'YYYY') between '1984' and '1993' then '30대'
        when to_char(user_birthdate, 'YYYY') between '1974' and '1983' then '40대'
        when to_char(user_birthdate, 'YYYY') between '1964' and '1973' then '50대'
        when to_char(user_birthdate, 'YYYY') <='1963' then '60대 이상'
        end as user_age
        from tb_user
        where user_id='{id}' """
        cursor.execute(sql)
        list = cursor.fetchall() # SQL 쿼리 실행 및 결과 가져오기

        result= {"user_model" : list[0][0], "user_age" : list[0][1]}

        return result
        

    return 'false'

# 최근 주행 정보
@app.route('/my_drive_info/<string:id>/',methods=['GET','POST'])
def my_drive_info(id):
    cursor, conn = connenct()

    if request.method == 'GET':
        sql = f"""-- 주행 날짜 & 주행시간 & 주행시작 후 첫 번째 졸음감지 & 최근 주행 졸음 빈도수
SELECT D.*
FROM(select day,drive_time,min(sl_time) as sl_time,count(dr_seq) AS FREQ
from(select c.dr_seq,
       to_char(c.start_time,'YYYY.MM.DD') as day,
       round((c.finish_time-c.start_time)*24*60*60,0) as drive_time, --초단위로
       round((c.sl_start_time-c.start_time)*24*60*60,0) as sl_time
from(select a.dr_seq, a.start_time, a.finish_time, b.sl_seq, b.sl_start_time
                    from tb_drive a, tb_sleep b
                    where a.dr_seq=b.dr_seq
                    and a.user_id='{id}'
                    order by a.dr_seq desc, sl_seq) c)
                    group by dr_seq,day,drive_time
                    order by dr_seq desc) D
WHERE ROWNUM=1 """
        cursor.execute(sql)
        tmp_list = cursor.fetchall() # SQL 쿼리 실행 및 결과 가져오기

        if len(tmp_list) != 0 :
            result= {"day" : tmp_list[0][0], "drive_time" : tmp_list[0][1],
                    "sl_time" : tmp_list[0][2], "freq" : tmp_list[0][3]}
        else :
            result= {}

        return result
        

    return 'false'





"""  tb_drive(주행정보)  """
# 주행시작시 주행정보 입력 
@app.route('/drive_insert/<string:id>/',methods=['GET','POST'])
def drive_insert(id):
    cursor, conn = connenct()
    if request.method == 'GET':

        # tb_drive 테이블에 insert하기
        cursor.execute(f"INSERT INTO tb_drive(dr_seq, user_id, start_time ) VALUES (dr_seq.NEXTVAL,'{id}',sysdate)")
        conn.commit() # 변경사항을 데이터베이스에 반영

        # dr_seq 를 select 후 반환하기
        cursor.execute(f"select dr_seq from tb_drive  where user_id = '{id}' and finish_time is NULL ORDER BY dr_seq desc")
        result = cursor.fetchall() # SQL 쿼리 실행 및 결과 가져오기

        result= {'dr_seq':result[0][0]}


        return result
     
    return 'false'

# 주행완료시 주행정보 업데이트 
@app.route('/drive_update/<string:dr_seq>/',methods=['GET','POST'])
def drive_update(dr_seq):
    cursor, conn = connenct()
    if request.method == 'GET':

        cursor.execute(f"UPDATE tb_drive set finish_time = sysdate WHERE dr_seq = {dr_seq}")
        conn.commit() # 변경사항을 데이터베이스에 반영


        return 'true' 
     
    return 'false'

# 총 운전시간 계산 주소 = http://218.157.24.41:5000/total_drive_time/아이디
@app.route('/total_drive_time/<string:id>',methods=['GET','POST'])
def total_drive_time(id):
    cursor, conn = connenct()
    if request.method == 'GET':

        cursor.execute(f"select sum(운행시간) from(SELECT ROUND((finish_time - start_time) * 24 * 60,0) AS 운행시간 FROM tb_drive WHERE user_id = '{id}')")
        time = cursor.fetchall() # SQL 쿼리 실행 및 결과 가져오기
        

        return str(time[0][0]) 
     
    return 'false'

"""  tb_sleep(졸음운전 상태분석)  """



# 1. 졸음운전 감지(안드용) 
@app.route('/sleep_sensors/android/<string:id>/<int:dr_seq>',methods=['GET','POST'])
def sleep_sensors_and(id,dr_seq):
    cursor, conn = connenct()
    if request.method == 'GET':
        if sleepCheck == "true":

            # tb_sleep 테이블 INSERT
            cursor.execute(f"INSERT INTO tb_sleep(sl_seq, user_id, dr_seq, sl_start_time ) VALUES (sl_seq.NEXTVAL,'{id}',{dr_seq},sysdate)")
            conn.commit() 

            # tb_sleep 를 select 후 반환하기
            cursor.execute(f"select sl_seq from tb_sleep where user_id = '{id}' and sl_fin_time is NULL")
            sl_seq = cursor.fetchall() # SQL 쿼리 실행 및 결과 가져오기   

            # tb_alarm 테이블 INSERT
            cursor.execute(f"INSERT INTO tb_alarm(al_seq, user_id, sl_seq, send_time,msg,msg_check) VALUES (al_seq.NEXTVAL,'{id}','{sl_seq[0][0]}',sysdate,'졸음운전감지','N')")
            conn.commit()

    return str(sleepCheck)

# 2. 졸음운전 통보 (딥러닝용) 주소 = http://218.157.24.41:5000/sleep_sensors/deepLearning/(True || False)
@app.route('/sleep_sensors/deepLearning/<string:sleep>',methods=['GET','POST'])
def sleep_sensors_deep(sleep):

    if request.method == 'GET':
        global sleepCheck  # 전역변수 선언
        sleepCheck = sleep
        

    return sleepCheck

# 3. 나의 총 졸음운전 빈도수 출력 주소 = http://218.157.24.41:5000/sleep_my_count/아이디
@app.route('/sleep_my_count/<string:id>',methods=['GET','POST'])
def sleep_my_count(id):
    cursor, conn = connenct()
    if request.method == 'GET':

        sql = f"select count(*) as 나의졸음운전빈도수 from tb_sleep where user_id='{id}'"
        
        cursor.execute(sql)
        count = cursor.fetchall() # SQL 쿼리 실행 및 결과 가져오기

        return str(count[0][0])
     
    return 'false'

# 4. 나의 월별 졸음운전 빈도수 출력 주소 = http://218.157.24.41:5000/sleep_my_month_count/아이디
@app.route('/sleep_my_month_count/<string:id>',methods=['GET','POST'])
def sleep_my_month_count(id):
    cursor, conn = connenct()
    if request.method == 'GET':

        sql = f"select to_char(sl_start_time, 'MM') as 월, count(*) as 월별졸음운전빈도수 from tb_sleep where user_id='{id}' group by to_char(sl_start_time, 'MM')"
        cursor.execute(sql)
        list = cursor.fetchall() # SQL 쿼리 실행 및 결과 가져오기

        result= {}
        for i in range(len(list)):

            result[f"{i}"] = {
                
                "month" : list[i][0], "sleep_my_month_count" : list[i][1]
            }
  
        return str(result)
     
    return 'false'

# 5. 회원별 졸음운전 빈도수 주소 = http://218.157.24.41:5000/sleep_user_count
@app.route('/sleep_user_count',methods=['GET','POST'])
def sleep_user_count():
    cursor, conn = connenct()
    if request.method == 'GET':

        sql = f"select user_id, count(user_id) as 회원별졸음운전빈도수 from tb_sleep group by user_id"

        cursor.execute(sql)
        list = cursor.fetchall() # SQL 쿼리 실행 및 결과 가져오기

        result= {}
        for i in range(len(list)):

            result[f"{i}"] = {
                
                "user_id" : list[i][0], "sleep_hour_count" : list[i][1]
            }
  
        return str(result)

     
    return 'false'

# 6. 전체평균 졸음운전 빈도수 주소 = http://218.157.24.41:5000/sleep_user_avg_count
@app.route('/sleep_user_avg_count',methods=['GET','POST'])
def sleep_user_avg_count():
    cursor, conn = connenct()
    if request.method == 'GET':

        sql = f"select round(avg(회원별졸음운전빈도수),1) as 전체평균 from(select user_id, count(user_id) as 회원별졸음운전빈도수 from tb_sleep group by user_id)"
        
        cursor.execute(sql)
        count = cursor.fetchall() # SQL 쿼리 실행 및 결과 가져오기

        return str(count[0][0])
     
    return 'false'

# 7. 나의졸음시간대 주소 = http://218.157.24.41:5000/sleep_my_hour_count/아이디
@app.route('/sleep_my_hour_count/<string:id>',methods=['GET','POST'])
def sleep_my_hour_count(id):
    cursor, conn = connenct()
    if request.method == 'GET':

        sql = f"select to_char(sl_start_time, 'HH24') as 시간, count(*) as 졸음시간빈도 from tb_sleep where user_id='{id}' group by to_char(sl_start_time, 'HH24')"
        cursor.execute(sql)
        list = cursor.fetchall() # SQL 쿼리 실행 및 결과 가져오기

        result= {}
        for i in range(len(list)):

            result[f"{i}"] = {
                
                "sl_start_time" : list[i][0], "sleep_hour_count" : list[i][1]
            }
            


        return str(result)
     
    return 'false'

# 나의 월별 평균 졸음운전 빈도수
@app.route('/sleep_my_month_avg_count/<string:id>',methods=['GET','POST'])
def sleep_my_month_avg_count(id):
    cursor, conn = connenct()
    if request.method == 'GET':

        sql = f"select round(sum(월빈도수)/6,2) as monthavg from( select to_char(sl_start_time, 'MM') as 월, count(*) as 월빈도수 from tb_sleep where user_id='{id}' group by to_char(sl_start_time, 'MM'))"
        cursor.execute(sql)
        list = cursor.fetchall() # SQL 쿼리 실행 및 결과 가져오기

        result= {}
        for i in range(len(list)):

            result[f"{i}"] = {
                
                "monthavg" : list[i][0]
            }
            
        return str(result)
     
    return 'false'

# 나의 총 졸음운전 빈도수 & 전체평균 졸음운전 빈도수
@app.route('/sleep_my_all/<string:id>',methods=['GET','POST'])
def sleep_my_all(id):
    cursor, conn = connenct()
    if request.method == 'GET':

        sql = f'''-- 나의 총 졸음운전 빈도수 & 전체평균 졸음운전 빈도수 & 차종별 평균 & 나이대 평균
-- 나의 총 졸음운전 빈도수
select 3,a.user_id, count(sl_seq) as freq
from tb_user a, tb_sleep b
where a.user_id=b.user_id(+)
and a.user_id='{id}'
group by a.user_id
union
-- 전체평균 졸음운전 빈도수
select 1,'ALL', round(avg(userfreq),1) as freq
from(select user_id, count(user_id) as userfreq
from tb_sleep
group by user_id)
union
-- 차종별 평균
select 2,'MODEL',round(avg(modelfreq),1) as freq
from (
select a.user_id, count(*) as modelfreq
from tb_sleep a, tb_user b
where a.user_id=b.user_id
and user_model=(select user_model
                from tb_user
                where user_id='{id}')
group by a.user_id)
union
-- 사용자 나이대 평균
select 0,'AGE',round(avg(userfreq),1) as freq
from (select a.user_id, a.user_age, count(*) as userfreq
        from
            (select user_id,
              case
            when to_char(user_birthdate, 'YYYY') between '1994' and '2004' then '20대'
            when to_char(user_birthdate, 'YYYY') between '1984' and '1993' then '30대'
            when to_char(user_birthdate, 'YYYY') between '1974' and '1983' then '40대'
            when to_char(user_birthdate, 'YYYY') between '1964' and '1973' then '50대'
            when to_char(user_birthdate, 'YYYY') <='1963' then '60대 이상'
            end as user_age
            from tb_user) a, tb_sleep b
            where a.user_id = b.user_id
            group by a.user_id, a.user_age) c
where c.user_age = (select
          case
        when to_char(user_birthdate, 'YYYY') between '1994' and '2004' then '20대'
        when to_char(user_birthdate, 'YYYY') between '1984' and '1993' then '30대'
        when to_char(user_birthdate, 'YYYY') between '1974' and '1983' then '40대'
        when to_char(user_birthdate, 'YYYY') between '1964' and '1973' then '50대'
        when to_char(user_birthdate, 'YYYY') <='1963' then '60대 이상'
        end as user_age
        from tb_user
        where user_id='{id}')'''

        cursor.execute(sql)
        list = cursor.fetchall() # SQL 쿼리 실행 및 결과 가져오기

        result= {}
        for i in range(len(list)):

            result[f"{i}"] = {
                
                "index" : list[i][0],"user_id" : list[i][1], "freq" : list[i][2]
            }
            
        return result
     
    return 'false'

# 나의 총 졸음운전 빈도수 & 전체평균 졸음운전 빈도수
@app.route('/sleep_time_rank/<string:id>',methods=['GET','POST'])
def sleep_time_rank(id):
    cursor, conn = connenct()
    if request.method == 'GET':
        sql = f'''-- 나의졸음시간대 상위2
select rownum, a.시간
    from(select to_char(sl_start_time, 'HH24') as 시간,
           count(*) as 졸음시간빈도
    from tb_sleep
    where user_id='{id}'
    group by to_char(sl_start_time, 'HH24')
    order by 졸음시간빈도 desc) a
where rownum<=2 '''

        cursor.execute(sql)
        list = cursor.fetchall()

        result= {}
        for i in range(len(list)):

            result[f"{i}"] = {
                
                "rownum" : list[i][0], "time" : list[i][1]
            }

        return result


# 주행정보 7개
@app.route('/my_drive_seven/<string:id>',methods=['GET','POST'])
def my_drive_seven(id):
    cursor, conn = connenct()
    if request.method == 'GET':
        sql = f'''---- 주행정보 7개(my_drive_seven)                    
SELECT D.*
FROM(select day,drive_time,min(sl_time) as sl_time,count(dr_seq) AS freq
from(select c.dr_seq,
       to_char(c.start_time,'YYYY.MM.DD') as day,
       round((c.finish_time-c.start_time)*24*60*60,0) as drive_time, --초단위로
       round((c.sl_start_time-c.start_time)*24*60*60,0) as sl_time
from(select a.dr_seq, a.start_time, a.finish_time, b.sl_seq, b.sl_start_time
                    from tb_drive a, tb_sleep b
                    where a.dr_seq=b.dr_seq
                    and a.user_id='{id}'
                    order by a.dr_seq desc, sl_seq) c)
                    group by dr_seq,day,drive_time
                    order by dr_seq desc) D
WHERE ROWNUM<=7 '''

        cursor.execute(sql)
        list = cursor.fetchall()

        result= {}
        for i in range(len(list)):

            result[f"{i}"] = {
                
                "day" : list[i][0], "drive_time" : list[i][1],
                "sl_time" : list[i][2], "freq" : list[i][3]
            }

        return result





"""  tb_alarm(알림내역)  """
# 1. 나의 월별 졸음운전 빈도수 출력 주소 = http://218.157.24.41:5000/alarm_select/아이디
@app.route('/alarm_select/<string:id>',methods=['GET','POST'])
def alarm_select(id):
    cursor, conn = connenct()
    if request.method == 'GET':

        sql = f"select SEND_TIME, GOAL_LAT, GOAL_LNG, MSG from tb_alarm where user_id = '{id}' order by al_seq desc3"
        cursor.execute(sql)
        list = cursor.fetchall() # SQL 쿼리 실행 및 결과 가져오기

        result= {}
        for i in range(len(list)):

            result[f"{i}"] = {
                
                "send_Time" : list[i][0], "GOAL_LAT" : list[i][1], 
                "GOAL_LNG" : list[i][2], "MSG" : list[i][3], 
                
            }
            result[f"{i}"]["send_Time"] = result[f"{i}"]["send_Time"].strftime("%Y-%m-%d %H:%M:%S")



        return str(result)
     
    return 'false'







""" 테스트 서버  """
import random
@app.route('/random1/',methods=['GET','POST'])
def random1():
    if request.method == 'GET':
        rd = random.randint(1,101)
    
        result = ''
        if rd <= 70 :
            result = 'false'
        elif rd <= 85 :
            result = 'true'
        else :
            result = '감지x'

        print(result) 
    return result


###################################### 이 아래로 코드 작성 금지 ######################################
if __name__ == "__main__":
    app.run(host='0.0.0.0', port='5001', debug=True)
    
    # app.run(port='5001', debug=True)
    # app.run(host = 'localhost', port='5001', debug=True)



                      