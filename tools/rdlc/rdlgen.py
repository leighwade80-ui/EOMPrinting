"""Helpers for generating RDLC layouts (2016 schema)."""
import uuid, os, itertools
import xml.dom.minidom as minidom
from xml.sax.saxutils import escape as x

FONT = "Arial"
MONEY = "#,##0.00;(#,##0.00)"
DATE = "dd/MM/yyyy"
NUM = "#,##0.00"
PCT = "0.00"
S, D, DT, B, I = "System.String", "System.Decimal", "System.DateTime", "System.Boolean", "System.Int32"
_ids = itertools.count(1)

CODE = """Public Function Nz(ByVal v As Object) As Decimal
    If v Is Nothing OrElse IsDBNull(v) Then Return 0D
    Return CDec(v)
End Function

Public Function SafeDiv(ByVal a As Object, ByVal b As Object) As Decimal
    Dim d As Decimal = Nz(b)
    If d = 0D Then Return 0D
    Return Nz(a) / d
End Function"""

def tb(value, size="8pt", bold=False, align="Left", fmt=None, border=None, pos=None, name=None, color=None, bg=None):
    name = name or f"Tb{next(_ids)}"
    st = f"<FontFamily>{FONT}</FontFamily><FontSize>{size}</FontSize>"
    if bold: st += "<FontWeight>Bold</FontWeight>"
    if fmt: st += f"<Format>{x(fmt)}</Format>"
    if color: st += f"<Color>{x(color)}</Color>"
    b = "".join(f"<{e}><Style>Solid</Style><Width>1pt</Width></{e}>" for e in (border or []))
    bgx = f"<BackgroundColor>{bg}</BackgroundColor>" if bg else ""
    p = ""
    if pos:
        top, left, w, h = pos
        p = f"<Top>{top}cm</Top><Left>{left}cm</Left><Height>{h}cm</Height><Width>{w}cm</Width>"
    return (f'<Textbox Name="{name}"><CanGrow>true</CanGrow><KeepTogether>true</KeepTogether>'
            f"<Paragraphs><Paragraph><TextRuns><TextRun><Value>{x(value)}</Value><Style>{st}</Style></TextRun></TextRuns>"
            f"<Style><TextAlign>{align}</TextAlign></Style></Paragraph></Paragraphs>"
            f"<rd:DefaultName>{name}</rd:DefaultName>{p}"
            f"<Style><Border><Style>None</Style></Border>{b}{bgx}<VerticalAlign>Middle</VerticalAlign>"
            f"<PaddingLeft>2pt</PaddingLeft><PaddingRight>2pt</PaddingRight><PaddingTop>1pt</PaddingTop><PaddingBottom>1pt</PaddingBottom></Style></Textbox>")

def cell(t, span=1):
    cs = f"<ColSpan>{span}</ColSpan>" if span > 1 else ""
    return f"<TablixCell><CellContents>{t}{cs}</CellContents></TablixCell>" + "<TablixCell />" * (span - 1)

class Col:
    def __init__(self, header, value, width, align="Left", fmt=None, total=None, group_total=None):
        self.header, self.value, self.width, self.align, self.fmt = header, value, width, align, fmt
        self.total = total
        # Group subtotal defaults to the same aggregate as the grand total, without a dataset scope.
        self.group_total = group_total if group_total is not None else total

def F(name): return f"=Fields!{name}.Value"
def olddate(name, sep=" "):
    """Date the way the Crystal reports printed it, e.g. 6 Nov 26 (always Sep, never Sept)."""
    v = f"Fields!{name}.Value"
    return (f'=IIf(IsNothing({v}), "", Day({v}) & "{sep}" & Left(MonthName(Month({v})), 3) & "{sep}" & Format({v}, "yy"))')
def yes(f, word="Yes"): return f'=IIf(Fields!{f}.Value = True, "{word}", "")'

def _total_row(cols, label, attr, bold=True, border="TopBorder", bg=None):
    cells, label_done = [], False
    for c in cols:
        v = getattr(c, attr)
        if v:
            cells.append(cell(tb(v, bold=bold, align=c.align, fmt=c.fmt, border=[border], bg=bg)))
        elif not label_done:
            cells.append(cell(tb(label, bold=bold, border=[border], bg=bg))); label_done = True
        else:
            cells.append(cell(tb("", border=[border], bg=bg)))
    return "".join(cells)

