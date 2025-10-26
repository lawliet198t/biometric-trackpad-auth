using System;
using System.Collections.Generic;
using System.Linq;
using System.Runtime.InteropServices;
using System.Text.Json;
using System.Windows;
using System.Windows.Interop;
using System.Windows.Media;
using System.Windows.Shapes;
using System.Windows.Controls;

namespace TouchpadCapture
{
    // Data structures for JSON output
    public class ContactData
    {
        public int ContactId { get; set; }
        public int X { get; set; }
        public int Y { get; set; }
        public long Timestamp { get; set; }
    }
    
    public class TouchOutput
    {
        public string Type { get; set; }
        public List<ContactData> Contacts { get; set; }
        public string Message { get; set; }
    }
    
    // Touchpad contact structure
    public struct TouchpadContact
    {
        public int ContactId { get; }
        public int X { get; }
        public int Y { get; }
        
        public TouchpadContact(int contactId, int x, int y)
        {
            ContactId = contactId;
            X = x;
            Y = y;
        }
        
        public override string ToString() => $"Contact ID:{ContactId} Point:{X},{Y}";
    }
    
    internal class TouchpadContactCreator
    {
        public int? ContactId { get; set; }
        public int? X { get; set; }
        public int? Y { get; set; }
        public bool? TipSwitch { get; set; }
        
        public bool TryCreate(out TouchpadContact contact)
        {
            // Only create contact if we have all data AND TipSwitch is true (or not reported)
            if (ContactId.HasValue && X.HasValue && Y.HasValue)
            {
                // If TipSwitch is reported and false, don't create contact
                if (TipSwitch.HasValue && !TipSwitch.Value)
                {
                    contact = default;
                    return false;
                }
                
                contact = new TouchpadContact(ContactId.Value, X.Value, Y.Value);
                return true;
            }
            contact = default;
            return false;
        }
        
        public void Clear()
        {
            ContactId = null;
            X = null;
            Y = null;
            TipSwitch = null;
        }
    }
    
    // Raw Input API helper
    internal static class TouchpadHelper
    {
        #region Win32 API Declarations
        
        [DllImport("User32", SetLastError = true)]
        private static extern uint GetRawInputDeviceList(
            [Out] RAWINPUTDEVICELIST[] pRawInputDeviceList,
            ref uint puiNumDevices,
            uint cbSize);
        
        [StructLayout(LayoutKind.Sequential)]
        private struct RAWINPUTDEVICELIST
        {
            public IntPtr hDevice;
            public uint dwType;
        }
        
        private const uint RIM_TYPEHID = 2;
        
        [DllImport("User32.dll", SetLastError = true)]
        [return: MarshalAs(UnmanagedType.Bool)]
        private static extern bool RegisterRawInputDevices(
            RAWINPUTDEVICE[] pRawInputDevices,
            uint uiNumDevices,
            uint cbSize);
        
        [StructLayout(LayoutKind.Sequential)]
        private struct RAWINPUTDEVICE
        {
            public ushort usUsagePage;
            public ushort usUsage;
            public uint dwFlags;
            public IntPtr hwndTarget;
        }
        
        [DllImport("User32.dll", SetLastError = true)]
        private static extern uint GetRawInputData(
            IntPtr hRawInput,
            uint uiCommand,
            IntPtr pData,
            ref uint pcbSize,
            uint cbSizeHeader);
        
        private const uint RID_INPUT = 0x10000003;
        
        [StructLayout(LayoutKind.Sequential)]
        private struct RAWINPUT
        {
            public RAWINPUTHEADER Header;
            public RAWHID Hid;
        }
        
        [StructLayout(LayoutKind.Sequential)]
        private struct RAWINPUTHEADER
        {
            public uint dwType;
            public uint dwSize;
            public IntPtr hDevice;
            public IntPtr wParam;
        }
        
        [StructLayout(LayoutKind.Sequential)]
        private struct RAWHID
        {
            public uint dwSizeHid;
            public uint dwCount;
            public IntPtr bRawData;
        }
        
