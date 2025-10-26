using System;
using System.Collections.Generic;
using System.Linq;
using System.Windows;
using System.Windows.Controls;
using System.Windows.Media;
using System.Windows.Shapes;
using System.IO;
using System.Text.Json;

namespace TouchpadCapture
{
    /// <summary>
    /// Complete Biometric Application - All in C#
    /// Captures touchpad, visualizes, and performs biometric training/verification
    /// </summary>
    public class BiometricApp : Window
    {
        // UI Elements
        private Canvas visualizationCanvas;
        private TextBlock statusText;
        private TextBlock modeText;
        private TextBlock instructionsText;
        private ProgressBar trainingProgress;
        private Button captureButton;
        private Button resetButton;
        private StackPanel resultsPanel;
        
        // Visualization
        private Dictionary<int, List<Point>> contactTrails = new Dictionary<int, List<Point>>();
        private Dictionary<int, Ellipse> contactCircles = new Dictionary<int, Ellipse>();
        private int maxTrailPoints = 100;
        
        // Colors for different contacts
        private Brush[] contactColors = new Brush[]
        {
            new SolidColorBrush(Color.FromRgb(255, 100, 100)),  // Red
            new SolidColorBrush(Color.FromRgb(100, 255, 100)),  // Green
            new SolidColorBrush(Color.FromRgb(100, 100, 255)),  // Blue
            new SolidColorBrush(Color.FromRgb(255, 255, 100)),  // Yellow
            new SolidColorBrush(Color.FromRgb(255, 100, 255)),  // Magenta
        };
        
        // Touchpad bounds (auto-detected)
        private int touchpadMinX = int.MaxValue;
        private int touchpadMaxX = int.MinValue;
        private int touchpadMinY = int.MaxValue;
        private int touchpadMaxY = int.MinValue;
        
        // Current contacts
        private TouchpadContact[] currentContacts = new TouchpadContact[0];
        
        // Biometric state
        private enum Mode { Training, Verification }
        private Mode currentMode = Mode.Training;
        private int trainingSamplesNeeded = 5;
        private List<GestureSample> trainingSamples = new List<GestureSample>();
        private BiometricBaseline baseline = null;
        
        // Gesture capture
        private bool isCapturing = false;
        private DateTime captureStartTime;
        private double captureDuration = 2.0; // seconds
        private List<GesturePoint> currentGesture = new List<GesturePoint>();
        
        public BiometricApp()
        {
            InitializeUI();
            StartVisualizationTimer();
        }
        
