# import warnings
# # Ignore the specific Protobuf UserWarning
# warnings.filterwarnings("ignore", message="SymbolDatabase.GetPrototype() is deprecated")

# import cv2
# import mediapipe as mp
# import numpy as np
# import win32com.client
# import pythoncom
# import tkinter as tk
# from tkinter import Label, Button, Text
# from PIL import Image, ImageTk
# import joblib
# import time
# import threading
# import queue
# import pandas as pd

# # ==================== 🧠 Load Trained Model ====================
# MODEL_PATH = "gesture_model.pkl"
# model = joblib.load(MODEL_PATH)
# try:
#     feature_names = pd.read_csv("gesture_data.csv").columns[1:]
#     print(f"✅ Model and {len(feature_names)} feature names loaded successfully!")
# except FileNotFoundError:
#     print("❌ ERROR: gesture_data.csv not found! Please run gesture_train.py first.")
#     feature_names = []
# except Exception as e:
#     print(f"❌ Error loading feature names: {e}")
#     feature_names = []

# # ==================== 🎤 Voice System (Thread-Safe) ====================
# speech_queue = queue.Queue()
# stop_threads = False
# is_muted = False

# def speak_text_async(text):
#     if not is_muted:
#         speech_queue.put(text)

# def speech_worker():
#     pythoncom.CoInitialize()
#     speak = win32com.client.Dispatch("SAPI.SpVoice")
#     zira_voice = None
#     for voice in speak.GetVoices():
#         if "zira" in voice.GetDescription().lower():
#             zira_voice = voice
#             break
#     if zira_voice:
#         speak.Voice = zira_voice
#     speak.Rate = 2
#     speak.Volume = 100
#     print("✅ Zira voice ready.")

#     while not stop_threads:
#         text = speech_queue.get()
#         if text == "STOP":
#             break
#         try:
#             print(f"🎤 Speaking: {text}")
#             speak.Speak(text)
#         except Exception as e:
#             print(f"⚠️ Voice error: {e}")
#         speech_queue.task_done()

# threading.Thread(target=speech_worker, daemon=True).start()

# # ==================== ✋ Mediapipe Setup ====================
# mp_hands = mp.solutions.hands
# hands = mp_hands.Hands(max_num_hands=1, min_detection_confidence=0.7)
# mp_draw = mp.solutions.drawing_utils

# # ==================== 🎥 Camera & Variables ====================
# cap = None
# running = False
# prev_prediction = ""
# last_spoken_time = 0
# frame_queue = queue.Queue(maxsize=1)
# camera_thread = None

# # ==================== ✋ Extract Hand Landmarks ====================
# def extract_landmarks(hand_landmarks):
#     landmarks = []
#     for lm in hand_landmarks.landmark:
#         landmarks.extend([lm.x, lm.y])
#     return np.array(landmarks).reshape(1, -1)

# # ==================== 🧠 Predict Gesture (NOW RETURNS CONFIDENCE) ====================
# def predict_gesture(landmarks):
#     try:
#         landmarks_df = pd.DataFrame(landmarks, columns=feature_names)
#         probabilities = model.predict_proba(landmarks_df)[0]
#         max_confidence = np.max(probabilities)
#         prediction_index = np.argmax(probabilities)
#         prediction_label = model.classes_[prediction_index]
        
#         if max_confidence > 0.60: # 60% threshold
#             return prediction_label, max_confidence
#         else:
#             return "Thinking...", max_confidence
#     except Exception as e:
#         return "Error", 0.0

# # ==================== 🎥 NEW: Camera Thread Function ====================
# def camera_worker():
#     global cap, running, prev_prediction, last_spoken_time
    
#     cap = cv2.VideoCapture(0)
    
#     while running:
#         ret, frame = cap.read()
#         if not ret:
#             time.sleep(0.1)
#             continue

#         img_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
#         results = hands.process(img_rgb)

#         prediction = ""
#         confidence = 0.0

#         if results.multi_hand_landmarks:
#             for hand_landmarks in results.multi_hand_landmarks:
#                 mp_draw.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)
#                 landmarks = extract_landmarks(hand_landmarks)
#                 prediction, confidence = predict_gesture(landmarks)

