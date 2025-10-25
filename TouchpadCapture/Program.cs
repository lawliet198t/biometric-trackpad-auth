using System;
using System.Text.Json;
using System.Collections.Generic;
using System.Windows;
using System.Linq;
using System.Reflection;
using System.Windows.Threading;

namespace TouchpadCapture
{
    public class TouchPointData
    {
        public int ContactId { get; set; }
        public double X { get; set; }
        public double Y { get; set; }
        public long Timestamp { get; set; }
    }
    
    public class TouchEvent
    {
        public string Type { get; set; }
        public List<TouchPointData> Contacts { get; set; }
        public string Message { get; set; }
    }
    
    class Program
    {
        private static Window window;
        private static DispatcherTimer timer;
        private static object lastContactsData;
        
        [STAThread]
        static void Main(string[] args)
        {
            try
            {
                // Load the RawInput.Touchpad assembly
                var assembly = Assembly.LoadFrom("RawInput.Touchpad.dll");
                
                // Find the MainWindow type
                var mainWindowType = assembly.GetType("RawInput.Touchpad.MainWindow");
                if (mainWindowType == null)
                {
                    OutputJson(new TouchEvent
                    {
                        Type = "error",
                        Message = "Could not find MainWindow type"
                    });
                    return;
                }
                
                // Create WPF application
                var app = new Application();
                
                // Create MainWindow instance
                window = Activator.CreateInstance(mainWindowType) as Window;
                if (window == null)
                {
                    OutputJson(new TouchEvent
                    {
                        Type = "error",
                        Message = "Could not create MainWindow instance"
                    });
                    return;
                }
                
                // Keep window visible but minimized so we can see it's working
                window.WindowState = WindowState.Minimized;
                window.Title = "TouchpadCapture (Minimized - Check Console)";
                
                OutputJson(new TouchEvent
                {
                    Type = "ready",
                    Message = "Touchpad capture ready - Touch your touchpad!"
                });
                
                // Poll for contact data using reflection
                timer = new DispatcherTimer();
                timer.Interval = TimeSpan.FromMilliseconds(16); // ~60 FPS
                timer.Tick += (s, e) => PollContacts(mainWindowType);
                timer.Start();
                
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
        
        static void PollContacts(Type mainWindowType)
        {
            try
            {
                // Try to find a property or field that contains contact data
                // Common names: Contacts, TouchContacts, CurrentContacts, etc.
                
                var properties = mainWindowType.GetProperties(BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Instance);
                var fields = mainWindowType.GetFields(BindingFlags.Public | BindingFlags.NonPublic | BindingFlags.Instance);
                
                // Look for anything that might contain contact data
                foreach (var prop in properties)
                {
                    if (prop.Name.Contains("Contact") || prop.Name.Contains("Touch"))
                    {
                        try
                        {
                            var value = prop.GetValue(window);
                            if (value != null)
                            {
                                ProcessContactData(value);
                                return;
                            }
                        }
                        catch { }
                    }
                }
                
                foreach (var field in fields)
                {
                    if (field.Name.Contains("Contact") || field.Name.Contains("Touch") || field.Name.Contains("contact") || field.Name.Contains("touch"))
                    {
                        try
                        {
                            var value = field.GetValue(window);
                            if (value != null)
                            {
                                ProcessContactData(value);
                                return;
                            }
                        }
                        catch { }
                    }
                }
            }
            catch (Exception ex)
            {
                // Silently ignore polling errors
            }
        }
        
        static void ProcessContactData(object contactData)
        {
            try
            {
                // Check if it's a collection
                if (contactData is System.Collections.IEnumerable enumerable)
                {
                    var contacts = new List<TouchPointData>();
                    
                    foreach (var item in enumerable)
                    {
                        if (item == null) continue;
                        
                        var itemType = item.GetType();
                        
                        // Try to extract ContactId, X, Y
                        int? contactId = null;
                        double? x = null;
                        double? y = null;
                        
                        foreach (var prop in itemType.GetProperties())
                        {
                            try
                            {
                                var value = prop.GetValue(item);
                                
                                if (prop.Name.Contains("ContactId") || prop.Name.Contains("Id"))
                                    contactId = Convert.ToInt32(value);
                                else if (prop.Name == "X")
                                    x = Convert.ToDouble(value);
                                else if (prop.Name == "Y")
                                    y = Convert.ToDouble(value);
                            }
                            catch { }
                        }
                        
                        if (contactId.HasValue && x.HasValue && y.HasValue)
                        {
                            contacts.Add(new TouchPointData
                            {
                                ContactId = contactId.Value,
                                X = x.Value,
                                Y = y.Value,
                                Timestamp = DateTimeOffset.UtcNow.ToUnixTimeMilliseconds()
                            });
                        }
                    }
                    
                    if (contacts.Count > 0)
                    {
                        OutputJson(new TouchEvent
                        {
                            Type = "contacts",
                            Contacts = contacts
                        });
                    }
                }
            }
            catch { }
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
                Console.Error.WriteLine($"JSON error: {ex.Message}");
            }
        }
    }
}
