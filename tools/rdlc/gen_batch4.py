import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from rdlgen import *
OUT = sys.argv[1]
def sumf(f): return f"=Sum(Fields!{f}.Value)"
QTY = "#,##0.##"

# ---------- Sales Report MTD / Sales Report Costing (usp_SalesReport) ----------
sales_fields = [("INVOICENo", S), ("PRODCODE", S), ("WebDescription", S), ("INVOICEDATE", DT), ("UNITS", D), ("WGT", D),
                ("KILOS", D), ("PRICE", D), ("VALUE", D), ("DISCOUNT", D), ("GST", D), ("DELIVERYPOINT", S), ("Month", S),
                ("CusGroup", S), ("Office", S), ("Export", D), ("Cost", D), ("Margin", D), ("PctMargin", D, "% Margin")]
lead = [Col("Invoice", F("INVOICENo"), 1.8), Col("Date", olddate("INVOICEDATE", "-"), 1.9),
        Col("Product", F("PRODCODE"), 1.8), Col("", F("WebDescription"), 4.4),
        Col("Delivery Point", F("DELIVERYPOINT"), 3.0), Col("Units", F("UNITS"), 1.4, "Right", QTY),
        Col("Weight", F("WGT"), 1.6, "Right", "0"), Col("Kilos", F("KILOS"), 1.7, "Right", "0"),
        Col("Price", F("PRICE"), 1.7, "Right", MONEY), Col("Value", F("VALUE"), 2.2, "Right", MONEY, sumf("VALUE"))]
group = dict(expr='=IIf(IsNothing(Fields!CusGroup.Value), "Others", Fields!CusGroup.Value)',
             label="=Fields!Office.Value", footer_label="Totals:")
heading = '="Sales Report - " & First(Fields!Month.Value, "Main")'

cols = lead + [Col("Discount", F("DISCOUNT"), 2.0, "Right", MONEY, sumf("DISCOUNT")),
               Col("GST", F("GST"), 1.8, "Right", MONEY, sumf("GST")),
               Col("Export", F("Export"), 2.0, "Right", MONEY, sumf("Export"))]
t, h = tablix(cols, totals_label="Grand Totals:", group=group)
report(OUT, "SalesReport.rdlc", {"Main": sales_fields}, t, h, title(heading), 1.2)

cols = lead + [Col("Cost", F("Cost"), 2.0, "Right", MONEY, sumf("Cost")),
               Col("Margin", F("Margin"), 1.8, "Right", MONEY, sumf("Margin")),
               Col("% Margin", F("PctMargin"), 2.0, "Right", PCT, "=Avg(Fields!PctMargin.Value)")]
t, h = tablix(cols, totals_label="Grand Totals:", group=group)
report(OUT, "SalesReportCosting.rdlc", {"Main": sales_fields}, t, h, title(heading), 1.2)

# ---------- Expiring Discount Prices (ut_EOM_PricingExpiration) ----------
cols = [Col("DP", F("DP"), 4.5), Col("Product", F("Product"), 6.0),
        Col("Start Date", F("StartDate"), 2.6, fmt=DATE), Col("Finish Date", F("FinishDate"), 2.6, fmt=DATE),
        Col("Discount Rate", F("DiscountRate"), 2.8, "Right", PCT), Col("Price", F("Price"), 2.6, "Right", MONEY)]
t, h = tablix(cols, sort=["=Fields!DP.Value", "=Fields!Product.Value"],
              group=dict(expr="=Fields!CusNUm.Value", label='="Customer " & Fields!CusNUm.Value & "   " & Fields!Office.Value'))
report(OUT, "ExpiringPrices.rdlc",
       {"Main": [("CusNUm", S), ("Office", S), ("DP", S), ("Product", S), ("StartDate", DT), ("FinishDate", DT),
                 ("DiscountRate", D), ("Price", D)]},
       t, h, title('="Expiring Discount Prices"'), 1.2)

# ---------- PackMat Detail (ut_EOM_PackMat) ----------
cols = [Col("Code", F("Code"), 2.6), Col("Description", F("Description"), 7.5), Col("Unit", F("Unit"), 2.0),
        Col("Opening Stock", F("OpeningStock"), 2.8, "Right", QTY), Col("Used", F("Used"), 2.6, "Right", QTY),
        Col("Purchased", F("Purchased"), 2.6, "Right", QTY), Col("Corrections", F("Corrections"), 2.6, "Right", QTY),
        Col("Closing Stock", F("ClosingStock"), 2.8, "Right", QTY)]
t, h = tablix(cols, sort=["=Fields!Code.Value"])
report(OUT, "Packing Material.rdlc",
       {"Main": [("Code", S), ("Description", S), ("Unit", S), ("OpeningStock", D), ("Used", D), ("Purchased", D),
                 ("Corrections", D), ("ClosingStock", D)]},
       t, h, title('="Packing Material"'), 1.2)