        private void InitializeUI()
        {
            // Window properties
            Title = "Touchpad Biometric System";
            Width = 1400;
            Height = 900;
            WindowStartupLocation = WindowStartupLocation.CenterScreen;
            Background = new SolidColorBrush(Color.FromRgb(20, 20, 30));
            
            // Main grid
            var mainGrid = new Grid();
            mainGrid.ColumnDefinitions.Add(new ColumnDefinition { Width = new GridLength(1, GridUnitType.Star) });
            mainGrid.ColumnDefinitions.Add(new ColumnDefinition { Width = new GridLength(400) });
            
            // Left: Visualization
            visualizationCanvas = new Canvas
            {
                Background = new SolidColorBrush(Color.FromRgb(30, 30, 40)),
                Margin = new Thickness(10)
            };
            Grid.SetColumn(visualizationCanvas, 0);
            mainGrid.Children.Add(visualizationCanvas);
            
            // Right: Control panel
            var controlPanel = new StackPanel
            {
                Background = new SolidColorBrush(Color.FromRgb(25, 25, 35)),
                Margin = new Thickness(10, 10, 10, 10)
            };
            Grid.SetColumn(controlPanel, 1);
            mainGrid.Children.Add(controlPanel);
            
            // Title
            var titleText = new TextBlock
            {
                Text = "Biometric Auth",
                FontSize = 36,
                FontWeight = FontWeights.Bold,
                Foreground = new SolidColorBrush(Color.FromRgb(0, 255, 100)),
                Margin = new Thickness(20, 20, 20, 10),
                TextAlignment = TextAlignment.Center
            };
            controlPanel.Children.Add(titleText);
            
            // Mode
            modeText = new TextBlock
            {
                Text = "TRAINING MODE",
                FontSize = 24,
                FontWeight = FontWeights.Bold,
                Foreground = new SolidColorBrush(Color.FromRgb(255, 165, 0)),
                Margin = new Thickness(20, 10, 20, 10),
                TextAlignment = TextAlignment.Center
            };
            controlPanel.Children.Add(modeText);
            
            // Status
            statusText = new TextBlock
            {
                Text = "Ready to train",
                FontSize = 18,
                Foreground = Brushes.White,
                Margin = new Thickness(20, 10, 20, 20),
                TextAlignment = TextAlignment.Center,
                TextWrapping = TextWrapping.Wrap
            };
            controlPanel.Children.Add(statusText);
            
            // Training progress
            trainingProgress = new ProgressBar
            {
                Height = 30,
                Margin = new Thickness(20, 10, 20, 10),
                Minimum = 0,
                Maximum = trainingSamplesNeeded,
                Value = 0
            };
            controlPanel.Children.Add(trainingProgress);
            
            var progressText = new TextBlock
            {
                Text = $"0/{trainingSamplesNeeded} samples",
                FontSize = 14,
                Foreground = new SolidColorBrush(Color.FromRgb(150, 150, 150)),
                Margin = new Thickness(20, 0, 20, 20),
                TextAlignment = TextAlignment.Center
            };
            trainingProgress.Tag = progressText;
            controlPanel.Children.Add(progressText);
            
            // Separator
            controlPanel.Children.Add(new Separator { Margin = new Thickness(20, 10, 20, 10) });
            
            // Buttons
            captureButton = new Button
            {
                Content = "CAPTURE GESTURE (SPACE)",
                FontSize = 16,
                FontWeight = FontWeights.Bold,
                Height = 50,
                Margin = new Thickness(20, 10, 20, 10),
                Background = new SolidColorBrush(Color.FromRgb(0, 120, 215)),
                Foreground = Brushes.White,
                BorderThickness = new Thickness(0)
            };
            captureButton.Click += CaptureButton_Click;
            controlPanel.Children.Add(captureButton);
            
            resetButton = new Button
            {
                Content = "Reset Training",
                FontSize = 14,
                Height = 40,
                Margin = new Thickness(20, 10, 20, 10),
                Background = new SolidColorBrush(Color.FromRgb(60, 60, 70)),
                Foreground = Brushes.White,
                BorderThickness = new Thickness(0)
            };
            resetButton.Click += ResetButton_Click;
            controlPanel.Children.Add(resetButton);
            
            // Separator
            controlPanel.Children.Add(new Separator { Margin = new Thickness(20, 10, 20, 10) });
            
            // Instructions
            instructionsText = new TextBlock
            {
                Text = "1. Click 'CAPTURE GESTURE' or press SPACE\n" +
                       "2. Perform your gesture (2 seconds)\n" +
                       "3. Repeat 5 times\n" +
                       "4. System will learn your pattern\n" +
                       "5. Then verify with same gesture",
                FontSize = 14,
                Foreground = new SolidColorBrush(Color.FromRgb(150, 150, 150)),
                Margin = new Thickness(20, 10, 20, 10),
                TextWrapping = TextWrapping.Wrap,
                LineHeight = 22
            };
            controlPanel.Children.Add(instructionsText);
            
            // Results panel (hidden initially)
            resultsPanel = new StackPanel
            {
                Margin = new Thickness(20, 10, 20, 10),
                Visibility = Visibility.Collapsed
            };
            controlPanel.Children.Add(resultsPanel);
            
            Content = mainGrid;
            
            // Keyboard shortcuts
            KeyDown += (s, e) =>
            {
                if (e.Key == System.Windows.Input.Key.Space && !isCapturing)
                {
                    StartCapture();
                }
                else if (e.Key == System.Windows.Input.Key.R)
                {
                    ResetTraining();
                }
            };
        }
        
        private void StartVisualizationTimer()
        {
            var timer = new System.Windows.Threading.DispatcherTimer();
            timer.Interval = TimeSpan.FromMilliseconds(16); // 60 FPS
            timer.Tick += UpdateVisualization;
            timer.Start();
        }
        
        private void CaptureButton_Click(object sender, RoutedEventArgs e)
        {
            if (!isCapturing)
            {
                StartCapture();
            }
        }
        
        private void ResetButton_Click(object sender, RoutedEventArgs e)
        {
            ResetTraining();
        }
        
        private void StartCapture()
        {
            isCapturing = true;
            captureStartTime = DateTime.Now;
            currentGesture.Clear();
            contactTrails.Clear();
            
            statusText.Text = "CAPTURING... Perform your gesture!";
            statusText.Foreground = new SolidColorBrush(Color.FromRgb(255, 165, 0));
            captureButton.IsEnabled = false;
        }
        
