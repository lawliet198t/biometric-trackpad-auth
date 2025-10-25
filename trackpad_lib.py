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
import platform
from dataclasses import dataclass
from typing import Dict, List, Optional, Callable, Union
import pygame

# Platform detection
IS_LINUX = platform.system() == 'Linux'
IS_WINDOWS = platform.system() == 'Windows'
IS_MACOS = platform.system() == 'Darwin'

# Import platform-specific modules
if IS_LINUX:
    try:
        from evdev import InputDevice, ecodes, list_devices
        LINUX_AVAILABLE = True
    except ImportError:
        print("⚠️  evdev not installed. Install with: pip install evdev")
        LINUX_AVAILABLE = False
elif IS_WINDOWS:
    # Try C# subprocess version first (true multi-touch)
    try:
        from windows_touchpad_subprocess import (
            WindowsTouchpadSubprocess as WindowsTouchpadCapture,
            detect_windows_touchpad,
            list_windows_touchpads,
            TouchPoint as WinTouchPoint
        )
        WINDOWS_AVAILABLE = True
        print("✓ Using C# subprocess backend (true multi-touch)")
    except (ImportError, FileNotFoundError) as e:
        # Fallback to mouse simulation
        try:
            from windows_touchpad import (
                WindowsTouchpadCapture,
                detect_windows_touchpad,
                list_windows_touchpads,
                TouchPoint as WinTouchPoint
            )
            WINDOWS_AVAILABLE = True
            print("⚠️  Using mouse simulation (single-point only)")
            print("   For multi-touch, run: build_touchpad.bat")
        except ImportError:
            print("⚠️  Windows touchpad support not available")
            WINDOWS_AVAILABLE = False
else:
    LINUX_AVAILABLE = False
    WINDOWS_AVAILABLE = False

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


def detect_trackpad() -> Optional[Union[str, bool]]:
    """
    Automatically detect trackpad device (cross-platform).
    
    Returns:
        - Linux: Device path (e.g., '/dev/input/event14') or None
        - Windows: True if touchpad detected, False otherwise
        - macOS: None (not yet supported)
    
    Detection strategy:
    - Linux: Look for devices with multi-touch capabilities
    - Windows: Check for Windows Precision Touchpad support
    """
    if IS_WINDOWS and WINDOWS_AVAILABLE:
        return detect_windows_touchpad()
    
    elif IS_LINUX and LINUX_AVAILABLE:
        return _detect_linux_trackpad()
    
    elif IS_MACOS:
        print("⚠️  macOS support not yet implemented")
        return None
    
    else:
        print(f"⚠️  Platform not supported: {platform.system()}")
        return None


def _detect_linux_trackpad() -> Optional[str]:
    """
    Detect trackpad on Linux using evdev.
    
    Returns:
        Device path or None if not found
    """
    trackpad_keywords = [
        'trackpad', 'touchpad', 'synaptics', 'elan', 'alps',
        'bcm5974',  # Apple trackpads
        'ps/2',     # Some laptop trackpads
    ]
    
    candidates = []
    
    try:
        devices = [InputDevice(path) for path in list_devices()]
        
        for device in devices:
            try:
                # Check if device has multi-touch capabilities
                caps = device.capabilities()
                
                # Must have absolute positioning
                if ecodes.EV_ABS not in caps:
                    continue
                
                abs_events = caps[ecodes.EV_ABS]
                abs_codes = [code for (code, _) in abs_events]
                
                # Must have multi-touch position tracking
                has_mt_x = ecodes.ABS_MT_POSITION_X in abs_codes
                has_mt_y = ecodes.ABS_MT_POSITION_Y in abs_codes
                has_mt_slot = ecodes.ABS_MT_SLOT in abs_codes
                has_mt_tracking = ecodes.ABS_MT_TRACKING_ID in abs_codes
                
                if not (has_mt_x and has_mt_y and has_mt_slot and has_mt_tracking):
                    continue
                
                # Check device name for trackpad keywords
                device_name_lower = device.name.lower()
                is_trackpad_name = any(keyword in device_name_lower for keyword in trackpad_keywords)
                
                # Calculate capability score
                capability_score = len(abs_codes)
                
                # Boost score if name matches
                if is_trackpad_name:
                    capability_score += 100
                
                candidates.append({
                    'path': device.path,
                    'name': device.name,
                    'score': capability_score,
                    'is_trackpad_name': is_trackpad_name
                })
                
            except (OSError, IOError):
                # Skip devices we can't access
                continue
    
    except Exception as e:
        print(f"⚠️  Error during device detection: {e}")
        return None
    
    if not candidates:
        return None
    
    # Sort by score (highest first)
    candidates.sort(key=lambda x: x['score'], reverse=True)
    
    # Return best candidate
    best = candidates[0]
    return best['path']