        [DllImport("User32.dll", SetLastError = true)]
        private static extern uint GetRawInputDeviceInfo(
            IntPtr hDevice,
            uint uiCommand,
            IntPtr pData,
            ref uint pcbSize);
        
        [DllImport("User32.dll", SetLastError = true)]
        private static extern uint GetRawInputDeviceInfo(
            IntPtr hDevice,
            uint uiCommand,
            ref RID_DEVICE_INFO pData,
            ref uint pcbSize);
        
        private const uint RIDI_PREPARSEDDATA = 0x20000005;
        private const uint RIDI_DEVICEINFO = 0x2000000b;
        
        [StructLayout(LayoutKind.Sequential)]
        private struct RID_DEVICE_INFO
        {
            public uint cbSize;
            public uint dwType;
            public RID_DEVICE_INFO_HID hid;
        }
        
        [StructLayout(LayoutKind.Sequential)]
        private struct RID_DEVICE_INFO_HID
        {
            public uint dwVendorId;
            public uint dwProductId;
            public uint dwVersionNumber;
            public ushort usUsagePage;
            public ushort usUsage;
        }
        
        [DllImport("Hid.dll", SetLastError = true)]
        private static extern uint HidP_GetCaps(
            IntPtr PreparsedData,
            out HIDP_CAPS Capabilities);
        
        private const uint HIDP_STATUS_SUCCESS = 0x00110000;
        
        [StructLayout(LayoutKind.Sequential)]
        private struct HIDP_CAPS
        {
            public ushort Usage;
            public ushort UsagePage;
            public ushort InputReportByteLength;
            public ushort OutputReportByteLength;
            public ushort FeatureReportByteLength;
            
            [MarshalAs(UnmanagedType.ByValArray, SizeConst = 17)]
            public ushort[] Reserved;
            
            public ushort NumberLinkCollectionNodes;
            public ushort NumberInputButtonCaps;
            public ushort NumberInputValueCaps;
            public ushort NumberInputDataIndices;
            public ushort NumberOutputButtonCaps;
            public ushort NumberOutputValueCaps;
            public ushort NumberOutputDataIndices;
            public ushort NumberFeatureButtonCaps;
            public ushort NumberFeatureValueCaps;
            public ushort NumberFeatureDataIndices;
        }
        
        [DllImport("Hid.dll", CharSet = CharSet.Auto)]
        private static extern uint HidP_GetValueCaps(
            HIDP_REPORT_TYPE ReportType,
            [Out] HIDP_VALUE_CAPS[] ValueCaps,
            ref ushort ValueCapsLength,
            IntPtr PreparsedData);
        
        private enum HIDP_REPORT_TYPE
        {
            HidP_Input,
            HidP_Output,
            HidP_Feature
        }
        
        [StructLayout(LayoutKind.Sequential)]
        private struct HIDP_VALUE_CAPS
        {
            public ushort UsagePage;
            public byte ReportID;
            
            [MarshalAs(UnmanagedType.U1)]
            public bool IsAlias;
            
            public ushort BitField;
            public ushort LinkCollection;
            public ushort LinkUsage;
            public ushort LinkUsagePage;
            
            [MarshalAs(UnmanagedType.U1)]
            public bool IsRange;
            [MarshalAs(UnmanagedType.U1)]
            public bool IsStringRange;
            [MarshalAs(UnmanagedType.U1)]
            public bool IsDesignatorRange;
            [MarshalAs(UnmanagedType.U1)]
            public bool IsAbsolute;
            [MarshalAs(UnmanagedType.U1)]
            public bool HasNull;
            
            public byte Reserved;
            public ushort BitSize;
            public ushort ReportCount;
            
            [MarshalAs(UnmanagedType.ByValArray, SizeConst = 5)]
            public ushort[] Reserved2;
            
            public uint UnitsExp;
            public uint Units;
            public int LogicalMin;
            public int LogicalMax;
            public int PhysicalMin;
            public int PhysicalMax;
            
            public ushort UsageMin;
            public ushort UsageMax;
            public ushort StringMin;
            public ushort StringMax;
            public ushort DesignatorMin;
            public ushort DesignatorMax;
            public ushort DataIndexMin;
            public ushort DataIndexMax;
            