        private void FinishCapture()
        {
            isCapturing = false;
            captureButton.IsEnabled = true;
            
            if (currentGesture.Count < 10)
            {
                statusText.Text = "Gesture too short! Try again.";
                statusText.Foreground = new SolidColorBrush(Color.FromRgb(255, 50, 50));
                return;
            }
            
            if (currentMode == Mode.Training)
            {
                // Add training sample
                var sample = new GestureSample { Points = new List<GesturePoint>(currentGesture) };
                trainingSamples.Add(sample);
                
                trainingProgress.Value = trainingSamples.Count;
                var progressText = trainingProgress.Tag as TextBlock;
                if (progressText != null)
                {
                    progressText.Text = $"{trainingSamples.Count}/{trainingSamplesNeeded} samples";
                }
                
                if (trainingSamples.Count >= trainingSamplesNeeded)
                {
                    TrainBaseline();
                }
                else
                {
                    int remaining = trainingSamplesNeeded - trainingSamples.Count;
                    statusText.Text = $"Good! {remaining} more sample(s) needed";
                    statusText.Foreground = new SolidColorBrush(Color.FromRgb(0, 255, 100));
                }
            }
            else
            {
                // Verify gesture
                VerifyGesture();
            }
        }
        
        private void TrainBaseline()
        {
            statusText.Text = "Training baseline...";
            
            // Simple baseline: calculate average duration and path length
            baseline = new BiometricBaseline();
            
            foreach (var sample in trainingSamples)
            {
                var features = ExtractFeatures(sample);
                baseline.Durations.Add(features.Duration);
                baseline.PathLengths.Add(features.PathLength);
                baseline.Velocities.Add(features.AvgVelocity);
            }
            
            baseline.CalculateStats();
            
            // Save baseline
            try
            {
                var json = JsonSerializer.Serialize(baseline);
                File.WriteAllText("baseline.json", json);
            }
            catch { }
            
            // Switch to verification mode
            currentMode = Mode.Verification;
            modeText.Text = "VERIFICATION MODE";
            modeText.Foreground = new SolidColorBrush(Color.FromRgb(0, 255, 100));
            statusText.Text = "Training complete! Now verify.";
            statusText.Foreground = new SolidColorBrush(Color.FromRgb(0, 255, 100));
            instructionsText.Text = "Perform your gesture to verify.\n\n" +
                                   "The system will check if it matches\n" +
                                   "your trained pattern.";
            trainingProgress.Visibility = Visibility.Collapsed;
            (trainingProgress.Tag as TextBlock).Visibility = Visibility.Collapsed;
        }
        
        private void VerifyGesture()
        {
            if (baseline == null) return;
            
            var sample = new GestureSample { Points = new List<GesturePoint>(currentGesture) };
            var features = ExtractFeatures(sample);
            
            // Calculate distances from baseline
            double durationDist = Math.Abs(features.Duration - baseline.DurationMean) / baseline.DurationStd;
            double pathDist = Math.Abs(features.PathLength - baseline.PathLengthMean) / baseline.PathLengthStd;
            double velocityDist = Math.Abs(features.AvgVelocity - baseline.VelocityMean) / baseline.VelocityStd;
            
            double totalDist = Math.Sqrt(durationDist * durationDist + pathDist * pathDist + velocityDist * velocityDist);
            
            double threshold = 3.0; // 3 standard deviations
            bool authenticated = totalDist < threshold;
            double confidence = Math.Max(0, 1 - (totalDist / threshold)) * 100;
            
            // Show results
            resultsPanel.Children.Clear();
            resultsPanel.Visibility = Visibility.Visible;
            
            var resultTitle = new TextBlock
            {
                Text = authenticated ? "✓ AUTHENTICATED" : "✗ REJECTED",
                FontSize = 28,
                FontWeight = FontWeights.Bold,
                Foreground = authenticated ? 
                    new SolidColorBrush(Color.FromRgb(0, 255, 100)) : 
                    new SolidColorBrush(Color.FromRgb(255, 50, 50)),
                Margin = new Thickness(0, 10, 0, 10),
                TextAlignment = TextAlignment.Center
            };
            resultsPanel.Children.Add(resultTitle);
            
            var confidenceText = new TextBlock
            {
                Text = $"Confidence: {confidence:F1}%",
                FontSize = 18,
                Foreground = Brushes.White,
                Margin = new Thickness(0, 5, 0, 5),
                TextAlignment = TextAlignment.Center
            };
            resultsPanel.Children.Add(confidenceText);
            
            var distanceText = new TextBlock
            {
                Text = $"Distance: {totalDist:F2} (threshold: {threshold:F1})",
                FontSize = 14,
                Foreground = new SolidColorBrush(Color.FromRgb(150, 150, 150)),
                Margin = new Thickness(0, 5, 0, 10),
                TextAlignment = TextAlignment.Center
            };
            resultsPanel.Children.Add(distanceText);
            
            statusText.Text = authenticated ? "Access granted!" : "Access denied!";
            statusText.Foreground = authenticated ? 
                new SolidColorBrush(Color.FromRgb(0, 255, 100)) : 
                new SolidColorBrush(Color.FromRgb(255, 50, 50));
        }
        
