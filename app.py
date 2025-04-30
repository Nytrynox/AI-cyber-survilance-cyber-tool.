#!/usr/bin/env python3
import os
import sys
import csv
import time
import threading
import cv2
import numpy as np
from datetime import datetime
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from PIL import Image, ImageTk
import random
import math
import json
import re

# Import custom modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
try:
    from modules.recon_engine import ReconEngine
    from modules.identity_profiler import IdentityProfiler
    from modules.phishing_generator import PhishingGenerator
    from modules.fake_popup import FakePopup
    from modules.network_scanner import NetworkScanner
    from modules.packet_sniffer import PacketSniffer
    from modules.keylogger import Keylogger
    from modules.face_tracker import FaceTracker
except ImportError:
    # Handle import errors for modules that might not exist yet
    pass

# Global constants
APP_NAME = "SpecterX"
APP_VERSION = "2.0.0"
LOG_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")

# Ensure log directory exists
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

class ParticleSystem:
    """Creates a matrix-like particle animation effect"""
    def __init__(self, canvas, width, height, color="#00ff00", particle_count=50):
        self.canvas = canvas
        self.width = width
        self.height = height
        self.color = color
        self.particle_count = particle_count
        self.particles = []
        self.active = False
        
    def initialize(self):
        self.particles = []
        for _ in range(self.particle_count):
            particle = {
                "x": random.randint(0, self.width),
                "y": random.randint(0, self.height),
                "speed": random.uniform(1, 5),
                "size": random.randint(1, 3),
                "opacity": random.uniform(0.3, 0.9),
                "direction": random.choice(["down", "right", "left", "up"])
            }
            self.particles.append(particle)
        self.active = True
            
    def update(self):
        if not self.active:
            return
            
        self.canvas.delete("particle")
        
        for particle in self.particles:
            # Update position
            if particle["direction"] == "down":
                particle["y"] += particle["speed"]
                if particle["y"] > self.height:
                    particle["y"] = 0
                    particle["x"] = random.randint(0, self.width)
            elif particle["direction"] == "right":
                particle["x"] += particle["speed"]
                if particle["x"] > self.width:
                    particle["x"] = 0
                    particle["y"] = random.randint(0, self.height)
            elif particle["direction"] == "left":
                particle["x"] -= particle["speed"]
                if particle["x"] < 0:
                    particle["x"] = self.width
                    particle["y"] = random.randint(0, self.height)
            else:  # up
                particle["y"] -= particle["speed"]
                if particle["y"] < 0:
                    particle["y"] = self.height
                    particle["x"] = random.randint(0, self.width)
            
            # Draw particle
            opacity_hex = int(particle["opacity"] * 255)
            # Fix the color format to ensure valid hex color with exactly 6 digits
            color = f"#{opacity_hex:02x}{opacity_hex:02x}{opacity_hex:02x}"
            
            self.canvas.create_oval(
                particle["x"] - particle["size"],
                particle["y"] - particle["size"],
                particle["x"] + particle["size"],
                particle["y"] + particle["size"],
                fill=color,
                outline="",
                tags="particle"
            )

class HexGrid:
    """Creates a futuristic hexagonal grid overlay"""
    def __init__(self, canvas, width, height, color="#00aa00", line_width=1):
        self.canvas = canvas
        self.width = width
        self.height = height
        self.color = color
        self.line_width = line_width
        self.hex_size = 30
        self.active = False
        
    def initialize(self):
        self.active = True
        
    def update(self):
        if not self.active:
            return
            
        self.canvas.delete("hexgrid")
        
        # Calculate hexagon vertices
        def hexagon_vertices(x, y, size):
            vertices = []
            for i in range(6):
                angle_deg = 60 * i - 30
                angle_rad = math.pi / 180 * angle_deg
                vertices.append(x + size * math.cos(angle_rad))
                vertices.append(y + size * math.sin(angle_rad))
            return vertices
        
        # Draw hexagonal grid
        y_offset = self.hex_size * math.sqrt(3) / 2
        for row in range(-1, int(self.height / y_offset) + 2):
            for col in range(-1, int(self.width / self.hex_size) + 2):
                x = col * self.hex_size * 1.5
                y = row * y_offset
                
                # Offset every other row
                if row % 2 == 1:
                    x += self.hex_size * 0.75
                
                if 0 <= x <= self.width and 0 <= y <= self.height:
                    # Vary opacity for visual effect
                    opacity = random.uniform(0.1, 0.3)
                    opacity_hex = int(opacity * 255)
                    color = f"#{opacity_hex:02x}{opacity_hex*2:02x}{opacity_hex:02x}"
                    
                    vertices = hexagon_vertices(x, y, self.hex_size / 2)
                    self.canvas.create_polygon(vertices, 
                                              outline=color, 
                                              fill="", 
                                              width=self.line_width,
                                              tags="hexgrid")

class RadarAnimation:
    """Creates a spinning radar sweep effect"""
    def __init__(self, canvas, cx, cy, radius, color="#00ff00"):
        self.canvas = canvas
        self.cx = cx
        self.cy = cy
        self.radius = radius
        self.color = color
        self.angle = 0
        self.active = False
        
    def initialize(self):
        self.active = True
        
    def update(self):
        if not self.active:
            return
            
        self.canvas.delete("radar")
        
        # Draw the radar circle
        self.canvas.create_oval(
            self.cx - self.radius,
            self.cy - self.radius,
            self.cx + self.radius,
            self.cy + self.radius,
            outline=self.color,
            width=1,
            tags="radar"
        )
        
        # Draw the sweeping line
        end_x = self.cx + self.radius * math.cos(math.radians(self.angle))
        end_y = self.cy + self.radius * math.sin(math.radians(self.angle))
        self.canvas.create_line(
            self.cx, self.cy, end_x, end_y,
            fill=self.color,
            width=2,
            tags="radar"
        )
        
        # Draw the sweep area
        sweep_points = [self.cx, self.cy]
        for a in range(0, int(self.angle), 5):
            x = self.cx + self.radius * math.cos(math.radians(a))
            y = self.cy + self.radius * math.sin(math.radians(a))
            sweep_points.extend([x, y])
        
        if len(sweep_points) > 2:
            self.canvas.create_polygon(
                sweep_points,
                fill=self.color,
                stipple="gray25",  # Use stipple for transparency effect
                outline="",
                tags="radar"
            )
        
        # Update the angle for next frame
        self.angle = (self.angle + 3) % 360

class PulseEffect:
    """Creates a pulsing circle effect"""
    def __init__(self, canvas, x, y, color="#00ff00", max_radius=50):
        self.canvas = canvas
        self.x = x
        self.y = y
        self.color = color
        self.radius = 5
        self.max_radius = max_radius
        self.growing = True
        self.active = False
        
    def initialize(self):
        self.active = True
        self.radius = 5
        self.growing = True
        
    def update(self):
        if not self.active:
            return
            
        self.canvas.delete("pulse")
        
        # Update radius
        if self.growing:
            self.radius += 1
            if self.radius >= self.max_radius:
                self.growing = False
        else:
            self.radius -= 1
            if self.radius <= 5:
                self.growing = True
        
        # Calculate opacity based on radius
        opacity = 1 - (self.radius / self.max_radius)
        opacity_hex = int(opacity * 255)
        color = f"#{opacity_hex:02x}{opacity_hex*2:02x}{opacity_hex:02x}"
        
        # Draw pulse circle
        self.canvas.create_oval(
            self.x - self.radius,
            self.y - self.radius,
            self.x + self.radius,
            self.y + self.radius,
            outline=color,
            width=2,
            tags="pulse"
        )

class FaceTrackingOverlay:
    """Creates a high-tech face tracking overlay animation"""
    def __init__(self, canvas, width, height):
        self.canvas = canvas
        self.width = width
        self.height = height
        self.faces = []
        self.active = False
        
    def initialize(self):
        self.active = True
        
    def update_faces(self, faces):
        """Update face positions from detection"""
        self.faces = faces
        
    def update(self):
        if not self.active:
            return
            
        self.canvas.delete("facetrack")
        
        for face in self.faces:
            x, y, w, h = face
            
            # Draw main rectangle
            self.canvas.create_rectangle(
                x, y, x+w, y+h,
                outline="#00ff00",
                width=1,
                tags="facetrack"
            )
            
            # Draw corner brackets
            bracket_length = min(w, h) * 0.2
            
            # Top-left corner
            self.canvas.create_line(x, y, x+bracket_length, y, fill="#00ff00", width=2, tags="facetrack")
            self.canvas.create_line(x, y, x, y+bracket_length, fill="#00ff00", width=2, tags="facetrack")
            
            # Top-right corner
            self.canvas.create_line(x+w, y, x+w-bracket_length, y, fill="#00ff00", width=2, tags="facetrack")
            self.canvas.create_line(x+w, y, x+w, y+bracket_length, fill="#00ff00", width=2, tags="facetrack")
            
            # Bottom-left corner
            self.canvas.create_line(x, y+h, x+bracket_length, y+h, fill="#00ff00", width=2, tags="facetrack")
            self.canvas.create_line(x, y+h, x, y+h-bracket_length, fill="#00ff00", width=2, tags="facetrack")
            
            # Bottom-right corner
            self.canvas.create_line(x+w, y+h, x+w-bracket_length, y+h, fill="#00ff00", width=2, tags="facetrack")
            self.canvas.create_line(x+w, y+h, x+w, y+h-bracket_length, fill="#00ff00", width=2, tags="facetrack")
            
            # Draw target crosshair at center
            cx, cy = x + w//2, y + h//2
            crosshair_size = min(w, h) * 0.1
            
            self.canvas.create_line(
                cx - crosshair_size, cy, cx + crosshair_size, cy,
                fill="#ff0000", width=1, tags="facetrack"
            )
            self.canvas.create_line(
                cx, cy - crosshair_size, cx, cy + crosshair_size,
                fill="#ff0000", width=1, tags="facetrack"
            )
            
            # Draw scanning animation
            scan_y = (y + (time.time() * 50) % h) % (y + h)
            self.canvas.create_line(
                x, scan_y, x + w, scan_y,
                fill="#00ffff", width=1, tags="facetrack"
            )
            
            # Draw identity text
            self.canvas.create_text(
                x, y - 15,
                text=f"ID: UNKNOWN-{random.randint(1000, 9999)}",
                fill="#00ff00",
                anchor="nw",
                font=("Courier", 8),
                tags="facetrack"
            )
            
            # Draw additional metrics
            metrics = [
                f"CONF: {random.randint(75, 99)}%",
                f"AGE: {random.randint(20, 40)}",
                f"MOOD: {random.choice(['NEUTRAL', 'FOCUSED', 'CONCERNED'])}"
            ]
            
            for i, metric in enumerate(metrics):
                self.canvas.create_text(
                    x, y + h + 5 + (i * 15),
                    text=metric,
                    fill="#00ff00",
                    anchor="nw",
                    font=("Courier", 8),
                    tags="facetrack"
                )

