import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from rdlgen import *
OUT = sys.argv[1]
def sumf(f, ds=None): return f'=Sum(Fields!{f}.Value, "{ds}")' if ds else f"=Sum(Fields!{f}.Value)"
def simple(filename, datasets, heading, cols, params=(), code=False, sort=None, group=None):
    t, h = tablix(cols, sort=sort, group=group)
    report(OUT, filename, datasets, t, h, title(heading), 1.2, params, code)

# ---------- Receipt Book MTD (spReceiptBookJrn) ----------
# Column order as the live S:\EOM report: debtors columns, then non-debtors value and posted.
simple("ReceiptBookJournal.rdlc",
       {"Main": [("pay", S), ("date", DT), ("genled", S), ("banked", D), ("office", S), ("DBDiscount", D), ("DBAdvertising", D),
                 ("DBValue", D), ("NDBValue", D), ("Posted", D), ("GST", D), ("Freight", D), ("Rebate", D), ("Month", S)]},
       '="Receipt Book Journal For " & Parameters!MonthName.Value',
       [Col("Pay", F("pay"), 1.6), Col("Date", F("date"), 2.0, fmt=DATE), Col("G/L", F("genled"), 1.3),
        Col("Banked", F("banked"), 2.5, "Right", MONEY, sumf("banked")), Col("Office", F("office"), 3.3),
        Col("Discount", F("DBDiscount"), 2.0, "Right", MONEY, sumf("DBDiscount")),
        Col("Advrts", F("DBAdvertising"), 1.9, "Right", MONEY, sumf("DBAdvertising")),
        Col("Freight", F("Freight"), 1.9, "Right", MONEY, sumf("Freight")),
        Col("Rebate", F("Rebate"), 1.9, "Right", MONEY, sumf("Rebate")),
        Col("Value", F("DBValue"), 2.5, "Right", MONEY, sumf("DBValue")),
        Col("GST", F("GST"), 1.8, "Right", MONEY, sumf("GST")),
        Col("Non-Debtors Value", F("NDBValue"), 2.5, "Right", MONEY, sumf("NDBValue")),
        Col("Posted", F("Posted"), 2.5, "Right", MONEY, sumf("Posted"))],
       params=("MonthName",), sort=["=Fields!date.Value", "=Fields!pay.Value"])

# ---------- Debtors Ledger (ut_DebtorsLedger + ut_DebtorsLedgerTotals) ----------
# Live report: one block per customer (CustCode), no group header; last column is the unpaid value
# (Value2 when PaidDate is empty). Customer subtotals add up that unpaid value; the grand total line shows
# ut_DebtorsLedgerTotals under Value/Discount/Advertising and the summed unpaid value in the last column.
DL = "d MMM yy"
newval = "IIf(IsNothing(Fields!PaidDate.Value), Code.Nz(Fields!Value2.Value), 0D)"
cols = [Col("Office", F("OFFICE"), 6.0), Col("Date", olddate("INVOICEDate"), 1.9), Col("Invoice", F("INVOICENo"), 1.8),
        Col("Charge To", F("CUSTCODE"), 1.6, "Right"),
        Col("Value", F("Value2"), 2.4, "Right", MONEY, '=First(Fields!Value.Value, "Totals")',
            group_total=f"=Sum({newval})"),
        Col("Discount", F("Discount"), 2.2, "Right", MONEY, '=First(Fields!Discount.Value, "Totals")', group_total=sumf("Discount")),
        Col("Advertising", F("Advertising"), 2.2, "Right", MONEY, '=First(Fields!Advertising.Value, "Totals")', group_total=sumf("Advertising")),
        Col("Freight", F("Freight"), 2.0, "Right", MONEY, group_total=sumf("Freight")),
        Col("Status", F("Status"), 3.0), Col("PaidDate", olddate("PaidDate"), 1.9),
        Col("", "=" + newval, 2.2, "Right", MONEY, f"=Sum({newval})", group_total="")]