#         root.after(0, lambda: confidence_label.config(text=f"Confidence: {confidence*100:0.1f}%"))
#         root.after(0, lambda: detected_label.config(text=f"Detected: {prediction}"))
        
#         if prediction != "" and prediction != "Thinking...":
#             current_time = time.time()
#             if prediction != prev_prediction:
#                 print(f"🖐️ Detected: {prediction}")
#                 while not speech_queue.empty():
#                     try: speech_queue.get_nowait()
#                     except queue.Empty: continue
#                 speak_text_async(prediction)
#                 root.after(0, lambda p=prediction: add_to_history(p))
#                 prev_prediction = prediction
#                 last_spoken_time = current_time
#             elif current_time - last_spoken_time > 3:
#                 print(f"🖐️ (Repeating): {prediction}")
#                 speak_text_async(prediction)
#                 last_spoken_time = current_time
#         else:
#             prev_prediction = ""

#         frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
#         if not frame_queue.full():
#             frame_queue.put(frame_rgb)
    
#     cap.release()
#     print("Camera thread stopped.")

# # ==================== GUI Update Loop (Now simple!) ====================
# def update_frame():
#     try:
#         frame = frame_queue.get_nowait()
#         img = Image.fromarray(frame)
#         img = img.resize((640, 480), Image.LANCZOS)
#         imgtk = ImageTk.PhotoImage(image=img)
        
#         video_label.imgtk = imgtk
#         video_label.configure(image=imgtk, text="")
#     except queue.Empty:
#         pass
    
#     if running:
#         root.after(20, update_frame)

# # ==================== GUI Button Functions ====================
# def start_camera():
#     global running, camera_thread
#     if not running:
#         running = True
#         camera_thread = threading.Thread(target=camera_worker, daemon=True)
#         camera_thread.start()
        
#         # --- NEW: Use aesthetic disabled color ---
#         start_btn.config(state=tk.DISABLED, bg=BTN_START_DISABLED_BG, relief=tk.FLAT)
#         stop_btn.config(state=tk.NORMAL, bg=BTN_STOP_BG, relief=tk.RAISED)
        
#         update_frame()

# def stop_camera():
#     global running
#     running = False
    
#     # --- NEW: Use aesthetic disabled color ---
#     start_btn.config(state=tk.NORMAL, bg=BTN_START_BG, relief=tk.RAISED)
#     stop_btn.config(state=tk.DISABLED, bg=BTN_STOP_DISABLED_BG, relief=tk.FLAT)
    
#     root.after(50, lambda: video_label.config(image='', text="🎥 Camera feed stopped.",
#                        font=(FONT_FAMILY, 14, "italic"), bg="#000000", fg=ACCENT_COLOR))

# def close_app():
#     global running, stop_threads
#     running = False
#     stop_threads = True
#     speech_queue.put("STOP")
#     root.destroy()

# def toggle_mute():
#     global is_muted
#     is_muted = not is_muted
#     if is_muted:
#         mute_btn.config(text="🔇 Unmute", bg=BTN_STOP_BG, relief=tk.SUNKEN)
#         mute_btn.bind("<Leave>", lambda e: on_leave(e, "mute_pressed"))
#     else:
#         mute_btn.config(text="🔊 Mute", bg=BTN_MUTE_BG, relief=tk.RAISED)
#         mute_btn.bind("<Leave>", lambda e: on_leave(e, "mute_raised"))

# def add_to_history(prediction):
#     history_log.config(state=tk.NORMAL)
#     history_log.insert("1.0", f"{prediction}\n") 
#     history_log.delete("6.0", tk.END) 
#     history_log.config(state=tk.DISABLED)

# # ==================== GUI Setup (Professional GRID Layout) ====================
# BG_COLOR = "#0A2342"       # Deep Navy Blue
# TEXT_COLOR = "#FFFFFF"     # White
# ACCENT_COLOR = "#2CA58D"   # Sea Green
# BTN_START_BG = "#2ECC71"   # Green
# BTN_STOP_BG = "#F39C12"    # Orange
# BTN_EXIT_BG = "#E74C3C"    # Red
# BTN_TEXT_COLOR = "#FFFFFF" # White
# BTN_MUTE_BG = "#555555"    # Gray for mute
# FONT_FAMILY = "Segoe UI"
# BTN_BORDER_WIDTH = 3

