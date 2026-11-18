# EOM Printing

A VB.NET rebuild of Rinoldi Pasta's VB6 **EOM Printing** app. It prints the end-of-month reports straight to the printer, landscape A4 and duplex, the same way the old app did, but without Crystal Reports or a DSN.

- **Stack:** VB.NET, Windows Forms, .NET 10, built in Visual Studio 2026.
- **Reports:** RDLC (Microsoft's report format), rendered with [ReportViewerCore.WinForms](https://github.com/lkosson/reportviewercore).
- **Data:** SQL Server on `rp-sql02`, database `Rinoldi`. The stored procedures and views are unchanged from the old app.

## Getting started

1. Open `EOMPrinting.sln` in Visual Studio 2026. NuGet restores the two packages on first build.
2. Check `src/EOMPrinting/appsettings.json`:
   - `ConnectionString` uses Windows authentication against `rp-sql02`. If you need SQL logins or the IP address (`192.168.0.204,52149`), change it here.
   - `PrinterName` blank means the Windows default printer, as before.
   - `ReportsFolder` is where the `.rdlc` files live. It defaults to the `Reports` folder next to the exe.
3. Press F5. The main menu has **EOM**, **EOM2** and **Close**, like the old app.

To edit a report layout in Visual Studio, install the **Microsoft RDLC Report Designer** extension.

## How it fits together

| File | What it does |
| --- | --- |
| `Core/ReportCatalog.vb` | Every report the old app printed, in print order, with its stored procedure or view and where its month comes from. |
| `Core/MonthPeriod.vb` | Reads the month to print from `tblCurrentMonth` (EOM) or `tblEOM2` (EOM2), as the old `getMonthDetails` did. |
| `Core/ReportPrinter.vb` | Runs the queries, fills the RDLC report and prints it with no preview. |
| `Forms/MainForm.vb`, `Forms/PrintForm.vb` | The menu and the two checkbox screens. |
| `Reports/*.rdlc` | Report layouts. |

A report shows as "(not rebuilt yet)" and can't be ticked until its `.rdlc` file exists in the `Reports` folder.

## Rebuild progress

| Report | Status |
| --- | --- |
| CashBook, Receipt Book, Petty Cash and Purchase Posting Blocks | Rebuilt as one shared layout (`PostingBlock.rdlc`). Needs checking against an old printout. |
| All other reports | Not rebuilt yet |

Open questions (missing `.rpt` files, the Access database reports, unused reports) are tracked in the project notes.
