Imports System.Windows.Forms

Public Module Program

    <STAThread>
    Public Sub Main()
        Application.SetHighDpiMode(HighDpiMode.SystemAware)
        Application.EnableVisualStyles()
        Application.SetCompatibleTextRenderingDefault(False)

        Try
            AppSettings.Load()
        Catch ex As Exception
            MessageBox.Show("Could not read appsettings.json:" & vbCrLf & ex.Message,
                            "EOM Printing", MessageBoxButtons.OK, MessageBoxIcon.Error)
            Return
        End Try

        Application.Run(New MainForm())
    End Sub

End Module
