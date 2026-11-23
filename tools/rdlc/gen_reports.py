"""Generates RDLC layouts for EOM Printing. Usage: gen_reports.py <Reports folder>"""
import uuid, sys, os, itertools
import xml.dom.minidom as minidom
from xml.sax.saxutils import escape as x

OUT = sys.argv[1]
FONT = "Arial"
MONEY = "#,##0.00;(#,##0.00)"
DATE = "dd/MM/yyyy"
NUM = "#,##0.00"
_ids = itertools.count(1)

def tb(value, size="9pt", bold=False, align="Left", fmt=None, border=None, pos=None, name=None, color=None):
    name = name or f"Tb{next(_ids)}"
    st = f"<FontFamily>{FONT}</FontFamily><FontSize>{size}</FontSize>"
    if bold: st += "<FontWeight>Bold</FontWeight>"
    if fmt: st += f"<Format>{x(fmt)}</Format>"
    if color: st += f"<Color>{x(color)}</Color>"
    b = "".join(f"<{e}><Style>Solid</Style><Width>1pt</Width></{e}>" for e in (border or []))
    p = ""
    if pos:
        top, left, w, h = pos
        p = f"<Top>{top}cm</Top><Left>{left}cm</Left><Height>{h}cm</Height><Width>{w}cm</Width>"
    return (f'<Textbox Name="{name}"><CanGrow>true</CanGrow><KeepTogether>true</KeepTogether>'
            f"<Paragraphs><Paragraph><TextRuns><TextRun><Value>{x(value)}</Value><Style>{st}</Style></TextRun></TextRuns>"
            f"<Style><TextAlign>{align}</TextAlign></Style></Paragraph></Paragraphs>"
            f"<rd:DefaultName>{name}</rd:DefaultName>{p}"
            f"<Style><Border><Style>None</Style></Border>{b}<VerticalAlign>Middle</VerticalAlign>"
            f"<PaddingLeft>2pt</PaddingLeft><PaddingRight>2pt</PaddingRight><PaddingTop>1pt</PaddingTop><PaddingBottom>1pt</PaddingBottom></Style></Textbox>")

def cell(t): return f"<TablixCell><CellContents>{t}</CellContents></TablixCell>"

class Col:
    def __init__(self, header, value, width, align="Left", fmt=None, total=None):
        self.header, self.value, self.width, self.align, self.fmt, self.total = header, value, width, align, fmt, total

def F(name): return f"=Fields!{name}.Value"
def first(name, ds="Main"): return f'First(Fields!{name}.Value, "{ds}")'

def tablix(cols, ds="Main", totals_label="Totals:", top=0.0, name="MainTable", sort=None):
    hdr = "".join(cell(tb(c.header, bold=True, align=c.align, border=["BottomBorder"])) for c in cols)
    det = "".join(cell(tb(c.value, align=c.align, fmt=c.fmt)) for c in cols)
    has_total = any(c.total for c in cols)
    rows = f"<TablixRow><Height>0.6cm</Height><TablixCells>{hdr}</TablixCells></TablixRow>"
    rows += f"<TablixRow><Height>0.5cm</Height><TablixCells>{det}</TablixCells></TablixRow>"
    members = '<TablixMember><KeepWithGroup>After</KeepWithGroup><RepeatOnNewPage>true</RepeatOnNewPage></TablixMember>'
    sort_xml = ""
    if sort:
        sort_xml = "<SortExpressions>" + "".join(f"<SortExpression><Value>{x(s)}</Value></SortExpression>" for s in sort) + "</SortExpressions>"
    members += f'<TablixMember><Group Name="{name}Details" />{sort_xml}</TablixMember>'
    if has_total:
        tcells = []
        label_done = False
        for c in cols:
            if c.total:
                tcells.append(cell(tb(c.total, bold=True, align=c.align, fmt=c.fmt, border=["TopBorder"])))
            elif not label_done:
                tcells.append(cell(tb(totals_label, bold=True, border=["TopBorder"]))); label_done = True
            else:
                tcells.append(cell(tb("", border=["TopBorder"])))
        rows += f"<TablixRow><Height>0.6cm</Height><TablixCells>{''.join(tcells)}</TablixCells></TablixRow>"
        members += "<TablixMember><KeepWithGroup>Before</KeepWithGroup></TablixMember>"
    width = sum(c.width for c in cols)
    height = 1.7 if has_total else 1.1
    xml = (f'<Tablix Name="{name}"><TablixBody><TablixColumns>'
           + "".join(f"<TablixColumn><Width>{c.width}cm</Width></TablixColumn>" for c in cols)
           + f"</TablixColumns><TablixRows>{rows}</TablixRows></TablixBody>"
           + "<TablixColumnHierarchy><TablixMembers>" + "<TablixMember />" * len(cols) + "</TablixMembers></TablixColumnHierarchy>"
           + f"<TablixRowHierarchy><TablixMembers>{members}</TablixMembers></TablixRowHierarchy>"
           + f"<DataSetName>{ds}</DataSetName><Top>{top}cm</Top><Left>0cm</Left><Height>{height}cm</Height><Width>{width}cm</Width>"
           + "<Style><Border><Style>None</Style></Border></Style></Tablix>")
    return xml, top + height, width

