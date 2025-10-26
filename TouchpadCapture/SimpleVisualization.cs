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
    /// <summary>
    /// Simple C# Visualization Window
    /// Shows touchpad visualization and outputs JSON for Python
    /// </summary>
    class SimpleVisualization
    {
        private static Window window;
        private static Canvas canvas;
        private static TextBlock statusText;
        private static Dictionary<int, List<Point>> trails = new Dictionary<int, List<Point>>();
        private static TouchpadContact[] currentContacts = new TouchpadContact[0];
        
        // Touchpad bounds
        private static int minX = int.MaxValue;
        private static int maxX = int.MinValue;
        private static int minY = int.MaxValue;
        private static int maxY = int.MinValue;
        
        // Colors
        private static Brush[] colors = new Brush[]
        {
            new SolidColorBrush(Color.FromRgb(255, 100, 100)),
            new SolidColorBrush(Color.FromRgb(100, 255, 100)),
            new SolidColorBrush(Color.FromRgb(100, 100, 255)),
            new SolidColorBrush(Color.FromRgb(255, 255, 100)),
            new SolidColorBrush(Color.FromRgb(255, 100, 255)),
        };
        
        [STAThread]
        static void Main(string[] args)
        {
            if (!TouchpadHelper.Exists())
            {
                Console.WriteLine("{\"Type\":\"error\",\"Message\":\"No Precision Touchpad detected\"}");
                return;
            }
            
            var app = new Application();
            
            // Create window
            window = new Window
            {
                Title = "Touchpad Visualization",
                Width = 800,
                Height = 600,
                WindowStartupLocation = WindowStartupLocation.Manual,
                Left = 50,
                Top = 50,
                Background = new SolidColorBrush(Color.FromRgb(20, 20, 30))
            };
            
            var grid = new Grid();
            
            // Canvas for visualization
            canvas = new Canvas
            {
                Background = new SolidColorBrush(Color.FromRgb(30, 30, 40))
            };
            grid.Children.Add(canvas);
            
            // Status text
            statusText = new TextBlock
            {
                Text = "Touch your touchpad",
                FontSize = 24,
                Foreground = new SolidColorBrush(Color.FromRgb(0, 255, 100)),
                HorizontalAlignment = HorizontalAlignment.Center,
                VerticalAlignment = VerticalAlignment.Top,
                Margin = new Thickness(0, 20, 0, 0)
            };
            grid.Children.Add(statusText);
            
            window.Content = grid;
            window.SourceInitialized += OnSourceInitialized;
            
            // Visualization timer
            var timer = new System.Windows.Threading.DispatcherTimer();
            timer.Interval = TimeSpan.FromMilliseconds(16);
            timer.Tick += UpdateVisualization;
            timer.Start();
            
            Console.WriteLine("{\"Type\":\"ready\",\"Message\":\"Touchpad visualization ready\"}");
            
            app.Run(window);
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
                    currentContacts = contacts;
                    
                    // Update bounds
                    foreach (var c in contacts)
                    {
                        minX = Math.Min(minX, c.X);
                        maxX = Math.Max(maxX, c.X);
                        minY = Math.Min(minY, c.Y);
                        maxY = Math.Max(maxY, c.Y);
                    }
                    
                    // Output JSON for Python
                    var output = new
                    {
                        Type = "contacts",
                        Contacts = contacts.Select(c => new
                        {
                            ContactId = c.ContactId,
                            X = c.X,
                            Y = c.Y,
                            Timestamp = DateTimeOffset.UtcNow.ToUnixTimeMilliseconds()
                        }).ToList()
                    };
                    
                    Console.WriteLine(JsonSerializer.Serialize(output));
                }
            }
            return IntPtr.Zero;
        }
        
        private static Point MapToCanvas(int x, int y)
        {
            double normX = maxX > minX ? (double)(x - minX) / (maxX - minX) : 0.5;
            double normY = maxY > minY ? (double)(y - minY) / (maxY - minY) : 0.5;
            
            double canvasX = 20 + normX * (canvas.ActualWidth - 40);
            double canvasY = 20 + normY * (canvas.ActualHeight - 40);
            
            return new Point(canvasX, canvasY);
        }
        
        private static void UpdateVisualization(object sender, EventArgs e)
        {
            canvas.Children.Clear();
            
            // Update status
            if (currentContacts.Length > 0)
            {
                statusText.Text = $"{currentContacts.Length} finger(s)";
            }
            else
            {
                statusText.Text = "Touch your touchpad";
            }
            
            // Update trails
            foreach (var contact in currentContacts)
            {
                if (!trails.ContainsKey(contact.ContactId))
                {
                    trails[contact.ContactId] = new List<Point>();
                }
                
                var pos = MapToCanvas(contact.X, contact.Y);
                trails[contact.ContactId].Add(pos);
                
                if (trails[contact.ContactId].Count > 100)
                {
                    trails[contact.ContactId].RemoveAt(0);
                }
            }
            
            // Draw trails
            foreach (var kvp in trails.ToList())
            {
                var trail = kvp.Value;
                var color = colors[kvp.Key % colors.Length];
                
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
                    canvas.Children.Add(line);
                }
                
                // Draw current position
                if (trail.Count > 0)
                {
                    var pos = trail.Last();
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
                    canvas.Children.Add(circle);
                    
                    var idText = new TextBlock
                    {
                        Text = kvp.Key.ToString(),
                        FontSize = 18,
                        FontWeight = FontWeights.Bold,
                        Foreground = Brushes.White
                    };
                    Canvas.SetLeft(idText, pos.X - 8);
                    Canvas.SetTop(idText, pos.Y - 10);
                    canvas.Children.Add(idText);
                }
            }
            
            // Remove old trails
            var activeIds = new HashSet<int>(currentContacts.Select(c => c.ContactId));
            foreach (var id in trails.Keys.ToList())
            {
                if (!activeIds.Contains(id))
                {
                    trails.Remove(id);
                }
            }
        }
    }
}