            public ushort Usage => UsageMin;
            public ushort StringIndex => StringMin;
            public ushort DesignatorIndex => DesignatorMin;
            public ushort DataIndex => DataIndexMin;
        }
        
        [DllImport("Hid.dll", CharSet = CharSet.Auto)]
        private static extern uint HidP_GetUsageValue(
            HIDP_REPORT_TYPE ReportType,
            ushort UsagePage,
            ushort LinkCollection,
            ushort Usage,
            out uint UsageValue,
            IntPtr PreparsedData,
            IntPtr Report,
            uint ReportLength);
        
        [DllImport("Hid.dll", CharSet = CharSet.Auto)]
        private static extern uint HidP_GetUsages(
            HIDP_REPORT_TYPE ReportType,
            ushort UsagePage,
            ushort LinkCollection,
            [Out] ushort[] UsageList,
            ref uint UsageLength,
            IntPtr PreparsedData,
            IntPtr Report,
            uint ReportLength);
        
        #endregion
        
        public static bool Exists()
        {
            uint deviceListCount = 0;
            uint rawInputDeviceListSize = (uint)Marshal.SizeOf<RAWINPUTDEVICELIST>();
            
            if (GetRawInputDeviceList(null, ref deviceListCount, rawInputDeviceListSize) != 0)
                return false;
            
            var devices = new RAWINPUTDEVICELIST[deviceListCount];
            
            if (GetRawInputDeviceList(devices, ref deviceListCount, rawInputDeviceListSize) != deviceListCount)
                return false;
            
            foreach (var device in devices.Where(x => x.dwType == RIM_TYPEHID))
            {
                uint deviceInfoSize = 0;
                
                if (GetRawInputDeviceInfo(device.hDevice, RIDI_DEVICEINFO, IntPtr.Zero, ref deviceInfoSize) != 0)
                    continue;
                
                var deviceInfo = new RID_DEVICE_INFO { cbSize = deviceInfoSize };
                
                if (GetRawInputDeviceInfo(device.hDevice, RIDI_DEVICEINFO, ref deviceInfo, ref deviceInfoSize) == unchecked((uint)-1))
                    continue;
                
                // Check for Precision Touchpad (UsagePage=0x000D, Usage=0x0005)
                if ((deviceInfo.hid.usUsagePage == 0x000D) && (deviceInfo.hid.usUsage == 0x0005))
                    return true;
            }
            return false;
        }
        
        private const uint RIDEV_INPUTSINK = 0x00000100;
        
        public static bool RegisterInput(IntPtr windowHandle)
        {
            // Precision Touchpad (PTP) HID device
            // RIDEV_INPUTSINK allows receiving input even when not in foreground
            var device = new RAWINPUTDEVICE
            {
                usUsagePage = 0x000D,
                usUsage = 0x0005,
                dwFlags = RIDEV_INPUTSINK,  // Receive input even in background
                hwndTarget = windowHandle
            };
            
            return RegisterRawInputDevices(new[] { device }, 1, (uint)Marshal.SizeOf<RAWINPUTDEVICE>());
        }
        
        public const int WM_INPUT = 0x00FF;
        
