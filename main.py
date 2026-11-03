import cv2
import numpy as np
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.image import Image
from kivy.clock import Clock
from kivy.graphics.texture import Texture
from kivy.core.audio import SoundLoader
from kivy.utils import platform

if platform == 'android':
    from android.permissions import request_permissions, Permission
    request_permissions([Permission.CAMERA, Permission.READ_EXTERNAL_STORAGE, Permission.WRITE_EXTERNAL_STORAGE])

class LaserGameLayout(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(orientation='vertical', **kwargs)
        self.score = 0
        self.shots = 0
        self.last_score = 0
        self.laser_detected = False
        
        self.snd_bullseye = SoundLoader.load('bullseye.wav')
        self.snd_shot = SoundLoader.load('shot.wav')
        
        self.info_label = Label(text="Score: 0 | Shots: 0", size_hint_y=0.1, font_size='22sp')
        self.add_widget(self.info_label)
        
        self.img_view = Image(size_hint_y=0.8)
        self.add_widget(self.img_view)
        
        btn_bar = BoxLayout(size_hint_y=0.1)
        btn_reset = Button(text="Reset Score", font_size='18sp')
        btn_reset.bind(on_release=self.reset_game)
        btn_bar.add_widget(btn_reset)
        self.add_widget(btn_bar)
        
        self.capture = cv2.VideoCapture(0)
        self.capture.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        
        Clock.schedule_interval(self.update, 1.0 / 30.0)

    def reset_game(self, instance):
        self.score = 0
        self.shots = 0
        self.last_score = 0
        self.info_label.text = "Score: 0 | Shots: 0"

    def update(self, dt):
        ret, frame = self.capture.read()
        if not ret:
            return
            
        h, w, _ = frame.shape
        cx, cy = w // 2, h // 2
        radius = int(min(w, h) * 0.4)
        
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        _, max_val, _, max_loc = cv2.minMaxLoc(gray)
        
        if max_val > 245:
            if not self.laser_detected:
                lx, ly = max_loc
                dist = np.hypot(lx - cx, ly - cy)
                ratio = dist / radius
                
                pts = 0
                if ratio <= 0.2: pts = 10
                elif ratio <= 0.4: pts = 8
                elif ratio <= 0.6: pts = 6
                elif ratio <= 0.8: pts = 4
                elif ratio <= 1.0: pts = 2
                
                if pts > 0:
                    self.score += pts
                    self.shots += 1
                    self.info_label.text = f"Score: {self.score} | Shots: {self.shots} (+{pts})"
                    if pts == 10 and self.snd_bullseye:
                        self.snd_bullseye.play()
                    elif self.snd_shot:
                        self.snd_shot.play()
                self.laser_detected = True
        else:
            self.laser_detected = False

        cv2.circle(frame, (cx, cy), radius, (0, 255, 0), 2)
        cv2.circle(frame, (cx, cy), int(radius * 0.2), (0, 0, 255), 2)

        buf = cv2.flip(frame, 0).tobytes()
        texture = Texture.create(size=(w, h), colorfmt='bgr')
        texture.blit_buffer(buf, colorfmt='bgr', bufferfmt='ubyte')
        self.img_view.texture = texture

    def on_stop(self):
        if self.capture.isOpened():
            self.capture.release()

class LaserApp(App):
    def build(self):
        return LaserGameLayout()

if __name__ == '__main__':
    LaserApp().run()