def footer():
    return (tb('="Printed " & Format(Globals!ExecutionTime, "dd/MM/yyyy h:mm tt")', size="8pt", pos=(0.1, 0, 10, 0.5), name="PrintedOn")
            + tb('="Page " & Globals!PageNumber & " of " & Globals!TotalPages', size="8pt", align="Right", pos=(0.1, 17.7, 10, 0.5), name="PageNumber"))

NZ_CODE = """Public Function Nz(ByVal v As Object) As Decimal
    If v Is Nothing OrElse IsDBNull(v) Then Return 0D
    Return CDec(v)
End Function"""

def report(filename, fields, body_items, body_height, header_items, header_height, params=(), code=None, ds="Main"):
    fx = "".join(f'<Field Name="{n}"><DataField>{n}</DataField><rd:TypeName>{t}</rd:TypeName></Field>' for n, t in fields)
    pxml = ""
    if params:
        pxml = "<ReportParameters>" + "".join(
            f'<ReportParameter Name="{p}"><DataType>String</DataType><Nullable>true</Nullable>'
            f"<DefaultValue><Values><Value></Value></Values></DefaultValue><AllowBlank>true</AllowBlank><Prompt>{p}</Prompt></ReportParameter>"
            for p in params) + "</ReportParameters>"
        pxml += ("<ReportParametersLayout><GridLayoutDefinition>"
                 f"<NumberOfColumns>{len(params)}</NumberOfColumns><NumberOfRows>1</NumberOfRows><CellDefinitions>"
                 + "".join(f"<CellDefinition><ColumnIndex>{i}</ColumnIndex><RowIndex>0</RowIndex><ParameterName>{p}</ParameterName></CellDefinition>" for i, p in enumerate(params))
                 + "</CellDefinitions></GridLayoutDefinition></ReportParametersLayout>")
    cxml = f"<Code>{x(code)}</Code>" if code else ""
    rdl = f"""<?xml version="1.0" encoding="utf-8"?>
<Report xmlns="http://schemas.microsoft.com/sqlserver/reporting/2016/01/reportdefinition" xmlns:rd="http://schemas.microsoft.com/SQLServer/reporting/reportdesigner">
<AutoRefresh>0</AutoRefresh>
<DataSources><DataSource Name="EOM"><ConnectionProperties><DataProvider>System.Data.DataSet</DataProvider><ConnectString>/* Local Connection */</ConnectString></ConnectionProperties><rd:DataSourceID>{uuid.uuid4()}</rd:DataSourceID></DataSource></DataSources>
<DataSets><DataSet Name="{ds}"><Query><DataSourceName>EOM</DataSourceName><CommandText>/* Local Query */</CommandText></Query><Fields>{fx}</Fields></DataSet></DataSets>
<ReportSections><ReportSection>
<Body><ReportItems>{body_items}</ReportItems><Height>{body_height:.2f}cm</Height><Style /></Body>
<Width>27.7cm</Width>
<Page>
<PageHeader><Height>{header_height}cm</Height><PrintOnFirstPage>true</PrintOnFirstPage><PrintOnLastPage>true</PrintOnLastPage><ReportItems>{header_items}</ReportItems><Style /></PageHeader>
<PageFooter><Height>0.7cm</Height><PrintOnFirstPage>true</PrintOnFirstPage><PrintOnLastPage>true</PrintOnLastPage><ReportItems>{footer()}</ReportItems><Style /></PageFooter>
<PageHeight>21cm</PageHeight><PageWidth>29.7cm</PageWidth>
<LeftMargin>1cm</LeftMargin><RightMargin>1cm</RightMargin><TopMargin>1cm</TopMargin><BottomMargin>1cm</BottomMargin>
<Style />
</Page>
</ReportSection></ReportSections>
{pxml}{cxml}
<rd:ReportUnitType>Cm</rd:ReportUnitType>
<rd:ReportID>{uuid.uuid4()}</rd:ReportID>
</Report>
"""
    pretty = minidom.parseString(rdl.encode()).toprettyxml(indent="  ", encoding="utf-8").decode()
    with open(os.path.join(OUT, filename), "w", encoding="utf-8", newline="\r\n") as fh:
        fh.write(pretty)
    print("wrote", filename)