        public static TouchpadContact[] ParseInput(IntPtr lParam)
        {
            uint rawInputSize = 0;
            uint rawInputHeaderSize = (uint)Marshal.SizeOf<RAWINPUTHEADER>();
            
            if (GetRawInputData(lParam, RID_INPUT, IntPtr.Zero, ref rawInputSize, rawInputHeaderSize) != 0)
                return null;
            
            RAWINPUT rawInput;
            byte[] rawHidRawData;
            
            IntPtr rawInputPointer = IntPtr.Zero;
            try
            {
                rawInputPointer = Marshal.AllocHGlobal((int)rawInputSize);
                
                if (GetRawInputData(lParam, RID_INPUT, rawInputPointer, ref rawInputSize, rawInputHeaderSize) != rawInputSize)
                    return null;
                
                rawInput = Marshal.PtrToStructure<RAWINPUT>(rawInputPointer);
                
                var rawInputData = new byte[rawInputSize];
                Marshal.Copy(rawInputPointer, rawInputData, 0, rawInputData.Length);
                
                rawHidRawData = new byte[rawInput.Hid.dwSizeHid * rawInput.Hid.dwCount];
                int rawInputOffset = (int)rawInputSize - rawHidRawData.Length;
                Buffer.BlockCopy(rawInputData, rawInputOffset, rawHidRawData, 0, rawHidRawData.Length);
            }
            finally
            {
                Marshal.FreeHGlobal(rawInputPointer);
            }
            
            IntPtr rawHidRawDataPointer = Marshal.AllocHGlobal(rawHidRawData.Length);
            Marshal.Copy(rawHidRawData, 0, rawHidRawDataPointer, rawHidRawData.Length);
            
            IntPtr preparsedDataPointer = IntPtr.Zero;
            try
            {
                uint preparsedDataSize = 0;
                
                if (GetRawInputDeviceInfo(rawInput.Header.hDevice, RIDI_PREPARSEDDATA, IntPtr.Zero, ref preparsedDataSize) != 0)
                    return null;
                
                preparsedDataPointer = Marshal.AllocHGlobal((int)preparsedDataSize);
                
                if (GetRawInputDeviceInfo(rawInput.Header.hDevice, RIDI_PREPARSEDDATA, preparsedDataPointer, ref preparsedDataSize) != preparsedDataSize)
                    return null;
                
                if (HidP_GetCaps(preparsedDataPointer, out HIDP_CAPS caps) != HIDP_STATUS_SUCCESS)
                    return null;
                
                ushort valueCapsLength = caps.NumberInputValueCaps;
                var valueCaps = new HIDP_VALUE_CAPS[valueCapsLength];
                
                if (HidP_GetValueCaps(HIDP_REPORT_TYPE.HidP_Input, valueCaps, ref valueCapsLength, preparsedDataPointer) != HIDP_STATUS_SUCCESS)
                    return null;
                
                uint contactCount = 0;
                TouchpadContactCreator creator = new();
                List<TouchpadContact> contacts = new();
                
                // Debug: Track all usage values we see
                var debugInfo = new System.Text.StringBuilder();
                
                foreach (var valueCap in valueCaps.OrderBy(x => x.LinkCollection))
                {
                    if (HidP_GetUsageValue(
                        HIDP_REPORT_TYPE.HidP_Input,
                        valueCap.UsagePage,
                        valueCap.LinkCollection,
                        valueCap.Usage,
                        out uint value,
                        preparsedDataPointer,
                        rawHidRawDataPointer,
                        (uint)rawHidRawData.Length) != HIDP_STATUS_SUCCESS)
                    {
                        continue;
                    }
                    
                    switch (valueCap.LinkCollection)
                    {
                        case 0:
                            if (valueCap.UsagePage == 0x0D && valueCap.Usage == 0x54) // Contact Count
                                contactCount = value;
                            break;
                        
                        default:
                            switch (valueCap.UsagePage, valueCap.Usage)
                            {
                                case (0x0D, 0x51): // Contact ID
                                    creator.ContactId = (int)value;
                                    break;
                                
                                case (0x01, 0x30): // X
                                    creator.X = (int)value;
                                    break;
                                
                                case (0x01, 0x31): // Y
                                    creator.Y = (int)value;
                                    break;
                                
                                case (0x0D, 0x42): // Tip Switch (1 = touching, 0 = not touching)
                                    creator.TipSwitch = value > 0;
                                    break;
                            }
                            break;
                    }
                    
                    // Only create contact if TipSwitch is true (finger is actually touching)
                    if (creator.TryCreate(out TouchpadContact contact))
                    {
                        contacts.Add(contact);
                        if (contacts.Count >= contactCount)
                            break;
                        
                        creator.Clear();
                    }
                }
                
                return contacts.ToArray();
            }
            finally
            {
                Marshal.FreeHGlobal(rawHidRawDataPointer);
                Marshal.FreeHGlobal(preparsedDataPointer);
            }
        }
    }
    
