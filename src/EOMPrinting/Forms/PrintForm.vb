Imports System.Drawing
Imports System.Windows.Forms

''' <summary>
''' The EOM or EOM2 screen: a ticked box per report, grouped like the old form,
''' with Select All / Deselect All, Print and Close. Replaces frmEOM and frmEOM2.
''' </summary>
<System.ComponentModel.DesignerCategory("Code")>
Public Class PrintForm
    Inherits Form

    Private ReadOnly _screen As String
    Private ReadOnly _boxes As New List(Of (Box As CheckBox, Report As ReportDefinition))
    Private ReadOnly _selectButton As Button
    Private ReadOnly _printButton As Button
    Private ReadOnly _status As Label

    Public Sub New(screen As String)
        _screen = screen
        Text = $"{screen} Printing"
        StartPosition = FormStartPosition.CenterScreen
        BackColor = Theme.BackgroundColor
        Font = New Font("Segoe UI", 9.75F)
        AutoScaleMode = AutoScaleMode.Font
        MinimumSize = New Size(560, 420)

        Dim title As New Label With {
            .Text = $"{screen} PRINTING",
            .ForeColor = Theme.TextColor,
            .Font = New Font("Segoe UI", 18.0F, FontStyle.Bold),
            .TextAlign = ContentAlignment.MiddleCenter,
            .Dock = DockStyle.Top,
            .Height = 56
        }

        ' Report groups flow left to right and wrap, like the panels on the old form.
        Dim groups As New FlowLayoutPanel With {
            .Dock = DockStyle.Fill,
            .AutoScroll = True,
            .Padding = New Padding(12),
            .BackColor = Theme.BackgroundColor
        }

        For Each grp In ReportCatalog.ForScreen(screen).GroupBy(Function(r) r.Group)
            Dim panel As New FlowLayoutPanel With {
                .FlowDirection = FlowDirection.TopDown,
                .WrapContents = False,
                .AutoSize = True,
                .BackColor = Theme.PanelColor,
                .Padding = New Padding(10),
                .Margin = New Padding(8)
            }
            panel.Controls.Add(New Label With {
                .Text = grp.Key,
                .ForeColor = Theme.TextColor,
                .Font = New Font(Font, FontStyle.Bold),
                .AutoSize = True,
                .Margin = New Padding(0, 0, 0, 6)
            })
            For Each def In grp
                Dim box As New CheckBox With {
                    .Text = If(def.IsAvailable, def.Title, def.Title & "  (not rebuilt yet)"),
                    .Checked = def.IsAvailable AndAlso def.DefaultChecked,
                    .Enabled = def.IsAvailable,
                    .ForeColor = Theme.TextColor,
                    .AutoSize = True
                }
                panel.Controls.Add(box)
                _boxes.Add((box, def))
            Next
            groups.Controls.Add(panel)
        Next

        _selectButton = New Button With {.Text = "Deselect All", .AutoSize = True, .BackColor = SystemColors.Control}
        _printButton = New Button With {.Text = "Print", .AutoSize = True, .BackColor = SystemColors.Control}
        Dim closeButton As New Button With {.Text = "Close", .AutoSize = True, .BackColor = SystemColors.Control,
                                            .DialogResult = DialogResult.Cancel}
        _status = New Label With {.ForeColor = Theme.TextColor, .AutoSize = True, .Margin = New Padding(12, 8, 0, 0)}

        Dim buttons As New FlowLayoutPanel With {
            .Dock = DockStyle.Bottom,
            .FlowDirection = FlowDirection.LeftToRight,
            .AutoSize = True,
            .Padding = New Padding(12),
            .BackColor = Theme.BackgroundColor
        }
        buttons.Controls.AddRange({_selectButton, _printButton, closeButton, _status})

        AddHandler _selectButton.Click, AddressOf ToggleAll
        AddHandler _printButton.Click, AddressOf PrintSelected
        CancelButton = closeButton

        Controls.Add(groups)
        Controls.Add(buttons)
        Controls.Add(title)

        Size = New Size(900, 620)
    End Sub

    Private Sub ToggleAll(sender As Object, e As EventArgs)
        Dim selectAll = _selectButton.Text = "Select All"
        For Each item In _boxes
            If item.Box.Enabled Then item.Box.Checked = selectAll
        Next
        _selectButton.Text = If(selectAll, "Deselect All", "Select All")
    End Sub

    Private Sub PrintSelected(sender As Object, e As EventArgs)
        Dim selected = _boxes.Where(Function(b) b.Box.Checked).Select(Function(b) b.Report).ToList()
        If selected.Count = 0 Then
            MessageBox.Show("No reports are ticked.", Text, MessageBoxButtons.OK, MessageBoxIcon.Information)
            Return
        End If

        Dim periods As New Dictionary(Of MonthSource, MonthPeriod)
        Dim failures As New List(Of String)

        _printButton.Enabled = False
        UseWaitCursor = True
        Try
            For Each def In selected
                _status.Text = If(AppSettings.SaveAsPdf, $"Saving {def.Title}...", $"Printing {def.Title}...")
                _status.Refresh()
                Try
                    Dim period As MonthPeriod = Nothing
                    If def.MonthSource <> MonthSource.None Then
                        If Not periods.TryGetValue(def.MonthSource, period) Then
                            period = MonthPeriod.Load(def.MonthSource)
                            periods(def.MonthSource) = period
                        End If
                    End If
                    ReportPrinter.Print(def, period)
                Catch ex As Exception
                    failures.Add($"{def.Title}: {ex.Message}")
                End Try
            Next
        Finally
            UseWaitCursor = False
            _printButton.Enabled = True
            _status.Text = ""
        End Try

        If failures.Count = 0 AndAlso AppSettings.SaveAsPdf Then
            MessageBox.Show($"{_screen} reports saved to {AppSettings.PdfOutputFolder()}", "Printing Complete",
                            MessageBoxButtons.OK, MessageBoxIcon.Information)
        ElseIf failures.Count = 0 Then
            MessageBox.Show($"{_screen} Printing is complete", "Printing Complete",
                            MessageBoxButtons.OK, MessageBoxIcon.Information)
        Else
            MessageBox.Show($"{_screen} Printing finished, but these reports failed:" & vbCrLf & vbCrLf &
                            String.Join(vbCrLf, failures),
                            "Printing Problems", MessageBoxButtons.OK, MessageBoxIcon.Warning)
        End If
    End Sub

End Class