# # --- NEW AESTHETIC COLORS ---
# BTN_START_DISABLED_BG = "#1A5A38" # Dark Green
# BTN_STOP_DISABLED_BG = "#9C640C"  # Dark Orange
# BTN_MUTE_HOVER = "#888888"        # Lighter Gray

# BTN_START_HOVER = "#39FF14"
# BTN_STOP_HOVER = "#D35400"        # <-- YOUR NEW DARKER HOVER
# BTN_EXIT_HOVER = "#FF5733"
# # --- END NEW COLORS ---

# root = tk.Tk()
# root.title("AI Gesture Assistant - Dashboard v3")
# root.configure(bg=BG_COLOR)

# root.grid_rowconfigure(0, weight=1)
# root.grid_columnconfigure(0, weight=3)
# root.grid_columnconfigure(1, weight=1)

# left_frame = tk.Frame(root, bg="#000000", relief=tk.SUNKEN, borderwidth=2)
# left_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
# left_frame.grid_propagate(False)

# video_label = Label(left_frame, text="🎥 Camera feed will appear here", 
#                     font=(FONT_FAMILY, 18, "italic"), 
#                     bg="#000000", fg=ACCENT_COLOR)
# video_label.pack(expand=True)

# right_frame = tk.Frame(root, bg=BG_COLOR)
# right_frame.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)

# right_frame.grid_columnconfigure(0, weight=1)
# right_frame.grid_rowconfigure(5, weight=1) # Spacer row

# title_label = Label(right_frame, text="🤖 AI Assistant", 
#                     font=(FONT_FAMILY, 24, "bold"), bg=BG_COLOR, fg=TEXT_COLOR)
# title_label.grid(row=0, column=0, pady=15)

# detected_label = Label(right_frame, text="Detected: None", 
#                        font=(FONT_FAMILY, 22, "bold"), bg=BG_COLOR, fg=ACCENT_COLOR)
# detected_label.grid(row=1, column=0, pady=(10, 0), sticky="w")

# confidence_label = Label(right_frame, text="Confidence: 0.0%", 
#                          font=(FONT_FAMILY, 16, "italic"), bg=BG_COLOR, fg=TEXT_COLOR)
# confidence_label.grid(row=2, column=0, pady=(0, 20), sticky="w")

# history_label = Label(right_frame, text="History:", 
#                       font=(FONT_FAMILY, 14, "bold"), bg=BG_COLOR, fg=TEXT_COLOR)
# history_label.grid(row=3, column=0, sticky="w")

# history_log = Text(right_frame, height=10, 
#                    font=(FONT_FAMILY, 12), bg="#1c3a5e", fg=TEXT_COLOR, 
#                    relief="flat", borderwidth=0, state=tk.DISABLED)
# history_log.grid(row=4, column=0, pady=5, sticky="nsew")

# tk.Label(right_frame, text="", bg=BG_COLOR).grid(row=5, column=0, sticky="nsew")

# mute_btn = Button(right_frame, text="🔊 Mute", command=toggle_mute,
#                   font=(FONT_FAMILY, 14), bg=BTN_MUTE_BG, fg=BTN_TEXT_COLOR,
#                   relief=tk.RAISED, borderwidth=BTN_BORDER_WIDTH, pady=5)
# mute_btn.grid(row=6, column=0, pady=10, sticky="ew")

# button_frame = tk.Frame(right_frame, bg=BG_COLOR)
# button_frame.grid(row=7, column=0, pady=10)

# start_btn = Button(button_frame, text="▶️ Start", command=start_camera, 
#                    font=(FONT_FAMILY, 14, "bold"), bg=BTN_START_BG, fg=BTN_TEXT_COLOR, 
#                    width=12, state=tk.NORMAL, 
#                    relief=tk.RAISED, borderwidth=BTN_BORDER_WIDTH, pady=5)
# start_btn.grid(row=0, column=0, padx=5)