def title(expr, top=0, size="14pt"):
    return tb(expr, size=size, bold=True, pos=(top, 0, 27.7, 0.8))

def simple(filename, fields, heading_expr, cols, params=(), code=None, sort=None):
    t, h, _ = tablix(cols, sort=sort)
    report(filename, fields, t, h, title(heading_expr), 1.2, params, code)

S, D, DT, B, I = "System.String", "System.Decimal", "System.DateTime", "System.Boolean", "System.Int32"
yes = lambda f: f'=IIf(Fields!{f}.Value = True, "Yes", "")'

# ---- EFT Transfer (spEFT) ----
simple("EFT.rdlc",
       [("GenLed", S), ("PaidDate", DT), ("PayRef", S), ("Description", S), ("SumInvValue", D), ("GST", D),
        ("Presented", B), ("PresentedDate", DT), ("EFT_Transmitted", S), ("Month", S)],
       '="EFT For " & Parameters!MonthName.Value',
       [Col("G/L", F("GenLed"), 2.2), Col("Paid Date", F("PaidDate"), 2.4, fmt=DATE), Col("Pay Ref", F("PayRef"), 2.6),
        Col("Name", F("Description"), 7.5), Col("Value", F("SumInvValue"), 2.8, "Right", MONEY, "=Sum(Fields!SumInvValue.Value)"),
        Col("GST", F("GST"), 2.4, "Right", MONEY, "=Sum(Fields!GST.Value)"), Col("Presented", F("Presented"), 2.0, "Center"),
        Col("Presented Date", F("PresentedDate"), 2.8, fmt=DATE), Col("EFT Transmitted", F("EFT_Transmitted"), 3.0)],
       params=("MonthName",))

# ---- Petty Cash Journal (spPettyCashJrn) ----
simple("PettyCashJournal.rdlc",
       [("GenLed", S), ("PettyCashID", S), ("Description", S), ("mDate", DT), ("mValue", D), ("mGST", D),
        ("PayRef", S), ("PaidStatus", B), ("FirstName", S), ("LastName", S), ("Month", S), ("ReportName", S)],
       '="Petty Cash Journal For " & Parameters!MonthName.Value',
       [Col("Gen Led", F("GenLed"), 2.2), Col("ID", F("PettyCashID"), 1.8), Col("Description", F("Description"), 7.5),
        Col("Date", F("mDate"), 2.4, fmt=DATE), Col("Value", F("mValue"), 2.8, "Right", MONEY, "=Sum(Fields!mValue.Value)"),
        Col("GST", F("mGST"), 2.4, "Right", MONEY, "=Sum(Fields!mGST.Value)"), Col("Pay Ref", F("PayRef"), 2.4),
        Col("Paid", yes("PaidStatus"), 1.6, "Center"), Col("Employee", '=Fields!FirstName.Value & " " & Fields!LastName.Value', 4.6)],
       params=("MonthName",))

# ---- Packing Summary (ut_rptMTDPackingSummary) ----
simple("PackingMTDSummary.rdlc",
       [("PRESS", S), ("Kilos", D), ("SRMD", D), ("PackMat", D)],
       "=\"Packing MTD Summary\"",
       [Col("Press", F("PRESS"), 4), Col("Kilos", F("Kilos"), 3.5, "Right", NUM, "=Sum(Fields!Kilos.Value)"),
        Col("SRM $", F("SRMD"), 3.5, "Right", MONEY, "=Sum(Fields!SRMD.Value)"),
        Col("Packing $", F("PackMat"), 3.5, "Right", MONEY, "=Sum(Fields!PackMat.Value)")])

