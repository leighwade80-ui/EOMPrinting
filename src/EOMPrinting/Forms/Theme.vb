Imports System.Drawing

''' <summary>Colours taken from the old VB6 forms so the app looks familiar.</summary>
Friend Module Theme
    ''' <summary>VB6 &amp;H00A56E32&amp; (blue background).</summary>
    Public ReadOnly BackgroundColor As Color = Color.FromArgb(&H32, &H6E, &HA5)
    ''' <summary>VB6 &amp;H004080FF&amp; (orange panels).</summary>
    Public ReadOnly PanelColor As Color = Color.FromArgb(&HFF, &H80, &H40)
    Public ReadOnly TextColor As Color = Color.White
End Module