t, h = tablix(cols, totals_label="Grand Total:", sort=["=Fields!INVOICEDate.Value", "=Fields!OFFICE.Value"],
              group=dict(expr='=Fields!OFFICE.Value & "|" & Fields!CUSTCODE.Value', label=None, footer_label="",
                         sort=["=Fields!OFFICE.Value", "=Fields!CUSTCODE.Value"]))
report(OUT, "DebtorsLedger.rdlc",
       {"Main": [("OFFICE", S), ("INVOICEDate", DT), ("INVOICENo", S), ("CUSTCODE", S), ("Value2", D), ("Discount", D),
                 ("Advertising", D), ("Freight", D), ("Status", S), ("PaidDate", DT)],
        "Totals": [("Value", D), ("Discount", D), ("Advertising", D)]},
       t, h, title('="DEBTORS LEDGER"'), 1.2, code=True)

# ---------- Receipts Banked (usp_ReceiptReport) ----------
# Live layout: per customer block with the name on its first line, "Total Receipts" with a count, then the period total.
RG = "Table_RH_Group"
cols = [Col("CUSTOMER", f'=IIf(RowNumber("{RG}") = 1, Fields!OFFICE.Value, Nothing)', 6.0),
        Col("PAY ID", F("PaymentID"), 2.0, "Right", total='=Count(Fields!PaymentID.Value)'),
        Col("DATE", F("DATE"), 2.4, fmt=DATE),
        Col("GST", F("GST"), 2.4, "Right", MONEY, sumf("GST")),
        Col("ADVERTISING", F("ADVERTISING"), 2.6, "Right", MONEY, sumf("ADVERTISING")),
        Col("DISCOUNT", F("DISCOUNT"), 2.6, "Right", MONEY, sumf("DISCOUNT")),
        Col("FREIGHT", F("FREIGHT"), 2.6, "Right", MONEY, sumf("FREIGHT")),
        Col("VALUE", F("VALUE"), 2.8, "Right", MONEY, sumf("VALUE"))]
t, h = tablix(cols, name="Table_RH", totals_label="Total Receipts for Period:", sort=["=Fields!DATE.Value", "=Fields!PaymentID.Value"],
              group=dict(expr="=Fields!OFFICE.Value", label=None, footer_label="Total Receipts"))
report(OUT, "ReceiptHistoryByCustomer.rdlc",
       {"Main": [("OFFICE", S), ("PaymentID", S), ("GenLed", S), ("DATE", DT), ("CUSNUM", S), ("ADVERTISING", D), ("DISCOUNT", D),
                 ("FREIGHT", D), ("VALUE", D), ("Complete", S), ("GST", D), ("InBank", S)]},
       t, h, title('="Rinoldi Pasta: Receipts by Customer from " & Parameters!StartDate.Value & " to " & Parameters!FinishDate.Value'),
       1.2, params=("StartDate", "FinishDate"))

# ---------- Cashbook MTD (spCashBookJrnMTD + usp_TotalCancelledMTD) ----------
main_cols = [Col("ID", F("SupplierID"), 2.4), Col("GenLed", F("GenLed"), 2.0), Col("Paid Date", F("PaidDate"), 2.4, fmt=DATE),
             Col("PayRef", F("PayRef"), 2.4), Col("Name", F("Description"), 7.0),
             Col("Value", F("Value"), 3.0, "Right", MONEY, sumf("Value")), Col("GST", F("GST"), 2.6, "Right", MONEY, sumf("GST")),
             Col("Status", '=IIf(Fields!Presented.Value = True, "Presented", "")', 2.4), Col("Presented Date", F("PresentedDate"), 2.6, fmt=DATE)]