def list_all_trackpads() -> List[Dict[str, str]]:
    """
    List all potential trackpad devices (cross-platform).
    
    Returns:
        List of dicts with device information
    """
    if IS_WINDOWS and WINDOWS_AVAILABLE:
        return list_windows_touchpads()
    
    elif IS_LINUX and LINUX_AVAILABLE:
        return _list_linux_trackpads()
    
    elif IS_MACOS:
        print("⚠️  macOS support not yet implemented")
        return []
    
    else:
        return []


def _list_linux_trackpads() -> List[Dict[str, str]]:
    """
    List all trackpad devices on Linux.
    
    Returns:
        List of dicts with 'path', 'name', and 'score' keys
    """
    trackpad_keywords = [
        'trackpad', 'touchpad', 'synaptics', 'elan', 'alps',
        'bcm5974', 'ps/2'
    ]
    
    candidates = []
    
    try:
        devices = [InputDevice(path) for path in list_devices()]
        
        for device in devices:
            try:
                caps = device.capabilities()
                
                if ecodes.EV_ABS not in caps:
                    continue
                
                abs_events = caps[ecodes.EV_ABS]
                abs_codes = [code for (code, _) in abs_events]
                
                has_mt_x = ecodes.ABS_MT_POSITION_X in abs_codes
                has_mt_y = ecodes.ABS_MT_POSITION_Y in abs_codes
                has_mt_slot = ecodes.ABS_MT_SLOT in abs_codes
                has_mt_tracking = ecodes.ABS_MT_TRACKING_ID in abs_codes
                
                if not (has_mt_x and has_mt_y and has_mt_slot and has_mt_tracking):
                    continue
                
                device_name_lower = device.name.lower()
                is_trackpad_name = any(keyword in device_name_lower for keyword in trackpad_keywords)
                
                capability_score = len(abs_codes)
                if is_trackpad_name:
                    capability_score += 100
                
                candidates.append({
                    'path': device.path,
                    'name': device.name,
                    'score': capability_score,
                    'is_trackpad_name': is_trackpad_name
                })
                
            except (OSError, IOError):
                continue
    
    except Exception as e:
        print(f"⚠️  Error listing devices: {e}")
        return []
    
    # Sort by score
    candidates.sort(key=lambda x: x['score'], reverse=True)
    
    return candidates

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
    Cross-platform trackpad device input and gesture tracking
    
    This class manages:
    - Opening and reading from trackpad device (Linux/Windows)
    - Multi-touch event processing
    - Coordinate normalization
    - Gesture track management
    
    Automatically detects platform and uses appropriate backend:
    - Linux: evdev
    - Windows: Windows Touch API
    """
    
    def __init__(self, device_path: Optional[str] = None):
        # Platform detection
        self.platform = platform.system()
        self.is_windows = IS_WINDOWS and WINDOWS_AVAILABLE
        self.is_linux = IS_LINUX and LINUX_AVAILABLE
        
        # Windows backend
        if self.is_windows:
            self.backend = WindowsTouchpadCapture()
            self.device_path = "Windows Touch API"
            print(f"🔍 Using Windows Precision Touchpad")
        
        # Linux backend
        elif self.is_linux:
            # Auto-detect if not specified
            if device_path is None:
                device_path = detect_trackpad()
                if device_path is None:
                    print("❌ No trackpad detected!")
                    print("\nAvailable devices with multi-touch:")
                    devices = list_all_trackpads()
                    if devices:
                        for i, dev in enumerate(devices, 1):
                            print(f"  {i}. {dev['path']}: {dev['name']} (score: {dev['score']})")
                        print("\nSpecify device manually with: TrackpadCapture(device_path='/dev/input/eventX')")
                    else:
                        print("  (none found)")
                    raise RuntimeError("No trackpad detected")
                print(f"🔍 Auto-detected trackpad: {device_path}")
            
            self.device_path = device_path
            self.device = None
            self.backend = None
        
        else:
            raise RuntimeError(f"Platform not supported: {self.platform}")
        
        # Common attributes (for Linux backend)
        
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
        if self.is_windows:
            return self.backend.open_device()
        
        elif self.is_linux:
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
        if self.is_windows:
            self.backend.start_capture()
        else:
            self.is_capturing = True
            self.gesture_tracks.clear()
            self.completed_tracks.clear()
    
    def stop_capture(self):
        """Stop capturing gestures"""
        if self.is_windows:
            self.backend.stop_capture()
        else:
            self.is_capturing = False
    
    def clear_gestures(self):
        """Clear all gesture data"""
        if self.is_windows:
            self.backend.clear_gestures()
        else:
            self.gesture_tracks.clear()
            self.completed_tracks.clear()
    
    def get_all_tracks(self) -> List:
        """Get all tracks (active + completed)"""
        if self.is_windows:
            # Convert Windows format to GestureTrack format
            tracks = []
            for i, points in enumerate(self.backend.get_all_tracks()):
                if points:
                    color = COLORS[i % len(COLORS)]
                    track = GestureTrack(i, color)
                    track.points = points
                    track.is_active = False
                    tracks.append(track)
            return tracks
        else:
            return list(self.gesture_tracks.values()) + self.completed_tracks
    
    async def process_device_events(self, on_finger_down: Optional[Callable] = None,
                                    on_finger_up: Optional[Callable] = None,
                                    on_point_added: Optional[Callable] = None):
        """
        Process trackpad events asynchronously (cross-platform)
        
        Callbacks:
            on_finger_down(slot_id): Called when finger touches trackpad
            on_finger_up(slot_id, track): Called when finger lifts
            on_point_added(slot_id, x, y): Called when point is added
        """
        if self.is_windows:
            # Windows backend handles events via pygame
            await self.backend.process_device_events(on_finger_down, on_finger_up, on_point_added)
        
        elif self.is_linux:
            await self._process_linux_events(on_finger_down, on_finger_up, on_point_added)
    
    async def _process_linux_events(self, on_finger_down, on_finger_up, on_point_added):
        """Process Linux evdev events"""
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
    
    # Windows mouse handling (touchpad sends mouse events)
    is_windows = capture.is_windows if hasattr(capture, 'is_windows') else False
    mouse_tracking = False
    mouse_track_id = 0
    
    while running:
        # Handle pygame events
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            
            # Windows: Use mouse events as touch simulation
            elif is_windows and event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if capture.backend and capture.is_capturing:
                    mouse_tracking = True
                    mouse_track_id += 1
                    capture.backend.process_touch_down(mouse_track_id, event.pos[0], event.pos[1])
                needs_redraw = True
            
            elif is_windows and event.type == pygame.MOUSEMOTION:
                if capture.backend and mouse_tracking:
                    capture.backend.process_touch_move(mouse_track_id, event.pos[0], event.pos[1])
                needs_redraw = True
            
            elif is_windows and event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                if capture.backend and mouse_tracking:
                    capture.backend.process_touch_up(mouse_track_id)
                    mouse_tracking = False
                needs_redraw = True
            
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
    
    # Create instances (auto-detects trackpad)
    capture = TrackpadCapture()  # Auto-detect trackpad
    # Or specify manually: capture = TrackpadCapture(device_path="/dev/input/event14")
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
