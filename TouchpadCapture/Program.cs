using System;
using System.Text.Json;
using System.Collections.Generic;
using System.Windows;
using System.Linq;
using System.Reflection;

// We'll use reflection to access RawInput.Touchpad without knowing exact API
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
                        Message = "Could not find MainWindow type in RawInput.Touchpad.dll"
                    });
                    return;
                }
                
                // Create WPF application
                var app = new Application();
                
                // Create MainWindow instance using reflection
                var window = Activator.CreateInstance(mainWindowType) as Window;
                if (window == null)
                {
                    OutputJson(new TouchEvent
                    {
                        Type = "error",
                        Message = "Could not create MainWindow instance"
                    });
                    return;
                }
                
                // Hide the window
                window.Visibility = Visibility.Hidden;
                window.ShowInTaskbar = false;
                
                OutputJson(new TouchEvent
                {
                    Type = "ready",
                    Message = "Touchpad capture ready (using reflection)"
                });
                
                // TODO: Hook into events using reflection
                // For now, just keep the window alive to register for Raw Input
                
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
    }
}
