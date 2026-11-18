Imports System.IO
Imports System.Text.Json

''' <summary>
''' Settings read from appsettings.json next to the exe.
''' Replaces the old file DSN (c:\rinoldi\barneysql.dsn) and the hard-coded S:\EOM\ path.
''' </summary>
Public NotInheritable Class AppSettings

    Public Shared Property ConnectionString As String = ""

    ''' <summary>Blank means the Windows default printer, as the old app did.</summary>
    Public Shared Property PrinterName As String = ""

    Public Shared Property ReportsFolder As String = "Reports"

    Private Sub New()
    End Sub

    Public Shared Sub Load()
        Dim settingsFile = IO.Path.Combine(AppContext.BaseDirectory, "appsettings.json")
        Using doc = JsonDocument.Parse(File.ReadAllText(settingsFile))
            Dim root = doc.RootElement
            ConnectionString = ReadString(root, "ConnectionString", ConnectionString)
            PrinterName = ReadString(root, "PrinterName", PrinterName)
            ReportsFolder = ReadString(root, "ReportsFolder", ReportsFolder)
        End Using

        If String.IsNullOrWhiteSpace(ConnectionString) Then
            Throw New InvalidDataException("ConnectionString is empty.")
        End If
    End Sub

    Public Shared Function ReportPath(fileName As String) As String
        Dim folder = If(IO.Path.IsPathRooted(ReportsFolder),
                        ReportsFolder,
                        IO.Path.Combine(AppContext.BaseDirectory, ReportsFolder))
        Return IO.Path.Combine(folder, fileName)
    End Function

    Private Shared Function ReadString(root As JsonElement, name As String, fallback As String) As String
        Dim value As JsonElement
        If root.TryGetProperty(name, value) AndAlso value.ValueKind = JsonValueKind.String Then
            Return value.GetString()
        End If
        Return fallback
    End Function

End Class