    // Main program
    class RawInputProgram
    {
        private static Window window;
        
        // Visualization state
        private static Canvas visualizationCanvas;
        private static Dictionary<int, List<Point>> contactTrails = new Dictionary<int, List<Point>>();
        private static Dictionary<int, Ellipse> contactCircles = new Dictionary<int, Ellipse>();
        private static TextBlock statusText;
        private static int maxTrailPoints = 100;
        
        // Colors for different contacts
        private static Brush[] contactColors = new Brush[]
        {
            new SolidColorBrush(Color.FromRgb(255, 100, 100)),  // Red
            new SolidColorBrush(Color.FromRgb(100, 255, 100)),  // Green
            new SolidColorBrush(Color.FromRgb(100, 100, 255)),  // Blue
            new SolidColorBrush(Color.FromRgb(255, 255, 100)),  // Yellow
            new SolidColorBrush(Color.FromRgb(255, 100, 255)),  // Magenta
        };
        
        [STAThread]
        static void Main(string[] args)
        {
            try
            {
                // Check if touchpad exists
                if (!TouchpadHelper.Exists())
                {
                    MessageBox.Show("No Precision Touchpad detected!", "Error", MessageBoxButton.OK, MessageBoxImage.Error);
                    return;
                }
                
                // Create WPF application
                var app = new Application();
                
                // Create main window with visualization
                window = new Window
                {
                    Title = "Touchpad Capture & Visualization",
                    Width = 1200,
                    Height = 800,
                    WindowStartupLocation = WindowStartupLocation.CenterScreen,
                    Background = new SolidColorBrush(Color.FromRgb(20, 20, 30)),
                    ResizeMode = ResizeMode.CanResize
                };
                
                // Create main grid layout
                var mainGrid = new Grid();
                mainGrid.ColumnDefinitions.Add(new ColumnDefinition { Width = new GridLength(1, GridUnitType.Star) });
                mainGrid.ColumnDefinitions.Add(new ColumnDefinition { Width = new GridLength(300) });
                
                // Left side: Visualization canvas
                visualizationCanvas = new Canvas
                {
                    Background = new SolidColorBrush(Color.FromRgb(30, 30, 40)),
                    Margin = new Thickness(10)
                };
                Grid.SetColumn(visualizationCanvas, 0);
                mainGrid.Children.Add(visualizationCanvas);
                
                // Right side: Info panel
                var infoPanel = new StackPanel
                {
                    Background = new SolidColorBrush(Color.FromRgb(25, 25, 35)),
                    Margin = new Thickness(10)
                };
                Grid.SetColumn(infoPanel, 1);
                mainGrid.Children.Add(infoPanel);
                
                // Title
                var titleText = new TextBlock
                {
                    Text = "Touchpad Capture",
                    FontSize = 32,
                    FontWeight = FontWeights.Bold,
                    Foreground = new SolidColorBrush(Color.FromRgb(0, 255, 100)),
                    Margin = new Thickness(20, 20, 20, 10),
                    TextAlignment = TextAlignment.Center
                };
                infoPanel.Children.Add(titleText);
                
                // Status
                statusText = new TextBlock
                {
                    Text = "Waiting for touch...",
                    FontSize = 20,
                    Foreground = Brushes.White,
                    Margin = new Thickness(20, 10, 20, 20),
                    TextAlignment = TextAlignment.Center,
                    TextWrapping = TextWrapping.Wrap
                };
                infoPanel.Children.Add(statusText);
                
                // Separator
                infoPanel.Children.Add(new Separator { Margin = new Thickness(10, 10, 10, 10) });
                
                // Instructions
                var instructionsText = new TextBlock
                {
                    Text = "Touch your touchpad to see real-time visualization!\n\n" +
                           "• Each finger gets a unique color\n" +
                           "• Trails show movement history\n" +
                           "• Data is also output as JSON",
                    FontSize = 14,
                    Foreground = new SolidColorBrush(Color.FromRgb(150, 150, 150)),
                    Margin = new Thickness(20),
                    TextWrapping = TextWrapping.Wrap
                };
                infoPanel.Children.Add(instructionsText);
                
                window.Content = mainGrid;
                window.SourceInitialized += OnSourceInitialized;
                
                // Start visualization update timer
                var vizTimer = new System.Windows.Threading.DispatcherTimer();
                vizTimer.Interval = TimeSpan.FromMilliseconds(16);  // ~60 FPS
                vizTimer.Tick += UpdateVisualization;
                vizTimer.Start();
                
                OutputJson(new TouchOutput
                {
                    Type = "ready",
                    Message = "Touchpad capture ready with visualization!"
                });
                
                app.Run(window);
            }
            catch (Exception ex)
            {
                MessageBox.Show($"Error: {ex.Message}", "Error", MessageBoxButton.OK, MessageBoxImage.Error);
                Environment.Exit(1);
            }
        }
        
