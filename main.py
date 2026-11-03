import os
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

# درخواست مجوز دوربین در اندروید
if platform == 'android'
    from android.permissions import request_permissions, Permission
    request_permissions([Permission.CAMERA, Permission.READ_EXTERNAL_STORAGE, Permission.WRITE_EXTERNAL_STORAGE])

class LaserGameLayout(BoxLayout)
    def __init__(self, kwargs)
        super().__init__(orientation='vertical', kwargs)
        
        # ۱. وضعیت بازی
        self.score = 0
        self.shots = 0
        self.last_score = 0
        self.laser_detected = False
        
        # ۲. بارگذاری صداها
        self.snd_bullseye = SoundLoader.load('bullseye.wav')
        self.snd_shot = SoundLoader.load('shot.wav')
        
        # ۳. رابط کاربری (UI)
        self.info_label = Label(
            text=[b]Score 0[b]    Shots 0,
            markup=True,
            size_hint_y=0.1,
            font_size='22sp'
        )
        self.add_widget(self.info_label)
        
        # ویجت نمایش زنده دوربین
        self.img_view = Image(size_hint_y=0.8)
        self.add_widget(self.img_view)
        
        # دکمه ریست امتیاز
        btn_bar = BoxLayout(size_hint_y=0.1)
        btn_reset = Button(text=Reset Score, font_size='18sp')
        btn_reset.bind(on_release=self.reset_game)
        btn_bar.add_widget(btn_reset)
        self.add_widget(btn_bar)
        
        # ۴. اتصال به دوربین گوشی (دوربین پشت معمولاً 0 است)
        self.capture = cv2.VideoCapture(0)
        self.capture.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        self.capture.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        
        # لوپ فریم‌ها (۳۰ فریم بر ثانیه)
        Clock.schedule_interval(self.update, 1.0  30.0)

    def reset_game(self, instance)
        self.score = 0
        self.shots = 0
        self.last_score = 0
        self.update_label()

    def update_label(self)
        self.info_label.text = f[b]Score {self.score}[b]    Shots {self.shots}  (+{self.last_score})

    def calculate_score(self, x, y, cx, cy, radius)
        محاسبه امتیاز بر اساس فاصله از مرکز سیبل
        dist = np.hypot(x - cx, y - cy)
        ratio = dist  radius
        if ratio = 0.2
            return 10
        elif ratio = 0.4
            return 8
        elif ratio = 0.6
            return 6
        elif ratio = 0.8
            return 4
        elif ratio = 1.0
            return 2
        return 0

    def update(self, dt)
        ret, frame = self.capture.read()
        if not ret
            return
            
        h, w, _ = frame.shape
        center_x, center_y = w  2, h  2
        target_radius = int(min(w, h)  0.42)
        
        # پردازش تصویر برای یافتن نقطه لیزر (HSV)
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        # ماسک برای رنگ قرمز در دو بازه طیف رنگ
        lower_red1 = np.array([0, 120, 200])
        upper_red1 = np.array([10, 255, 255])
        lower_red2 = np.array([170, 120, 200])
        upper_red2 = np.array([180, 255, 255])
        
        mask = cv2.bitwise_or(
            cv2.inRange(hsv, lower_red1, upper_red1),
            cv2.inRange(hsv, lower_red2, upper_red2)
        )
        
        # پیدا کردن روشن‌ترین نقطه لیزر
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY), mask=mask)
        
        if max_val  240  # تشخیص شلیک لیزر
            if not self.laser_detected
                lx, ly = max_loc
                pts = self.calculate_score(lx, ly, center_x, center_y, target_radius)
                
                if pts  0
                    self.score += pts
                    self.shots += 1
                    self.last_score = pts
                    self.update_label()
                    
                    # پخش صدای متناسب
                    if pts == 10 and self.snd_bullseye
                        self.snd_bullseye.play()
                    elif self.snd_shot
                        self.snd_shot.play()
                        
                self.laser_detected = True
        else
            self.laser_detected = False

        # رسم حلقه‌های سیبل روی پیش‌نمایش تصویر
        cv2.circle(frame, (center_x, center_y), target_radius, (0, 255, 0), 2)
        cv2.circle(frame, (center_x, center_y), int(target_radius  0.2), (0, 0, 255), 2)
        cv2.drawMarker(frame, (center_x, center_y), (255, 255, 255), cv2.MARKER_CROSS, 20, 2)

        # تبدیل فریم OpenCV به بافت قابل نمایش در Kivy
        buf = cv2.flip(frame, 0).tobytes()
        texture = Texture.create(size=(frame.shape[1], frame.shape[0]), colorfmt='bgr')
        texture.blit_buffer(buf, colorfmt='bgr', bufferfmt='ubyte')
        self.img_view.texture = texture

    def on_stop(self)
        if self.capture.isOpened()
            self.capture.release()

class LaserApp(App)
    def build(self)
        return LaserGameLayout()

    def on_stop(self)
        self.root.on_stop()

if __name__ == '__main__'
    LaserApp().run()