# ---- MTD Packing (ut_rptPackingMTD) ----
simple("packingMTDAll.rdlc",
       [("ProdCode", S), ("DESCRIPTION", S), ("Kilos", D), ("Date", DT), ("Correction", S), ("SRMD", D),
        ("PackMat", D), ("Press", S), ("DieCode", S), ("Month", S), ("CurrentMonth", S)],
       '="Packing For " & First(Fields!CurrentMonth.Value, "Main")',
       [Col("Product", F("ProdCode"), 2.4), Col("Description", F("DESCRIPTION"), 7.0),
        Col("Quantity", F("Kilos"), 2.6, "Right", NUM, "=Sum(Fields!Kilos.Value)"), Col("Date", F("Date"), 2.4, fmt=DATE),
        Col("Correction", F("Correction"), 2.4), Col("SRM $", F("SRMD"), 2.6, "Right", MONEY, "=Sum(Fields!SRMD.Value)"),
        Col("Packaging $", F("PackMat"), 2.8, "Right", MONEY, "=Sum(Fields!PackMat.Value)"),
        Col("Press", F("Press"), 2.0), Col("Die Code", F("DieCode"), 2.4)],
       sort=["=Fields!Date.Value", "=Fields!ProdCode.Value"])

# ---- Debtors Age Analysis (ut_rptDebtorsAgeEOM) ----
simple("DebtorsAgeAnalysis.rdlc",
       [("CUSNUM", S), ("OFFICE", S), ("Previous", D), ("TwoMonthsAgo", D), ("Last", D), ("Current", D), ("TotalValue", D),
        ("TwoMonthsAgoMonth", S), ("LastMonth", S), ("CurrentMonth", S)],
       '="Debtors Age Analysis"',
       [Col("No.", F("CUSNUM"), 2.4), Col("Office", F("OFFICE"), 8.0),
        Col("Previous", F("Previous"), 3.2, "Right", MONEY, "=Sum(Fields!Previous.Value)"),
        Col('=First(Fields!TwoMonthsAgoMonth.Value, "Main")', F("TwoMonthsAgo"), 3.2, "Right", MONEY, "=Sum(Fields!TwoMonthsAgo.Value)"),
        Col('=First(Fields!LastMonth.Value, "Main")', F("Last"), 3.2, "Right", MONEY, "=Sum(Fields!Last.Value)"),
        Col('=First(Fields!CurrentMonth.Value, "Main")', F("Current"), 3.2, "Right", MONEY, "=Sum(Fields!Current.Value)"),
        Col("Total", F("TotalValue"), 3.4, "Right", MONEY, "=Sum(Fields!TotalValue.Value)")],
       sort=["=Fields!OFFICE.Value"])

# ---- Creditors Age Analysis EOM2 (ut_RptCAAEOM2) ----
total4 = "Code.Nz(Fields!Previous.Value) + Code.Nz(Fields!TwoMonthsAgo.Value) + Code.Nz(Fields!LastMonth.Value) + Code.Nz(Fields!CurrentMonth.Value)"
simple("CreditorsAgeAnalysisEOM2.rdlc",
       [("SupplierID", S), ("mNAME", S), ("Previous", D), ("TwoMonthsAgo", D), ("LastMonth", D), ("CurrentMonth", D),
        ("currMonth", S), ("LasMonth", S), ("TwoMnthAgo", S), ("Payment", D)],
       '="Creditors Age Analysis - EOM2    " & First(Fields!currMonth.Value, "Main") & "  " & Year(Today())',
       [Col("ID", F("SupplierID"), 2.0), Col("Supplier", F("mNAME"), 6.6),
        Col("Previous", F("Previous"), 3.0, "Right", MONEY, "=Sum(Fields!Previous.Value)"),
        Col('=First(Fields!TwoMnthAgo.Value, "Main")', F("TwoMonthsAgo"), 3.0, "Right", MONEY, "=Sum(Fields!TwoMonthsAgo.Value)"),
        Col('=First(Fields!LasMonth.Value, "Main")', F("LastMonth"), 3.0, "Right", MONEY, "=Sum(Fields!LastMonth.Value)"),
        Col('=First(Fields!currMonth.Value, "Main")', F("CurrentMonth"), 3.0, "Right", MONEY, "=Sum(Fields!CurrentMonth.Value)"),
        Col("Total", "=" + total4, 3.2, "Right", MONEY, "=Sum(" + total4 + ")"),
        Col("Payment", F("Payment"), 3.0, "Right", MONEY)],
       code=NZ_CODE, sort=["=Fields!mNAME.Value"])

# ---- Bank Transactions (ut_RptBankTransactionsMTD) ----
bt_fields = [("TRAN_DATE", DT), ("TRAN_TYPE", S), ("TRAN_REF", S), ("Debit", D), ("Credit", D),
             ("StartingDate", DT), ("FinishingDate", DT), ("OpeningBalance", D), ("ClosingBalance", D)]
