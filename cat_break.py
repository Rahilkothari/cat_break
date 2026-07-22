import sys
import os
import glob
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QSystemTrayIcon, QMenu, QAction
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QPixmap, QBitmap, QIcon

class CatBreakWindow(QWidget):
    def __init__(self):
        super().__init__()
        # Keep window on top and frameless
        # We DO NOT use WA_TransparentForMouseEvents here because we want the cat to be clickable
        self.setWindowFlags(Qt.WindowStaysOnTopHint | Qt.FramelessWindowHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        screen = QApplication.primaryScreen().geometry()
        self.screen_w = screen.width()
        self.screen_h = screen.height()
        
        self.video_w = self.screen_w
        self.video_h = int(self.screen_w * 9 / 16)
        self.y_pos = self.screen_h - self.video_h
        
        self.initUI()
        self.load_frames()
        
    def initUI(self):
        self.resize(self.video_w, self.video_h)
        self.move(0, self.y_pos)
        
        self.image_label = QLabel(self)
        self.image_label.setGeometry(0, 0, self.video_w, self.video_h)
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setAttribute(Qt.WA_TransparentForMouseEvents)
        
        self.frame_timer = QTimer(self)
        self.frame_timer.timeout.connect(self.update_frame)
        self.current_frame = 0
        
        self.sleep_timer = QTimer(self)
        self.sleep_timer.timeout.connect(self.wake_up)
        self.sleep_timer.setSingleShot(True)
        
        self.is_sleeping = False
        self.has_slept = False
        
    def load_frames(self):
        self.frames = []
        if getattr(sys, 'frozen', False):
            base_dir = sys._MEIPASS
        else:
            base_dir = os.path.dirname(os.path.abspath(__file__))
        frames_dir = os.path.join(base_dir, 'cat_frames')
        
        if os.path.exists(frames_dir):
            print("Loading cat frames...")
            frame_files = sorted(glob.glob(os.path.join(frames_dir, '*.png')))
            for f in frame_files:
                pixmap = QPixmap(f)
                if not pixmap.isNull():
                    scaled = pixmap.scaled(self.video_w, self.video_h, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                    self.frames.append(scaled)
            print(f"Loaded {len(self.frames)} frames.")
        else:
            print(f"Directory not found: {frames_dir}")
            
    def show_window(self):
        if not self.frames:
            print("No frames available to show.")
            return
            
        self.current_frame = 0
        self.is_sleeping = False
        self.has_slept = False
        self.image_label.setPixmap(self.frames[0])
        self.setMask(self.frames[0].mask())
        self.show()
        
        # 12 fps = ~83ms per frame
        self.frame_timer.start(83)
        
    def update_frame(self):
        if self.current_frame == 65 and not self.has_slept:
            # Reached the sleeping frame
            self.is_sleeping = True
            self.frame_timer.stop()
            # Sleep for 1 minute (60000 ms)
            self.sleep_timer.start(60000)
            return

        self.current_frame += 1
        if self.current_frame >= len(self.frames):
            # Animation finished
            self.frame_timer.stop()
            self.hide()
            return
            
        pixmap = self.frames[self.current_frame]
        self.image_label.setPixmap(pixmap)
        
        # Make the transparent parts click-through and the cat clickable
        # Generating a mask might be slow if done too often, but for 12fps it's usually fine
        if pixmap.mask() and not pixmap.mask().isNull():
            self.setMask(pixmap.mask())

    def wake_up(self):
        if self.is_sleeping:
            self.is_sleeping = False
            self.has_slept = True
            self.sleep_timer.stop()
            # Resume animation
            self.frame_timer.start(83)
            
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            # If the user clicks the cat while it's sleeping, wake it up!
            if self.is_sleeping:
                self.wake_up()

class CatBreakApp:
    def __init__(self):
        self.app = QApplication(sys.argv)
        self.app.setQuitOnLastWindowClosed(False)
        self.window = CatBreakWindow()
        
        # Show immediately on startup
        self.window.show_window()
        
        if getattr(sys, 'frozen', False):
            base_dir = sys._MEIPASS
        else:
            base_dir = os.path.dirname(os.path.abspath(__file__))
            
        icon_path = os.path.join(base_dir, 'cat_frames', 'frame_0000.png')
        
        # Setup system tray icon
        self.tray_icon = QSystemTrayIcon(self.app)
        if os.path.exists(icon_path):
            self.tray_icon.setIcon(QIcon(icon_path))
            
        # Create tray menu
        tray_menu = QMenu()
        
        show_action = QAction("Show Cat", self.app)
        show_action.triggered.connect(self.window.show_window)
        tray_menu.addAction(show_action)
        
        quit_action = QAction("Quit", self.app)
        quit_action.triggered.connect(self.app.quit)
        tray_menu.addAction(quit_action)
        
        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.setToolTip("Cat Break Timer")
        self.tray_icon.show()
        
        self.timer = QTimer()
        self.timer.timeout.connect(self.window.show_window)
        # Show every 1 hour (3600000 ms)
        self.timer.start(3600000)
        
    def run(self):
        sys.exit(self.app.exec_())

if __name__ == '__main__':
    app = CatBreakApp()
    app.run()