# stop_btn = Button(button_frame, text="⏸️ Stop", command=stop_camera, 
#                   font=(FONT_FAMILY, 14, "bold"), bg=BTN_STOP_DISABLED_BG, fg=BTN_TEXT_COLOR, 
#                   width=12, state=tk.DISABLED,
#                   relief=tk.FLAT, borderwidth=BTN_BORDER_WIDTH, pady=5) # <-- NEW: Starts with dark orange bg
# stop_btn.grid(row=0, column=1, padx=5)

# exit_btn = Button(button_frame, text="❌ Exit", command=close_app, 
#                   font=(FONT_FAMILY, 14, "bold"), bg=BTN_EXIT_BG, fg=BTN_TEXT_COLOR, 
#                   width=12, relief=tk.RAISED, borderwidth=BTN_BORDER_WIDTH, pady=5)
# exit_btn.grid(row=0, column=2, padx=5)


# # --- Hover Effect Functions ---
# def on_enter(e, button_type):
#     if button_type == "start" and start_btn['state'] == tk.NORMAL:
#         start_btn['background'] = BTN_START_HOVER
#     elif button_type == "stop" and stop_btn['state'] == tk.NORMAL:
#         stop_btn['background'] = BTN_STOP_HOVER
#     elif button_type == "exit":
#         exit_btn['background'] = BTN_EXIT_HOVER
#     elif button_type == "mute":
#         if mute_btn['relief'] == tk.RAISED:
#             mute_btn['background'] = BTN_MUTE_HOVER

# def on_leave(e, button_type):
#     # --- NEW: Smart leave function ---
#     if button_type == "start":
#         if start_btn['state'] == tk.NORMAL:
#             start_btn['background'] = BTN_START_BG
#         else:
#             start_btn['background'] = BTN_START_DISABLED_BG
#     elif button_type == "stop":
#         if stop_btn['state'] == tk.NORMAL:
#             stop_btn['background'] = BTN_STOP_BG
#         else:
#             stop_btn['background'] = BTN_STOP_DISABLED_BG
#     elif button_type == "exit":
#         exit_btn['background'] = BTN_EXIT_BG
#     elif button_type == "mute_raised":
#         mute_btn['background'] = BTN_MUTE_BG
#     elif button_type == "mute_pressed":
#         mute_btn['background'] = BTN_STOP_BG
#     # --- END NEW ---


# start_btn.bind("<Enter>", lambda e: on_enter(e, "start"))
# start_btn.bind("<Leave>", lambda e: on_leave(e, "start"))

# stop_btn.bind("<Enter>", lambda e: on_enter(e, "stop"))
# stop_btn.bind("<Leave>", lambda e: on_leave(e, "stop"))

# exit_btn.bind("<Enter>", lambda e: on_enter(e, "exit"))
# exit_btn.bind("<Leave>", lambda e: on_leave(e, "exit"))

# # --- NEW: Updated mute bindings ---
# mute_btn.bind("<Enter>", lambda e: on_enter(e, "mute"))
# mute_btn.bind("<Leave>", lambda e: on_leave(e, "mute_raised"))

# root.mainloop()


import warnings
warnings.filterwarnings("ignore", message="SymbolDatabase.GetPrototype() is deprecated")

import cv2
import mediapipe as mp
import numpy as np
import win32com.client
import pythoncom
import tkinter as tk
from tkinter import Label, Button, Text
from PIL import Image, ImageTk
import joblib
import time
import threading
import queue
import pandas as pd

MODEL_PATH = "gesture_model.pkl"
model = joblib.load(MODEL_PATH)
try:
    feature_names = pd.read_csv("gesture_data.csv").columns[1:]
    print(f"✅ Model and {len(feature_names)} feature names loaded successfully!")
except FileNotFoundError:
    print("❌ ERROR: gesture_data.csv not found! Please run gesture_train.py first.")
    feature_names = []
except Exception as e:
    print(f"❌ Error loading feature names: {e}")
    feature_names = []

speech_queue = queue.Queue()
stop_threads = False
is_muted = False

def speak_text_async(text):
    if not is_muted:
        speech_queue.put(text)

