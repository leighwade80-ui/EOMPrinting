Imports Microsoft.Data.SqlClient

''' <summary>Where a report gets its month from. Matches the old app's getMonthDetails.</summary>
Public Enum MonthSource
    ''' <summary>The report reads a view that works out the month itself.</summary>
    None
    ''' <summary>tblCurrentMonth, used by the EOM screen.</summary>
    CurrentMonth
    ''' <summary>tblEOM2, used by the EOM2 screen.</summary>
    Eom2
End Enum

''' <summary>The month being printed: start date, finish date and its name (e.g. "October").</summary>
Public NotInheritable Class MonthPeriod

    Public Property StartDate As Date
    Public Property FinishDate As Date
    Public Property MonthName As String = ""

    Public Shared Function Load(source As MonthSource) As MonthPeriod
        Dim table As String
        Select Case source
            Case MonthSource.CurrentMonth : table = "tblCurrentMonth"
            Case MonthSource.Eom2 : table = "tblEOM2"
            Case Else : Return Nothing
        End Select

        Using conn As New SqlConnection(AppSettings.ConnectionString)
            conn.Open()
            Using cmd As New SqlCommand($"SELECT TOP 1 startingDate, finishingDate, [Month] FROM dbo.{table}", conn)
                Using reader = cmd.ExecuteReader()
                    If Not reader.Read() Then
                        Throw New InvalidOperationException($"{table} has no rows, so the month to print is unknown.")
                    End If
                    Return New MonthPeriod With {
                        .StartDate = reader.GetDateTime(0),
                        .FinishDate = reader.GetDateTime(1),
                        .MonthName = Convert.ToString(reader.GetValue(2)).Trim()
                    }
                End Using
            End Using
        End Using
    End Function

End Class
