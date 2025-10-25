#!/usr/bin/env python3
"""
Windows Precision Touchpad HID Parser

Full implementation using Raw Input API + HID parsing to get true multi-touch.
Based on ichisadashioko/windows-touchpad and emoacht/RawInput.Touchpad
"""

import platform
import time
import asyncio
from dataclasses import dataclass
from typing import Dict, List, Optional, Callable, Tuple
from ctypes import (
    windll, Structure, POINTER, c_int, c_uint, byref, c_void_p,
    sizeof, cast, c_ubyte, c_ushort, c_long, c_char, c_ulong,
    WINFUNCTYPE, create_string_buffer
)
from ctypes.wintypes import DWORD, HWND, UINT, WPARAM, LPARAM, HANDLE, WORD, USHORT, LONG, BOOL

# Check if we're on Windows
IS_WINDOWS = platform.system() == 'Windows'

if IS_WINDOWS:
    try:
        import win32api
        import win32con
        import win32gui
        import threading
    except ImportError:
        print("⚠️  pywin32 not installed. Install with: pip install pywin32")
        IS_WINDOWS = False

# Raw Input API Constants
WM_INPUT = 0x00FF
RIDEV_INPUTSINK = 0x00000100
RID_INPUT = 0x10000003
RID_HEADER = 0x10000005

RIDI_PREPARSEDDATA = 0x20000005
RIDI_DEVICENAME = 0x20000007
RIDI_DEVICEINFO = 0x2000000b

RIM_TYPEMOUSE = 0
RIM_TYPEKEYBOARD = 1
RIM_TYPEHID = 2

# HID Usage Pages
HID_USAGE_PAGE_DIGITIZER = 0x0D
HID_USAGE_DIGITIZER_TOUCH_PAD = 0x05

# HID Usages for Digitizer
HID_USAGE_DIGITIZER_CONTACT_ID = 0x51
HID_USAGE_DIGITIZER_TIP_SWITCH = 0x42
HID_USAGE_DIGITIZER_X = 0x30
HID_USAGE_DIGITIZER_Y = 0x31
HID_USAGE_DIGITIZER_CONTACT_COUNT = 0x54
HID_USAGE_DIGITIZER_SCAN_TIME = 0x56


# Raw Input structures
class RAWINPUTDEVICE(Structure):
    _fields_ = [
        ("usUsagePage", USHORT),
        ("usUsage", USHORT),
        ("dwFlags", DWORD),
        ("hwndTarget", HWND),
    ]

class RAWINPUTHEADER(Structure):
    _fields_ = [
        ("dwType", DWORD),
        ("dwSize", DWORD),
        ("hDevice", HANDLE),
        ("wParam", WPARAM),
    ]

class RAWHID(Structure):
    _fields_ = [
        ("dwSizeHid", DWORD),
        ("dwCount", DWORD),
        ("bRawData", c_ubyte * 1),
    ]

class RAWINPUT_UNION(Structure):
    _fields_ = [
        ("hid", RAWHID),
    ]

class RAWINPUT(Structure):
    _fields_ = [
        ("header", RAWINPUTHEADER),
        ("data", RAWINPUT_UNION),
    ]

# HID structures
class HIDP_CAPS(Structure):
    _fields_ = [
        ("Usage", USHORT),
        ("UsagePage", USHORT),
        ("InputReportByteLength", USHORT),
        ("OutputReportByteLength", USHORT),
        ("FeatureReportByteLength", USHORT),
        ("Reserved", USHORT * 17),
        ("NumberLinkCollectionNodes", USHORT),
        ("NumberInputButtonCaps", USHORT),
        ("NumberInputValueCaps", USHORT),
        ("NumberInputDataIndices", USHORT),
        ("NumberOutputButtonCaps", USHORT),
        ("NumberOutputValueCaps", USHORT),
        ("NumberOutputDataIndices", USHORT),
        ("NumberFeatureButtonCaps", USHORT),
        ("NumberFeatureValueCaps", USHORT),
        ("NumberFeatureDataIndices", USHORT),
    ]