t1, h1 = tablix(main_cols, ds="Main", sort=["=Fields!PaidDate.Value", "=Fields!PayRef.Value"])
head2, top2 = section_heading('=First(Fields!Month.Value, "Main") & " Cancelled Cheques"', h1 + 0.6)
canc_cols = [Col("GenLed", F("GenLed"), 2.0), Col("Paid Date", F("mDate"), 2.4, fmt=DATE), Col("PayRef", F("PayRef"), 2.4),
             Col("Name", F("Description"), 7.0), Col("Value", F("Value"), 3.0, "Right", MONEY, sumf("Value")),
             Col("GST", F("GST"), 2.6, "Right", MONEY, sumf("GST")),
             Col("Status", '=IIf(Fields!Presented.Value = True, "Presented", "")', 2.4), Col("Presented Date", F("PresentedDate"), 2.6, fmt=DATE)]
t2, h2 = tablix(canc_cols, ds="Cancelled", top=top2, sort=["=Fields!mDate.Value"])
report(OUT, "CashBookMTD.rdlc",
       {"Main": [("SupplierID", S), ("GenLed", S), ("PaidDate", DT), ("PayRef", S), ("Description", S), ("Value", D), ("GST", D),
                 ("Presented", B), ("PresentedDate", DT), ("Month", S), ("PaymentType", S), ("is_cancelled", B)],
        "Cancelled": [("GenLed", S), ("mDate", DT), ("PayRef", S), ("Description", S), ("Value", D), ("GST", D), ("Presented", B),
                      ("PresentedDate", DT), ("PaymentType", S), ("month", S)]},
       t1 + head2 + t2, h2, title('="Cashbook For " & First(Fields!Month.Value, "Main")'), 1.2)

# ---------- Unpresented Cheques (four views) ----------
body, top = "", 0.0
pay_type = lambda f: f'=IIf(Fields!{f}.Value = 1, "Cheque", "EFT")'
sections = [
    ("Unpresented Payment", "Unpresented",
     [Col("Pay Ref", F("PayRef"), 2.6), Col("Description", F("Description"), 8.0), Col("Value", F("Value"), 3.0, "Right", MONEY, sumf("Value")),
      Col("Process Date", F("ProcessDate"), 2.6, fmt=DATE), Col("Payment Type", pay_type("PaymentType"), 2.6)], ["=Fields!ProcessDate.Value"]),
    ("Payments that are not a purchase", "NotPurchase",
     [Col("Pay Ref", F("PayRef"), 2.4), Col("Description", F("Description"), 7.0), Col("Value", F("Value"), 2.8, "Right", MONEY, sumf("Value")),
      Col("GST", F("GST"), 2.4, "Right", MONEY, sumf("GST")), Col("Paid Date", F("PaidDate"), 2.4, fmt=DATE),
      Col("Presented", yes("Presented"), 2.0, "Center"), Col("Presented Date", F("PresentedDate"), 2.6, fmt=DATE),
      Col("Payment Type", pay_type("PaymentType"), 2.6), Col("GenLed", F("GenLed"), 2.0)], ["=Fields!PaidDate.Value"]),
    ("Presented Payments Not in CashBook", "NotInCashBook",
     [Col("Tran Date", F("TRAN_DATE"), 2.6, fmt=DATE), Col("Tran Type", F("TRAN_TYPE"), 4.0),
      Col("Amount", F("Amount"), 3.0, "Right", MONEY, sumf("Amount")), Col("Tran Number", F("TRAN_NUMB"), 3.0)], ["=Fields!TRAN_DATE.Value"]),
    ("Non-Matching Cheques", "NonMatching",
     [Col("Pay Ref", F("PayRef"), 2.4), Col("Paid Date", F("PaidDate"), 2.4, fmt=DATE), Col("GenLed", F("GenLed"), 2.0),
      Col("Pay Type", pay_type("PaymentType"), 2.2), Col("Tran Date", F("TRAN_DATE"), 2.4, fmt=DATE), Col("Tran Type", F("TRAN_TYPE"), 3.4),
      Col("Value", F("Value"), 3.0, "Right", MONEY), Col("Presented Amount", F("PresentedAmount"), 3.0, "Right", MONEY),
      Col("Variation", F("Variation"), 2.8, "Right", MONEY)], ["=Fields!PaidDate.Value"]),
]
for heading, ds, cols, sort in sections:
    hx, top = section_heading(heading, top)
    t, top = tablix(cols, ds=ds, top=top, sort=sort)
    body += hx + t
    top += 0.6
