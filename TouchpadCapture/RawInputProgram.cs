using System;
using System.Collections.Generic;
using System.Linq;
using System.Runtime.InteropServices;
using System.Text.Json;
using System.Windows;
using System.Windows.Interop;

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
        
        public bool TryCreate(out TouchpadContact contact)
        {
            if (ContactId.HasValue && X.HasValue && Y.HasValue)
            {
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
        
        public static bool RegisterInput(IntPtr windowHandle)
        {
            // Precision Touchpad (PTP) HID device
            var device = new RAWINPUTDEVICE
            {
                usUsagePage = 0x000D,
                usUsage = 0x0005,
                dwFlags = 0,
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
                            }
                            break;
                    }
                    
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
        
        [STAThread]
        static void Main(string[] args)
        {
            try
            {
                // Check if touchpad exists
                if (!TouchpadHelper.Exists())
                {
                    OutputJson(new TouchOutput
                    {
                        Type = "error",
                        Message = "No Precision Touchpad detected"
                    });
                    return;
                }
                
                // Create WPF window with UI
                var app = new Application();
                window = new Window
                {
                    Title = "Raw Input Touchpad Capture - Touch your touchpad!",
                    Width = 600,
                    Height = 400,
                    WindowState = WindowState.Normal,
                    WindowStartupLocation = System.Windows.WindowStartupLocation.CenterScreen,
                    Background = System.Windows.Media.Brushes.Black
                };
                
                // Add text display
                var textBlock = new System.Windows.Controls.TextBlock
                {
                    Text = "Waiting for touch...",
                    Foreground = System.Windows.Media.Brushes.Lime,
                    FontSize = 16,
                    FontFamily = new System.Windows.Media.FontFamily("Consolas"),
                    Margin = new Thickness(20),
                    TextWrapping = System.Windows.TextWrapping.Wrap
                };
                
                window.Content = textBlock;
                window.SourceInitialized += OnSourceInitialized;
                window.Tag = textBlock;  // Store reference
                
                OutputJson(new TouchOutput
                {
                    Type = "ready",
                    Message = "Raw Input touchpad capture ready - Touch your touchpad!"
                });
                
                app.Run(window);
            }
            catch (Exception ex)
            {
                OutputJson(new TouchOutput
                {
                    Type = "error",
                    Message = $"Error: {ex.Message}"
                });
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
        
        private static IntPtr WndProc(IntPtr hwnd, int msg, IntPtr wParam, IntPtr lParam, ref bool handled)
        {
            if (msg == TouchpadHelper.WM_INPUT)
            {
                var contacts = TouchpadHelper.ParseInput(lParam);
                
                if (contacts != null)
                {
                    var contactList = new List<ContactData>();
                    long timestamp = DateTimeOffset.UtcNow.ToUnixTimeMilliseconds();
                    
                    // Update UI
                    if (window.Tag is System.Windows.Controls.TextBlock textBlock)
                    {
                        if (contacts.Length > 0)
                        {
                            var text = $"✓ {contacts.Length} finger(s) detected:\n\n";
                            foreach (var contact in contacts)
                            {
                                text += $"Finger {contact.ContactId}:\n";
                                text += $"  X = {contact.X}\n";
                                text += $"  Y = {contact.Y}\n\n";
                                
                                contactList.Add(new ContactData
                                {
                                    ContactId = contact.ContactId,
                                    X = contact.X,
                                    Y = contact.Y,
                                    Timestamp = timestamp
                                });
                            }
                            textBlock.Text = text;
                        }
                        else
                        {
                            textBlock.Text = "Waiting for touch...";
                        }
                    }
                    
                    // Output JSON (only if there are contacts)
                    if (contactList.Count > 0)
                    {
                        OutputJson(new TouchOutput
                        {
                            Type = "contacts",
                            Contacts = contactList
                        });
                    }
                }
            }
            return IntPtr.Zero;
        }
        
        private static void OutputJson(TouchOutput output)
        {
            try
            {
                var json = JsonSerializer.Serialize(output);
                Console.WriteLine(json);
                Console.Out.Flush();
            }
            catch (Exception ex)
            {
                Console.Error.WriteLine($"JSON error: {ex.Message}");
            }
        }
    }
}