def speech_worker():
    pythoncom.CoInitialize()
    speak = win32com.client.Dispatch("SAPI.SpVoice")
    zira_voice = None
    for voice in speak.GetVoices():
        if "zira" in voice.GetDescription().lower():
            zira_voice = voice
            break
    if zira_voice:
        speak.Voice = zira_voice
    speak.Rate = 2
    speak.Volume = 100
    print("✅ Zira voice ready.")

    while not stop_threads:
        text = speech_queue.get()
        if text == "STOP":
            break
        try:
            print(f"🎤 Speaking: {text}")
            speak.Speak(text)
        except Exception as e:
            print(f"⚠️ Voice error: {e}")
        speech_queue.task_done()

threading.Thread(target=speech_worker, daemon=True).start()

mp_hands = mp.solutions.hands
hands = mp_hands.Hands(max_num_hands=1, min_detection_confidence=0.7)
mp_draw = mp.solutions.drawing_utils

cap = None
running = False
prev_prediction = ""
last_spoken_time = 0
frame_queue = queue.Queue(maxsize=1)
camera_thread = None

def extract_landmarks(hand_landmarks):
    landmarks = []
    for lm in hand_landmarks.landmark:
        landmarks.extend([lm.x, lm.y])
    return np.array(landmarks).reshape(1, -1)

def predict_gesture(landmarks):
    try:
        landmarks_df = pd.DataFrame(landmarks, columns=feature_names)
        probabilities = model.predict_proba(landmarks_df)[0]
        max_confidence = np.max(probabilities)
        prediction_index = np.argmax(probabilities)
        prediction_label = model.classes_[prediction_index]
        
        if max_confidence > 0.60:
            return prediction_label, max_confidence
        else:
            return "Thinking...", max_confidence
    except Exception as e:
        return "Error", 0.0

def camera_worker():
    global cap, running, prev_prediction, last_spoken_time
    
    cap = cv2.VideoCapture(0)
    
    while running:
        ret, frame = cap.read()
        if not ret:
            time.sleep(0.1)
            continue

        img_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = hands.process(img_rgb)

        prediction = ""
        confidence = 0.0

        if results.multi_hand_landmarks:
            for hand_landmarks in results.multi_hand_landmarks:
                mp_draw.draw_landmarks(frame, hand_landmarks, mp_hands.HAND_CONNECTIONS)
                landmarks = extract_landmarks(hand_landmarks)
                prediction, confidence = predict_gesture(landmarks)

        root.after(0, lambda: confidence_label.config(text=f"Confidence: {confidence*100:0.1f}%"))
        root.after(0, lambda: detected_label.config(text=f"Detected: {prediction}"))
        
        if prediction != "" and prediction != "Thinking...":
            current_time = time.time()
            if prediction != prev_prediction:
                print(f"🖐️ Detected: {prediction}")
                while not speech_queue.empty():
                    try: speech_queue.get_nowait()
                    except queue.Empty: continue
                speak_text_async(prediction)
                root.after(0, lambda p=prediction: add_to_history(p))
                prev_prediction = prediction
                last_spoken_time = current_time
            elif current_time - last_spoken_time > 3:
                print(f"🖐️ (Repeating): {prediction}")
                speak_text_async(prediction)
                last_spoken_time = current_time
        else:
            prev_prediction = ""

        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        if not frame_queue.full():
            frame_queue.put(frame_rgb)
    
    cap.release()
    print("Camera thread stopped.")

def update_frame():
    try:
        frame = frame_queue.get_nowait()
        img = Image.fromarray(frame)
        img = img.resize((640, 480), Image.LANCZOS)
        imgtk = ImageTk.PhotoImage(image=img)
        
        video_label.imgtk = imgtk
        video_label.configure(image=imgtk, text="")
    except queue.Empty:
        pass
    
    if running:
        root.after(20, update_frame)

def start_camera():
    global running, camera_thread
    if not running:
        running = True
        camera_thread = threading.Thread(target=camera_worker, daemon=True)
        camera_thread.start()
        
        start_btn.config(state=tk.DISABLED, bg=BTN_START_DISABLED_BG, relief=tk.FLAT)
        stop_btn.config(state=tk.NORMAL, bg=BTN_STOP_BG, relief=tk.RAISED)
        
        update_frame()

