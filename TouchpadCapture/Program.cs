using System;
using System.Text.Json;
using System.Collections.Generic;
using System.Windows;
using System.Linq;
using RawInput.Touchpad;

namespace TouchpadCapture
{
    // JSON-based touchpad capture for Python subprocess communication
    
    public class TouchPointData
    {
        public int ContactId { get; set; }
        public double X { get; set; }
        public double Y { get; set; }
        public bool TipSwitch { get; set; }
        public long Timestamp { get; set; }
    }
    
    public class TouchEvent
    {
        public string Type { get; set; }  // "contacts", "ready", or "error"
        public List<TouchPointData> Contacts { get; set; }
        public string Message { get; set; }
    }
    
    class Program
    {
        private static MainWindow window;
        
        [STAThread]
        static void Main(string[] args)
        {
            try
            {
                // Create WPF application
                var app = new Application();
                
                // Create main window (this registers for Raw Input)
                window = new MainWindow();
                
                // Hide the window (we don't need UI)
                window.Visibility = Visibility.Hidden;
                window.ShowInTaskbar = false;
                
                // Hook into touchpad events
                // The MainWindow class should have some way to get contacts
                // We'll need to inspect the actual implementation
                
                // Output ready message
                OutputJson(new TouchEvent
                {
                    Type = "ready",
                    Message = "Touchpad capture ready"
                });
                
                // Start the WPF message loop
                app.Run(window);
            }
            catch (Exception ex)
            {
                OutputJson(new TouchEvent
                {
                    Type = "error",
                    Message = $"Error: {ex.Message}\nStack: {ex.StackTrace}"
                });
                Environment.Exit(1);
            }
        }
        
        static void OutputJson(TouchEvent evt)
        {
            try
            {
                var json = JsonSerializer.Serialize(evt);
                Console.WriteLine(json);
                Console.Out.Flush();
            }
            catch (Exception ex)
            {
                Console.Error.WriteLine($"JSON serialization error: {ex.Message}");
            }
        }
        
        // This will be called when contacts are received
        // You'll need to wire this up to MainWindow's event/callback
        static void OnContactsReceived(IEnumerable<TouchpadContact> contacts)
        {
            var touchPoints = contacts.Select(c => new TouchPointData
            {
                ContactId = c.ContactId,
                X = c.X,
                Y = c.Y,
                TipSwitch = c.TipSwitch,
                Timestamp = DateTimeOffset.UtcNow.ToUnixTimeMilliseconds()
            }).ToList();
            
            OutputJson(new TouchEvent
            {
                Type = "contacts",
                Contacts = touchPoints
            });
        }
    }
}