        private GestureFeatures ExtractFeatures(GestureSample sample)
        {
            var features = new GestureFeatures();
            
            if (sample.Points.Count < 2) return features;
            
            features.Duration = (sample.Points.Last().Timestamp - sample.Points.First().Timestamp).TotalSeconds;
            
            double totalDistance = 0;
            for (int i = 1; i < sample.Points.Count; i++)
            {
                double dx = sample.Points[i].X - sample.Points[i - 1].X;
                double dy = sample.Points[i].Y - sample.Points[i - 1].Y;
                totalDistance += Math.Sqrt(dx * dx + dy * dy);
            }
            
            features.PathLength = totalDistance;
            features.AvgVelocity = features.Duration > 0 ? totalDistance / features.Duration : 0;
            
            return features;
        }
        
        private void ResetTraining()
        {
            trainingSamples.Clear();
            baseline = null;
            currentMode = Mode.Training;
            trainingProgress.Value = 0;
            trainingProgress.Visibility = Visibility.Visible;
            (trainingProgress.Tag as TextBlock).Visibility = Visibility.Visible;
            (trainingProgress.Tag as TextBlock).Text = $"0/{trainingSamplesNeeded} samples";
            
            modeText.Text = "TRAINING MODE";
            modeText.Foreground = new SolidColorBrush(Color.FromRgb(255, 165, 0));
            statusText.Text = "Ready to train";
            statusText.Foreground = Brushes.White;
            instructionsText.Text = "1. Click 'CAPTURE GESTURE' or press SPACE\n" +
                                   "2. Perform your gesture (2 seconds)\n" +
                                   "3. Repeat 5 times\n" +
                                   "4. System will learn your pattern\n" +
                                   "5. Then verify with same gesture";
            resultsPanel.Visibility = Visibility.Collapsed;
        }
        
        public void UpdateContacts(TouchpadContact[] contacts)
        {
            currentContacts = contacts;
            
            // Update bounds
            foreach (var contact in contacts)
            {
                touchpadMinX = Math.Min(touchpadMinX, contact.X);
                touchpadMaxX = Math.Max(touchpadMaxX, contact.X);
                touchpadMinY = Math.Min(touchpadMinY, contact.Y);
                touchpadMaxY = Math.Max(touchpadMaxY, contact.Y);
            }
            
            // Capture gesture data
            if (isCapturing)
            {
                foreach (var contact in contacts)
                {
                    currentGesture.Add(new GesturePoint
                    {
                        X = contact.X,
                        Y = contact.Y,
                        ContactId = contact.ContactId,
                        Timestamp = DateTime.Now
                    });
                }
                
                // Check if capture duration elapsed
                if ((DateTime.Now - captureStartTime).TotalSeconds >= captureDuration)
                {
                    FinishCapture();
                }
            }
        }
        
        private Point MapToCanvas(int x, int y)
        {
            double normX = touchpadMaxX > touchpadMinX ? 
                (double)(x - touchpadMinX) / (touchpadMaxX - touchpadMinX) : 0.5;
            double normY = touchpadMaxY > touchpadMinY ? 
                (double)(y - touchpadMinY) / (touchpadMaxY - touchpadMinY) : 0.5;
            
            double canvasX = 20 + normX * (visualizationCanvas.ActualWidth - 40);
            double canvasY = 20 + normY * (visualizationCanvas.ActualHeight - 40);
            
            return new Point(canvasX, canvasY);
        }
        