report(OUT, "UnpresentedCheques.rdlc",
       {"Unpresented": [("PayRef", S), ("Description", S), ("Value", D), ("ProcessDate", DT), ("PaymentType", I), ("GST", D), ("GenLed", S),
                        ("Presented", B), ("is_cancelled", B), ("TRAN_NUMB", S)],
        "NotPurchase": [("PayRef", S), ("Description", S), ("Value", D), ("GST", D), ("PaidDate", DT), ("Presented", B),
                        ("PresentedDate", DT), ("PaymentType", I), ("GenLed", S), ("is_cancelled", B)],
        "NotInCashBook": [("TRAN_DATE", DT), ("TRAN_TYPE", S), ("Amount", D), ("TRAN_NUMB", S), ("PayRef", S), ("TRAN_IDNN", S)],
        "NonMatching": [("PayRef", S), ("PaidDate", DT), ("GenLed", S), ("PaymentType", I), ("TRAN_DATE", DT), ("TRAN_TYPE", S),
                        ("Value", D), ("PresentedAmount", D), ("Variation", D)]},
       body, top, title('="Payment Information"'), 1.2)

# ---------- Creditors Ledger EOM2 (ut_CreditorsLedgerEOM2) ----------
# Live layout: supplier name on every line, one block per supplier, totals are Sum(AccruedValue) under Accrued
# and Sum(InvValue) under Dollars; rows in invoice-date order.
cols = [Col("Office", F("SupplierDescription"), 4.5), Col("InvDate", F("InvDate"), 1.8, fmt=DATE), Col("Inv. No", F("InvoiceNo"), 1.8),
        Col("Cred #", F("SupplierID"), 1.4), Col("GenLed", F("GenLed"), 1.4), Col("D/Doc #", F("DDocket"), 1.6),
        Col("Accrued", F("Accrued"), 2.0, "Right", MONEY, sumf("AccruedValue")),
        Col("Dollars", F("InvValue"), 2.3, "Right", MONEY, sumf("InvValue")),
        Col("Month", F("mMonth"), 1.6), Col("Status", F("Status"), 1.6), Col("PaidDate", F("PaidDate"), 1.8, fmt=DATE),
        Col("Chq. No", F("Payref"), 1.6), Col("Balance", F("Balance"), 2.2, "Right", MONEY), Col("Paid in Month", F("PaidMonth"), 2.0)]
t, h = tablix(cols, totals_label="Total:", sort=["=Fields!InvDate.Value"],
              group=dict(expr="=Fields!SupplierDescription.Value", label=None, footer_label=""))
report(OUT, "CreditorsLedgerEOM2.rdlc",
       {"Main": [("SupplierDescription", S), ("InvDate", DT), ("InvoiceNo", S), ("SupplierID", S), ("GenLed", S), ("DDocket", S),
                 ("Accrued", D), ("InvValue", D), ("mMonth", S), ("Status", S), ("PaidDate", DT), ("Payref", S), ("Balance", D),
                 ("PaidMonth", S), ("AccruedValue", D), ("UnpaidValue", D), ("theMonth", S)]},
       t, h, title('="Creditors Ledger - EOM2  " & First(Fields!theMonth.Value, "Main") & " " & Year(Today().AddDays(-25))'), 1.2)