class NetworkGraphAnimation:
    """Creates an animated network connection graph"""
    def __init__(self, canvas, width, height):
        self.canvas = canvas
        self.width = width
        self.height = height
        self.nodes = []
        self.connections = []
        self.active = False
        
    def initialize(self):
        self.active = True
        # Create sample nodes
        center_x, center_y = self.width//2, self.height//2
        
        # Center node (representing the main system)
        self.nodes.append({
            "x": center_x,
            "y": center_y,
            "radius": 20,
            "color": "#ff0000",
            "label": "SYSTEM",
            "pulse": True
        })
        
        # Surrounding nodes (representing connected devices)
        for i in range(8):
            angle = math.radians(i * 45)
            distance = min(self.width, self.height) * 0.35
            
            x = center_x + distance * math.cos(angle)
            y = center_y + distance * math.sin(angle)
            
            self.nodes.append({
                "x": x,
                "y": y,
                "radius": 10,
                "color": "#00aa00",
                "label": f"NODE-{i+1}",
                "pulse": False
            })
            
            # Create connection to center
            self.connections.append({
                "from": 0,
                "to": i + 1,
                "active": random.choice([True, False]),
                "flow_particles": [random.random() for _ in range(3)]
            })
    
    def update(self):
        if not self.active:
            return
            
        self.canvas.delete("network")
        
        # Draw connections first (behind nodes)
        for conn in self.connections:
            from_node = self.nodes[conn["from"]]
            to_node = self.nodes[conn["to"]]
            
            # Draw connection line
            line_color = "#00ff00" if conn["active"] else "#555555"
            self.canvas.create_line(
                from_node["x"], from_node["y"],
                to_node["x"], to_node["y"],
                fill=line_color, width=1,
                dash=(4, 4) if not conn["active"] else None,
                tags="network"
            )
            
            # Draw flow particles if connection is active
            if conn["active"]:
                # Calculate vector
                dx = to_node["x"] - from_node["x"]
                dy = to_node["y"] - from_node["y"]
                distance = math.sqrt(dx*dx + dy*dy)
                
                # Update and draw particles
                for i, pos in enumerate(conn["flow_particles"]):
                    # Update position
                    pos = (pos + 0.02) % 1.0
                    conn["flow_particles"][i] = pos
                    
                    # Calculate particle position
                    px = from_node["x"] + dx * pos
                    py = from_node["y"] + dy * pos
                    
                    # Draw the particle
                    self.canvas.create_oval(
                        px-3, py-3, px+3, py+3,
                        fill="#00ffff", outline="",
                        tags="network"
                    )
        
        # Draw nodes
        for node in self.nodes:
            # Draw node circle
            if node["pulse"]:
                # Central node has pulsing effect
                pulse_radius = node["radius"] + 5 * (0.5 + 0.5 * math.sin(time.time() * 3))
                
                # Outer glow
                self.canvas.create_oval(
                    node["x"] - pulse_radius, node["y"] - pulse_radius,
                    node["x"] + pulse_radius, node["y"] + pulse_radius,
                    outline="#ff6666", width=1,
                    tags="network"
                )
            
            # Node circle
            self.canvas.create_oval(
                node["x"] - node["radius"], node["y"] - node["radius"],
                node["x"] + node["radius"], node["y"] + node["radius"],
                fill=node["color"], outline="#ffffff",
                tags="network"
            )
            
            # Node label
            self.canvas.create_text(
                node["x"], node["y"] + node["radius"] + 10,
                text=node["label"],
                fill="#ffffff",
                font=("Courier", 8),
                tags="network"
            )

class Loading3DAnimation:
    """Creates a 3D rotating cube animation for loading screens"""
    def __init__(self, canvas, x, y, size):
        self.canvas = canvas
        self.x = x
        self.y = y
        self.size = size
        self.angle_x = 0
        self.angle_y = 0
        self.angle_z = 0
        self.active = False
        
        # Define cube vertices (normalized coordinates from -1 to 1)
        self.vertices = [
            [-1, -1, -1],  # 0: back bottom left
            [1, -1, -1],   # 1: back bottom right
            [1, 1, -1],    # 2: back top right
            [-1, 1, -1],   # 3: back top left
            [-1, -1, 1],   # 4: front bottom left
            [1, -1, 1],    # 5: front bottom right
            [1, 1, 1],     # 6: front top right
            [-1, 1, 1]     # 7: front top left
        ]
        
        # Define cube edges as pairs of vertex indices
        self.edges = [
            [0, 1], [1, 2], [2, 3], [3, 0],  # back face
            [4, 5], [5, 6], [6, 7], [7, 4],  # front face
            [0, 4], [1, 5], [2, 6], [3, 7]   # connecting edges
        ]
    
    def initialize(self):
        self.active = True
    
    def update(self):
        if not self.active:
            return
            
        self.canvas.delete("loading3d")
        
        # Update rotation angles
        self.angle_x += 0.03
        self.angle_y += 0.05
        self.angle_z += 0.02
        
        # Rotation matrices
        def rotate_x(point, angle):
            x, y, z = point
            new_y = y * math.cos(angle) - z * math.sin(angle)
            new_z = y * math.sin(angle) + z * math.cos(angle)
            return [x, new_y, new_z]
        
        def rotate_y(point, angle):
            x, y, z = point
            new_x = x * math.cos(angle) + z * math.sin(angle)
            new_z = -x * math.sin(angle) + z * math.cos(angle)
            return [new_x, y, new_z]
        
        def rotate_z(point, angle):
            x, y, z = point
            new_x = x * math.cos(angle) - y * math.sin(angle)
            new_y = x * math.sin(angle) + y * math.cos(angle)
            return [new_x, new_y, z]
        
        # Project 3D to 2D
        projected_vertices = []
        for vertex in self.vertices:
            # Apply rotations
            rotated = rotate_x(vertex, self.angle_x)
            rotated = rotate_y(rotated, self.angle_y)
            rotated = rotate_z(rotated, self.angle_z)
            
            # Simple scale and projection
            scale = self.size / (4 - rotated[2])  # Perspective division
            x_proj = rotated[0] * scale + self.x
            y_proj = rotated[1] * scale + self.y
            
            projected_vertices.append([x_proj, y_proj, rotated[2]])
        
        # Draw edges with depth-based color
        for edge in self.edges:
            v1 = projected_vertices[edge[0]]
            v2 = projected_vertices[edge[1]]
            
            # Calculate average z for depth
            z_avg = (v1[2] + v2[2]) / 2
            
            # Map z to color (further back is darker)
            intensity = int(192 * (z_avg + 1) / 2) + 64  # Map -1,1 to 64-255
            color = f"#{intensity:02x}{intensity*2:02x}{intensity:02x}"
            
            # Draw the edge
            self.canvas.create_line(
                v1[0], v1[1], v2[0], v2[1],
                fill=color, width=2,
                tags="loading3d"
            )
        
        # Draw vertices with depth-based size
        for vertex in projected_vertices:
            # Map z to size (closer is larger)
            size = 3 + 2 * (vertex[2] + 1)
            
            # Map z to color
            intensity = int(192 * (vertex[2] + 1) / 2) + 64
            color = f"#{intensity:02x}{intensity*2:02x}{intensity:02x}"
            
            self.canvas.create_oval(
                vertex[0] - size/2, vertex[1] - size/2,
                vertex[0] + size/2, vertex[1] + size/2,
                fill=color, outline="",
                tags="loading3d"
            )

