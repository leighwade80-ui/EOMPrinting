import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from rdlgen import *
OUT = sys.argv[1]
def sumf(f): return f"=Sum(Fields!{f}.Value)"
INT, P0 = "#,##0", "0"
G = "Table_TPS_Group"
def share_of_class(f): return f'=Code.SafeDiv(Fields!{f}.Value, Sum(Fields!{f}.Value, "{G}")) * 100'
def share_of_all_line(f): return f'=Code.SafeDiv(Fields!{f}.Value, Sum(Fields!{f}.Value, "Main")) * 100'
def class_share(f): return f'=Code.SafeDiv(Sum(Fields!{f}.Value), Sum(Fields!{f}.Value, "Main")) * 100'
# Data: ut_EOM_StockSummary (the live report's qryPackST alias).
# Same percentages as the Crystal formulas: cartons % on each line is of the grand total,
# kilos % and dollars % on each line are of the class; class totals are % of the grand total.
cols = [Col("Length", F("LENGTH"), 3.4),
        Col("Cartons", F("CARTONS"), 2.8, "Right", INT, sumf("CARTONS")),
        Col("%", share_of_all_line("CARTONS"), 1.4, "Right", P0, group_total=class_share("CARTONS")),
        Col("Kilos", F("STOCK"), 3.2, "Right", NUM, sumf("STOCK")),
        Col("%", share_of_class("STOCK"), 1.4, "Right", P0, group_total=class_share("STOCK")),
        Col("Dollars", F("DOLLARS"), 3.4, "Right", MONEY, sumf("DOLLARS")),
        Col("%", share_of_class("DOLLARS"), 1.4, "Right", P0, group_total=class_share("DOLLARS"))]
for c in cols:
    if c.header in ("Cartons", "Kilos", "Dollars"):
        c.group_total = c.total
t1, h1 = tablix(cols, name="Table_TPS", totals_label="Grand Total:", sort=["=Fields!LENGTH.Value"],
                group=dict(expr="=Fields!SALESCLAS.Value", label="=Fields!SALESCLAS.Value", footer_label="Total:"))
head2, top2 = section_heading("Totals", h1 + 0.6)
# Long / Short totals from ut_EOM_StockSummaryTotals, as the live report's subreport.
t2, h2 = tablix([Col("Length", F("Length"), 3.4, total=None),
                 Col("Cartons", F("TotalCartons"), 2.8, "Right", INT, sumf("TotalCartons")),
                 Col("Kilos", F("TotalStock"), 3.2, "Right", NUM, sumf("TotalStock")),
                 Col("Dollars", F("TotalDollars"), 3.4, "Right", MONEY, sumf("TotalDollars"))],
                ds="Totals", name="Table_TPS_Totals", top=top2, totals_label="Total")
report(OUT, "TotalPackedStock.rdlc",
       {"Main": [("SALESCLAS", S, "SalesClas"), ("LENGTH", S, "Length"), ("STOCK", D, "Stock"), ("CARTONS", D, "Cartons"),
                 ("DOLLARS", D, "Dollars")],
        "Totals": [("Length", S), ("TotalCartons", D), ("TotalStock", D), ("TotalDollars", D)]},
       t1 + head2 + t2, h2, title('="Total Packed Stock"'), 1.2, code=True)