        private void UpdateVisualization(object sender, EventArgs e)
        {
            if (visualizationCanvas == null) return;
            
            // Clear old visuals
            visualizationCanvas.Children.Clear();
            
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
                
                if (contactTrails[contact.ContactId].Count > maxTrailPoints)
                {
                    contactTrails[contact.ContactId].RemoveAt(0);
                }
            }
            
            // Draw trails
            foreach (var kvp in contactTrails.ToList())
            {
                var trail = kvp.Value;
                var color = contactColors[kvp.Key % contactColors.Length];
                
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
                
                // Draw current position
                if (trail.Count > 0)
                {
                    var lastPos = trail.Last();
                    var circle = new Ellipse
                    {
                        Width = 40,
                        Height = 40,
                        Fill = color,
                        Stroke = Brushes.White,
                        StrokeThickness = 3
                    };
                    Canvas.SetLeft(circle, lastPos.X - 20);
                    Canvas.SetTop(circle, lastPos.Y - 20);
                    visualizationCanvas.Children.Add(circle);
                    
                    var idText = new TextBlock
                    {
                        Text = kvp.Key.ToString(),
                        FontSize = 18,
                        FontWeight = FontWeights.Bold,
                        Foreground = Brushes.White
                    };
                    Canvas.SetLeft(idText, lastPos.X - 8);
                    Canvas.SetTop(idText, lastPos.Y - 10);
                    visualizationCanvas.Children.Add(idText);
                }
            }
            
            // Remove old trails
            var activeIds = new HashSet<int>(currentContacts.Select(c => c.ContactId));
            var toRemove = contactTrails.Keys.Where(id => !activeIds.Contains(id)).ToList();
            foreach (var id in toRemove)
            {
                contactTrails.Remove(id);
            }
            
            // Draw capture progress bar
            if (isCapturing)
            {
                double elapsed = (DateTime.Now - captureStartTime).TotalSeconds;
                double progress = Math.Min(1.0, elapsed / captureDuration);
                
                double barWidth = visualizationCanvas.ActualWidth - 40;
                double barHeight = 30;
                double barX = 20;
                double barY = visualizationCanvas.ActualHeight - 50;
                
                var bgRect = new Rectangle
                {
                    Width = barWidth,
                    Height = barHeight,
                    Fill = new SolidColorBrush(Color.FromRgb(50, 50, 50))
                };
                Canvas.SetLeft(bgRect, barX);
                Canvas.SetTop(bgRect, barY);
                visualizationCanvas.Children.Add(bgRect);
                
                var progressRect = new Rectangle
                {
                    Width = barWidth * progress,
                    Height = barHeight,
                    Fill = new SolidColorBrush(Color.FromRgb(255, 165, 0))
                };
                Canvas.SetLeft(progressRect, barX);
                Canvas.SetTop(progressRect, barY);
                visualizationCanvas.Children.Add(progressRect);
            }
        }
    }
    
    // Data structures
    public class GesturePoint
    {
        public int X { get; set; }
        public int Y { get; set; }
        public int ContactId { get; set; }
        public DateTime Timestamp { get; set; }
    }
    
    public class GestureSample
    {
        public List<GesturePoint> Points { get; set; }
    }
    
    public class GestureFeatures
    {
        public double Duration { get; set; }
        public double PathLength { get; set; }
        public double AvgVelocity { get; set; }
    }
    
    public class BiometricBaseline
    {
        public List<double> Durations { get; set; } = new List<double>();
        public List<double> PathLengths { get; set; } = new List<double>();
        public List<double> Velocities { get; set; } = new List<double>();
        
        public double DurationMean { get; set; }
        public double DurationStd { get; set; }
        public double PathLengthMean { get; set; }
        public double PathLengthStd { get; set; }
        public double VelocityMean { get; set; }
        public double VelocityStd { get; set; }
        
        public void CalculateStats()
        {
            DurationMean = Durations.Average();
            DurationStd = Math.Sqrt(Durations.Average(d => Math.Pow(d - DurationMean, 2))) + 0.0001;
            
            PathLengthMean = PathLengths.Average();
            PathLengthStd = Math.Sqrt(PathLengths.Average(p => Math.Pow(p - PathLengthMean, 2))) + 0.0001;
            
            VelocityMean = Velocities.Average();
            VelocityStd = Math.Sqrt(Velocities.Average(v => Math.Pow(v - VelocityMean, 2))) + 0.0001;
        }
    }
}