bt_cols = [Col("Date", F("TRAN_DATE"), 2.6, fmt=DATE), Col("Tran Type", F("TRAN_TYPE"), 4.0),
           Col("Agnt/Chq/Ref/No", F("TRAN_REF"), 6.0),
           Col("Debit", "=IIf(IsNothing(Fields!Debit.Value), Nothing, Math.Abs(CDec(Fields!Debit.Value)))", 3.4, "Right", MONEY,
               "=Sum(IIf(IsNothing(Fields!Debit.Value), 0D, Math.Abs(CDec(Fields!Debit.Value))))"),
           Col("Credit", F("Credit"), 3.4, "Right", MONEY, "=Sum(Fields!Credit.Value)")]
t, h, w = tablix(bt_cols, sort=["=Fields!TRAN_DATE.Value"])
sumtop = h + 0.3
summary = (
    tb("Transactions", bold=True, pos=(sumtop, 0, 4, 0.5)) + tb('=Count(Fields!TRAN_DATE.Value, "Main")', align="Right", pos=(sumtop, 4, 2, 0.5)) +
    tb("Debits", bold=True, pos=(sumtop + 0.5, 0, 4, 0.5)) + tb('=Count(Fields!Debit.Value, "Main")', align="Right", pos=(sumtop + 0.5, 4, 2, 0.5)) +
    tb("Credits", bold=True, pos=(sumtop + 1.0, 0, 4, 0.5)) + tb('=Count(Fields!Credit.Value, "Main")', align="Right", pos=(sumtop + 1.0, 4, 2, 0.5)) +
    tb("Closing Balance", bold=True, pos=(sumtop, 12.6, 3.4, 0.5)) +
    tb('=First(Fields!ClosingBalance.Value, "Main")', bold=True, align="Right", fmt=MONEY, pos=(sumtop, 16.0, 3.4, 0.5)))
hdr = (tb("Rinoldi Pasta Pty Ltd", size="14pt", bold=True, pos=(0, 0, 14, 0.8)) +
       tb('="Statement Report as at " & Format(First(Fields!FinishingDate.Value, "Main"), "dd/MM/yyyy")', size="11pt", bold=True, align="Right", pos=(0, 13.7, 14, 0.8)) +
       tb("Acct No: 06300-0190346 Rinoldi Pasta Pty Ltd", pos=(0.9, 0, 14, 0.5)) +
       tb("Account / Sub Account Details", pos=(1.4, 0, 8, 0.5)) + tb("Currency: AUD", pos=(1.4, 8, 6, 0.5)) +
       tb('="From " & Format(First(Fields!StartingDate.Value, "Main"), "dd/MM/yyyy") & " to " & Format(First(Fields!FinishingDate.Value, "Main"), "dd/MM/yyyy")', pos=(1.9, 0, 10, 0.5)) +
       tb("Opening Balance", bold=True, pos=(1.9, 12.6, 3.4, 0.5)) +
       tb('=First(Fields!OpeningBalance.Value, "Main")', bold=True, align="Right", fmt=MONEY, pos=(1.9, 16.0, 3.4, 0.5)))
report("BankTransactionsMTD.rdlc", bt_fields, t + summary, sumtop + 1.6, hdr, 2.6)

# ---- Bank Reconciliation (ut_rptBankReconciliation): one row, laid out as a form ----
br_fields = [("UnpresentedChequesValue", D), ("CashBookValue", D), ("ReceiptBookValue", D), ("ReceiptBookLastUpdate", DT),
             ("CashBookLastUpdated", DT), ("StartingDate", DT), ("FinishingDate", DT), ("OpeningBalance", D),
             ("ClosingBalance", D), ("Unpresented", D), ("CurrentMonth", S), ("BankCreditValue", D), ("BankDebitValue", D),
             ("UnpresentedVChequeLastUpdate", DT), ("LastMonth", S)]