# ---------- Purchase Journal (spPurchaseJournal) ----------
month_of = lambda f: f'=IIf(IsNothing(Fields!{f}.Value), "", MonthName(Month(Fields!{f}.Value)))'
cols = [Col("Date", F("InvDate"), 1.8, fmt=DATE), Col("Cred #", F("SupplierID"), 1.5), Col("Inv #", F("InvoiceNo"), 1.9),
        Col("GenLed #", F("GenLed"), 1.6), Col("D/Doc #", F("DDocket"), 1.7), Col("Name", F("mName"), 3.2),
        Col("Value", F("InvValue"), 2.2, "Right", MONEY, sumf("InvValue")), Col("GST", F("GST"), 1.9, "Right", MONEY, sumf("GST")),
        Col("Accrued", F("Accrued"), 2.0, "Right", MONEY, sumf("Accrued")), Col("Invoiced", yes("Invoiced", "INVOICED"), 1.7),
        Col("Purchase Month", month_of("InvDate"), 1.9), Col("Status", yes("PaidStatus", "PAID"), 1.2),
        Col("Paid Date", F("PaidDate"), 1.8, fmt=DATE), Col("PayRef", F("PayRef"), 1.5), Col("Paid in Month", month_of("PaidDate"), 1.8)]
t, h = tablix(cols, sort=["=Fields!InvDate.Value", "=Fields!SupplierID.Value"])
hdr = (tb("RINOLDI PASTA PTY LTD", size="12pt", bold=True, pos=(0, 0, 14, 0.6)) +
       tb('="PURCHASE JOURNAL FOR " & UCase(Parameters!MonthName.Value) & " " & Year(Today())', size="12pt", bold=True, pos=(0.6, 0, 20, 0.7)))
report(OUT, "PurchaseJournal.rdlc",
       {"Main": [("InvDate", DT), ("SupplierID", S), ("InvoiceNo", S), ("GenLed", S), ("DDocket", S), ("mName", S), ("InvValue", D),
                 ("GST", D), ("Accrued", D), ("Invoiced", B), ("PaidStatus", B), ("PaidDate", DT), ("PayRef", S), ("Month", S)]},
       t, h, hdr, 1.4, params=("MonthName",))

# ---------- Packing Stocks Detail (SQL view ut_rptPackStockDetailMTD, as the live report) ----------
cols = [Col("PROD CODE", F("ProdCode"), 2.6), Col("DESCRIPTION", F("Description"), 7.5),
        Col("KG", F("KG"), 2.6, "Right", "#,##0", '=Format(Sum(Fields!KG.Value), "#,##0.00")'),
        Col("Units", F("Cartons"), 2.2, "Right", "#,##0", '=Format(Sum(Fields!Cartons.Value), "#,##0.00")'),
        Col("Dollars", F("Dollars"), 3.0, "Right", MONEY, sumf("Dollars")), Col("Cost", F("Cost"), 3.0, "Right", MONEY, sumf("Cost")),
        Col("Margin", F("Margin"), 3.0, "Right", MONEY, sumf("Margin")),
        Col("Margin %", F("PctMargin"), 2.2, "Right", NUM, "=Avg(Fields!PctMargin.Value)")]
t, h = tablix(cols, totals_label="Grand Total:", sort=["=Fields!ProdCode.Value"])
report(OUT, "PackingStocksDetail.rdlc",
       {"Main": [("ProdCode", S), ("Description", S), ("KG", D), ("Cartons", D), ("Dollars", D), ("Cost", D), ("Margin", D),
                 ("PctMargin", D, "% Margin")]},
       t, h, title('="Packing Stocks Detail"'), 1.2)