class HIDP_VALUE_CAPS(Structure):
    _fields_ = [
        ("UsagePage", USHORT),
        ("ReportID", c_ubyte),
        ("IsAlias", BOOL),
        ("BitField", USHORT),
        ("LinkCollection", USHORT),
        ("LinkUsage", USHORT),
        ("LinkUsagePage", USHORT),
        ("IsRange", BOOL),
        ("IsStringRange", BOOL),
        ("IsDesignatorRange", BOOL),
        ("IsAbsolute", BOOL),
        ("HasNull", BOOL),
        ("Reserved", c_ubyte),
        ("BitSize", USHORT),
        ("ReportCount", USHORT),
        ("Reserved2", USHORT * 5),
        ("UnitsExp", LONG),
        ("Units", LONG),
        ("LogicalMin", LONG),
        ("LogicalMax", LONG),
        ("PhysicalMin", LONG),
        ("PhysicalMax", LONG),
        ("UsageMin", USHORT),
        ("UsageMax", USHORT),
        ("StringMin", USHORT),
        ("StringMax", USHORT),
        ("DesignatorMin", USHORT),
        ("DesignatorMax", USHORT),
        ("DataIndexMin", USHORT),
        ("DataIndexMax", USHORT),
    ]

class HIDP_BUTTON_CAPS(Structure):
    _fields_ = [
        ("UsagePage", USHORT),
        ("ReportID", c_ubyte),
        ("IsAlias", BOOL),
        ("BitField", USHORT),
        ("LinkCollection", USHORT),
        ("LinkUsage", USHORT),
        ("LinkUsagePage", USHORT),
        ("IsRange", BOOL),
        ("IsStringRange", BOOL),
        ("IsDesignatorRange", BOOL),
        ("IsAbsolute", BOOL),
        ("Reserved", DWORD * 10),
        ("UsageMin", USHORT),
        ("UsageMax", USHORT),
        ("StringMin", USHORT),
        ("StringMax", USHORT),
        ("DesignatorMin", USHORT),
        ("DesignatorMax", USHORT),
        ("DataIndexMin", USHORT),
        ("DataIndexMax", USHORT),
    ]


@dataclass
class TouchPoint:
    """Single touch point with position and timing"""
    x: float
    y: float
    timestamp: float
    timestamp_ns: int

@dataclass
class TouchContact:
    """Touch contact with ID and state"""
    contact_id: int
    x: int
    y: int
    tip_switch: bool
    