def stop_camera():
    global running
    running = False
    
    start_btn.config(state=tk.NORMAL, bg=BTN_START_BG, relief=tk.RAISED)
    stop_btn.config(state=tk.DISABLED, bg=BTN_STOP_DISABLED_BG, relief=tk.FLAT)
    
    root.after(50, lambda: video_label.config(image='', text="🎥 Camera feed stopped.",
                       font=(FONT_FAMILY, 14, "italic"), bg="#000000", fg=ACCENT_COLOR))

def close_app():
    global running, stop_threads
    running = False
    stop_threads = True
    speech_queue.put("STOP")
    root.destroy()

def toggle_mute():
    global is_muted
    is_muted = not is_muted
    if is_muted:
        mute_btn.config(text="🔇 Unmute", bg=BTN_STOP_BG, relief=tk.SUNKEN)
        mute_btn.bind("<Leave>", lambda e: on_leave(e, "mute_pressed"))
    else:
        mute_btn.config(text="🔊 Mute", bg=BTN_MUTE_BG, relief=tk.RAISED)
        mute_btn.bind("<Leave>", lambda e: on_leave(e, "mute_raised"))

def add_to_history(prediction):
    history_log.config(state=tk.NORMAL)
    history_log.insert("1.0", f"{prediction}\n") 
    history_log.delete("6.0", tk.END) 
    history_log.config(state=tk.DISABLED)

BG_COLOR = "#0A2342"
TEXT_COLOR = "#FFFFFF"
ACCENT_COLOR = "#2CA58D"
BTN_START_BG = "#2ECC71"
BTN_STOP_BG = "#F39C12"
BTN_EXIT_BG = "#E74C3C"
BTN_TEXT_COLOR = "#FFFFFF"
BTN_MUTE_BG = "#555555"
FONT_FAMILY = "Segoe UI"
BTN_BORDER_WIDTH = 3

BTN_START_DISABLED_BG = "#1A5A38"
BTN_STOP_DISABLED_BG = "#9C640C"
BTN_MUTE_HOVER = "#888888"

BTN_START_HOVER = "#39FF14"
BTN_STOP_HOVER = "#D35400"
BTN_EXIT_HOVER = "#FF5733"

root = tk.Tk()
root.title("AI Gesture Assistant - Dashboard v3")
root.configure(bg=BG_COLOR)

root.grid_rowconfigure(0, weight=1)
root.grid_columnconfigure(0, weight=3)
root.grid_columnconfigure(1, weight=1)

left_frame = tk.Frame(root, bg="#000000", relief=tk.SUNKEN, borderwidth=2)
left_frame.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)
left_frame.grid_propagate(False)

video_label = Label(left_frame, text="🎥 Camera feed will appear here", 
                    font=(FONT_FAMILY, 18, "italic"), 
                    bg="#000000", fg=ACCENT_COLOR)
video_label.pack(expand=True)

right_frame = tk.Frame(root, bg=BG_COLOR)
right_frame.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)

right_frame.grid_columnconfigure(0, weight=1)
right_frame.grid_rowconfigure(5, weight=1)

title_label = Label(right_frame, text="🤖 AI Assistant", 
                    font=(FONT_FAMILY, 24, "bold"), bg=BG_COLOR, fg=TEXT_COLOR)
title_label.grid(row=0, column=0, pady=15)

detected_label = Label(right_frame, text="Detected: None", 
                       font=(FONT_FAMILY, 22, "bold"), bg=BG_COLOR, fg=ACCENT_COLOR)
detected_label.grid(row=1, column=0, pady=(10, 0), sticky="w")

confidence_label = Label(right_frame, text="Confidence: 0.0%", 
                         font=(FONT_FAMILY, 16, "italic"), bg=BG_COLOR, fg=TEXT_COLOR)
confidence_label.grid(row=2, column=0, pady=(0, 20), sticky="w")

history_label = Label(right_frame, text="History:", 
                      font=(FONT_FAMILY, 14, "bold"), bg=BG_COLOR, fg=TEXT_COLOR)
history_label.grid(row=3, column=0, sticky="w")

