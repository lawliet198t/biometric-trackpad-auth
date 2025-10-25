using System;
using System.Text.Json;
using System.Collections.Generic;
using System.Windows;
using System.Windows.Input;
using System.Windows.Threading;

namespace TouchpadCapture
{
    public class ContactData
    {
        public int ContactId { get; set; }
        public double X { get; set; }
        public double Y { get; set; }
        public long Timestamp { get; set; }
    }
    
    public class TouchOutput
    {
        public string Type { get; set; }
        public List<ContactData> Contacts { get; set; }
        public string Message { get; set; }
    }
    
    class SimpleProgram
    {
        private static Window window;
        private static Dictionary<int, ContactData> activeContacts = new Dictionary<int, ContactData>();
        
        [STAThread]
        static void Main(string[] args)
        {
            try
            {
                // Create simple WPF window
                var app = new Application();
                window = new Window
                {
                    Title = "Simple Touchpad Capture",
                    Width = 800,
                    Height = 600,
                    WindowState = WindowState.Normal
                };
                
                // Subscribe to touch events
                window.TouchDown += OnTouchDown;
                window.TouchMove += OnTouchMove;
                window.TouchUp += OnTouchUp;
                
                OutputJson(new TouchOutput
                {
                    Type = "ready",
                    Message = "Simple touchpad capture ready - Touch the window!"
                });
                
                // Start WPF message loop
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
        
        static void OnTouchDown(object sender, TouchEventArgs e)
        {
            try
            {
                var touchPoint = e.GetTouchPoint(window);
                int contactId = e.TouchDevice.Id;
                
                var contact = new ContactData
                {
                    ContactId = contactId,
                    X = touchPoint.Position.X,
                    Y = touchPoint.Position.Y,
                    Timestamp = DateTimeOffset.UtcNow.ToUnixTimeMilliseconds()
                };
                
                activeContacts[contactId] = contact;
                OutputContacts();
            }
            catch (Exception ex)
            {
                Console.Error.WriteLine($"TouchDown error: {ex.Message}");
            }
        }
        
        static void OnTouchMove(object sender, TouchEventArgs e)
        {
            try
            {
                var touchPoint = e.GetTouchPoint(window);
                int contactId = e.TouchDevice.Id;
                
                var contact = new ContactData
                {
                    ContactId = contactId,
                    X = touchPoint.Position.X,
                    Y = touchPoint.Position.Y,
                    Timestamp = DateTimeOffset.UtcNow.ToUnixTimeMilliseconds()
                };
                
                activeContacts[contactId] = contact;
                OutputContacts();
            }
            catch (Exception ex)
            {
                Console.Error.WriteLine($"TouchMove error: {ex.Message}");
            }
        }
        
        static void OnTouchUp(object sender, TouchEventArgs e)
        {
            try
            {
                int contactId = e.TouchDevice.Id;
                activeContacts.Remove(contactId);
                OutputContacts();
            }
            catch (Exception ex)
            {
                Console.Error.WriteLine($"TouchUp error: {ex.Message}");
            }
        }
        
        static void OutputContacts()
        {
            var contactList = new List<ContactData>(activeContacts.Values);
            
            OutputJson(new TouchOutput
            {
                Type = "contacts",
                Contacts = contactList
            });
        }
        
        static void OutputJson(TouchOutput output)
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