        private static void OnSourceInitialized(object sender, EventArgs e)
        {
            var source = PresentationSource.FromVisual(window) as HwndSource;
            source?.AddHook(WndProc);
            
            if (source != null)
            {
                TouchpadHelper.RegisterInput(source.Handle);
            }
        }
        
        private static Point MapToCanvas(int x, int y)
        {
            // Normalize coordinates
            double normX = touchpadMaxX > touchpadMinX ? 
                (double)(x - touchpadMinX) / (touchpadMaxX - touchpadMinX) : 0.5;
            double normY = touchpadMaxY > touchpadMinY ? 
                (double)(y - touchpadMinY) / (touchpadMaxY - touchpadMinY) : 0.5;
            
            // Map to canvas with margins
            double canvasX = 20 + normX * (visualizationCanvas.ActualWidth - 40);
            double canvasY = 20 + normY * (visualizationCanvas.ActualHeight - 40);
            
            return new Point(canvasX, canvasY);
        }
        
        private static void UpdateVisualization(object sender, EventArgs e)
        {
            if (visualizationCanvas == null || currentContacts == null)
                return;
            
            // Update status
            if (currentContacts.Length > 0)
            {
                statusText.Text = $"{currentContacts.Length} finger(s) detected";
                statusText.Foreground = new SolidColorBrush(Color.FromRgb(0, 255, 100));
            }
            else
            {
                statusText.Text = "Waiting for touch...";
                statusText.Foreground = Brushes.White;
            }
            
            // Clear old circles
            foreach (var circle in contactCircles.Values)
            {
                visualizationCanvas.Children.Remove(circle);
            }
            contactCircles.Clear();
            
            // Draw current contacts
            foreach (var contact in currentContacts)
            {
                var pos = MapToCanvas(contact.X, contact.Y);
                var color = contactColors[contact.ContactId % contactColors.Length];
                
                // Add to trail
                if (!contactTrails.ContainsKey(contact.ContactId))
                {
                    contactTrails[contact.ContactId] = new List<Point>();
                }
                contactTrails[contact.ContactId].Add(pos);
                
                // Limit trail length
                if (contactTrails[contact.ContactId].Count > maxTrailPoints)
                {
                    contactTrails[contact.ContactId].RemoveAt(0);
                }
                
                // Draw trail
                var trail = contactTrails[contact.ContactId];
                for (int i = 1; i < trail.Count; i++)
                {
                    var line = new Line
                    {
                        X1 = trail[i - 1].X,
                        Y1 = trail[i - 1].Y,
                        X2 = trail[i].X,
                        Y2 = trail[i].Y,
                        Stroke = color,
                        StrokeThickness = 3 + (i / (double)trail.Count) * 5,
                        Opacity = 0.3 + (i / (double)trail.Count) * 0.7
                    };
                    visualizationCanvas.Children.Add(line);
                }
                
                // Draw current position circle
                var circle = new Ellipse
                {
                    Width = 40,
                    Height = 40,
                    Fill = color,
                    Stroke = Brushes.White,
                    StrokeThickness = 3
                };
                Canvas.SetLeft(circle, pos.X - 20);
                Canvas.SetTop(circle, pos.Y - 20);
                visualizationCanvas.Children.Add(circle);
                contactCircles[contact.ContactId] = circle;
                
                // Draw contact ID
                var idText = new TextBlock
                {
                    Text = contact.ContactId.ToString(),
                    FontSize = 18,
                    FontWeight = FontWeights.Bold,
                    Foreground = Brushes.White,
                    TextAlignment = TextAlignment.Center
                };
                Canvas.SetLeft(idText, pos.X - 10);
                Canvas.SetTop(idText, pos.Y - 10);
                visualizationCanvas.Children.Add(idText);
            }
            
            // Remove old trails for contacts no longer active
            var activeIds = new HashSet<int>(currentContacts.Select(c => c.ContactId));
            var toRemove = contactTrails.Keys.Where(id => !activeIds.Contains(id)).ToList();
            foreach (var id in toRemove)
            {
                contactTrails.Remove(id);
            }
        }
        