def tablix(cols, ds="Main", name=None, top=0.0, sort=None, group=None, totals_label="Totals:", left=0.0):
    """group = dict(expr=..., label=..., footer_label=..., sort=...) for one grouping level."""
    name = name or f"Table{next(_ids)}"
    n = len(cols)
    rows = [("0.55cm", "".join(cell(tb(c.header, bold=True, align=c.align, border=["BottomBorder"])) for c in cols))]
    detail_row = ("0.45cm", "".join(cell(tb(c.value, align=c.align, fmt=c.fmt)) for c in cols))
    sort_xml = ""
    if sort:
        sort_xml = "<SortExpressions>" + "".join(f"<SortExpression><Value>{x(s)}</Value></SortExpression>" for s in sort) + "</SortExpressions>"
    head_member = "<TablixMember><KeepWithGroup>After</KeepWithGroup><RepeatOnNewPage>true</RepeatOnNewPage></TablixMember>"
    detail_member = f'<TablixMember><Group Name="{name}_Details" />{sort_xml}</TablixMember>'
    if group:
        gname = f"{name}_Group"
        members = head_member
        inner = ""
        if group.get("label"):
            rows.append(("0.55cm", cell(tb(group["label"], bold=True, size="9pt", border=["BottomBorder"]), n)))
            inner = "<TablixMember><KeepWithGroup>After</KeepWithGroup></TablixMember>"
        rows.append(detail_row)
        inner += detail_member
        if any(c.group_total for c in cols):
            rows.append(("0.5cm", _total_row(cols, group.get("footer_label", "Total"), "group_total", border="TopBorder")))
            inner += "<TablixMember><KeepWithGroup>Before</KeepWithGroup></TablixMember>"
        gsort = "".join(f"<SortExpression><Value>{x(s)}</Value></SortExpression>" for s in group.get("sort", [group["expr"]]))
        members += (f'<TablixMember><Group Name="{gname}"><GroupExpressions><GroupExpression>{x(group["expr"])}</GroupExpression></GroupExpressions></Group>'
                    f"<SortExpressions>{gsort}</SortExpressions><TablixMembers>{inner}</TablixMembers></TablixMember>")
    else:
        rows.append(detail_row)
        members = head_member + detail_member
    if any(c.total for c in cols):
        rows.append(("0.6cm", _total_row(cols, totals_label, "total", border="TopBorder")))
        members += "<TablixMember><KeepWithGroup>Before</KeepWithGroup></TablixMember>"
    height = sum(float(h[:-2]) for h, _ in rows)
    width = sum(c.width for c in cols)
    xml = (f'<Tablix Name="{name}"><TablixBody><TablixColumns>'
           + "".join(f"<TablixColumn><Width>{c.width}cm</Width></TablixColumn>" for c in cols)
           + "</TablixColumns><TablixRows>"
           + "".join(f"<TablixRow><Height>{h}</Height><TablixCells>{cs}</TablixCells></TablixRow>" for h, cs in rows)
           + "</TablixRows></TablixBody>"
           + "<TablixColumnHierarchy><TablixMembers>" + "<TablixMember />" * n + "</TablixMembers></TablixColumnHierarchy>"
           + f"<TablixRowHierarchy><TablixMembers>{members}</TablixMembers></TablixRowHierarchy>"
           + f"<DataSetName>{ds}</DataSetName><Top>{top:.2f}cm</Top><Left>{left}cm</Left><Height>{height:.2f}cm</Height><Width>{width:.2f}cm</Width>"
           + "<Style><Border><Style>None</Style></Border></Style></Tablix>")
    assert width <= 27.71, (name, width)
    return xml, top + height

def footer():
    return (tb('="Printed " & Format(Globals!ExecutionTime, "dd/MM/yyyy h:mm tt")', pos=(0.1, 0, 10, 0.5), name="PrintedOn")
            + tb('="Page " & Globals!PageNumber & " of " & Globals!TotalPages', align="Right", pos=(0.1, 17.7, 10, 0.5), name="PageNumber"))

def title(expr, top=0, size="14pt", width=27.7):
    return tb(expr, size=size, bold=True, pos=(top, 0, width, 0.8))

def section_heading(text, top):
    return tb(text, size="11pt", bold=True, pos=(top, 0, 20, 0.7)), top + 0.8

def field_xml(fields):
    out = ""
    for f in fields:
        if len(f) == 2: name, t = f; data = name
        else: name, t, data = f
        out += f'<Field Name="{name}"><DataField>{x(data)}</DataField><rd:TypeName>{t}</rd:TypeName></Field>'
    return out

def report(out_dir, filename, datasets, body_items, body_height, header_items, header_height, params=(), code=False):
    """datasets = {name: [(field, type) or (field, type, datafield)]}"""
    ds_xml = "".join(
        f'<DataSet Name="{n}"><Query><DataSourceName>EOM</DataSourceName><CommandText>/* Local Query */</CommandText></Query><Fields>{field_xml(fs)}</Fields></DataSet>'
        for n, fs in datasets.items())
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
    cxml = f"<Code>{x(CODE)}</Code>" if code else ""
    rdl = f"""<?xml version="1.0" encoding="utf-8"?>
<Report xmlns="http://schemas.microsoft.com/sqlserver/reporting/2016/01/reportdefinition" xmlns:rd="http://schemas.microsoft.com/SQLServer/reporting/reportdesigner">
<AutoRefresh>0</AutoRefresh>
<DataSources><DataSource Name="EOM"><ConnectionProperties><DataProvider>System.Data.DataSet</DataProvider><ConnectString>/* Local Connection */</ConnectString></ConnectionProperties><rd:DataSourceID>{uuid.uuid4()}</rd:DataSourceID></DataSource></DataSources>
<DataSets>{ds_xml}</DataSets>
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
    with open(os.path.join(out_dir, filename), "w", encoding="utf-8", newline="\r\n") as fh:
        fh.write(pretty)
    print("wrote", filename)
