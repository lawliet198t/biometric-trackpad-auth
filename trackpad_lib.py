#!/usr/bin/env python3
"""
Reusable Trackpad Capture & Visualization Library

This module provides a clean interface for capturing multi-touch trackpad gestures
with real-time visualization. Extract from trackpad_visualizer.py for reuse.

Usage:
    from trackpad_lib import TrackpadCapture, GestureVisualizer
    
    # Create capture instance
    capture = TrackpadCapture(device_path="/dev/input/event14")
    
    # Create visualizer
    visualizer = GestureVisualizer(width=1200, height=800)
    
    # Run with custom callback
    async def on_gesture_complete(tracks):
        print(f"Gesture captured with {len(tracks)} fingers")
    
    await capture.run(visualizer, on_gesture_complete)
"""

import asyncio
import time
from dataclasses import dataclass
from typing import Dict, List, Optional, Callable
from evdev import InputDevice, ecodes
import pygame

# Colors for different fingers
COLORS = [
    (0, 255, 136),   # Green
    (255, 136, 0),   # Orange
    (136, 0, 255),   # Purple
    (0, 255, 255),   # Cyan
    (255, 0, 136),   # Pink
    (255, 255, 0),   # Yellow
    (0, 136, 255),   # Blue
    (255, 0, 0),     # Red
    (0, 255, 0),     # Lime
    (255, 0, 255),   # Magenta
]

@dataclass
class TouchPoint:
    """Single touch point with position and timing"""
    x: float
    y: float
    timestamp: float
    timestamp_ns: int

class GestureTrack:
    """Track for a single finger"""
    def __init__(self, finger_id: int, color: tuple):
        self.finger_id = finger_id
        self.points: List[TouchPoint] = []
        self.color = color
        self.is_active = True
    
    def add_point(self, x: float, y: float, timestamp: float, timestamp_ns: int):
        """Add a point to this track"""
        self.points.append(TouchPoint(x, y, timestamp, timestamp_ns))

