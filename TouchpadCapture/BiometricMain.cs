using System;
using System.Windows;
using System.Windows.Interop;

namespace TouchpadCapture
{
    /// <summary>
    /// Main entry point for the complete C# Biometric Application
    /// </summary>
    class BiometricMain
    {
        private static BiometricApp mainWindow;
        
        [STAThread]
        static void Main(string[] args)
        {
            try
            {
                // Check if touchpad exists
                if (!TouchpadHelper.Exists())
                {
                    MessageBox.Show(
                        "No Precision Touchpad detected!\n\nThis application requires a Windows Precision Touchpad.",
                        "Error",
                        MessageBoxButton.OK,
                        MessageBoxImage.Error
                    );
                    return;
                }
                
                // Create application
                var app = new Application();
                
                // Create main window
                mainWindow = new BiometricApp();
                mainWindow.SourceInitialized += OnSourceInitialized;
                
                // Run application
                app.Run(mainWindow);
            }
            catch (Exception ex)
            {
                MessageBox.Show(
                    $"Error: {ex.Message}\n\n{ex.StackTrace}",
                    "Error",
                    MessageBoxButton.OK,
                    MessageBoxImage.Error
                );
            }
        }
        
        private static void OnSourceInitialized(object sender, EventArgs e)
        {
            // Register for Raw Input
            var source = PresentationSource.FromVisual(mainWindow) as HwndSource;
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
                
                if (contacts != null && mainWindow != null)
                {
                    mainWindow.UpdateContacts(contacts);
                }
            }
            return IntPtr.Zero;
        }
    }
}
