import io
from threading import Condition

from flask import Flask, Response
import picamera

app = Flask(__name__)


class StreamingOutput(object):
    def __init__(self):
        self.frame = None
        self.buffer = io.BytesIO()
        self.condition = Condition()

    def write(self, buf):
        if buf.startswith(b'\xff\xd8'):
            self.buffer.truncate()
            with self.condition:
                self.frame = self.buffer.getvalue()
                self.condition.notify_all()
            self.buffer.seek(0)
        return self.buffer.write(buf)


with picamera.PiCamera(resolution='1280x720', framerate=30) as camera:
    output = StreamingOutput()
    camera.start_recording(output, format='mjpeg')


def gen():
    while True:
        with output.condition:
            print('got it')
            output.condition.wait()
            frame = output.frame
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')


@app.route('/monitor.mjpeg')
def monitor():
    return Response(gen(), mimetype='multipart/x-mixed-replace; boundary=frame')


app.run('0.0.0.0')