class TrackpadCapture:
    """
    Handles trackpad device input and gesture tracking
    
    This class manages:
    - Opening and reading from trackpad device
    - Multi-touch event processing
    - Coordinate normalization
    - Gesture track management
    """
    
    def __init__(self, device_path: str = "/dev/input/event14"):
        self.device_path = device_path
        self.device = None
        
        # Trackpad dimensions (will be read from device)
        self.abs_x_min = 0
        self.abs_x_max = 1
        self.abs_y_min = 0
        self.abs_y_max = 1
        
        # Screen dimensions (set by visualizer)
        self.screen_width = 1200
        self.screen_height = 800
        
        # Gesture tracking
        self.gesture_tracks: Dict[int, GestureTrack] = {}
        self.completed_tracks: List[GestureTrack] = []
        self.is_capturing = False
    
    def open_device(self) -> bool:
        """Open the trackpad device and read capabilities"""
        try:
            self.device = InputDevice(self.device_path)
            
            # Read trackpad dimensions
            caps = self.device.capabilities(verbose=True)
            if ('EV_ABS', ecodes.EV_ABS) in caps:
                abs_info = caps[('EV_ABS', ecodes.EV_ABS)]
                for (code_name, code_num), absinfo in abs_info:
                    if code_name == 'ABS_MT_POSITION_X':
                        self.abs_x_min = absinfo.min
                        self.abs_x_max = absinfo.max
                    elif code_name == 'ABS_MT_POSITION_Y':
                        self.abs_y_min = absinfo.min
                        self.abs_y_max = absinfo.max
            
            print(f"✓ Opened device: {self.device.name}")
            print(f"  Path: {self.device_path}")
            print(f"  Trackpad range: X({self.abs_x_min}-{self.abs_x_max}), Y({self.abs_y_min}-{self.abs_y_max})")
            return True
        except Exception as e:
            print(f"✗ Error opening device: {e}")
            return False
    
    def normalize_coords(self, x: int, y: int) -> tuple:
        """Normalize trackpad coordinates to screen coordinates"""
        if self.abs_x_max > self.abs_x_min:
            norm_x = (x - self.abs_x_min) / (self.abs_x_max - self.abs_x_min)
        else:
            norm_x = 0.5
        
        if self.abs_y_max > self.abs_y_min:
            norm_y = (y - self.abs_y_min) / (self.abs_y_max - self.abs_y_min)
        else:
            norm_y = 0.5
        
        screen_x = norm_x * self.screen_width
        screen_y = norm_y * self.screen_height
        
        return (screen_x, screen_y)
    
    def start_capture(self):
        """Start capturing gestures"""
        self.is_capturing = True
        self.gesture_tracks.clear()
        self.completed_tracks.clear()
    
    def stop_capture(self):
        """Stop capturing gestures"""
        self.is_capturing = False
    
    def clear_gestures(self):
        """Clear all gesture data"""
        self.gesture_tracks.clear()
        self.completed_tracks.clear()
    
    def get_all_tracks(self) -> List[GestureTrack]:
        """Get all tracks (active + completed)"""
        return list(self.gesture_tracks.values()) + self.completed_tracks
    
    async def process_device_events(self, on_finger_down: Optional[Callable] = None,
                                    on_finger_up: Optional[Callable] = None,
                                    on_point_added: Optional[Callable] = None):
        """
        Process trackpad events asynchronously
        
        Callbacks:
            on_finger_down(slot_id): Called when finger touches trackpad
            on_finger_up(slot_id, track): Called when finger lifts
            on_point_added(slot_id, x, y): Called when point is added
        """
        current_slot = 0
        slot_positions = {}
        slots_updated_this_frame = set()
        
        try:
            async for event in self.device.async_read_loop():
                if event.type == ecodes.EV_ABS:
                    if event.code == ecodes.ABS_MT_SLOT:
                        current_slot = event.value
                    
                    elif event.code == ecodes.ABS_MT_TRACKING_ID:
                        if event.value == -1:
                            # Finger lifted
                            if current_slot in self.gesture_tracks:
                                track = self.gesture_tracks[current_slot]
                                track.is_active = False
                                self.completed_tracks.append(track)
                                
                                if on_finger_up:
                                    on_finger_up(current_slot, track)
                                
                                del self.gesture_tracks[current_slot]
                                if current_slot in slot_positions:
                                    del slot_positions[current_slot]
                        else:
                            # New finger detected
                            if self.is_capturing:
                                color = COLORS[current_slot % len(COLORS)]
                                new_track = GestureTrack(current_slot, color)
                                self.gesture_tracks[current_slot] = new_track
                                
                                if on_finger_down:
                                    on_finger_down(current_slot)
                    
                    elif event.code == ecodes.ABS_MT_POSITION_X:
                        if current_slot not in slot_positions:
                            slot_positions[current_slot] = [0, 0]
                        slot_positions[current_slot][0] = event.value
                        slots_updated_this_frame.add(current_slot)
                    
                    elif event.code == ecodes.ABS_MT_POSITION_Y:
                        if current_slot not in slot_positions:
                            slot_positions[current_slot] = [0, 0]
                        slot_positions[current_slot][1] = event.value
                        slots_updated_this_frame.add(current_slot)
                
                elif event.type == ecodes.EV_SYN and event.code == ecodes.SYN_REPORT:
                    # End of event frame - process all updated slots
                    if self.is_capturing and slots_updated_this_frame:
                        timestamp = time.monotonic()
                        timestamp_ns = time.monotonic_ns()
                        
                        for slot_id in slots_updated_this_frame:
                            if slot_id in self.gesture_tracks and slot_id in slot_positions:
                                track = self.gesture_tracks[slot_id]
                                if track.is_active:
                                    x, y = slot_positions[slot_id]
                                    screen_x, screen_y = self.normalize_coords(x, y)
                                    track.add_point(screen_x, screen_y, timestamp, timestamp_ns)
                                    
                                    if on_point_added:
                                        on_point_added(slot_id, screen_x, screen_y)
                        
                        slots_updated_this_frame.clear()
        
        except Exception as e:
            print(f"Device read error: {e}")