history_log = Text(right_frame, height=10, 
                   font=(FONT_FAMILY, 12), bg="#1c3a5e", fg=TEXT_COLOR, 
                   relief="flat", borderwidth=0, state=tk.DISABLED)
history_log.grid(row=4, column=0, pady=5, sticky="nsew")

tk.Label(right_frame, text="", bg=BG_COLOR).grid(row=5, column=0, sticky="nsew")

mute_btn = Button(right_frame, text="🔊 Mute", command=toggle_mute,
                  font=(FONT_FAMILY, 14), bg=BTN_MUTE_BG, fg=BTN_TEXT_COLOR,
                  relief=tk.RAISED, borderwidth=BTN_BORDER_WIDTH, pady=5)
mute_btn.grid(row=6, column=0, pady=10, sticky="ew")

button_frame = tk.Frame(right_frame, bg=BG_COLOR)
button_frame.grid(row=7, column=0, pady=10)

start_btn = Button(button_frame, text="▶️ Start", command=start_camera, 
                   font=(FONT_FAMILY, 14, "bold"), bg=BTN_START_BG, fg=BTN_TEXT_COLOR, 
                   width=12, state=tk.NORMAL, 
                   relief=tk.RAISED, borderwidth=BTN_BORDER_WIDTH, pady=5)
start_btn.grid(row=0, column=0, padx=5)

stop_btn = Button(button_frame, text="⏸️ Stop", command=stop_camera, 
                  font=(FONT_FAMILY, 14, "bold"), bg=BTN_STOP_DISABLED_BG, fg=BTN_TEXT_COLOR, 
                  width=12, state=tk.DISABLED,
                  relief=tk.FLAT, borderwidth=BTN_BORDER_WIDTH, pady=5)
stop_btn.grid(row=0, column=1, padx=5)

exit_btn = Button(button_frame, text="❌ Exit", command=close_app, 
                  font=(FONT_FAMILY, 14, "bold"), bg=BTN_EXIT_BG, fg=BTN_TEXT_COLOR, 
                  width=12, relief=tk.RAISED, borderwidth=BTN_BORDER_WIDTH, pady=5)
exit_btn.grid(row=0, column=2, padx=5)


def on_enter(e, button_type):
    if button_type == "start" and start_btn['state'] == tk.NORMAL:
        start_btn['background'] = BTN_START_HOVER
    elif button_type == "stop" and stop_btn['state'] == tk.NORMAL:
        stop_btn['background'] = BTN_STOP_HOVER
    elif button_type == "exit":
        exit_btn['background'] = BTN_EXIT_HOVER
    elif button_type == "mute":
        if mute_btn['relief'] == tk.RAISED:
            mute_btn['background'] = BTN_MUTE_HOVER

def on_leave(e, button_type):
    if button_type == "start":
        if start_btn['state'] == tk.NORMAL:
            start_btn['background'] = BTN_START_BG
        else:
            start_btn['background'] = BTN_START_DISABLED_BG
    elif button_type == "stop":
        if stop_btn['state'] == tk.NORMAL:
            stop_btn['background'] = BTN_STOP_BG
        else:
            stop_btn['background'] = BTN_STOP_DISABLED_BG
    elif button_type == "exit":
        exit_btn['background'] = BTN_EXIT_BG
    elif button_type == "mute_raised":
        mute_btn['background'] = BTN_MUTE_BG
    elif button_type == "mute_pressed":
        mute_btn['background'] = BTN_STOP_BG


start_btn.bind("<Enter>", lambda e: on_enter(e, "start"))
start_btn.bind("<Leave>", lambda e: on_leave(e, "start"))

stop_btn.bind("<Enter>", lambda e: on_enter(e, "stop"))
stop_btn.bind("<Leave>", lambda e: on_leave(e, "stop"))

exit_btn.bind("<Enter>", lambda e: on_enter(e, "exit"))
exit_btn.bind("<Leave>", lambda e: on_leave(e, "exit"))

mute_btn.bind("<Enter>", lambda e: on_enter(e, "mute"))
mute_btn.bind("<Leave>", lambda e: on_leave(e, "mute_raised"))

root.mainloop()