# ---------- Access (PackProd.mdb) reports ----------
# Total Packed Stock (with % of class) + class totals
G = "Table_TPS_Group"
cols = [Col("Length", F("LENGTH"), 3.0), Col("Date", F("DATE"), 2.4, fmt=DATE),
        Col("Stock (kg)", F("STOCK"), 3.0, "Right", NUM, sumf("STOCK")),
        Col("Kilos %", f'=Code.SafeDiv(Fields!STOCK.Value, Sum(Fields!STOCK.Value, "{G}")) * 100', 2.2, "Right", PCT,
            group_total=f'=Code.SafeDiv(Sum(Fields!STOCK.Value), Sum(Fields!STOCK.Value, "Main")) * 100'),
        Col("Cartons", F("CARTONS"), 2.8, "Right", NUM, sumf("CARTONS")),
        Col("Cartons %", f'=Code.SafeDiv(Fields!CARTONS.Value, Sum(Fields!CARTONS.Value, "{G}")) * 100', 2.2, "Right", PCT,
            group_total=f'=Code.SafeDiv(Sum(Fields!CARTONS.Value), Sum(Fields!CARTONS.Value, "Main")) * 100'),
        Col("Dollars", F("DOLLARS"), 3.0, "Right", MONEY, sumf("DOLLARS")),
        Col("Dollars %", f'=Code.SafeDiv(Fields!DOLLARS.Value, Sum(Fields!DOLLARS.Value, "{G}")) * 100', 2.2, "Right", PCT,
            group_total=f'=Code.SafeDiv(Sum(Fields!DOLLARS.Value), Sum(Fields!DOLLARS.Value, "Main")) * 100')]
for c in cols:   # class subtotal rows: plain sums for the quantity columns
    if c.header in ("Stock (kg)", "Cartons", "Dollars"):
        c.group_total = c.total
t1, h1 = tablix(cols, name="Table_TPS", totals_label="Grand Total:", sort=["=Fields!LENGTH.Value"],
                group=dict(expr="=Fields!SALESCLAS.Value", label="=Fields!SALESCLAS.Value", footer_label="Class Total"))
head2, top2 = section_heading("Totals", h1 + 0.6)
t2, h2 = tablix([Col("Class", F("CLASS"), 6.0), Col("Total Stock", F("TotalStock"), 3.0, "Right", NUM, sumf("TotalStock")),
                 Col("Total Cartons", F("TotalCartons"), 3.0, "Right", NUM, sumf("TotalCartons")),
                 Col("Total Dollars", F("TotalDollars"), 3.2, "Right", MONEY, sumf("TotalDollars"))], ds="Totals", top=top2)
report(OUT, "TotalPackedStock.rdlc",
       {"Main": [("SALESCLAS", S), ("LENGTH", S), ("DATE", DT), ("STOCK", D), ("CARTONS", D), ("DOLLARS", D)],
        "Totals": [("CLASS", S), ("TotalStock", D), ("TotalCartons", D), ("TotalDollars", D)]},
       t1 + head2 + t2, h2, title('="Total Packed Stock"'), 1.2, code=True)

# MTD Production
simple("ProdMTD.rdlc",
       {"Main": [("ProdCode", S), ("Date", DT), ("Press", S), ("Hours", D), ("Rate", D), ("Kilograms", D), ("Correction", S), ("Month", S)]},
       '="Production For " & First(Fields!Month.Value, "Main")',
       [Col("Prod Code", F("ProdCode"), 3.0), Col("Date", F("Date"), 2.6, fmt=DATE), Col("Press", F("Press"), 2.4),
        Col("Hours", F("Hours"), 2.6, "Right", NUM, sumf("Hours")), Col("Rate", F("Rate"), 2.6, "Right", NUM),
        Col("Kilograms", F("Kilograms"), 3.0, "Right", NUM, sumf("Kilograms")), Col("Correction", F("Correction"), 3.0)],
       sort=["=Fields!Date.Value", "=Fields!Press.Value"])

# Production Summary
simple("MTDProdSummary.rdlc",
       {"Main": [("Press", S), ("Hours", D), ("Kilograms", D)]},
       '="Production MTD Summary"',
       [Col("Press", F("Press"), 4.0), Col("Hours", F("Hours"), 3.5, "Right", NUM, sumf("Hours")),
        Col("Kilograms", F("Kilograms"), 3.5, "Right", NUM, sumf("Kilograms"))])
