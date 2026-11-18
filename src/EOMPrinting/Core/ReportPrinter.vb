Imports System.Data
Imports System.Drawing
Imports System.Drawing.Imaging
Imports System.Drawing.Printing
Imports System.IO
Imports System.Xml.Linq
Imports Microsoft.Data.SqlClient
Imports Microsoft.Reporting.WinForms

''' <summary>
''' Fills an RDLC report from SQL Server and sends it straight to the printer,
''' landscape A4 and duplex, with no preview. This is what the old ViewReport sub did with Crystal.
''' When OutputMode is "Pdf", it saves a PDF named after the report instead, with no prompt.
''' </summary>
Public NotInheritable Class ReportPrinter
    Implements IDisposable

    Private ReadOnly _pages As New List(Of Stream)
    Private _pageIndex As Integer

    Public Shared Sub Print(def As ReportDefinition, period As MonthPeriod)
        Using printer As New ReportPrinter()
            printer.Run(def, period)
        End Using
    End Sub

    Private Sub Run(def As ReportDefinition, period As MonthPeriod)
        Dim rdlcPath = AppSettings.ReportPath(def.RdlcFile)

        Using report As New LocalReport()
            report.ReportPath = rdlcPath

            Dim fieldNames = ReadFieldNames(rdlcPath)
            For Each ds In def.DataSets
                Dim table = LoadData(ds, period)
                Dim names As List(Of String) = Nothing
                If fieldNames.TryGetValue(ds.Name, names) Then MatchColumnCase(table, names)
                report.DataSources.Add(New ReportDataSource(ds.Name, table))
            Next

            SetParameters(report, def, period)

            If AppSettings.SaveAsPdf Then
                SavePdf(report, def)
                Return
            End If

            RenderPages(report)
        End Using

        PrintPages(def.Title)
    End Sub

    ' ---------- PDF ----------

    ''' <summary>Saves e.g. S:\EOM\Reports\20261119\CBPB.pdf, named after the old Crystal file. Overwrites a file from an earlier run today.</summary>
    Private Shared Sub SavePdf(report As LocalReport, def As ReportDefinition)
        Const deviceInfo =
            "<DeviceInfo>" &
            "<PageWidth>29.7cm</PageWidth><PageHeight>21cm</PageHeight>" &
            "<MarginTop>1cm</MarginTop><MarginLeft>1cm</MarginLeft>" &
            "<MarginRight>1cm</MarginRight><MarginBottom>1cm</MarginBottom>" &
            "</DeviceInfo>"
        Dim pdf = report.Render("PDF", deviceInfo)

        Dim folder = AppSettings.PdfOutputFolder()
        Directory.CreateDirectory(folder)
        Dim fileName = Path.GetFileNameWithoutExtension(def.OldFile) & ".pdf"
        File.WriteAllBytes(Path.Combine(folder, fileName), pdf)
    End Sub

    ' ---------- Data ----------

    Private Shared Function LoadData(ds As ReportDataSet, period As MonthPeriod) As DataTable
        Using conn As New SqlConnection(AppSettings.ConnectionString)
            Using cmd As New SqlCommand(ds.CommandText, conn)
                cmd.CommandTimeout = 300
                If ds.IsStoredProcedure Then
                    cmd.CommandType = CommandType.StoredProcedure
                    For Each name In ds.MonthParameters
                        cmd.Parameters.AddWithValue(name, MonthParameterValue(name, period))
                    Next
                End If

                Dim table As New DataTable(ds.Name)
                Using adapter As New SqlDataAdapter(cmd)
                    adapter.Fill(table)
                End Using
                Return table
            End Using
        End Using
    End Function

    Private Shared Function MonthParameterValue(name As String, period As MonthPeriod) As Object
        If period Is Nothing AndAlso Not name.Equals("@reportName", StringComparison.OrdinalIgnoreCase) Then
            Throw New InvalidOperationException($"Parameter {name} needs a month, but the report has no month source.")
        End If
        Select Case name.ToLowerInvariant()
            Case "@startdate" : Return period.StartDate
            Case "@finishdate" : Return period.FinishDate
            Case "@month" : Return period.MonthName
            Case "@reportname" : Return ""   ' The old app always passed a blank report name.
            Case Else : Throw New ArgumentException($"Unknown month parameter {name}.")
        End Select
    End Function

    ''' <summary>
    ''' SQL column names don't always match the case used in the report (e.g. "description" vs "Description").
    ''' Rename columns so the report finds them.
    ''' </summary>
    Private Shared Sub MatchColumnCase(table As DataTable, fieldNames As IEnumerable(Of String))
        For Each wanted In fieldNames
            Dim col = table.Columns.Cast(Of DataColumn)().
                FirstOrDefault(Function(c) String.Equals(c.ColumnName, wanted, StringComparison.OrdinalIgnoreCase))
            If col IsNot Nothing AndAlso col.ColumnName <> wanted Then col.ColumnName = wanted
        Next
    End Sub

    ''' <summary>Reads each DataSet's field names (DataField) from the .rdlc file.</summary>
    Private Shared Function ReadFieldNames(rdlcPath As String) As Dictionary(Of String, List(Of String))
        Dim result As New Dictionary(Of String, List(Of String))(StringComparer.OrdinalIgnoreCase)
        Dim doc = XDocument.Load(rdlcPath)
        For Each dsEl In doc.Descendants().Where(Function(e) e.Name.LocalName = "DataSet")
            Dim name = CStr(dsEl.Attribute("Name"))
            result(name) = dsEl.Descendants().
                Where(Function(e) e.Name.LocalName = "DataField").
                Select(Function(e) e.Value).ToList()
        Next
        Return result
    End Function

    Private Shared Sub SetParameters(report As LocalReport, def As ReportDefinition, period As MonthPeriod)
        Dim available As New HashSet(Of String)(
            report.GetParameters().Select(Function(p) p.Name), StringComparer.OrdinalIgnoreCase)
        Dim values As New List(Of ReportParameter)

        For Each kv In def.FixedParameters
            If available.Contains(kv.Key) Then values.Add(New ReportParameter(kv.Key, kv.Value))
        Next
        If period IsNot Nothing Then
            If available.Contains("MonthName") Then values.Add(New ReportParameter("MonthName", period.MonthName))
            If available.Contains("StartDate") Then values.Add(New ReportParameter("StartDate", period.StartDate.ToString("dd/MM/yyyy")))
            If available.Contains("FinishDate") Then values.Add(New ReportParameter("FinishDate", period.FinishDate.ToString("dd/MM/yyyy")))
        End If

        If values.Count > 0 Then report.SetParameters(values)
    End Sub

    ' ---------- Printing ----------
    ' Render to EMF pages, then draw each page with PrintDocument.
    ' This is Microsoft's documented way to print a LocalReport without showing the viewer.

    Private Sub RenderPages(report As LocalReport)
        Const deviceInfo =
            "<DeviceInfo>" &
            "<OutputFormat>EMF</OutputFormat>" &
            "<PageWidth>29.7cm</PageWidth><PageHeight>21cm</PageHeight>" &
            "<MarginTop>1cm</MarginTop><MarginLeft>1cm</MarginLeft>" &
            "<MarginRight>1cm</MarginRight><MarginBottom>1cm</MarginBottom>" &
            "</DeviceInfo>"
        Dim warnings As Warning() = Nothing
        report.Render("Image", deviceInfo, AddressOf CreateStream, warnings)
        For Each s In _pages
            s.Position = 0
        Next
    End Sub

    Private Function CreateStream(name As String, extension As String, encoding As System.Text.Encoding,
                                  mimeType As String, willSeek As Boolean) As Stream
        Dim s As New MemoryStream()
        _pages.Add(s)
        Return s
    End Function

    Private Sub PrintPages(documentName As String)
        If _pages.Count = 0 Then Return

        Using doc As New PrintDocument()
            doc.DocumentName = "EOM - " & documentName
            If Not String.IsNullOrWhiteSpace(AppSettings.PrinterName) Then
                doc.PrinterSettings.PrinterName = AppSettings.PrinterName
            End If
            If Not doc.PrinterSettings.IsValid Then
                Throw New InvalidOperationException($"Printer '{doc.PrinterSettings.PrinterName}' was not found.")
            End If

            ' Same settings as the old app: landscape, A4, duplex (crPRDPVertical).
            doc.DefaultPageSettings.Landscape = True
            Dim a4 = doc.PrinterSettings.PaperSizes.Cast(Of PaperSize)().
                FirstOrDefault(Function(p) p.Kind = PaperKind.A4)
            If a4 IsNot Nothing Then doc.DefaultPageSettings.PaperSize = a4
            If doc.PrinterSettings.CanDuplex Then doc.PrinterSettings.Duplex = Duplex.Vertical

            _pageIndex = 0
            AddHandler doc.PrintPage, AddressOf OnPrintPage
            doc.Print()
        End Using
    End Sub

    Private Sub OnPrintPage(sender As Object, e As PrintPageEventArgs)
        Using page As New Metafile(_pages(_pageIndex))
            Dim area As New Rectangle(
                e.PageBounds.Left - CInt(e.PageSettings.HardMarginX),
                e.PageBounds.Top - CInt(e.PageSettings.HardMarginY),
                e.PageBounds.Width,
                e.PageBounds.Height)
            e.Graphics.FillRectangle(Brushes.White, area)
            e.Graphics.DrawImage(page, area)
        End Using
        _pageIndex += 1
        e.HasMorePages = _pageIndex < _pages.Count
    End Sub

    Public Sub Dispose() Implements IDisposable.Dispose
        For Each s In _pages
            s.Dispose()
        Next
        _pages.Clear()
    End Sub

End Class
