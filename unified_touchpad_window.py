#!/usr/bin/env python3
"""
Unified Touchpad Window

Single pygame window that shows:
1. Real-time touchpad visualization
2. Contact information
3. Biometric training/verification status

No separate C# window needed - runs in headless mode!
"""

import pygame
import time
from simple_windows_touchpad import SimpleTouchpadReader
from typing import Dict, List, Optional


class UnifiedTouchpadWindow:
    """Single window for touchpad capture and visualization"""
    
    def __init__(self, width: int = 1200, height: int = 800):
        pygame.init()
        
        self.width = width
        self.height = height
        self.screen = pygame.display.set_mode((width, height))
        pygame.display.set_caption("Unified Touchpad Capture")
        
        # Fonts
        self.font_large = pygame.font.Font(None, 48)
        self.font_medium = pygame.font.Font(None, 32)
        self.font_small = pygame.font.Font(None, 24)
        
        # Colors
        self.bg_color = (20, 20, 30)
        self.panel_color = (30, 30, 40)
        self.text_color = (200, 200, 200)
        self.accent_color = (0, 255, 100)
        self.contact_colors = [
            (255, 100, 100),  # Red
            (100, 255, 100),  # Green
            (100, 100, 255),  # Blue
            (255, 255, 100),  # Yellow
            (255, 100, 255),  # Magenta
        ]
        
        # Touchpad reader (headless mode!)
        self.reader = SimpleTouchpadReader(headless=True)
        
        # Visualization state
        self.contact_trails: Dict[int, List[tuple]] = {}  # {contact_id: [(x, y, time), ...]}
        self.trail_max_age = 1.0  # seconds
        self.trail_max_points = 100
        
        # Touchpad bounds (will be auto-detected)
        self.touchpad_min_x = 0
        self.touchpad_max_x = 10000
        self.touchpad_min_y = 0
        self.touchpad_max_y = 10000
        
        # Visualization area (left side of screen)
        self.viz_area = pygame.Rect(20, 20, width - 500, height - 40)
        
        # Info panel (right side)
        self.info_panel = pygame.Rect(width - 460, 20, 440, height - 40)
        
        # Status
        self.status_text = "Initializing..."
        self.status_color = self.accent_color
        
        # FPS tracking
        self.clock = pygame.time.Clock()
        self.fps = 0
    
    def start(self) -> bool:
        """Start the touchpad reader"""
        return self.reader.start()
    
    def stop(self):
        """Stop the touchpad reader"""
        self.reader.stop()
    
    def map_touchpad_to_screen(self, x: int, y: int) -> tuple:
        """Map touchpad coordinates to screen visualization area"""
        # Normalize to 0-1
        norm_x = (x - self.touchpad_min_x) / (self.touchpad_max_x - self.touchpad_min_x)
        norm_y = (y - self.touchpad_min_y) / (self.touchpad_max_y - self.touchpad_min_y)
        
        # Clamp
        norm_x = max(0, min(1, norm_x))
        norm_y = max(0, min(1, norm_y))
        
        # Map to viz area
        screen_x = self.viz_area.x + norm_x * self.viz_area.width
        screen_y = self.viz_area.y + norm_y * self.viz_area.height
        
        return int(screen_x), int(screen_y)
    
    def update_trails(self, contacts: List[Dict]):
        """Update contact trails"""
        current_time = time.time()
        current_ids = set()
        
        # Add new points
        for contact in contacts:
            contact_id = contact['ContactId']
            current_ids.add(contact_id)
            
            # Update bounds
            self.touchpad_min_x = min(self.touchpad_min_x, contact['X'])
            self.touchpad_max_x = max(self.touchpad_max_x, contact['X'])
            self.touchpad_min_y = min(self.touchpad_min_y, contact['Y'])
            self.touchpad_max_y = max(self.touchpad_max_y, contact['Y'])
            
            # Add to trail
            if contact_id not in self.contact_trails:
                self.contact_trails[contact_id] = []
            
            screen_pos = self.map_touchpad_to_screen(contact['X'], contact['Y'])
            self.contact_trails[contact_id].append((*screen_pos, current_time))
            
            # Limit trail length
            if len(self.contact_trails[contact_id]) > self.trail_max_points:
                self.contact_trails[contact_id].pop(0)
        
        # Remove old points and inactive contacts
        for contact_id in list(self.contact_trails.keys()):
            trail = self.contact_trails[contact_id]
            
            # Remove old points
            trail[:] = [(x, y, t) for x, y, t in trail if current_time - t < self.trail_max_age]
            
            # Remove empty trails
            if not trail:
                del self.contact_trails[contact_id]
    
    def draw_visualization(self):
        """Draw the touchpad visualization"""
        # Draw viz area background
        pygame.draw.rect(self.screen, (40, 40, 50), self.viz_area)
        pygame.draw.rect(self.screen, (60, 60, 70), self.viz_area, 2)
        
        # Draw trails
        for contact_id, trail in self.contact_trails.items():
            if len(trail) < 2:
                continue
            
            color = self.contact_colors[contact_id % len(self.contact_colors)]
            current_time = time.time()
            
            # Draw trail with fading
            for i in range(len(trail) - 1):
                x1, y1, t1 = trail[i]
                x2, y2, t2 = trail[i + 1]
                
                # Calculate alpha based on age
                age = current_time - t2
                alpha = int(255 * (1 - age / self.trail_max_age))
                alpha = max(0, min(255, alpha))
                
                # Draw line segment
                if alpha > 0:
                    # Calculate thickness based on age (thicker = newer)
                    thickness = int(3 + 5 * (1 - age / self.trail_max_age))
                    pygame.draw.line(self.screen, color, (x1, y1), (x2, y2), thickness)
            
            # Draw current position (larger circle)
            if trail:
                x, y, t = trail[-1]
                pygame.draw.circle(self.screen, color, (x, y), 15)
                pygame.draw.circle(self.screen, (255, 255, 255), (x, y), 15, 2)
                
                # Draw contact ID
                id_text = self.font_small.render(str(contact_id), True, (255, 255, 255))
                self.screen.blit(id_text, (x - 8, y - 10))
    
    def draw_info_panel(self, contacts: List[Dict]):
        """Draw the info panel"""
        # Panel background
        pygame.draw.rect(self.screen, self.panel_color, self.info_panel)
        pygame.draw.rect(self.screen, (60, 60, 70), self.info_panel, 2)
        
        y_offset = self.info_panel.y + 20
        
        # Title
        title = self.font_large.render("Touchpad", True, self.accent_color)
        self.screen.blit(title, (self.info_panel.x + 20, y_offset))
        y_offset += 60
        
        # Status
        status = self.font_medium.render(self.status_text, True, self.status_color)
        self.screen.blit(status, (self.info_panel.x + 20, y_offset))
        y_offset += 50
        
        # Contact count
        count_text = f"{len(contacts)} finger(s)"
        count = self.font_medium.render(count_text, True, self.text_color)
        self.screen.blit(count, (self.info_panel.x + 20, y_offset))
        y_offset += 50
        
        # Contact details
        if contacts:
            details_title = self.font_small.render("Contact Details:", True, self.accent_color)
            self.screen.blit(details_title, (self.info_panel.x + 20, y_offset))
            y_offset += 35
            
            for contact in contacts:
                contact_id = contact['ContactId']
                color = self.contact_colors[contact_id % len(self.contact_colors)]
                
                # Contact ID
                id_text = self.font_small.render(f"Contact #{contact_id}", True, color)
                self.screen.blit(id_text, (self.info_panel.x + 30, y_offset))
                y_offset += 25
                
                # Coordinates
                coord_text = f"  X: {contact['X']:5d}  Y: {contact['Y']:5d}"
                coord = self.font_small.render(coord_text, True, self.text_color)
                self.screen.blit(coord, (self.info_panel.x + 30, y_offset))
                y_offset += 30
        
        # FPS
        y_offset = self.info_panel.bottom - 40
        fps_text = f"FPS: {self.fps:.0f}"
        fps = self.font_small.render(fps_text, True, (150, 150, 150))
        self.screen.blit(fps, (self.info_panel.x + 20, y_offset))
        
        # Instructions
        y_offset = self.info_panel.bottom - 120
        instructions = [
            "Touch your touchpad",
            "to see visualization",
            "",
            "Press ESC to exit"
        ]
        for line in instructions:
            text = self.font_small.render(line, True, (150, 150, 150))
            self.screen.blit(text, (self.info_panel.x + 20, y_offset))
            y_offset += 25
    
    def run(self):
        """Main run loop"""
        running = True
        
        while running:
            # Handle events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
            
            # Read touchpad data
            contacts_data = self.reader.read_contacts()
            
            if contacts_data is not None:
                if len(contacts_data) > 0:
                    self.update_trails(contacts_data)
                    self.status_text = "Active"
                    self.status_color = self.accent_color
                elif len(self.contact_trails) == 0:
                    self.status_text = "Waiting..."
                    self.status_color = (150, 150, 150)
            
            # Get current contacts for display
            current_contacts = list(self.reader.get_current_contacts().values())
            display_contacts = [
                {
                    'ContactId': c['ContactId'],
                    'X': c['X'],
                    'Y': c['Y']
                }
                for c in current_contacts
            ]
            
            # Draw
            self.screen.fill(self.bg_color)
            self.draw_visualization()
            self.draw_info_panel(display_contacts)
            
            pygame.display.flip()
            
            # Update FPS
            self.fps = self.clock.get_fps()
            self.clock.tick(60)  # 60 FPS


def main():
    """Main entry point"""
    print("="*60)
    print("Unified Touchpad Window")
    print("="*60)
    print("\nStarting touchpad capture in headless mode...")
    print("(No separate C# window will appear)")
    
    window = UnifiedTouchpadWindow()
    
    if not window.start():
        print("\n✗ Failed to start touchpad reader")
        print("  Make sure TouchpadCapture.exe is built")
        print("  Run: build_rawinput.bat")
        return
    
    print("✓ Touchpad reader started")
    print("\nTouch your touchpad to see visualization!")
    print("Press ESC to exit\n")
    
    try:
        window.run()
    except KeyboardInterrupt:
        print("\n\nInterrupted...")
    finally:
        window.stop()
        pygame.quit()
        print("✓ Stopped")


if __name__ == "__main__":
    main()