class GestureVisualizer:
    """
    Handles pygame visualization of gestures
    
    This class manages:
    - Pygame window and rendering
    - Drawing gesture tracks
    - UI elements (status, instructions, etc.)
    - Keyboard input handling
    """
    
    def __init__(self, width: int = 1200, height: int = 800, title: str = "Trackpad Gesture Capture"):
        self.width = width
        self.height = height
        self.title = title
        
        # Pygame components
        self.screen = None
        self.clock = None
        self.font = None
        self.small_font = None
        self.large_font = None
        self.tiny_font = None
        
        # UI state
        self.status_text = "READY"
        self.status_color = (128, 128, 128)
        self.info_lines = []
        self.custom_ui_callback = None
    
    def init_pygame(self):
        """Initialize pygame display and fonts"""
        pygame.init()
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption(self.title)
        self.clock = pygame.time.Clock()
        
        self.font = pygame.font.Font(None, 36)
        self.small_font = pygame.font.Font(None, 24)
        self.large_font = pygame.font.Font(None, 72)
        self.tiny_font = pygame.font.Font(None, 18)
    
    def set_status(self, text: str, color: tuple = (255, 255, 255)):
        """Set status text and color"""
        self.status_text = text
        self.status_color = color
    
    def set_info_lines(self, lines: List[str]):
        """Set info lines to display"""
        self.info_lines = lines
    
    def set_custom_ui_callback(self, callback: Callable):
        """Set custom UI drawing callback"""
        self.custom_ui_callback = callback
    
    def draw_gesture_track(self, track: GestureTrack, is_active: bool = True):
        """Draw a gesture track"""
        if len(track.points) < 2:
            return
        
        # Dim color for inactive tracks
        color = track.color if is_active else tuple(c // 2 for c in track.color)
        
        # Draw lines connecting points
        points_to_draw = [(p.x, p.y) for p in track.points]
        if len(points_to_draw) >= 2:
            pygame.draw.lines(self.screen, color, False, points_to_draw, 3)
        
        # Draw dots at sample points
        for point in track.points[::5]:  # Every 5th point
            pygame.draw.circle(self.screen, color, (int(point.x), int(point.y)), 2)
    
    def draw_ui(self, capture: TrackpadCapture):
        """Draw standard UI elements"""
        # Background
        self.screen.fill((26, 26, 46))
        
        # Title
        title = self.font.render(self.title, True, (100, 255, 255))
        self.screen.blit(title, (20, 20))
        
        # Status
        status = self.small_font.render(f"Status: {self.status_text}", True, self.status_color)
        self.screen.blit(status, (20, 60))
        
        # Info lines
        y = 100
        for line in self.info_lines:
            text = self.tiny_font.render(line, True, (200, 200, 200))
            self.screen.blit(text, (20, y))
            y += 20
        
        # Instructions (bottom)
        instructions = [
            "SPACE: start/stop capture",
            "C: clear",
            "Q/ESC: quit"
        ]
        y = self.height - 80
        for inst in instructions:
            text = self.tiny_font.render(inst, True, (150, 150, 150))
            self.screen.blit(text, (20, y))
            y += 20
        
        # Custom UI callback
        if self.custom_ui_callback:
            self.custom_ui_callback(self.screen, self.font, self.small_font, self.tiny_font)
    
    def render(self, capture: TrackpadCapture):
        """Render complete frame"""
        self.draw_ui(capture)
        
        # Draw completed tracks
        for track in capture.completed_tracks:
            self.draw_gesture_track(track, False)
        
        # Draw active tracks
        for track in capture.gesture_tracks.values():
            self.draw_gesture_track(track, True)
        
        pygame.display.flip()
        self.clock.tick(60)

async def run_capture_loop(capture: TrackpadCapture, 
                           visualizer: GestureVisualizer,
                           on_gesture_complete: Optional[Callable] = None,
                           on_key_press: Optional[Callable] = None):
    """
    Main capture loop with visualization
    
    Args:
        capture: TrackpadCapture instance
        visualizer: GestureVisualizer instance
        on_gesture_complete: Callback(tracks) when capture stops
        on_key_press: Callback(key) for custom key handling
    """
    # Set screen dimensions
    capture.screen_width = visualizer.width
    capture.screen_height = visualizer.height
    
    # Open device
    if not capture.open_device():
        return
    
    # Initialize pygame
    visualizer.init_pygame()
    
    # Callbacks for device events
    def on_finger_down(slot_id):
        print(f"👇 Finger {slot_id} detected")
    
    def on_finger_up(slot_id, track):
        print(f"👆 Finger {slot_id} lifted ({len(track.points)} points)")
    
    # Start device event processing
    device_task = asyncio.create_task(
        capture.process_device_events(on_finger_down, on_finger_up)
    )
    
    # Main event loop
    running = True
    needs_redraw = True
    
    while running:
        # Handle pygame events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    if not capture.is_capturing:
                        capture.start_capture()
                        visualizer.set_status("CAPTURING", (0, 255, 0))
                        print("🎬 Started capturing")
                    else:
                        capture.stop_capture()
                        visualizer.set_status("STOPPED", (255, 165, 0))
                        print("⏹️ Stopped capturing")
                        
                        # Callback with completed gesture
                        if on_gesture_complete:
                            all_tracks = capture.get_all_tracks()
                            await on_gesture_complete(all_tracks)
                    
                    needs_redraw = True
                
                elif event.key == pygame.K_c:
                    capture.clear_gestures()
                    visualizer.set_status("CLEARED", (128, 128, 128))
                    print("🗑️ Cleared")
                    needs_redraw = True
                
                elif event.key == pygame.K_q or event.key == pygame.K_ESCAPE:
                    running = False
                
                else:
                    # Custom key handling
                    if on_key_press:
                        await on_key_press(event.key)
        
        # Render
        if needs_redraw or capture.is_capturing:
            visualizer.render(capture)
            needs_redraw = False
        
        await asyncio.sleep(0.001)
    
    # Cleanup
    device_task.cancel()
    try:
        await device_task
    except asyncio.CancelledError:
        pass
    
    pygame.quit()

# Example usage
async def example_usage():
    """Example of how to use the library"""
    
    # Create instances
    capture = TrackpadCapture(device_path="/dev/input/event14")
    visualizer = GestureVisualizer(width=1200, height=800, title="My Gesture App")
    
    # Custom callback when gesture is complete
    async def on_gesture_complete(tracks):
        print(f"\n✓ Gesture captured!")
        print(f"  Fingers: {len(tracks)}")
        for track in tracks:
            print(f"  Finger {track.finger_id}: {len(track.points)} points")
    
    # Custom key handler
    async def on_key_press(key):
        if key == pygame.K_s:
            print("Custom key 'S' pressed!")
    
    # Run the capture loop
    await run_capture_loop(capture, visualizer, on_gesture_complete, on_key_press)

if __name__ == "__main__":
    # Run example
    asyncio.run(example_usage())