class SpecterXApp:
    def __init__(self):
        # Initialize flags and states
        self.webcam_active = False
        self.network_scanning = False
        self.keylogging_active = False
        self.recording_active = False
        self.emotion_detection_active = False
        self.face_tracking_active = False
        
        # Initialize module instances
        try:
            self.recon_engine = ReconEngine()
            self.identity_profiler = IdentityProfiler()
            self.phishing_generator = PhishingGenerator()
            self.fake_popup = FakePopup()
            self.network_scanner = NetworkScanner()
            self.packet_sniffer = PacketSniffer()
            self.keylogger = Keylogger()
            self.face_tracker = FaceTracker()
        except NameError:
            # These modules might not be implemented yet
            pass
        
        # Video capture
        self.cam = None
        self.frame = None
        self.webcam_thread = None
        self.emotion_data = {"Neutral": 0, "Happy": 0, "Sad": 0, "Angry": 0, "Surprised": 0}
        self.detected_faces = []
        
        # Animation objects
        self.animations = {}
        
        # Set up the main window
        self.root = tk.Tk()
        self.root.title(f"{APP_NAME} v{APP_VERSION}")
        self.root.geometry("1200x800")
        self.root.configure(bg="#1a1a1a")  # Darker background for more futuristic look
        
        # Set dark theme
        self.apply_dark_theme()
        
        # Create main layout
        try:
            self.create_layout()
        except Exception as e:
            self.add_console_message(f"Error creating layout: {str(e)}")
        
        # Initialize animations
        self.initialize_animations()
        
        # Set up animation timers
        self.root.after(25, self.update_animations)  # Faster refresh rate for smoother animations
        self.root.after(1000, self.update_stats)
        self.root.after(1000, self.update_time)
        
        # Start with a welcome message
        self.add_console_message(f"Welcome to {APP_NAME} v{APP_VERSION}")
        self.add_console_message("System initialized and ready")
        self.add_console_message("All modules loaded successfully")
        self.add_console_message("Enhanced visual interface activated")

    def apply_dark_theme(self):
        # Configure ttk styles for dark theme with futuristic accent
        style = ttk.Style()
        style.theme_use('clam')
        
        # Configure colors - using darker background and neon accent colors
        style.configure(".", 
                        background="#1a1a1a",
                        foreground="#00cc00",  # Neon green text
                        fieldbackground="#111111")
        
        style.configure("TNotebook", 
                        background="#111111",
                        tabmargins=[2, 5, 2, 0])
        
        style.configure("TNotebook.Tab", 
                        background="#222222", 
                        foreground="#00cc00",
                        padding=[10, 5])
                        
        style.map("TNotebook.Tab", 
                  background=[("selected", "#333333")],
                  foreground=[("selected", "#00ff00")])
                  
        style.configure("TButton", 
                        background="#222222",
                        foreground="#00cc00",
                        padding=6)
                        
        style.map("TButton",
                  background=[("active", "#2a2a2a")],
                  foreground=[("active", "#00ff00")])
                  
        style.configure("Sidebar.TButton", 
                        background="#151515",
                        foreground="#00cc00",
                        padding=10)
                        
        style.map("Sidebar.TButton",
                  background=[("active", "#252525")],
                  foreground=[("active", "#00ff00")])
                  
        style.configure("TFrame", background="#1a1a1a")
        style.configure("TLabel", background="#1a1a1a", foreground="#00cc00")
        style.configure("TEntry", foreground="black")
        style.configure("Console.TFrame", background="#0a0a0a")
        
        # Configure progressbar style for neon look
        style.configure("TProgressbar", 
                        background="#00cc00",
                        troughcolor="#111111",
                        borderwidth=0,
                        thickness=7)

    def create_layout(self):
        # Main container
        main_frame = ttk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Left sidebar
        sidebar = self.create_sidebar(main_frame)
        sidebar.pack(side=tk.LEFT, fill=tk.Y, padx=10, pady=10)
        
        # Right content area
        content_frame = ttk.Frame(main_frame)
        content_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Header bar
        header = self.create_header(content_frame)
        header.pack(fill=tk.X, padx=10, pady=10)
        
        # Main content (notebook with tabs)
        self.notebook = ttk.Notebook(content_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Add tabs
        self.add_dashboard_tab()
        self.add_webcam_tab()
        self.add_network_tab()
        self.add_logs_tab()
        self.add_console_tab()
        
        # Footer status bar
        footer = self.create_footer(content_frame)
        footer.pack(fill=tk.X, padx=10, pady=5)

    def create_sidebar(self, parent):
        sidebar = ttk.Frame(parent, width=200)
        
        # Logo area with animation canvas
        logo_frame = ttk.Frame(sidebar)
        logo_frame.pack(fill=tk.X, pady=10)
        
        # Create canvas for logo animation
        self.logo_canvas = tk.Canvas(logo_frame, width=180, height=80, bg="#111111", highlightthickness=0)
        self.logo_canvas.pack(pady=5)
        
        # Logo text with glow effect
        self.logo_canvas.create_text(90, 30, text=APP_NAME, fill="#00ff00", font=('Courier', 24, 'bold'), tags="logo")
        self.logo_canvas.create_text(90, 55, text=f"v{APP_VERSION}", fill="#00cc00", font=('Courier', 12), tags="logo")
        
        # Separator with animation
        separator_canvas = tk.Canvas(sidebar, height=10, bg="#1a1a1a", highlightthickness=0)
        separator_canvas.pack(fill=tk.X, pady=5)
        separator_canvas.create_line(0, 5, 200, 5, fill="#005500", width=1, tags="separator")
        self.separator_canvas = separator_canvas
        
        # Action buttons
        button_data = [
            ("Dashboard", self.show_dashboard, "dashboard"),
            ("Start Webcam", self.toggle_webcam, "webcam"),
            ("Face Tracking", self.toggle_face_tracking, "facetrack"),
            ("Scan Network", self.toggle_network_scan, "network"),
            ("Record", self.toggle_recording, "record"),
            ("Keylogger", self.toggle_keylogger, "keylog"),
            ("Emotion Analysis", self.toggle_emotion_detection, "emotion")
        ]
        
        self.action_buttons = {}
        buttons_frame = ttk.Frame(sidebar)
        buttons_frame.pack(fill=tk.X, padx=5, pady=10)
        
        for text, command, name in button_data:
            btn = ttk.Button(buttons_frame, text=text, command=command, style="Sidebar.TButton")
            btn.pack(fill=tk.X, pady=3)
            self.action_buttons[name] = btn
            
        # Status indicators
        status_frame = ttk.Frame(sidebar)
        status_frame.pack(fill=tk.X, padx=5, pady=10)
        
        ttk.Label(status_frame, text="SYSTEM STATUS", font=('Courier', 10, 'bold')).pack(anchor=tk.W)
        
        self.status_indicators = {}
        status_items = [
            ("CPU Usage", "cpu"),
            ("Memory", "memory"),
            ("Network", "network"),
            ("Security Level", "security")
        ]
        
        for text, name in status_items:
            frame = ttk.Frame(status_frame)
            frame.pack(fill=tk.X, pady=5)
            
            ttk.Label(frame, text=text).pack(side=tk.LEFT)
            
            var = tk.StringVar(value="0%")
            label = ttk.Label(frame, textvariable=var, font=('Courier', 9))
            label.pack(side=tk.RIGHT)
            
            progress = ttk.Progressbar(status_frame, length=180)
            progress.pack(fill=tk.X, pady=2)
            
            self.status_indicators[name] = {"var": var, "progress": progress}
        
        # System time display
        time_frame = ttk.Frame(sidebar)
        time_frame.pack(fill=tk.X, side=tk.BOTTOM, padx=5, pady=10)
        
        self.system_time_var = tk.StringVar(value="00:00:00")
        ttk.Label(time_frame, text="SYSTEM TIME", font=('Courier', 9)).pack(anchor=tk.W)
        ttk.Label(time_frame, textvariable=self.system_time_var, font=('Courier', 12, 'bold')).pack(anchor=tk.W)
        
        return sidebar

    def create_header(self, parent):
        header = ttk.Frame(parent)
        
        # Status label
        self.status_var = tk.StringVar(value="Ready")
        status_label = ttk.Label(header, textvariable=self.status_var, font=('Courier', 12, 'bold'))
        status_label.pack(side=tk.LEFT)
        
        # Right-aligned controls
        controls = ttk.Frame(header)
        controls.pack(side=tk.RIGHT)
        
        # Search box
        search_frame = ttk.Frame(controls)
        search_frame.pack(side=tk.RIGHT, padx=10)
        
        self.search_var = tk.StringVar()
        search_entry = ttk.Entry(search_frame, textvariable=self.search_var, width=20)
        search_entry.pack(side=tk.LEFT)
        
        search_button = ttk.Button(search_frame, text="Search", command=self.search)
        search_button.pack(side=tk.LEFT, padx=5)
        
        # Settings button
        settings_button = ttk.Button(controls, text="Settings", command=self.show_settings)
        settings_button.pack(side=tk.RIGHT, padx=5)
        
        return header

    def create_footer(self, parent):
        footer = ttk.Frame(parent)
        
        # Status message
        self.footer_status = tk.StringVar(value="Ready")
        status_label = ttk.Label(footer, textvariable=self.footer_status, font=('Courier', 9))
        status_label.pack(side=tk.LEFT)
        
        # Connection indicator with animated canvas
        self.conn_canvas = tk.Canvas(footer, width=100, height=20, bg="#1a1a1a", highlightthickness=0)
        self.conn_canvas.pack(side=tk.RIGHT)
        
        # Add pulsing connection indicator
        self.conn_canvas.create_oval(80, 5, 95, 20, fill="#00cc00", tags="conn_indicator")
        self.conn_canvas.create_text(60, 12, text="ONLINE", fill="#00cc00", font=('Courier', 9), tags="conn_text")
        
        return footer

    def add_dashboard_tab(self):
        dashboard = ttk.Frame(self.notebook)
        self.notebook.add(dashboard, text="Dashboard")
        
        # Main dashboard layout - split into two columns
        left_col = ttk.Frame(dashboard)
        left_col.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        right_col = ttk.Frame(dashboard)
        right_col.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # System overview panel
        overview = ttk.LabelFrame(left_col, text="System Overview")
        overview.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Status canvas with animated elements
        self.dashboard_canvas = tk.Canvas(overview, bg="#111111", highlightthickness=0)
        self.dashboard_canvas.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Activity log panel
        log_frame = ttk.LabelFrame(right_col, text="Recent Activity")
        log_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.activity_text = tk.Text(log_frame, bg="#111111", fg="#00cc00", height=10, wrap=tk.WORD, font=('Courier', 10))
        self.activity_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.activity_text.config(state=tk.DISABLED)
        
        # Quick actions panel
        actions_frame = ttk.LabelFrame(right_col, text="Quick Actions")
        actions_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Action buttons in a grid
        quick_actions = [
            ("Scan System", self.scan_system),
            ("Clear Logs", self.clear_logs),
            ("Generate Report", self.generate_report),
            ("Security Check", self.security_check)
        ]
        
        actions_grid = ttk.Frame(actions_frame)
        actions_grid.pack(fill=tk.X, padx=5, pady=5)
        
        for i, (text, command) in enumerate(quick_actions):
            row, col = divmod(i, 2)
            btn = ttk.Button(actions_grid, text=text, command=command)
            btn.grid(row=row, column=col, padx=5, pady=5, sticky="ew")
        
        # Configure grid columns
        actions_grid.columnconfigure(0, weight=1)
        actions_grid.columnconfigure(1, weight=1)

    def add_webcam_tab(self):
        webcam_tab = ttk.Frame(self.notebook)
        self.notebook.add(webcam_tab, text="Webcam")
        
        # Left side - camera feed
        cam_frame = ttk.LabelFrame(webcam_tab, text="Camera Feed")
        cam_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Canvas for camera feed with overlay animations
        self.cam_canvas = tk.Canvas(cam_frame, bg="#111111", highlightthickness=0)
        self.cam_canvas.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.cam_canvas.create_text(
            320, 240, 
            text="Webcam feed not active\nPress 'Start Webcam' to begin", 
            fill="#00cc00", 
            font=('Courier', 12),
            justify=tk.CENTER
        )
        
        # Right side - controls and metrics
        controls_frame = ttk.Frame(webcam_tab)
        controls_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=5, pady=5)
        
        # Camera controls
        cam_controls = ttk.LabelFrame(controls_frame, text="Controls")
        cam_controls.pack(fill=tk.X, padx=5, pady=5)
        
        # Control buttons
        control_buttons = [
            ("Start Camera", self.toggle_webcam),
            ("Capture Image", self.capture_image),
            ("Record Video", self.toggle_recording),
            ("Face Tracking", self.toggle_face_tracking)
        ]
        
        for text, command in control_buttons:
            btn = ttk.Button(cam_controls, text=text, command=command)
            btn.pack(fill=tk.X, pady=3)
        
        # Emotion analysis panel
        emotion_frame = ttk.LabelFrame(controls_frame, text="Emotion Analysis")
        emotion_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Emotion bars
        self.emotion_bars = {}
        emotions = ["Neutral", "Happy", "Sad", "Angry", "Surprised"]
        
        for emotion in emotions:
            frame = ttk.Frame(emotion_frame)
            frame.pack(fill=tk.X, pady=2)
            
            ttk.Label(frame, text=emotion, width=10).pack(side=tk.LEFT)
            
            var = tk.StringVar(value="0%")
            ttk.Label(frame, textvariable=var, width=5).pack(side=tk.RIGHT)
            
            progress = ttk.Progressbar(frame, length=150)
            progress.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
            
            self.emotion_bars[emotion] = {"var": var, "progress": progress}
        
        # Face data panel
        face_frame = ttk.LabelFrame(controls_frame, text="Detection Data")
        face_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.face_data_text = tk.Text(face_frame, bg="#111111", fg="#00cc00", height=10, font=('Courier', 10))
        self.face_data_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.face_data_text.config(state=tk.DISABLED)
        self.face_data_text.insert(tk.END, "No face detected")
        self.face_data_text.config(state=tk.DISABLED)

    def add_network_tab(self):
        network_tab = ttk.Frame(self.notebook)
        self.notebook.add(network_tab, text="Network")
        
        # Split into two panes
        top_frame = ttk.Frame(network_tab)
        top_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        bottom_frame = ttk.Frame(network_tab)
        bottom_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Network topology visualization
        topo_frame = ttk.LabelFrame(top_frame, text="Network Topology")
        topo_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Canvas for network visualization
        self.network_canvas = tk.Canvas(topo_frame, bg="#111111", highlightthickness=0)
        self.network_canvas.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Network device list
        devices_frame = ttk.LabelFrame(top_frame, text="Connected Devices")
        devices_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=5, pady=5)
        devices_frame.config(width=300)
        
        self.device_list = ttk.Treeview(devices_frame, columns=("ip", "type", "status"), show="headings")
        self.device_list.heading("ip", text="IP Address")
        self.device_list.heading("type", text="Device Type")
        self.device_list.heading("status", text="Status")
        self.device_list.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.device_list.tag_configure("offline", background="#333333", foreground="#ff0000")
        self.device_list.tag_configure("online", background="#111111", foreground="#00cc00")
        
        # Add sample devices
        sample_devices = [
            ("192.168.1.1", "Router", "Online"),
            ("192.168.1.100", "Desktop", "Online"),
            ("192.168.1.101", "Mobile", "Online"),
            ("192.168.1.102", "IoT Device", "Offline")
        ]
        
        for ip, dev_type, status in sample_devices:
            self.device_list.insert("", tk.END, values=(ip, dev_type, status))
        
        # Network controls
        controls_frame = ttk.LabelFrame(bottom_frame, text="Network Controls")
        controls_frame.pack(fill=tk.X, padx=5, pady=5)
        
        controls_grid = ttk.Frame(controls_frame)
        controls_grid.pack(fill=tk.X, padx=5, pady=5)
        
        network_actions = [
            ("Scan Network", self.toggle_network_scan),
            ("Packet Sniffer", self.toggle_packet_sniffer),
            ("Block Device", self.block_device),
            ("Network Settings", self.network_settings)
        ]
        
        for i, (text, command) in enumerate(network_actions):
            btn = ttk.Button(controls_grid, text=text, command=command)
            btn.grid(row=0, column=i, padx=5, pady=5, sticky="ew")
            
        # Configure grid columns
        for i in range(4):
            controls_grid.columnconfigure(i, weight=1)
        
        # Packet data panel
        packet_frame = ttk.LabelFrame(bottom_frame, text="Packet Data")
        packet_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        self.packet_text = tk.Text(packet_frame, bg="#111111", fg="#00cc00", height=10, font=('Courier', 10))
        self.packet_text.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.packet_text.insert(tk.END, "Packet data will appear here...\n")
        self.packet_text.config(state=tk.DISABLED)

    def add_logs_tab(self):
        logs_tab = ttk.Frame(self.notebook)
        self.notebook.add(logs_tab, text="Logs")
        
        # Split into two panes
        top_frame = ttk.Frame(logs_tab)
        top_frame.pack(fill=tk.X, padx=5, pady=5)
        
        bottom_frame = ttk.Frame(logs_tab)
        bottom_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Log filter controls
        filter_frame = ttk.LabelFrame(top_frame, text="Log Filters")
        filter_frame.pack(fill=tk.X, padx=5, pady=5)
        
        filter_controls = ttk.Frame(filter_frame)
        filter_controls.pack(fill=tk.X, padx=5, pady=5)
        
        # Log type selector
        ttk.Label(filter_controls, text="Log Type:").grid(row=0, column=0, padx=5, pady=5)
        log_types = ["All", "System", "Network", "Security", "Errors"]
        log_type_var = tk.StringVar(value=log_types[0])
        log_type_menu = ttk.Combobox(filter_controls, textvariable=log_type_var, values=log_types, state="readonly")
        log_type_menu.grid(row=0, column=1, padx=5, pady=5)
        
        # Date range
        ttk.Label(filter_controls, text="Date Range:").grid(row=0, column=2, padx=5, pady=5)
        date_range_var = tk.StringVar(value="Today")
        date_ranges = ["Today", "Yesterday", "Last 7 Days", "Last 30 Days", "Custom"]
        date_range_menu = ttk.Combobox(filter_controls, textvariable=date_range_var, values=date_ranges, state="readonly")
        date_range_menu.grid(row=0, column=3, padx=5, pady=5)
        
        # Search in logs
        ttk.Label(filter_controls, text="Search:").grid(row=0, column=4, padx=5, pady=5)
        search_var = tk.StringVar()
        search_entry = ttk.Entry(filter_controls, textvariable=search_var)
        search_entry.grid(row=0, column=5, padx=5, pady=5)
        
        # Filter button
        filter_btn = ttk.Button(filter_controls, text="Apply Filter", command=self.filter_logs)
        filter_btn.grid(row=0, column=6, padx=5, pady=5)
        
        # Configure grid columns
        for i in range(7):
            filter_controls.columnconfigure(i, weight=1 if i == 5 else 0)
        
        # Log content
        log_frame = ttk.LabelFrame(bottom_frame, text="Log Entries")
        log_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Treeview for log entries
        self.log_tree = ttk.Treeview(log_frame, columns=("time", "type", "message"), show="headings")
        self.log_tree.heading("time", text="Timestamp")
        self.log_tree.heading("type", text="Type")
        self.log_tree.heading("message", text="Message")
        
        self.log_tree.column("time", width=150)
        self.log_tree.column("type", width=100)
        self.log_tree.column("message", width=500)
        
        # Add scrollbar
        log_scroll = ttk.Scrollbar(log_frame, orient="vertical", command=self.log_tree.yview)
        self.log_tree.configure(yscrollcommand=log_scroll.set)
        
        # Pack tree and scrollbar
        self.log_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        log_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Add sample log entries
        sample_logs = [
            (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "System", "Application started"),
            (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "Security", "Authentication successful"),
            (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "Network", "Connected to network"),
            (datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "Error", "Failed to connect to database")
        ]
        
        for timestamp, log_type, message in sample_logs:
            self.log_tree.insert("", tk.END, values=(timestamp, log_type, message))

    def add_console_tab(self):
        console_tab = ttk.Frame(self.notebook)
        self.notebook.add(console_tab, text="Console")
        
        # Console output area
        console_frame = ttk.Frame(console_tab, style="Console.TFrame")
        console_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Console text area with scrollbar
        self.console_text = tk.Text(console_frame, bg="#000000", fg="#00ff00", font=('Courier', 11))
        console_scroll = ttk.Scrollbar(console_frame, orient="vertical", command=self.console_text.yview)
        self.console_text.configure(yscrollcommand=console_scroll.set)
        
        self.console_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        console_scroll.pack(side=tk.RIGHT, fill=tk.Y)
        
        # Input command line
        input_frame = ttk.Frame(console_tab)
        input_frame.pack(fill=tk.X, padx=5, pady=5)
        
        ttk.Label(input_frame, text="Command:").pack(side=tk.LEFT)
        
        self.command_var = tk.StringVar()
        command_entry = ttk.Entry(input_frame, textvariable=self.command_var)
        command_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=5)
        command_entry.bind("<Return>", self.execute_command)
        
        send_button = ttk.Button(input_frame, text="Execute", command=self.execute_command)
        send_button.pack(side=tk.RIGHT)
        
        # Add welcome message to console
        self.add_console_message(f"{APP_NAME} v{APP_VERSION} Console")
        self.add_console_message("Type 'help' for a list of available commands")

    def initialize_animations(self):
        # Initialize various animations
        self.animations["particles"] = ParticleSystem(self.dashboard_canvas, 600, 400)
        self.animations["hexgrid"] = HexGrid(self.network_canvas, 600, 400)
        self.animations["radar"] = RadarAnimation(self.dashboard_canvas, 300, 200, 100)
        self.animations["pulse"] = PulseEffect(self.dashboard_canvas, 450, 200)
        self.animations["network_graph"] = NetworkGraphAnimation(self.network_canvas, 600, 400)
        self.animations["loading3d"] = Loading3DAnimation(self.cam_canvas, 320, 240, 100)
        self.animations["face_tracking"] = FaceTrackingOverlay(self.cam_canvas, 640, 480)
        
        # Start animations
        for name, anim in self.animations.items():
            anim.initialize()

    def update_animations(self):
        # Update all active animations
        for name, anim in self.animations.items():
            if anim.active:
                anim.update()
        
        # Schedule next update
        self.root.after(40, self.update_animations)  # ~25 FPS
        
        # Update connection indicator pulse
        self.conn_canvas.delete("conn_indicator")
        pulse_size = 5 * (0.8 + 0.2 * math.sin(time.time() * 4))
        self.conn_canvas.create_oval(
            80 - pulse_size, 12 - pulse_size,
            80 + pulse_size, 12 + pulse_size,
            fill="#00cc00", tags="conn_indicator"
        )

    def update_stats(self):
        # Simulated system stats
        cpu = random.randint(5, 30)
        memory = random.randint(20, 60)
        network = random.randint(1, 40)
        security = random.randint(70, 95)
        
        # Update status indicators
        stats = {
            "cpu": cpu,
            "memory": memory,
            "network": network,
            "security": security
        }
        
        for name, value in stats.items():
            if name in self.status_indicators:
                self.status_indicators[name]["var"].set(f"{value}%")
                self.status_indicators[name]["progress"]["value"] = value
        
        # Schedule next update
        self.root.after(2000, self.update_stats)

    def update_time(self):
        # Update system time display
        current_time = datetime.now().strftime("%H:%M:%S")
        self.system_time_var.set(current_time)
        
        # Schedule next update
        self.root.after(1000, self.update_time)

    def add_console_message(self, message):
        # Add message to console with timestamp
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.console_text.config(state=tk.NORMAL)
        self.console_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.console_text.see(tk.END)
        self.console_text.config(state=tk.DISABLED)
        
        # Also add to activity log if it's open
        try:
            self.activity_text.config(state=tk.NORMAL)
            self.activity_text.insert(tk.END, f"[{timestamp}] {message}\n")
            self.activity_text.see(tk.END)
            self.activity_text.config(state=tk.DISABLED)
        except:
            pass  # Activity log might not be initialized yet

    def execute_command(self, event=None):
        # Get command from entry
        command = self.command_var.get().strip()
        if not command:
            return
        
        # Clear command entry
        self.command_var.set("")
        
        # Echo command to console
        self.add_console_message(f"> {command}")
        
        # Process command
        parts = command.split()
        cmd = parts[0].lower()
        args = parts[1:] if len(parts) > 1 else []
        
        if cmd == "help":
            self.add_console_message("Available commands:")
            self.add_console_message("  help - Show this help message")
            self.add_console_message("  scan [target] - Scan network or specific target")
            self.add_console_message("  webcam [on|off] - Control webcam")
            self.add_console_message("  record [start|stop] - Control recording")
            self.add_console_message("  track [on|off] - Control face tracking")
            self.add_console_message("  keylog [start|stop] - Control keylogger")
            self.add_console_message("  clear - Clear console")
            self.add_console_message("  exit - Exit application")
        
        elif cmd == "scan":
            target = args[0] if args else "network"
            self.add_console_message(f"Scanning {target}...")
            self.toggle_network_scan()
        
        elif cmd == "webcam":
            action = args[0] if args else "toggle"
            if action.lower() in ["on", "start"]:
                if not self.webcam_active:
                    self.toggle_webcam()
            elif action.lower() in ["off", "stop"]:
                if self.webcam_active:
                    self.toggle_webcam()
            else:
                self.toggle_webcam()
        
        elif cmd == "record":
            action = args[0] if args else "toggle"
            if action.lower() in ["start"]:
                if not self.recording_active:
                    self.toggle_recording()
            elif action.lower() in ["stop"]:
                if self.recording_active:
                    self.toggle_recording()
            else:
                self.toggle_recording()
        
        elif cmd == "track":
            action = args[0] if args else "toggle"
            if action.lower() in ["on", "start"]:
                if not self.face_tracking_active:
                    self.toggle_face_tracking()
            elif action.lower() in ["off", "stop"]:
                if self.face_tracking_active:
                    self.toggle_face_tracking()
            else:
                self.toggle_face_tracking()
        
        elif cmd == "keylog":
            action = args[0] if args else "toggle"
            if action.lower() in ["start"]:
                if not self.keylogging_active:
                    self.toggle_keylogger()
            elif action.lower() in ["stop"]:
                if self.keylogging_active:
                    self.toggle_keylogger()
            else:
                self.toggle_keylogger()
        
        elif cmd == "clear":
            self.console_text.config(state=tk.NORMAL)
            self.console_text.delete(1.0, tk.END)
            self.console_text.config(state=tk.DISABLED)
            self.add_console_message("Console cleared")
        
        elif cmd == "exit":
            self.add_console_message("Exiting application...")
            self.root.after(1000, self.root.destroy)
        
        else:
            self.add_console_message(f"Unknown command: {cmd}")
            self.add_console_message("Type 'help' for a list of available commands")

    # Button command methods
    def show_dashboard(self):
        self.notebook.select(0)  # Switch to dashboard tab
        self.add_console_message("Switched to Dashboard view")
        
    def toggle_webcam(self):
        if self.webcam_active:
            # Stop webcam
            self.webcam_active = False
            self.action_buttons["webcam"].config(text="Start Webcam")
            self.add_console_message("Webcam stopped")
            
            # Release camera if it exists
            if self.cam is not None:
                self.cam.release()
                self.cam = None
            
            # Reset webcam canvas
            self.cam_canvas.delete("all")
            self.cam_canvas.create_text(
                320, 240, 
                text="Webcam feed not active\nPress 'Start Webcam' to begin", 
                fill="#00cc00", 
                font=('Courier', 12),
                justify=tk.CENTER
            )
            
            # Stop webcam thread if running
            if self.webcam_thread is not None and self.webcam_thread.is_alive():
                self.webcam_thread = None
        else:
            # Start webcam
            self.webcam_active = True
            self.action_buttons["webcam"].config(text="Stop Webcam")
            self.add_console_message("Starting webcam...")
            
            # Switch to webcam tab
            self.notebook.select(1)  # Switch to webcam tab
            
            # Start webcam thread
            self.webcam_thread = threading.Thread(target=self.update_webcam, daemon=True)
            self.webcam_thread.start()
    
    def update_webcam(self):
        # Initialize camera
        try:
            self.cam = cv2.VideoCapture(0)
            if not self.cam.isOpened():
                self.add_console_message("Error: Could not open webcam")
                self.toggle_webcam()  # Turn it back off
                return
        except Exception as e:
            self.add_console_message(f"Error initializing webcam: {str(e)}")
            self.toggle_webcam()  # Turn it back off
            return
        
        # Main webcam loop
        while self.webcam_active:
            ret, frame = self.cam.read()
            if not ret:
                self.add_console_message("Error: Failed to grab frame from webcam")
                break
            
            # Store the current frame
            self.frame = frame
            
            # Process frame if needed (face tracking, emotion detection)
            if self.face_tracking_active:
                # Simple face detection with OpenCV
                try:
                    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
                    faces = face_cascade.detectMultiScale(gray, 1.3, 5)
                    
                    # Store detected faces
                    self.detected_faces = faces
                    
                    # Update face tracking overlay
                    self.animations["face_tracking"].update_faces(faces)
                    
                    # Update face data text
                    self.update_face_data(faces)
                    
                except Exception as e:
                    self.add_console_message(f"Face detection error: {str(e)}")
            
            # Convert to format for tkinter
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(frame_rgb)
            img = ImageTk.PhotoImage(image=img)
            
            # Update canvas
            self.cam_canvas.delete("all")
            self.cam_canvas.create_image(320, 240, image=img)
            self.cam_canvas.image = img  # Keep a reference
            
            # Simulate emotional analysis if active
            if self.emotion_detection_active:
                self.update_emotion_analysis()
            
            # Sleep to reduce CPU usage
            time.sleep(0.03)  # ~30 FPS
    
    def update_face_data(self, faces):
        # Update face data text area with detected face information
        self.face_data_text.config(state=tk.NORMAL)
        self.face_data_text.delete(1.0, tk.END)
        
        if len(faces) == 0:
            self.face_data_text.insert(tk.END, "No faces detected")
        else:
            for i, (x, y, w, h) in enumerate(faces):
                self.face_data_text.insert(tk.END, f"Face #{i+1}:\n")
                self.face_data_text.insert(tk.END, f"  Position: ({x}, {y})\n")
                self.face_data_text.insert(tk.END, f"  Size: {w}x{h}\n")
                
                # Add some simulated data
                confidence = random.randint(75, 99)
                age = random.randint(20, 40)
                gender = random.choice(["Male", "Female"])
                
                self.face_data_text.insert(tk.END, f"  Confidence: {confidence}%\n")
                self.face_data_text.insert(tk.END, f"  Est. Age: {age}\n")
                self.face_data_text.insert(tk.END, f"  Est. Gender: {gender}\n")
                self.face_data_text.insert(tk.END, "\n")
        
        self.face_data_text.config(state=tk.DISABLED)
    
    def update_emotion_analysis(self):
        # Simulate emotion analysis with random values
        emotions = {
            "Neutral": random.randint(40, 90),
            "Happy": random.randint(0, 30),
            "Sad": random.randint(0, 20),
            "Angry": random.randint(0, 15),
            "Surprised": random.randint(0, 25)
        }
        
        # Ensure values sum to 100%
        total = sum(emotions.values())
        if total > 0:
            for emotion in emotions:
                emotions[emotion] = int((emotions[emotion] / total) * 100)
        
        # Update emotion bars
        for emotion, value in emotions.items():
            self.emotion_bars[emotion]["var"].set(f"{value}%")
            self.emotion_bars[emotion]["progress"]["value"] = value
        
        # Store emotion data
        self.emotion_data = emotions
    
    def toggle_face_tracking(self):
        self.face_tracking_active = not self.face_tracking_active
        
        if self.face_tracking_active:
            self.action_buttons["facetrack"].config(text="Stop Tracking")
            self.add_console_message("Face tracking activated")
            self.animations["face_tracking"].active = True
            
            # Start webcam if not already active
            if not self.webcam_active:
                self.toggle_webcam()
        else:
            self.action_buttons["facetrack"].config(text="Face Tracking")
            self.add_console_message("Face tracking deactivated")
            self.animations["face_tracking"].active = False
            
            # Clear detected faces
            self.detected_faces = []
            self.update_face_data([])
    
    def toggle_emotion_detection(self):
        self.emotion_detection_active = not self.emotion_detection_active
        
        if self.emotion_detection_active:
            self.action_buttons["emotion"].config(text="Stop Analysis")
            self.add_console_message("Emotion analysis activated")
            
            # Start webcam if not already active
            if not self.webcam_active:
                self.toggle_webcam()
        else:
            self.action_buttons["emotion"].config(text="Emotion Analysis")
            self.add_console_message("Emotion analysis deactivated")
            
            # Reset emotion bars
            for emotion in self.emotion_bars:
                self.emotion_bars[emotion]["var"].set("0%")
                self.emotion_bars[emotion]["progress"]["value"] = 0
    
    def toggle_network_scan(self):
        self.network_scanning = not self.network_scanning
        
        if self.network_scanning:
            self.action_buttons["network"].config(text="Stop Scanning")
            self.add_console_message("Network scanning started")
            self.status_var.set("Scanning network...")
            
            # Activate network animation
            self.animations["network_graph"].active = True
            self.animations["hexgrid"].active = True
            
            # Switch to network tab
            self.notebook.select(2)  # Network tab
            
            # Simulate scanning with a thread
            threading.Thread(target=self.simulate_network_scan, daemon=True).start()
        else:
            self.action_buttons["network"].config(text="Scan Network")
            self.add_console_message("Network scanning stopped")
            self.status_var.set("Ready")
    
    def simulate_network_scan(self):
        # Simulate scanning process
        for i in range(5):
            if not self.network_scanning:
                break
                
            # Update packet data with simulated packets
            self.packet_text.config(state=tk.NORMAL)
            self.packet_text.delete(1.0, tk.END)
            
            # Generate some random packet data
            for _ in range(10):
                src_ip = f"192.168.1.{random.randint(1, 254)}"
                dst_ip = f"192.168.1.{random.randint(1, 254)}"
                protocol = random.choice(["TCP", "UDP", "ICMP", "HTTP", "DNS"])
                size = random.randint(64, 1500)
                flags = random.choice(["SYN", "ACK", "PSH-ACK", "FIN", "RST"])
                
                packet_line = f"{src_ip} > {protocol} > {dst_ip} > {size} bytes > {flags}\n"
                self.packet_text.insert(tk.END, packet_line)
            
            self.packet_text.config(state=tk.NORMAL)
            
            # Log the scan progress
            self.add_console_message(f"Scanning network... {(i+1)*20}% complete")
            self.footer_status.set(f"Network scan in progress: {(i+1)*20}%")
            
            # Update device list with newly "discovered" devices
            if i == 1:
                device_ip = f"192.168.1.{random.randint(110, 120)}"
                self.device_list.insert("", tk.END, values=(device_ip, "Smartphone", "Online"), tags=("online",))
                self.add_console_message(f"New device discovered: {device_ip}")
            
            if i == 3:
                smart_tv_ip = f"192.168.1.{random.randint(130, 140)}"
                suspicious_ip = f"192.168.1.{random.randint(150, 160)}"
                
                self.device_list.insert("", tk.END, values=(smart_tv_ip, "Smart TV", "Online"), tags=("online",))
                self.device_list.insert("", tk.END, values=(suspicious_ip, "Unknown", "Offline"), tags=("offline",))
                self.add_console_message(f"Suspicious device detected: {suspicious_ip}")
                
                # Add to log entries
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                self.log_tree.insert("", 0, values=(timestamp, "Security", "Suspicious device detected on network"))
            
            # Write to network log file
            try:
                log_file = os.path.join(LOG_DIR, "network_logs.csv")
                with open(log_file, 'a', newline='') as f:
                    writer = csv.writer(f)
                    writer.writerow([
                        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        f"Scan progress: {(i+1)*20}%",
                        f"Active connections: {random.randint(3, 10)}"
                    ])
            except Exception as e:
                self.add_console_message(f"Error writing to log: {str(e)}")
                
            # Slight pause to simulate real scanning
            time.sleep(1.5)
        
        if self.network_scanning:  # Only if not cancelled mid-scan
            # Scan complete
            self.add_console_message("Network scan complete")
            self.footer_status.set("Network scan complete")
            self.status_var.set("Ready")
            
            # Add final log entry
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            self.log_tree.insert("", 0, values=(timestamp, "Network", "Network scan completed successfully"))
            
            # Deactivate animations after a short delay
            def deactivate_animations():
                if not self.network_scanning:  # Double-check we're still not scanning
                    self.animations["network_graph"].active = False
                    self.animations["hexgrid"].active = False
            
            self.root.after(5000, deactivate_animations)
            
            # Switch button back
            self.action_buttons["network"].config(text="Scan Network")
            self.network_scanning = False
    
    def toggle_packet_sniffer(self):
        # Simulate packet sniffer functionality
        self.add_console_message("Packet sniffer not implemented yet")
        messagebox.showinfo("Coming Soon", "Packet sniffer functionality will be available in the next update.")
    
    def block_device(self):
        # Get selected device
        selected = self.device_list.selection()
        if not selected:
            messagebox.showinfo("No Selection", "Please select a device to block")
            return
            
        # Get device info
        values = self.device_list.item(selected[0], "values")
        ip = values[0]
        
        # Simulate blocking
        self.add_console_message(f"Blocking device at {ip}...")
        
        # Update status in the list
        self.device_list.item(selected[0], values=(ip, values[1], "Blocked"), tags=("offline",))
        
        # Add to log
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.log_tree.insert("", 0, values=(timestamp, "Security", f"Blocked device: {ip}"))
        
        messagebox.showinfo("Device Blocked", f"Device at {ip} has been blocked from the network")
    
    def network_settings(self):
        # Placeholder for network settings dialog
        self.add_console_message("Opening network settings...")
        messagebox.showinfo("Coming Soon", "Network settings dialog will be available in the next update.")
    
    def capture_image(self):
        """Capture a still image from the webcam feed"""
        if not self.webcam_active or self.frame is None:
            self.add_console_message("Error: Webcam is not active")
            messagebox.showinfo("Webcam Error", "Please start the webcam first")
            return
            
        # Create screenshot directory if it doesn't exist
        screenshot_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "screenshots")
        if not os.path.exists(screenshot_dir):
            os.makedirs(screenshot_dir)
            
        # Generate filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = os.path.join(screenshot_dir, f"screen_{timestamp}.png")
        
        # Save the current frame
        try:
            cv2.imwrite(filename, self.frame)
            self.add_console_message(f"Image captured and saved to {filename}")
            
            # Add to logs
            log_entry = f"Screenshot captured: {os.path.basename(filename)}"
            self.log_tree.insert("", 0, values=(datetime.now().strftime("%Y-%m-%d %H:%M:%S"), "System", log_entry))
            
            # Show confirmation
            messagebox.showinfo("Capture Successful", f"Image saved to {filename}")
        except Exception as e:
            self.add_console_message(f"Error saving image: {str(e)}")
            messagebox.showerror("Capture Failed", f"Failed to save image: {str(e)}")
    
    def toggle_recording(self):
        """Toggle video recording from the webcam feed"""
        if self.recording_active:
            # Stop recording
            self.recording_active = False
            self.action_buttons["record"].config(text="Record")
            self.add_console_message("Recording stopped")
            
            # Close video writer
            if hasattr(self, 'video_writer') and self.video_writer is not None:
                self.video_writer.release()
                self.video_writer = None
                
            # Add to logs
            self.log_tree.insert("", 0, values=(
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 
                "System", 
                f"Video recording stopped: {os.path.basename(self.recording_filename)}"
            ))
        else:
            # Check if webcam is active
            if not self.webcam_active or self.frame is None:
                self.add_console_message("Error: Webcam is not active")
                messagebox.showinfo("Recording Error", "Please start the webcam first")
                return
                
            # Create recordings directory if it doesn't exist
            recordings_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "recordings")
            if not os.path.exists(recordings_dir):
                os.makedirs(recordings_dir)
                
            # Generate filename with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            self.recording_filename = os.path.join(recordings_dir, f"video_{timestamp}.avi")
            
            # Get frame dimensions
            height, width = self.frame.shape[:2]
            
            # Initialize video writer
            fourcc = cv2.VideoWriter_fourcc(*'XVID')
            self.video_writer = cv2.VideoWriter(self.recording_filename, fourcc, 20.0, (width, height))
            
            # Start recording
            self.recording_active = True
            self.action_buttons["record"].config(text="Stop Recording")
            self.add_console_message(f"Recording started: {self.recording_filename}")
            
            # Start recording thread
            threading.Thread(target=self.record_video, daemon=True).start()
    
    def record_video(self):
        """Record video frames in a separate thread"""
        while self.recording_active and self.webcam_active and self.video_writer is not None:
            if self.frame is not None:
                self.video_writer.write(self.frame)
            time.sleep(0.05)  # ~20 FPS for recording
    
    def toggle_keylogger(self):
        """Toggle the keylogger functionality"""
        self.keylogging_active = not self.keylogging_active
        
        if self.keylogging_active:
            self.action_buttons["keylog"].config(text="Stop Keylogger")
            self.add_console_message("Keylogger activated")
            
            try:
                # Initialize keylogger if available
                if hasattr(self, 'keylogger') and self.keylogger is not None:
                    self.keylogger.start_logging()
                else:
                    # Simulate keylogger in this demo
                    self.simulate_keylogger()
                    
                # Add to logs
                self.log_tree.insert("", 0, values=(
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 
                    "Security", 
                    "Keylogger activated"
                ))
            except Exception as e:
                self.add_console_message(f"Error starting keylogger: {str(e)}")
        else:
            self.action_buttons["keylog"].config(text="Keylogger")
            self.add_console_message("Keylogger deactivated")
            
            try:
                # Stop keylogger if available
                if hasattr(self, 'keylogger') and self.keylogger is not None:
                    self.keylogger.stop_logging()
                    
                # Add to logs
                self.log_tree.insert("", 0, values=(
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 
                    "Security", 
                    "Keylogger deactivated"
                ))
            except Exception as e:
                self.add_console_message(f"Error stopping keylogger: {str(e)}")
    
    def simulate_keylogger(self):
        """Simulate keylogger activity for demo purposes"""
        if not self.keylogging_active:
            return
            
        # Create log directory if it doesn't exist
        keylog_file = os.path.join(LOG_DIR, "keylog.txt")
        
        # Simulate keystrokes
        sample_keystrokes = [
            "user@email.com",
            "password123",
            "https://bank.example.com",
            "login",
            "confidential information",
            "credit card number"
        ]
        
        # Write to log file
        try:
            with open(keylog_file, 'a') as f:
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                f.write(f"[{timestamp}] Keylogger session started\n")
                
                # Pick a random keystroke to simulate
                keystroke = random.choice(sample_keystrokes)
                f.write(f"[{timestamp}] Captured: {keystroke}\n")
                
            self.add_console_message(f"Keystrokes logged to {keylog_file}")
            
            # Schedule next simulation if still active
            if self.keylogging_active:
                self.root.after(10000, self.simulate_keylogger)  # Every 10 seconds
        except Exception as e:
            self.add_console_message(f"Error writing to keylog: {str(e)}")
            
    # Dashboard action functions
    def scan_system(self):
        """Scan the system for potential security issues"""
        self.add_console_message("Starting system scan...")
        self.status_var.set("Scanning system...")
        
        # Create a progress dialog
        progress_window = tk.Toplevel(self.root)
        progress_window.title("System Scan")
        progress_window.geometry("400x150")
        progress_window.transient(self.root)
        progress_window.grab_set()
        
        # Add progress bar and status
        ttk.Label(progress_window, text="Scanning system for security issues...").pack(pady=10)
        progress = ttk.Progressbar(progress_window, mode="determinate", length=350)
        progress.pack(pady=10, padx=20)
        
        status_var = tk.StringVar(value="Initializing scan...")
        status_label = ttk.Label(progress_window, textvariable=status_var)
        status_label.pack(pady=5)
        
        # Simulate scanning process in a separate thread
        def simulate_scan():
            scan_items = [
                "Checking system files...",
                "Scanning for malware...",
                "Checking network configurations...",
                "Scanning for suspicious processes...",
                "Checking system vulnerabilities...",
                "Generating report..."
            ]
            
            findings = []
            
            for i, item in enumerate(scan_items):
                # Update progress
                progress["value"] = (i / len(scan_items)) * 100
                status_var.set(item)
                
                # Simulate finding issues
                if random.random() < 0.3:  # 30% chance of finding an issue
                    issue = random.choice([
                        "Outdated system package detected",
                        "Suspicious network activity detected",
                        "Unusual process behavior detected",
                        "Potential security vulnerability found",
                        "Unencrypted connection detected"
                    ])
                    findings.append(issue)
                    
                    # Add to log
                    self.log_tree.insert("", 0, values=(
                        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "Security",
                        issue
                    ))
                
                # Simulate processing time
                time.sleep(random.uniform(0.5, 1.5))
            
            # Complete the scan
            progress["value"] = 100
            status_var.set("Scan complete")
            
            # Update console and logs
            self.add_console_message("System scan complete")
            if findings:
                self.add_console_message(f"Found {len(findings)} potential issues")
                for finding in findings:
                    self.add_console_message(f"- {finding}")
            else:
                self.add_console_message("No security issues found")
            
            # Reset status
            self.status_var.set("Ready")
            
            # Close progress window after a delay
            self.root.after(1500, progress_window.destroy)
        
        # Start scan thread
        threading.Thread(target=simulate_scan, daemon=True).start()
    
    def clear_logs(self):
        """Clear the application logs"""
        # Ask for confirmation
        if not messagebox.askyesno("Confirm Clear Logs", "Are you sure you want to clear all logs? This cannot be undone."):
            return
            
        # Clear log display
        for item in self.log_tree.get_children():
            self.log_tree.delete(item)
            
        # Add a single entry about clearing logs
        self.log_tree.insert("", 0, values=(
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "System",
            "Logs cleared by user"
        ))
        
        # Clear console
        self.console_text.config(state=tk.NORMAL)
        self.console_text.delete(1.0, tk.END)
        self.console_text.config(state=tk.DISABLED)
        self.add_console_message("Console and logs cleared")
        
        # Clear activity log
        self.activity_text.config(state=tk.NORMAL)
        self.activity_text.delete(1.0, tk.END)
        self.activity_text.config(state=tk.DISABLED)
        self.add_console_message("Activity log cleared")
        
        # Optionally clear log files
        try:
            # List log files
            log_files = [f for f in os.listdir(LOG_DIR) if f.endswith('.csv') or f.endswith('.log')]
            
            for log_file in log_files:
                # Keep the file but clear its contents
                with open(os.path.join(LOG_DIR, log_file), 'w') as f:
                    f.write(f"# Log file cleared on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                    
            self.add_console_message(f"Cleared {len(log_files)} log files")
        except Exception as e:
            self.add_console_message(f"Error clearing log files: {str(e)}")
    
    def generate_report(self):
        """Generate a security report"""
        self.add_console_message("Generating security report...")
        
        # Create report file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = os.path.join(LOG_DIR, f"report_{timestamp}.csv")
        
        try:
            with open(report_file, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(["Timestamp", "Category", "Description", "Risk Level"])
                
                # Generate sample report data
                categories = ["System", "Network", "Security", "Privacy"]
                risk_levels = ["Low", "Medium", "High", "Critical"]
                
                # Add some sample findings
                for _ in range(10):
                    category = random.choice(categories)
                    risk = random.choice(risk_levels)
                    
                    if category == "System":
                        finding = random.choice([
                            "Operating system not up to date",
                            "System firewall disabled",
                            "Suspicious system process detected",
                            "System resource usage abnormal",
                            "Unauthorized system changes detected"
                        ])
                    elif category == "Network":
                        finding = random.choice([
                            "Unencrypted network traffic detected",
                            "Suspicious inbound connection attempt",
                            "Abnormal outbound traffic detected",
                            "Potential DNS spoofing attempt",
                            "Unusual network scanning activity"
                        ])
                    elif category == "Security":
                        finding = random.choice([
                            "Weak password policy detected",
                            "Multiple failed login attempts",
                            "Security software disabled",
                            "Potential data exfiltration detected",
                            "Critical security update missing"
                        ])
                    else:  # Privacy
                        finding = random.choice([
                            "Webcam accessed by unknown application",
                            "Microphone activated without user consent",
                            "Location data accessed by background process",
                            "Sensitive data transmitted unencrypted",
                            "Browser history accessed by unknown process"
                        ])
                    
                    writer.writerow([
                        datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        category,
                        finding,
                        risk
                    ])
            
            # Show success message
            self.add_console_message(f"Security report generated: {report_file}")
            messagebox.showinfo("Report Generated", f"Security report saved to:\n{report_file}")
            
            # Add to logs
            self.log_tree.insert("", 0, values=(
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "System",
                f"Security report generated: {os.path.basename(report_file)}"
            ))
        except Exception as e:
            self.add_console_message(f"Error generating report: {str(e)}")
            messagebox.showerror("Report Error", f"Failed to generate report: {str(e)}")
    
    def security_check(self):
        """Run a quick security check"""
        self.add_console_message("Running security check...")
        
        # Create security check window
        check_window = tk.Toplevel(self.root)
        check_window.title("Security Check")
        check_window.geometry("500x400")
        check_window.transient(self.root)
        
        # Add a frame for the report
        report_frame = ttk.LabelFrame(check_window, text="Security Status")
        report_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create a canvas with scrollbar for results
        canvas = tk.Canvas(report_frame, bg="#111111")
        scrollbar = ttk.Scrollbar(report_frame, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(
                scrollregion=canvas.bbox("all")
            )
        )
        
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Run security checks in a separate thread
        def run_checks():
            # Definition of security checks to run
            checks = [
                {
                    "name": "Firewall Status",
                    "status": random.choice(["Active", "Disabled"]),
                    "recommendation": "Ensure firewall is enabled for all networks",
                    "risk": "High" if random.random() < 0.3 else "Low"
                },
                {
                    "name": "Antivirus Status",
                    "status": random.choice(["Up to date", "Out of date", "Not installed"]),
                    "recommendation": "Update antivirus definitions regularly",
                    "risk": "Medium" if random.random() < 0.5 else "Low"
                },
                {
                    "name": "System Updates",
                    "status": random.choice(["Current", "Updates available", "Critical updates missing"]),
                    "recommendation": "Install all available system updates",
                    "risk": "High" if random.random() < 0.4 else "Medium"
                },
                {
                    "name": "Password Strength",
                    "status": random.choice(["Strong", "Medium", "Weak"]),
                    "recommendation": "Use complex passwords with a mix of characters",
                    "risk": "Critical" if random.random() < 0.2 else "Medium"
                },
                {
                    "name": "Data Encryption",
                    "status": random.choice(["Enabled", "Partial", "Disabled"]),
                    "recommendation": "Enable full disk encryption",
                    "risk": "High" if random.random() < 0.3 else "Medium"
                },
                {
                    "name": "Network Security",
                    "status": random.choice(["Secure", "Potentially Insecure", "Vulnerable"]),
                    "recommendation": "Use VPN on public networks",
                    "risk": "Medium" if random.random() < 0.6 else "Low"
                },
                {
                    "name": "Browser Security",
                    "status": random.choice(["Secure", "Extensions need review", "Outdated"]),
                    "recommendation": "Review browser extensions and keep updated",
                    "risk": "Medium" if random.random() < 0.4 else "Low"
                },
                {
                    "name": "Webcam Protection",
                    "status": random.choice(["Protected", "Accessible"]),
                    "recommendation": "Use webcam protection software",
                    "risk": "Medium" if random.random() < 0.5 else "Low"
                }
            ]
            
            # Display results
            overall_risk = 0
            
            for i, check in enumerate(checks):
                # Add a slight delay to simulate processing
                time.sleep(0.3)
                
                # Create a frame for each check
                check_frame = ttk.Frame(scrollable_frame)
                check_frame.pack(fill=tk.X, padx=5, pady=5)
                
                # Background color based on risk
                if check["risk"] == "Critical":
                    risk_color = "#ff0000"  # Red
                    overall_risk += 3
                elif check["risk"] == "High":
                    risk_color = "#ff6600"  # Orange
                    overall_risk += 2
                elif check["risk"] == "Medium":
                    risk_color = "#ffcc00"  # Yellow
                    overall_risk += 1
                else:
                    risk_color = "#00cc00"  # Green
                
                # Status color based on status
                if "disabled" in check["status"].lower() or "missing" in check["status"].lower() or "weak" in check["status"].lower() or "outdated" in check["status"].lower() or "vulnerable" in check["status"].lower():
                    status_color = "#ff0000"  # Red
                elif "partial" in check["status"].lower() or "available" in check["status"].lower() or "need" in check["status"].lower():
                    status_color = "#ffcc00"  # Yellow
                else:
                    status_color = "#00cc00"  # Green
                
                # Check name and risk level
                header_frame = ttk.Frame(check_frame)
                header_frame.pack(fill=tk.X)
                
                ttk.Label(header_frame, text=check["name"], font=('Courier', 11, 'bold')).pack(side=tk.LEFT)
                ttk.Label(header_frame, text=f"Risk: {check['risk']}", foreground=risk_color).pack(side=tk.RIGHT)
                
                # Status
                status_frame = ttk.Frame(check_frame)
                status_frame.pack(fill=tk.X, pady=3)
                
                ttk.Label(status_frame, text="Status:").pack(side=tk.LEFT, padx=(20, 5))
                ttk.Label(status_frame, text=check["status"], foreground=status_color).pack(side=tk.LEFT)
                
                # Recommendation
                rec_frame = ttk.Frame(check_frame)
                rec_frame.pack(fill=tk.X, pady=3)
                
                ttk.Label(rec_frame, text="Recommendation:").pack(side=tk.LEFT, padx=(20, 5))
                ttk.Label(rec_frame, text=check["recommendation"], wraplength=350).pack(side=tk.LEFT)
                
                # Add separator
                if i < len(checks) - 1:
                    ttk.Separator(scrollable_frame, orient='horizontal').pack(fill=tk.X, padx=5, pady=5)
            
            # Add overall score at the top
            overall_frame = ttk.Frame(scrollable_frame)
            overall_frame.pack(fill=tk.X, padx=5, pady=10)
            
            # Calculate overall security score
            max_score = len(checks) * 3  # Maximum possible risk score
            security_score = int(100 - (overall_risk / max_score) * 100)
            
            if security_score >= 90:
                score_color = "#00ff00"  # Bright green
                rating = "Excellent"
            elif security_score >= 70:
                score_color = "#99ff00"  # Light green
                rating = "Good"
            elif security_score >= 50:
                score_color = "#ffcc00"  # Yellow
                rating = "Fair"
            else:
                score_color = "#ff0000"  # Red
                rating = "Poor"
            
            ttk.Label(overall_frame, text=f"Overall Security Score: ", font=('Courier', 12, 'bold')).pack(side=tk.LEFT)
            ttk.Label(overall_frame, text=f"{security_score}% - {rating}", foreground=score_color, font=('Courier', 12, 'bold')).pack(side=tk.LEFT)
            
            # Move overall frame to the top
            overall_frame.pack_forget()
            overall_frame.pack(fill=tk.X, padx=5, pady=10, before=scrollable_frame.winfo_children()[0])
            
            # Add to application logs
            self.add_console_message(f"Security check complete. Overall score: {security_score}%")
            self.log_tree.insert("", 0, values=(
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "Security",
                f"Security check completed. Score: {security_score}% ({rating})"
            ))
        
        # Start checking thread
        threading.Thread(target=run_checks, daemon=True).start()
        
        # Add close button
        close_button = ttk.Button(check_window, text="Close", command=check_window.destroy)
        close_button.pack(pady=10)
    
    def search(self):
        """Search within the application logs and data"""
        search_term = self.search_var.get().strip().lower()
        
        if not search_term:
            messagebox.showinfo("Search", "Please enter a search term")
            return
            
        self.add_console_message(f"Searching for: {search_term}")
        
        # Create search results window
        results_window = tk.Toplevel(self.root)
        results_window.title(f"Search Results: {search_term}")
        results_window.geometry("800x500")
        results_window.transient(self.root)
        
        # Create results tree
        columns = ("source", "date", "match")
        results_tree = ttk.Treeview(results_window, columns=columns, show="headings")
        
        # Define column headings
        results_tree.heading("source", text="Source")
        results_tree.heading("date", text="Date")
        results_tree.heading("match", text="Matching Content")
        
        # Column widths
        results_tree.column("source", width=100)
        results_tree.column("date", width=150)
        results_tree.column("match", width=500)
        
        # Add scrollbar
        scrollbar = ttk.Scrollbar(results_window, orient="vertical", command=results_tree.yview)
        results_tree.configure(yscrollcommand=scrollbar.set)
        
        # Pack widgets
        results_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=10, pady=10)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y, pady=10)
        
        # Search through logs in a thread
        def perform_search():
            found_items = 0
            
            # Search log entries
            for item in self.log_tree.get_children():
                values = self.log_tree.item(item, "values")
                if any(search_term in str(value).lower() for value in values):
                    results_tree.insert("", tk.END, values=(
                        "Log Entry",
                        values[0],  # timestamp
                        values[2]   # message
                    ))
                    found_items += 1
                    
            # Search log files
            log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "logs")
            if os.path.exists(log_dir):
                for filename in os.listdir(log_dir):
                    if filename.endswith(".csv") or filename.endswith(".log") or filename.endswith(".txt"):
                        file_path = os.path.join(log_dir, filename)
                        try:
                            with open(file_path, 'r') as f:
                                for line_num, line in enumerate(f, 1):
                                    if search_term in line.lower():
                                        # Get date from line if possible, otherwise use file mod time
                                        date_match = re.search(r'\d{4}-\d{2}-\d{2}', line)
                                        if date_match:
                                            date = date_match.group(0)
                                        else:
                                            date = datetime.fromtimestamp(os.path.getmtime(file_path)).strftime("%Y-%m-%d")
                                            
                                        # Clean up the line for display
                                        display_line = line.strip()
                                        if len(display_line) > 80:
                                            display_line = display_line[:77] + "..."
                                            
                                        results_tree.insert("", tk.END, values=(
                                            f"{filename}:{line_num}",
                                            date,
                                            display_line
                                        ))
                                        found_items += 1
                        except Exception as e:
                            self.add_console_message(f"Error searching file {filename}: {str(e)}")
            
            # Show message if no results found
            if found_items == 0:
                results_tree.insert("", tk.END, values=(
                    "No Results",
                    datetime.now().strftime("%Y-%m-%d"),
                    f"No matches found for '{search_term}'"
                ))
                
            # Add a summary at the top
            results_tree.insert("", 0, values=(
                "Summary",
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                f"Found {found_items} matches for '{search_term}'"
            ))
            
            # Add to console
            self.add_console_message(f"Search complete: found {found_items} matches for '{search_term}'")
        
        # Start search thread
        threading.Thread(target=perform_search, daemon=True).start()
        
        # Add close button
        close_button = ttk.Button(results_window, text="Close", command=results_window.destroy)
        close_button.pack(pady=10)
    
    def show_settings(self):
        """Show application settings dialog"""
        settings_window = tk.Toplevel(self.root)
        settings_window.title("Settings")
        settings_window.geometry("500x400")
        settings_window.transient(self.root)
        settings_window.grab_set()
        
        # Create notebook for settings tabs
        settings_tabs = ttk.Notebook(settings_window)
        settings_tabs.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # General settings tab
        general_tab = ttk.Frame(settings_tabs)
        settings_tabs.add(general_tab, text="General")
        
        # Application theme
        theme_frame = ttk.LabelFrame(general_tab, text="Application Theme")
        theme_frame.pack(fill=tk.X, padx=10, pady=10)
        
        theme_var = tk.StringVar(value="Dark")
        ttk.Radiobutton(theme_frame, text="Dark Theme", variable=theme_var, value="Dark").pack(anchor=tk.W, padx=20, pady=5)
        ttk.Radiobutton(theme_frame, text="Light Theme", variable=theme_var, value="Light").pack(anchor=tk.W, padx=20, pady=5)
        
        # Startup options
        startup_frame = ttk.LabelFrame(general_tab, text="Startup Options")
        startup_frame.pack(fill=tk.X, padx=10, pady=10)
        
        start_minimized_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(startup_frame, text="Start minimized", variable=start_minimized_var).pack(anchor=tk.W, padx=20, pady=5)
        
        auto_update_var = tk.BooleanVar(value=True)
        ttk.Checkbutton(startup_frame, text="Check for updates on startup", variable=auto_update_var).pack(anchor=tk.W, padx=20, pady=5)
        
        # Security settings tab
        security_tab = ttk.Frame(settings_tabs)
        settings_tabs.add(security_tab, text="Security")
        
        # Logging settings
        logging_frame = ttk.LabelFrame(security_tab, text="Logging Options")
        logging_frame.pack(fill=tk.X, padx=10, pady=10)
        
        log_level_var = tk.StringVar(value="Info")
        ttk.Label(logging_frame, text="Log Level:").pack(anchor=tk.W, padx=20, pady=5)
        log_level_combo = ttk.Combobox(logging_frame, values=["Debug", "Info", "Warning", "Error"], textvariable=log_level_var, state="readonly")
        log_level_combo.pack(anchor=tk.W, padx=20, pady=5)
        
        log_retention_var = tk.StringVar(value="30 days")
        ttk.Label(logging_frame, text="Log Retention:").pack(anchor=tk.W, padx=20, pady=5)
        log_retention_combo = ttk.Combobox(logging_frame, values=["7 days", "30 days", "90 days", "1 year"], textvariable=log_retention_var, state="readonly")
        log_retention_combo.pack(anchor=tk.W, padx=20, pady=5)
        
        # Encryption settings
        encryption_frame = ttk.LabelFrame(security_tab, text="Encryption")
        encryption_frame.pack(fill=tk.X, padx=10, pady=10)
        
        encrypt_logs_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(encryption_frame, text="Encrypt log files", variable=encrypt_logs_var).pack(anchor=tk.W, padx=20, pady=5)
        
        # Advanced settings tab
        advanced_tab = ttk.Frame(settings_tabs)
        settings_tabs.add(advanced_tab, text="Advanced")
        
        # Advanced options
        network_frame = ttk.LabelFrame(advanced_tab, text="Network Settings")
        network_frame.pack(fill=tk.X, padx=10, pady=10)
        
        ttk.Label(network_frame, text="Proxy Server:").pack(anchor=tk.W, padx=20, pady=5)
        proxy_entry = ttk.Entry(network_frame, width=30)
        proxy_entry.pack(anchor=tk.W, padx=20, pady=5)
        
        # Save & cancel buttons
        button_frame = ttk.Frame(settings_window)
        button_frame.pack(fill=tk.X, padx=10, pady=10)
        
        save_button = ttk.Button(button_frame, text="Save", command=lambda: self.save_settings(
            theme_var.get(),
            start_minimized_var.get(),
            auto_update_var.get(),
            log_level_var.get(),
            log_retention_var.get(),
            encrypt_logs_var.get(),
            proxy_entry.get(),
            settings_window
        ))
        save_button.pack(side=tk.RIGHT, padx=5)
        
        cancel_button = ttk.Button(button_frame, text="Cancel", command=settings_window.destroy)
        cancel_button.pack(side=tk.RIGHT, padx=5)
    
    def save_settings(self, theme, start_minimized, auto_update, log_level, log_retention, encrypt_logs, proxy, window):
        """Save application settings"""
        settings = {
            "theme": theme,
            "start_minimized": start_minimized,
            "auto_update": auto_update,
            "log_level": log_level,
            "log_retention": log_retention,
            "encrypt_logs": encrypt_logs,
            "proxy": proxy
        }
        
        # Save settings to file
        settings_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "settings.json")
        
        try:
            with open(settings_file, 'w') as f:
                json.dump(settings, f, indent=4)
                
            self.add_console_message("Settings saved successfully")
            window.destroy()
        except Exception as e:
            self.add_console_message(f"Error saving settings: {str(e)}")
            messagebox.showerror("Error", f"Failed to save settings: {str(e)}")
            
    def filter_logs(self):
        """Apply filters to the log view"""
        self.add_console_message("Log filters applied")
        # This would actually filter the logs based on the criteria in the UI
        # For demo purposes, we're just acknowledging the action
            
def main():
    app = SpecterXApp()
    app.root.mainloop()

if __name__ == "__main__":
    main()