def v(f): return f'Code.Nz(First(Fields!{f}.Value, "Main"))'
open_bal = f"({v('OpeningBalance')} - {v('Unpresented')})"
close_bal = f"({open_bal} - {v('CashBookValue')} + {v('ReceiptBookValue')})"
close_calc = f"({v('ClosingBalance')} - {v('UnpresentedChequesValue')})"
variation = f"({close_bal} - {close_calc})"
bank_date = 'IIf(Today() < First(Fields!FinishingDate.Value, "Main"), Today(), First(Fields!FinishingDate.Value, "Main"))'
L, V = 0.0, 8.0   # label column, value column
rows = [
    ("#", "Rinoldi"),
    ("Opening Balance", "=" + open_bal),
    ("Cheques Drawn + Charges", "=" + v("CashBookValue")),
    ("Deposits To", "=" + v("ReceiptBookValue")),
    ("Closing Balance", "=" + close_bal),
    (None, None),
    ("#", "Bank"),
    ('="Balance At Bank as at " & Format(' + bank_date + ', "dd/MM/yyyy")', "=" + v("ClosingBalance")),
    ("Unpresented Cheques", "=" + v("UnpresentedChequesValue")),
    ("Closing Balance", "=" + close_calc),
    (None, None),
    ("Variations", "=" + variation),
]
body = ""
top = 0.0
for label, expr in rows:
    if label is None:
        top += 0.3; continue
    if label == "#":
        body += tb(expr, bold=True, align="Right", pos=(top, V, 3.6, 0.5), border=["BottomBorder"])
        top += 0.6; continue
    body += tb(label, bold=label.startswith("Closing") or label == "Variations", pos=(top, L, 8, 0.55))
    body += tb(expr, align="Right", fmt=MONEY, bold=label.startswith("Closing") or label == "Variations", pos=(top, V, 3.6, 0.55))
    top += 0.6
body += tb(f'=IIf({variation} <> 0, "ERROR", "MAGIC")', size="12pt", bold=True, align="Center",
           pos=(top - 0.6, 12.0, 3.0, 0.6), color=f'=IIf({variation} <> 0, "Red", "Green")')
# Source figures, as printed in the old report's lower block
top += 0.6
body += tb("Source figures", size="10pt", bold=True, pos=(top, 0, 8, 0.6), border=["BottomBorder"]); top += 0.8
body += tb("Value", bold=True, align="Right", pos=(top, 6.0, 3.4, 0.5)) + tb("Last Updated", bold=True, align="Right", pos=(top, 9.6, 3.4, 0.5)); top += 0.5
for label, val, upd in [("Receipt Book", "ReceiptBookValue", "ReceiptBookLastUpdate"),
                        ("Cashbook", "CashBookValue", "CashBookLastUpdated"),
                        ("Unpresented Cheques", "UnpresentedChequesValue", "UnpresentedVChequeLastUpdate"),
                        ("Bank Credit", "BankCreditValue", None),
                        ("Bank Debit", "BankDebitValue", None)]:
    body += tb(label, pos=(top, 0, 6, 0.5))
    body += tb(f'=First(Fields!{val}.Value, "Main")', align="Right", fmt=MONEY, pos=(top, 6.0, 3.4, 0.5))
    if upd: body += tb(f'=First(Fields!{upd}.Value, "Main")', align="Right", fmt="dd/MM/yyyy h:mm tt", pos=(top, 9.6, 3.4, 0.5))
    top += 0.5
top += 0.3
for label, expr, fmt in [("Current Month", '=First(Fields!CurrentMonth.Value, "Main")', None),
                         ("Last Month", '=First(Fields!LastMonth.Value, "Main")', None),
                         ("Starting Date", '=First(Fields!StartingDate.Value, "Main")', DATE),
                         ("Finishing Date", '=First(Fields!FinishingDate.Value, "Main")', DATE),
                         ("Opening Balance (bank)", '=First(Fields!OpeningBalance.Value, "Main")', MONEY),
                         ("Closing Balance (bank)", '=First(Fields!ClosingBalance.Value, "Main")', MONEY),
                         ("Unpresented (start of month)", '=First(Fields!Unpresented.Value, "Main")', MONEY)]:
    body += tb(label, pos=(top, 0, 6, 0.5)) + tb(expr, align="Right", fmt=fmt, pos=(top, 6.0, 3.4, 0.5))
    top += 0.5
hdr = (tb("RINOLDI PASTA PTY LTD", size="14pt", bold=True, pos=(0, 0, 14, 0.8)) +
       tb('="Run Date " & Format(Globals!ExecutionTime, "dd/MM/yyyy h:mm tt")', size="8pt", align="Right", pos=(0, 17.7, 10, 0.5)) +
       tb('="Bank Reconciliation for the Month of " & First(Fields!CurrentMonth.Value, "Main")', size="12pt", bold=True, pos=(0.8, 0, 20, 0.7)))
report("BankReconciliation.rdlc", br_fields, body, top + 0.2, hdr, 1.8, code=NZ_CODE)
