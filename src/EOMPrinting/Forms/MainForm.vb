Imports System.Drawing
Imports System.Windows.Forms

''' <summary>The opening menu: EOM, EOM2 or Close. Replaces frmMain.</summary>
Public Class MainForm
    Inherits Form

    Public Sub New()
        Text = "EOM Printing"
        StartPosition = FormStartPosition.CenterScreen
        FormBorderStyle = FormBorderStyle.FixedDialog
        MaximizeBox = False
        BackColor = Theme.BackgroundColor
        ClientSize = New Size(360, 260)
        Font = New Font("Segoe UI", 10.0F)

        Dim title As New Label With {
            .Text = "EOM PRINTING",
            .ForeColor = Theme.TextColor,
            .Font = New Font("Segoe UI", 18.0F, FontStyle.Bold),
            .TextAlign = ContentAlignment.MiddleCenter,
            .Dock = DockStyle.Top,
            .Height = 70
        }

        Dim eom = MakeButton("EOM", 85)
        Dim eom2 = MakeButton("EOM2", 135)
        Dim close = MakeButton("Close", 195)

        AddHandler eom.Click, Sub() OpenScreen("EOM")
        AddHandler eom2.Click, Sub() OpenScreen("EOM2")
        AddHandler close.Click, Sub() Me.Close()

        Controls.AddRange({title, eom, eom2, close})
    End Sub

    Private Function MakeButton(caption As String, top As Integer) As Button
        Return New Button With {
            .Text = caption,
            .Size = New Size(160, 38),
            .Location = New Point((ClientSize.Width - 160) \ 2, top),
            .BackColor = SystemColors.Control
        }
    End Function

    Private Sub OpenScreen(screen As String)
        Using form As New PrintForm(screen)
            Hide()
            form.ShowDialog()
            Show()
        End Using
    End Sub

End Class
