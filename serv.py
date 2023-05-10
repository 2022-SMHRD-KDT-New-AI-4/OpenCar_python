from flask import Flask
from flask import request
from flask import Response
from flask import stream_with_context
import requests

from stream import Streamer

app = Flask( __name__ )
streamer = Streamer()

broadcast = "http://211.63.240.23:5001/"
@app.route('/on', methods= ['GET','POST'])
def on():
    
    return ''

@app.route('/stream', methods= ['GET','POST'])
def stream():
    
    src = request.args.get( 'src', default = 0, type = int )
    
    try :
        
        return Response(
                                stream_with_context( stream_gen( src ) ),
                                mimetype='multipart/x-mixed-replace; boundary=frame' )
        
    except Exception as e :
        
        print('[wandlab] ', 'stream error : ',str(e))

def stream_gen( src ):   
  
    try : 
        
        streamer.run( src )
        cnt=0
        while True :

            result1 = streamer.update()
            # print(result1)
            # case 1: 감긴눈이 0.5초 이상 지속되면 졸음운전이라고 판별
            cnt+=result1
            if cnt> 10:
                result="true"
                cnt=0
            
            else :
                result="false"

            url = broadcast+"sleep_sensors/deepLearning/"+result
            requests.get(url)
            print("ddddddd")
            frame = streamer.bytescode()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
                    
    except GeneratorExit :
        # print( '[wandlab]', 'disconnected stream' )
        streamer.stop()

if __name__ == "__main__":
    app.run(host='0.0.0.0', debug=True)