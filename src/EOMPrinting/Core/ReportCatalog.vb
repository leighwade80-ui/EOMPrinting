Imports System.IO

''' <summary>Which database a dataset reads from.</summary>
Public Enum DataSourceKind
    ''' <summary>SQL Server (rp-sql02, database Rinoldi).</summary>
    Rinoldi
    ''' <summary>The Access database J:\ACCESS\PackProd.mdb, used by the packing and production reports.</summary>
    PackProd
End Enum

''' <summary>One query that feeds a dataset in an RDLC report.</summary>
Public NotInheritable Class ReportDataSet

    ''' <summary>The DataSet name inside the .rdlc file.</summary>
    Public Property Name As String = "Main"

    ''' <summary>A stored procedure name, or a SELECT statement.</summary>
    Public Property CommandText As String = ""

    Public Property IsStoredProcedure As Boolean

    ''' <summary>
    ''' Which month parameters the stored procedure takes. The old app always passed
    ''' @startDate, @finishDate, @month and a blank @reportName.
    ''' </summary>
    Public Property MonthParameters As String() = Array.Empty(Of String)()

    Public Property Source As DataSourceKind = DataSourceKind.Rinoldi

    Public Shared Function Proc(name As String, Optional dataSetName As String = "Main") As ReportDataSet
        Return New ReportDataSet With {
            .Name = dataSetName,
            .CommandText = name,
            .IsStoredProcedure = True,
            .MonthParameters = {"@startDate", "@finishDate", "@month", "@reportName"}
        }
    End Function

    Public Shared Function View(viewName As String, Optional dataSetName As String = "Main") As ReportDataSet
        Return New ReportDataSet With {
            .Name = dataSetName,
            .CommandText = $"SELECT * FROM dbo.{viewName}"
        }
    End Function

    ''' <summary>A saved query or table in PackProd.mdb.</summary>
    Public Shared Function AccessQuery(queryName As String, Optional dataSetName As String = "Main") As ReportDataSet
        Return New ReportDataSet With {
            .Name = dataSetName,
            .CommandText = $"SELECT * FROM [{queryName}]",
            .Source = DataSourceKind.PackProd
        }
    End Function

End Class

''' <summary>One report on the EOM or EOM2 screen.</summary>
Public NotInheritable Class ReportDefinition

    Public Property Screen As String = "EOM"
    Public Property Group As String = ""
    Public Property Title As String = ""

    ''' <summary>The old Crystal file, kept for reference.</summary>
    Public Property OldFile As String = ""

    Public Property RdlcFile As String = ""
    Public Property MonthSource As MonthSource = MonthSource.None
    Public Property DataSets As New List(Of ReportDataSet)

    ''' <summary>Fixed report parameters, such as the title shared by the posting block layout.</summary>
    Public Property FixedParameters As New Dictionary(Of String, String)

    Public Property DefaultChecked As Boolean = True

    ''' <summary>False until the report has been rebuilt as an .rdlc file.</summary>
    Public ReadOnly Property IsAvailable As Boolean
        Get
            Return DataSets.Count > 0 AndAlso File.Exists(AppSettings.ReportPath(RdlcFile))
        End Get
    End Property

End Class

''' <summary>
''' Every report the old app printed, in the order it printed them.
''' Source: frmEOM.checkPrints and frmEOM2.checkPrints in the VB6 project.
''' </summary>
Public Module ReportCatalog

    Public ReadOnly Property All As IReadOnlyList(Of ReportDefinition) = Build()

    Public Function ForScreen(screen As String) As IEnumerable(Of ReportDefinition)
        Return All.Where(Function(r) String.Equals(r.Screen, screen, StringComparison.OrdinalIgnoreCase))
    End Function

    Private Function PostingBlock(screen As String, group As String, title As String, oldFile As String,
                                  procName As String, month As MonthSource) As ReportDefinition
        Dim def As New ReportDefinition With {
            .Screen = screen, .Group = group, .Title = title, .OldFile = oldFile,
            .RdlcFile = "PostingBlock.rdlc", .MonthSource = month
        }
        def.DataSets.Add(ReportDataSet.Proc(procName, "PostingBlock"))
        def.FixedParameters("ReportTitle") = title
        Return def
    End Function

    Private Function Report(screen As String, group As String, title As String, oldFile As String,
                            month As MonthSource, ParamArray dataSets As ReportDataSet()) As ReportDefinition
        Dim def As New ReportDefinition With {
            .Screen = screen, .Group = group, .Title = title, .OldFile = oldFile,
            .RdlcFile = Path.ChangeExtension(oldFile, ".rdlc"), .MonthSource = month
        }
        def.DataSets.AddRange(dataSets)
        Return def
    End Function

    Private Function Build() As IReadOnlyList(Of ReportDefinition)
        Const PP = "Packing and Production"
        Const DR = "Debtors"
        Const CR = "Creditors"
        Const SA = "Sales"
        Dim cur = MonthSource.CurrentMonth
        Dim none = MonthSource.None

        Dim list As New List(Of ReportDefinition)

        ' ---------- EOM: Packing and Production ----------
        ' Packing Stocks Detail, Packing Stocks, MTD Production and Production Summary read the Access database PackProd.mdb.
        ' Unpacked was dropped: no longer needed.
        list.Add(Report("EOM", PP, "Packing Stocks Detail", "PackingStocksDetail.rpt", none, ReportDataSet.AccessQuery("ut_rptPackStockDetailMTD")))
        list.Add(Report("EOM", PP, "Packing Stocks", "TotalPackedStock.rpt", none,
                   ReportDataSet.AccessQuery("qryPackST"), ReportDataSet.AccessQuery("ut_rptPackingStocksTotals", "Totals")))
        list.Add(Report("EOM", PP, "MTD Packing", "packingMTDAll.rpt", none, ReportDataSet.View("ut_rptPackingMTD")))
        list.Add(Report("EOM", PP, "MTD Production", "ProdMTD.rpt", none, ReportDataSet.AccessQuery("ut_productionmtd")))
        list.Add(Report("EOM", PP, "Packing Summary", "PackingMTDSummary.rpt", none, ReportDataSet.View("ut_rptMTDPackingSummary")))
        list.Add(Report("EOM", PP, "Production Summary", "MTDProdSummary.rpt", none, ReportDataSet.AccessQuery("ut_MTDProdSummary")))
        list.Add(Report("EOM", PP, "PackMat Detail", "Packing Material.rpt", none, ReportDataSet.View("ut_EOM_PackMat")))

        ' ---------- EOM: Debtors ----------
        list.Add(Report("EOM", DR, "Receipt Book MTD", "ReceiptBookJournal.rpt", cur, ReportDataSet.Proc("spReceiptBookJrn")))
        list.Add(PostingBlock("EOM", DR, "Receipt Book Posting Block", "RBPB.rpt", "spPostingReceiptBook", cur))
        list.Add(Report("EOM", DR, "Debtors Age Analysis", "DebtorsAgeAnalysis.rpt", none, ReportDataSet.View("ut_rptDebtorsAgeEOM")))
        list.Add(Report("EOM", DR, "Debtors Ledger", "DebtorsLedger.rpt", none,
                   ReportDataSet.View("ut_DebtorsLedger"), ReportDataSet.View("ut_DebtorsLedgerTotals", "Totals")))
        list.Add(Report("EOM", DR, "Receipts Banked", "ReceiptHistoryByCustomer.rpt", cur,
                   New ReportDataSet With {.CommandText = "usp_ReceiptReport", .IsStoredProcedure = True,
                                           .MonthParameters = {"@startDate", "@finishDate"}}))

        ' ---------- EOM: Creditors ----------
        list.Add(Report("EOM", CR, "Cashbook MTD", "CashBookMTD.rpt", cur,
                   New ReportDataSet With {.CommandText = "spCashBookJrnMTD", .IsStoredProcedure = True,
                                           .MonthParameters = {"@reportName"}},
                   New ReportDataSet With {.Name = "Cancelled", .CommandText = "usp_TotalCancelledMTD", .IsStoredProcedure = True}))
        list.Add(Report("EOM", CR, "Unpresented Cheques", "UnpresentedCheques.rpt", none,
                   ReportDataSet.View("ut_unpresentedChq", "Unpresented"),
                   ReportDataSet.View("ut_ChequeNoPurchase", "NotPurchase"),
                   ReportDataSet.View("ut_PresentedChqNoCashBook", "NotInCashBook"),
                   ReportDataSet.View("ut_NonMatchingCheques", "NonMatching")))
        list.Add(Report("EOM", CR, "EFT Transfer", "EFT.rpt", cur, ReportDataSet.Proc("spEFT")))
        list.Add(PostingBlock("EOM", CR, "CashBook Posting Block", "CBPB.rpt", "spPostingCashBook", cur))
        list.Add(Report("EOM", CR, "Petty Cash Journal", "PettyCashJournal.rpt", cur, ReportDataSet.Proc("spPettyCashJrn")))
        list.Add(PostingBlock("EOM", CR, "Petty Cash Posting Block", "PCPB.rpt", "spPostingPettyCash", cur))
        list.Add(Report("EOM", CR, "Bank Transactions", "BankTransactionsMTD.rpt", none, ReportDataSet.View("ut_RptBankTransactionsMTD")))
        list.Add(Report("EOM", CR, "Bank Reconciliation", "BankReconciliation.rpt", none, ReportDataSet.View("ut_rptBankReconciliation")))

        ' ---------- EOM: Sales ----------
        list.Add(Report("EOM", SA, "Sales Report MTD", "SalesReport.rpt", cur, ReportDataSet.Proc("usp_SalesReport")))
        list.Add(Report("EOM", SA, "Expiring Discount Prices", "ExpiringPrices.rpt", none, ReportDataSet.View("ut_EOM_PricingExpiration")))
        list.Add(Report("EOM", SA, "Sales Report Costing", "SalesReportCosting.rpt", cur, ReportDataSet.Proc("usp_SalesReport")))

        ' ---------- EOM2 ----------
        list.Add(Report("EOM2", CR, "Creditors Age Analysis", "CreditorsAgeAnalysisEOM2.rpt", none, ReportDataSet.View("ut_RptCAAEOM2")))
        list.Add(Report("EOM2", CR, "Creditors Ledger", "CreditorsLedgerEOM2.rpt", none, ReportDataSet.View("ut_CreditorsLedgerEOM2")))
        list.Add(PostingBlock("EOM2", CR, "Purchase Posting Block", "PurchasePostingBlock.rpt", "spPostingPurchase", MonthSource.Eom2))
        list.Add(Report("EOM2", CR, "Purchase Journal", "PurchaseJournal.rpt", MonthSource.Eom2, ReportDataSet.Proc("spPurchaseJournal")))

        Return list.AsReadOnly()
    End Function

End Module