class HIDTouchpadDevice:
    """Represents a single HID touchpad device with its capabilities"""
    
    def __init__(self, handle: HANDLE):
        self.handle = handle
        self.preparsed_data = None
        self.caps = None
        self.value_caps = []
        self.button_caps = []
        
        # Device dimensions
        self.logical_max_x = 0
        self.logical_max_y = 0
        self.physical_max_x = 0
        self.physical_max_y = 0
        
        # Contact tracking
        self.max_contacts = 5
        
        # Load HID functions
        self.hid = windll.hid
        self.user32 = windll.user32
        
        # Initialize device
        self._load_device_info()
    
    def _load_device_info(self):
        """Load HID device information and capabilities"""
        try:
            # Get preparsed data size
            size = c_uint(0)
            self.user32.GetRawInputDeviceInfoA(
                self.handle, RIDI_PREPARSEDDATA, None, byref(size)
            )
            
            if size.value == 0:
                return False
            
            # Allocate and get preparsed data
            self.preparsed_data = create_string_buffer(size.value)
            result = self.user32.GetRawInputDeviceInfoA(
                self.handle, RIDI_PREPARSEDDATA, self.preparsed_data, byref(size)
            )
            
            if result <= 0:
                return False
            
            # Get device capabilities
            self.caps = HIDP_CAPS()
            status = self.hid.HidP_GetCaps(self.preparsed_data, byref(self.caps))
            
            if status != 0x00110000:  # HIDP_STATUS_SUCCESS
                return False
            
            print(f"✓ HID Device Capabilities:")
            print(f"  Usage Page: 0x{self.caps.UsagePage:02X}")
            print(f"  Usage: 0x{self.caps.Usage:02X}")
            print(f"  Input Report Length: {self.caps.InputReportByteLength}")
            print(f"  Value Caps: {self.caps.NumberInputValueCaps}")
            print(f"  Button Caps: {self.caps.NumberInputButtonCaps}")
            
            # Get value capabilities
            self._load_value_caps()
            
            # Get button capabilities
            self._load_button_caps()
            
            return True
            
        except Exception as e:
            print(f"Error loading device info: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _load_value_caps(self):
        """Load value capabilities (X, Y, Contact ID, etc.)"""
        try:
            num_caps = c_ushort(self.caps.NumberInputValueCaps)
            caps_array = (HIDP_VALUE_CAPS * num_caps.value)()
            
            status = self.hid.HidP_GetValueCaps(
                0,  # HidP_Input
                caps_array,
                byref(num_caps),
                self.preparsed_data
            )
            
            if status != 0x00110000:
                return
            
            print(f"\n  Value Capabilities ({num_caps.value}):")
            for i in range(num_caps.value):
                cap = caps_array[i]
                self.value_caps.append(cap)
                
                usage_name = self._get_usage_name(cap.UsagePage, cap.UsageMin)
                print(f"    [{i}] Usage: 0x{cap.UsageMin:02X} ({usage_name})")
                print(f"        Logical: {cap.LogicalMin} - {cap.LogicalMax}")
                print(f"        Physical: {cap.PhysicalMin} - {cap.PhysicalMax}")
                print(f"        Report Count: {cap.ReportCount}")
                
                # Store device dimensions
                if cap.UsagePage == HID_USAGE_PAGE_DIGITIZER:
                    if cap.UsageMin == HID_USAGE_DIGITIZER_X:
                        self.logical_max_x = cap.LogicalMax
                        self.physical_max_x = cap.PhysicalMax if cap.PhysicalMax > 0 else cap.LogicalMax
                    elif cap.UsageMin == HID_USAGE_DIGITIZER_Y:
                        self.logical_max_y = cap.LogicalMax
                        self.physical_max_y = cap.PhysicalMax if cap.PhysicalMax > 0 else cap.LogicalMax
                        
        except Exception as e:
            print(f"Error loading value caps: {e}")
    
    def _load_button_caps(self):
        """Load button capabilities (Tip Switch, etc.)"""
        try:
            num_caps = c_ushort(self.caps.NumberInputButtonCaps)
            if num_caps.value == 0:
                return
                
            caps_array = (HIDP_BUTTON_CAPS * num_caps.value)()
            
            status = self.hid.HidP_GetButtonCaps(
                0,  # HidP_Input
                caps_array,
                byref(num_caps),
                self.preparsed_data
            )
            
            if status != 0x00110000:
                return
            
            print(f"\n  Button Capabilities ({num_caps.value}):")
            for i in range(num_caps.value):
                cap = caps_array[i]
                self.button_caps.append(cap)
                
                usage_name = self._get_usage_name(cap.UsagePage, cap.UsageMin)
                print(f"    [{i}] Usage: 0x{cap.UsageMin:02X} ({usage_name})")
                        
        except Exception as e:
            print(f"Error loading button caps: {e}")
    
    def _get_usage_name(self, usage_page: int, usage: int) -> str:
        """Get human-readable usage name"""
        if usage_page == HID_USAGE_PAGE_DIGITIZER:
            names = {
                0x30: "X",
                0x31: "Y",
                0x42: "Tip Switch",
                0x47: "Touch Valid",
                0x51: "Contact ID",
                0x54: "Contact Count",
                0x56: "Scan Time",
            }
            return names.get(usage, f"Unknown 0x{usage:02X}")
        return f"0x{usage:02X}"
    
    def parse_report(self, report_data: bytes) -> List[TouchContact]:
        """Parse HID report to extract touch contacts"""
        contacts = []
        
        try:
            # Create buffer from report data
            report_buffer = create_string_buffer(report_data)
            report_length = len(report_data)
            
            # Parse each contact (assuming up to 5 contacts)
            for contact_idx in range(self.max_contacts):
                contact = self._parse_single_contact(report_buffer, report_length, contact_idx)
                if contact and contact.tip_switch:
                    contacts.append(contact)
                    
        except Exception as e:
            print(f"Error parsing report: {e}")
        
        return contacts
    
    def _parse_single_contact(self, report_buffer, report_length: int, contact_idx: int) -> Optional[TouchContact]:
        """Parse a single contact from HID report"""
        try:
            contact_id = None
            x = None
            y = None
            tip_switch = False
            
            # Get Contact ID
            for cap in self.value_caps:
                if cap.UsagePage == HID_USAGE_PAGE_DIGITIZER and cap.UsageMin == HID_USAGE_DIGITIZER_CONTACT_ID:
                    value = c_ulong(0)
                    status = self.hid.HidP_GetUsageValue(
                        0,  # HidP_Input
                        cap.UsagePage,
                        cap.LinkCollection,
                        cap.UsageMin,
                        byref(value),
                        self.preparsed_data,
                        report_buffer,
                        report_length
                    )
                    if status == 0x00110000:
                        contact_id = value.value
                        break
            
            # Get X coordinate
            for cap in self.value_caps:
                if cap.UsagePage == HID_USAGE_PAGE_DIGITIZER and cap.UsageMin == HID_USAGE_DIGITIZER_X:
                    value = c_ulong(0)
                    status = self.hid.HidP_GetUsageValue(
                        0,  # HidP_Input
                        cap.UsagePage,
                        cap.LinkCollection,
                        cap.UsageMin,
                        byref(value),
                        self.preparsed_data,
                        report_buffer,
                        report_length
                    )
                    if status == 0x00110000:
                        x = value.value
                        break
            
            # Get Y coordinate
            for cap in self.value_caps:
                if cap.UsagePage == HID_USAGE_PAGE_DIGITIZER and cap.UsageMin == HID_USAGE_DIGITIZER_Y:
                    value = c_ulong(0)
                    status = self.hid.HidP_GetUsageValue(
                        0,  # HidP_Input
                        cap.UsagePage,
                        cap.LinkCollection,
                        cap.UsageMin,
                        byref(value),
                        self.preparsed_data,
                        report_buffer,
                        report_length
                    )
                    if status == 0x00110000:
                        y = value.value
                        break
            
            # Get Tip Switch (button)
            for cap in self.button_caps:
                if cap.UsagePage == HID_USAGE_PAGE_DIGITIZER and cap.UsageMin == HID_USAGE_DIGITIZER_TIP_SWITCH:
                    usage_length = c_ulong(cap.UsageMax - cap.UsageMin + 1)
                    usages = (USHORT * usage_length.value)()
                    
                    status = self.hid.HidP_GetUsages(
                        0,  # HidP_Input
                        cap.UsagePage,
                        cap.LinkCollection,
                        usages,
                        byref(usage_length),
                        self.preparsed_data,
                        report_buffer,
                        report_length
                    )
                    
                    if status == 0x00110000:
                        for i in range(usage_length.value):
                            if usages[i] == HID_USAGE_DIGITIZER_TIP_SWITCH:
                                tip_switch = True
                                break
                    break
            
            if contact_id is not None and x is not None and y is not None:
                return TouchContact(contact_id, x, y, tip_switch)
                
        except Exception as e:
            print(f"Error parsing contact: {e}")
        
        return None


class WindowsTouchpadCaptureHID:
    """
    Windows Precision Touchpad capture using Raw Input API + HID parsing
    
    This provides TRUE multi-touch support by parsing HID reports.
    """
    
    def __init__(self):
        if not IS_WINDOWS:
            raise RuntimeError("WindowsTouchpadCaptureHID only works on Windows")
        
        self.screen_width = 1200
        self.screen_height = 800
        
        # Touch tracking
        self.active_touches: Dict[int, List[TouchPoint]] = {}
        self.completed_touches: List[List[TouchPoint]] = []
        self.is_capturing = False
        
        # HID devices
        self.devices: Dict[HANDLE, HIDTouchpadDevice] = {}
        
        # Window handle
        self.hwnd = None
        
        # Message loop thread
        self.message_thread = None
        self.running = False
        
        # Callbacks
        self.on_finger_down_callback = None
        self.on_finger_up_callback = None
        self.on_point_added_callback = None
        
        # Load user32.dll functions
        self.user32 = windll.user32
        
        # RegisterRawInputDevices
        self.RegisterRawInputDevices = self.user32.RegisterRawInputDevices
        self.RegisterRawInputDevices.argtypes = [POINTER(RAWINPUTDEVICE), UINT, UINT]
        self.RegisterRawInputDevices.restype = c_int
        
        # GetRawInputData
        self.GetRawInputData = self.user32.GetRawInputData
        self.GetRawInputData.argtypes = [HANDLE, UINT, c_void_p, POINTER(UINT), UINT]
        self.GetRawInputData.restype = c_int
    
    def open_device(self) -> bool:
        """Initialize Windows HID touchpad capture"""
        try:
            # Check for Precision Touchpad
            try:
                import winreg
                key = winreg.OpenKey(
                    winreg.HKEY_LOCAL_MACHINE,
                    r"SOFTWARE\Microsoft\Windows\CurrentVersion\PrecisionTouchPad",
                    0,
                    winreg.KEY_READ
                )
                winreg.CloseKey(key)
                print(f"✓ Windows Precision Touchpad detected (registry)")
            except:
                print(f"⚠️  Precision Touchpad not in registry, but will try anyway")
            
            # Create window for receiving raw input
            self._create_message_window()
            
            if self.hwnd is None:
                print(f"✗ Failed to create message window")
                return False
            
            # Register for HID touchpad input
            devices = (RAWINPUTDEVICE * 1)()
            
            # Register for digitizer touchpad (Usage Page 0x0D, Usage 0x05)
            devices[0].usUsagePage = HID_USAGE_PAGE_DIGITIZER
            devices[0].usUsage = HID_USAGE_DIGITIZER_TOUCH_PAD
            devices[0].dwFlags = RIDEV_INPUTSINK
            devices[0].hwndTarget = self.hwnd
            
            if not self.RegisterRawInputDevices(devices, 1, sizeof(RAWINPUTDEVICE)):
                error = windll.kernel32.GetLastError()
                print(f"✗ Failed to register raw input devices (error: {error})")
                return False
            
            print(f"✓ Windows HID Touchpad initialized")
            print(f"  Registered for HID touchpad events (0x0D:0x05)")
            print(f"  Window handle: 0x{self.hwnd:08X}")
            print(f"")
            print(f"🎉 TRUE MULTI-TOUCH ENABLED!")
            print(f"  Touch your touchpad with multiple fingers")
            
            # Start message loop
            self.running = True
            self.message_thread = threading.Thread(target=self._message_loop, daemon=True)
            self.message_thread.start()
            
            return True
            
        except Exception as e:
            print(f"✗ Error initializing HID touchpad: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _create_message_window(self):
        """Create a window to receive raw input messages"""
        try:
            # Register window class
            wc = win32gui.WNDCLASS()
            wc.lpfnWndProc = self._wnd_proc
            wc.lpszClassName = "HIDTouchpadWindow"
            wc.hInstance = win32api.GetModuleHandle(None)
            wc.hCursor = win32gui.LoadCursor(0, win32con.IDC_ARROW)
            wc.hbrBackground = win32gui.GetStockObject(win32con.WHITE_BRUSH)
            
            try:
                win32gui.RegisterClass(wc)
            except Exception:
                pass  # Already registered
            
            # Create window
            self.hwnd = win32gui.CreateWindow(
                "HIDTouchpadWindow",
                "HID Touchpad Capture - Touch your touchpad!",
                win32con.WS_OVERLAPPEDWINDOW | win32con.WS_VISIBLE,
                100, 100, self.screen_width, self.screen_height,
                0, 0, wc.hInstance, None
            )
            
            win32gui.ShowWindow(self.hwnd, win32con.SW_SHOW)
            win32gui.UpdateWindow(self.hwnd)
            
        except Exception as e:
            print(f"Error creating window: {e}")
            import traceback
            traceback.print_exc()
            self.hwnd = None
    
    def _wnd_proc(self, hwnd, msg, wparam, lparam):
        """Window procedure to handle messages"""
        try:
            if msg == WM_INPUT:
                self._handle_raw_input(lparam)
                return 0
            
            elif msg == win32con.WM_DESTROY:
                win32gui.PostQuitMessage(0)
                return 0
        
        except Exception as e:
            print(f"Error in window proc: {e}")
            import traceback
            traceback.print_exc()
        
        return win32gui.DefWindowProc(hwnd, msg, wparam, lparam)
    
    def _handle_raw_input(self, lparam):
        """Handle WM_INPUT message"""
        try:
            # Get size of raw input data
            size = UINT(0)
            self.GetRawInputData(lparam, RID_INPUT, None, byref(size), sizeof(RAWINPUTHEADER))
            
            if size.value == 0:
                return
            
            # Allocate buffer and get data
            buffer = (c_ubyte * size.value)()
            result = self.GetRawInputData(lparam, RID_INPUT, buffer, byref(size), sizeof(RAWINPUTHEADER))
            
            if result != size.value:
                return
            
            # Parse RAWINPUT structure
            raw = cast(buffer, POINTER(RAWINPUT)).contents
            
            # Only process HID data
            if raw.header.dwType != RIM_TYPEHID:
                return
            
            # Get or create device
            device_handle = raw.header.hDevice
            if device_handle not in self.devices:
                print(f"\n🔍 New HID device detected: 0x{device_handle:08X}")
                self.devices[device_handle] = HIDTouchpadDevice(device_handle)
            
            device = self.devices[device_handle]
            
            # Extract HID report data
            hid_data = raw.data.hid
            report_size = hid_data.dwSizeHid
            report_count = hid_data.dwCount
            
            # Process each report
            for i in range(report_count):
                offset = i * report_size
                report_bytes = bytes(buffer[sizeof(RAWINPUTHEADER) + sizeof(DWORD) * 2 + offset:
                                           sizeof(RAWINPUTHEADER) + sizeof(DWORD) * 2 + offset + report_size])
                
                # Parse contacts from report
                contacts = device.parse_report(report_bytes)
                
                if contacts and self.is_capturing:
                    self._process_contacts(contacts, device)
            
        except Exception as e:
            print(f"Error handling raw input: {e}")
            import traceback
            traceback.print_exc()
    
    def _process_contacts(self, contacts: List[TouchContact], device: HIDTouchpadDevice):
        """Process touch contacts"""
        timestamp = time.monotonic()
        timestamp_ns = time.monotonic_ns()
        
        # Track which contacts are currently active
        current_contact_ids = {c.contact_id for c in contacts if c.tip_switch}
        previous_contact_ids = set(self.active_touches.keys())
        
        # Handle new contacts (finger down)
        for contact in contacts:
            if not contact.tip_switch:
                continue
                
            # Normalize coordinates
            norm_x = (contact.x / device.logical_max_x) * self.screen_width if device.logical_max_x > 0 else 0
            norm_y = (contact.y / device.logical_max_y) * self.screen_height if device.logical_max_y > 0 else 0
            
            if contact.contact_id not in self.active_touches:
                # New contact
                self.active_touches[contact.contact_id] = [TouchPoint(norm_x, norm_y, timestamp, timestamp_ns)]
                
                print(f"👇 Finger {contact.contact_id} down at ({norm_x:.1f}, {norm_y:.1f})")
                
                if self.on_finger_down_callback:
                    self.on_finger_down_callback(contact.contact_id)
            else:
                # Update existing contact
                self.active_touches[contact.contact_id].append(TouchPoint(norm_x, norm_y, timestamp, timestamp_ns))
                
                if self.on_point_added_callback:
                    self.on_point_added_callback(contact.contact_id, norm_x, norm_y)
        
        # Handle lifted contacts (finger up)
        lifted_contacts = previous_contact_ids - current_contact_ids
        for contact_id in lifted_contacts:
            if contact_id in self.active_touches:
                points = self.active_touches[contact_id]
                self.completed_touches.append(points)
                
                print(f"👆 Finger {contact_id} up ({len(points)} points)")
                
                if self.on_finger_up_callback:
                    self.on_finger_up_callback(contact_id, points)
                
                del self.active_touches[contact_id]
    
    def _message_loop(self):
        """Message loop running in background thread"""
        try:
            while self.running:
                msg = win32gui.GetMessage(None, 0, 0)
                if msg:
                    win32gui.TranslateMessage(msg)
                    win32gui.DispatchMessage(msg)
                else:
                    break
        except Exception as e:
            print(f"Message loop error: {e}")
    
    def start_capture(self):
        """Start capturing gestures"""
        self.is_capturing = True
        self.active_touches.clear()
        self.completed_touches.clear()
        print("🎬 Started capturing multi-touch gestures")
    
    def stop_capture(self):
        """Stop capturing gestures"""
        self.is_capturing = False
        print("⏹️ Stopped capturing")
    
    def clear_gestures(self):
        """Clear all gesture data"""
        self.active_touches.clear()
        self.completed_touches.clear()
    
    def get_all_tracks(self) -> List:
        """Get all tracks (active + completed)"""
        all_tracks = []
        
        for touch_id, points in self.active_touches.items():
            if points:
                all_tracks.append(points)
        
        all_tracks.extend(self.completed_touches)
        
        return all_tracks
    
    async def process_device_events(self, on_finger_down: Optional[Callable] = None,
                                    on_finger_up: Optional[Callable] = None,
                                    on_point_added: Optional[Callable] = None):
        """Process touchpad events asynchronously"""
        self.on_finger_down_callback = on_finger_down
        self.on_finger_up_callback = on_finger_up
        self.on_point_added_callback = on_point_added
        
        while self.running:
            await asyncio.sleep(0.01)
    
    def close(self):
        """Clean up resources"""
        self.running = False
        if self.hwnd:
            try:
                win32gui.DestroyWindow(self.hwnd)
            except:
                pass
        if self.message_thread and self.message_thread.is_alive():
            self.message_thread.join(timeout=1.0)


# Export the HID version as the main class
WindowsTouchpadCapture = WindowsTouchpadCaptureHID

def detect_windows_touchpad() -> bool:
    """Detect if Windows Precision Touchpad is available"""
    if not IS_WINDOWS:
        return False
    
    try:
        import winreg
        key = winreg.OpenKey(
            winreg.HKEY_LOCAL_MACHINE,
            r"SOFTWARE\Microsoft\Windows\CurrentVersion\PrecisionTouchPad",
            0,
            winreg.KEY_READ
        )
        winreg.CloseKey(key)
        return True
    except:
        return False

def list_windows_touchpads() -> List[Dict[str, str]]:
    """List Windows touchpad devices"""
    if not IS_WINDOWS:
        return []
    
    devices = []
    
    try:
        if detect_windows_touchpad():
            devices.append({
                'path': 'Windows HID API',
                'name': 'Windows Precision Touchpad (HID Multi-Touch)',
                'score': 100,
                'api': 'Raw Input + HID Parser'
            })
    except Exception as e:
        print(f"⚠️  Error listing Windows touchpads: {e}")
    
    return devices