        // Removed heartbeat - causes gaps in continuous gestures
        // Python will track contact IDs and detect lifts
        
        private static DateTime lastJsonOutput = DateTime.MinValue;
        private static readonly TimeSpan jsonOutputInterval = TimeSpan.FromMilliseconds(16); // ~60 FPS
        private static HashSet<int> lastSeenContactIds = new HashSet<int>();
        private static TouchpadContact[] currentContacts = new TouchpadContact[0];
        
        // Touchpad bounds (auto-detected)
        private static int touchpadMinX = int.MaxValue;
        private static int touchpadMaxX = int.MinValue;
        private static int touchpadMinY = int.MaxValue;
        private static int touchpadMaxY = int.MinValue;
        
        private static IntPtr WndProc(IntPtr hwnd, int msg, IntPtr wParam, IntPtr lParam, ref bool handled)
        {
            if (msg == TouchpadHelper.WM_INPUT)
            {
                var contacts = TouchpadHelper.ParseInput(lParam);
                
                if (contacts != null)
                {
                    var now = DateTime.UtcNow;
                    var contactList = new List<ContactData>();
                    long timestamp = DateTimeOffset.UtcNow.ToUnixTimeMilliseconds();
                    
                    // Store contacts for visualization
                    currentContacts = contacts;
                    
                    // Update touchpad bounds
                    foreach (var contact in contacts)
                    {
                        touchpadMinX = Math.Min(touchpadMinX, contact.X);
                        touchpadMaxX = Math.Max(touchpadMaxX, contact.X);
                        touchpadMinY = Math.Min(touchpadMinY, contact.Y);
                        touchpadMaxY = Math.Max(touchpadMaxY, contact.Y);
                        
                        contactList.Add(new ContactData
                        {
                            ContactId = contact.ContactId,
                            X = contact.X,
                            Y = contact.Y,
                            Timestamp = timestamp
                        });
                    }
                    
                    // Track current contact IDs
                    var currentContactIds = new HashSet<int>(contactList.Select(c => c.ContactId));
                    
                    // Output JSON (throttled to 60 FPS)
                    if (now - lastJsonOutput > jsonOutputInterval)
                    {
                        // Always output - even if empty (for lift detection)
                        OutputJson(new TouchOutput
                        {
                            Type = "contacts",
                            Contacts = contactList
                        });
                        lastJsonOutput = now;
                        lastSeenContactIds = currentContactIds;
                    }
                }
            }
            return IntPtr.Zero;
        }
        
        private static readonly System.Text.Json.JsonSerializerOptions jsonOptions = new()
        {
            WriteIndented = false,  // Compact JSON for speed
            DefaultIgnoreCondition = System.Text.Json.Serialization.JsonIgnoreCondition.Never
        };
        
        private static void OutputJson(TouchOutput output)
        {
            try
            {
                // Ultra-fast: Write directly to stdout buffer
                var json = JsonSerializer.Serialize(output, jsonOptions);
                Console.Out.WriteLine(json);
                Console.Out.Flush();  // Immediate flush for low latency
            }
            catch (Exception ex)
            {
                Console.Error.WriteLine($"JSON error: {ex.Message}");
            }
        }
    }
}
