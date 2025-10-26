#!/usr/bin/env python3
"""
Embedded Window - C# inside Python

Embeds the C# WPF window inside a pygame window using Windows API.
This creates ONE single window with everything!
"""

import pygame
import ctypes
import time
import sys
from simple_windows_touchpad import SimpleTouchpadReader

# Windows API functions
user32 = ctypes.windll.user32
SetParent = user32.SetParent
SetWindowLong = user32.SetWindowLongW
GetWindowLong = user32.GetWindowLongW
SetWindowPos = user32.SetWindowPos
FindWindow = user32.FindWindowW

# Window styles
GWL_STYLE = -16
WS_VISIBLE = 0x10000000
WS_CHILD = 0x40000000
WS_POPUP = 0x80000000
SWP_FRAMECHANGED = 0x0020
SWP_NOMOVE = 0x0002
SWP_NOSIZE = 0x0001
SWP_NOZORDER = 0x0004


class EmbeddedTouchpadWindow:
    """Single window with embedded C# capture"""
    
    def __init__(self, width=1400, height=900):
        pygame.init()
        
        self.width = width
        self.height = height
        
        # Create pygame window
        self.screen = pygame.display.set_mode((width, height), pygame.RESIZABLE)
        pygame.display.set_caption("Touchpad Biometric System")
        
        # Get pygame window handle
        self.pygame_hwnd = pygame.display.get_wm_info()['window']
        print(f"Pygame window handle: {self.pygame_hwnd}")
        
        # Colors
        self.bg_color = (20, 20, 30)
        self.panel_color = (30, 30, 40)
        self.text_color = (200, 200, 200)
        self.accent_color = (0, 255, 100)
        
        # Fonts
        self.font_large = pygame.font.Font(None, 48)
        self.font_medium = pygame.font.Font(None, 32)
        self.font_small = pygame.font.Font(None, 24)
        
        # Layout - reserve space for embedded C# window
        self.csharp_area = pygame.Rect(20, 20, 800, 600)
        self.info_area = pygame.Rect(840, 20, width - 860, height - 40)
        
        # Touchpad reader
        self.reader = None
        self.csharp_hwnd = None
        
        # State
        self.status = "Initializing..."
        self.contact_count = 0
        
        # FPS
        self.clock = pygame.time.Clock()
        self.fps = 0
    
    def _list_all_windows(self):
        """List all visible windows (for debugging)"""
        EnumWindows = user32.EnumWindows
        EnumWindowsProc = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.POINTER(ctypes.c_int), ctypes.POINTER(ctypes.c_int))
        GetWindowText = user32.GetWindowTextW
        GetWindowTextLength = user32.GetWindowTextLengthW
        IsWindowVisible = user32.IsWindowVisible
        
        windows = []
        
        def foreach_window(hwnd, lParam):
            if IsWindowVisible(hwnd):
                length = GetWindowTextLength(hwnd)
                if length > 0:
                    buff = ctypes.create_unicode_buffer(length + 1)
                    GetWindowText(hwnd, buff, length + 1)
                    title = buff.value
                    if title and "touchpad" in title.lower():
                        windows.append((hwnd, title))
            return True
        
        EnumWindows(EnumWindowsProc(foreach_window), 0)
        
        if windows:
            print("\nFound windows with 'touchpad' in title:")
            for hwnd, title in windows:
                print(f"  HWND: {hwnd} - Title: '{title}'")
        else:
            print("\nNo windows found with 'touchpad' in title")
    
    def start_reader(self):
        """Start the touchpad reader and embed its window"""
        print("\nStarting touchpad reader...")
        
        # Start reader (will create C# window)
        self.reader = SimpleTouchpadReader(headless=False)
        
        if not self.reader.start():
            print("✗ Failed to start reader")
            return False
        
        print("✓ Reader started")
        
        # Wait for C# window to be created
        print("Waiting for C# window...")
        time.sleep(2.0)
        
        # Try multiple possible window titles
        possible_titles = [
            "Touchpad Capture (Keep this window open)",
            "Touchpad Capture & Visualization",
            "Touchpad Capture",
            "Touchpad Capture (Headless)",
        ]
        
        print("Searching for C# window...")
        for title in possible_titles:
            print(f"  Trying: '{title}'")
            self.csharp_hwnd = FindWindow(None, title)
            if self.csharp_hwnd:
                print(f"  ✓ Found with title: '{title}'")
                break
        
        if not self.csharp_hwnd:
            print("\n✗ Could not find C# window with any known title")
            print("\nTrying to enumerate all windows...")
            self._list_all_windows()
            print("\nPlease check if the C# window appeared separately.")
            print("If yes, note its exact title and update embedded_window.py")
            return False
        
        print(f"✓ Found C# window handle: {self.csharp_hwnd}")
        
        # Embed the C# window inside pygame window
        print("Embedding C# window...")
        
        # Change window style to child
        style = GetWindowLong(self.csharp_hwnd, GWL_STYLE)
        style = (style & ~WS_POPUP) | WS_CHILD
        SetWindowLong(self.csharp_hwnd, GWL_STYLE, style)
        
        # Set pygame window as parent
        result = SetParent(self.csharp_hwnd, self.pygame_hwnd)
        
        if result:
            print(f"✓ Embedded successfully (previous parent: {result})")
        else:
            print("✗ Failed to embed window")
            return False
        
        # Position and resize the embedded window
        SetWindowPos(
            self.csharp_hwnd,
            0,  # HWND_TOP
            self.csharp_area.x,
            self.csharp_area.y,
            self.csharp_area.width,
            self.csharp_area.height,
            SWP_FRAMECHANGED
        )
        
        print("✓ Window embedded and positioned")
        self.status = "Ready"
        
        return True
    
    def stop_reader(self):
        """Stop the reader"""
        if self.reader:
            self.reader.stop()
    
    def update(self):
        """Update state"""
        if self.reader:
            contacts = self.reader.read_contacts()
            if contacts is not None:
                self.contact_count = len(contacts)
    
    def draw(self):
        """Draw the UI"""
        # Fill background
        self.screen.fill(self.bg_color)
        
        # Draw area for embedded C# window (border)
        pygame.draw.rect(self.screen, (60, 60, 70), self.csharp_area, 2)
        
        # Draw info panel
        pygame.draw.rect(self.screen, self.panel_color, self.info_area)
        pygame.draw.rect(self.screen, (60, 60, 70), self.info_area, 2)
        
        # Title
        title = self.font_large.render("Biometric System", True, self.accent_color)
        self.screen.blit(title, (self.info_area.x + 20, self.info_area.y + 20))
        
        # Status
        y = self.info_area.y + 80
        status_text = self.font_medium.render(self.status, True, self.text_color)
        self.screen.blit(status_text, (self.info_area.x + 20, y))
        y += 50
        
        # Contact count
        if self.contact_count > 0:
            count_text = self.font_medium.render(f"{self.contact_count} finger(s)", True, self.accent_color)
        else:
            count_text = self.font_medium.render("No touch", True, (150, 150, 150))
        self.screen.blit(count_text, (self.info_area.x + 20, y))
        y += 60
        
        # Instructions
        instructions = [
            "C# Window (Left):",
            "• Real-time visualization",
            "• Colored finger trails",
            "",
            "Python Panel (Right):",
            "• Biometric analysis",
            "• Training/verification",
            "",
            "All in ONE window!"
        ]
        
        for line in instructions:
            text = self.font_small.render(line, True, (150, 150, 150))
            self.screen.blit(text, (self.info_area.x + 20, y))
            y += 28
        
        # FPS
        fps_text = self.font_small.render(f"FPS: {self.fps:.0f}", True, (100, 100, 100))
        self.screen.blit(fps_text, (self.info_area.x + 20, self.info_area.bottom - 40))
        
        pygame.display.flip()
    
    def run(self):
        """Main loop"""
        running = True
        
        while running:
            # Handle events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                elif event.type == pygame.VIDEORESIZE:
                    # Handle window resize
                    self.width = event.w
                    self.height = event.h
                    self.screen = pygame.display.set_mode((self.width, self.height), pygame.RESIZABLE)
                    
                    # Reposition embedded window
                    if self.csharp_hwnd:
                        SetWindowPos(
                            self.csharp_hwnd,
                            0,
                            self.csharp_area.x,
                            self.csharp_area.y,
                            self.csharp_area.width,
                            self.csharp_area.height,
                            0
                        )
            
            # Update
            self.update()
            
            # Draw
            self.draw()
            
            # FPS
            self.fps = self.clock.get_fps()
            self.clock.tick(60)


def main():
    print("="*70)
    print("EMBEDDED WINDOW - C# inside Python")
    print("="*70)
    print("\nThis creates ONE single window with:")
    print("  • C# WPF window embedded on the left (touchpad visualization)")
    print("  • Python pygame panel on the right (biometric analysis)")
    print("\nAll in ONE window!\n")
    
    window = EmbeddedTouchpadWindow()
    
    if not window.start_reader():
        print("\n✗ Failed to start")
        print("\nMake sure:")
        print("  1. TouchpadCapture.exe is built (run build_rawinput.bat)")
        print("  2. You're on Windows")
        print("  3. You have a Precision Touchpad")
        return
    
    print("\n" + "="*70)
    print("✓ EMBEDDED WINDOW READY!")
    print("="*70)
    print("\nYou should see ONE window with:")
    print("  • C# visualization on the left")
    print("  • Python info panel on the right")
    print("\nTouch your touchpad to test!")
    print("Press ESC to exit\n")
    
    try:
        window.run()
    except KeyboardInterrupt:
        print("\n\nInterrupted...")
    finally:
        window.stop_reader()
        pygame.quit()
        print("✓ Stopped")


if __name__ == "__main__":
    main()
