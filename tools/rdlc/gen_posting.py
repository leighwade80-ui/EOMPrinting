import uuid, sys
from xml.sax.saxutils import escape as x
FONT="Arial"
def tb(name,value,size="9pt",bold=False,align="Left",fmt=None,border=None,width=None):
    st=f"<FontFamily>{FONT}</FontFamily><FontSize>{size}</FontSize>"
    if bold: st+="<FontWeight>Bold</FontWeight>"
    if fmt: st+=f"<Format>{x(fmt)}</Format>"
    b=""
    if border: b=f"<{border}><Style>Solid</Style><Width>1pt</Width></{border}>"
    return f"""<Textbox Name="{name}"><CanGrow>true</CanGrow><KeepTogether>true</KeepTogether><Paragraphs><Paragraph><TextRuns><TextRun><Value>{x(value)}</Value><Style>{st}</Style></TextRun></TextRuns><Style><TextAlign>{align}</TextAlign></Style></Paragraph></Paragraphs><rd:DefaultName>{name}</rd:DefaultName><Style><Border><Style>None</Style></Border>{b}<VerticalAlign>Middle</VerticalAlign><PaddingLeft>2pt</PaddingLeft><PaddingRight>2pt</PaddingRight><PaddingTop>1pt</PaddingTop><PaddingBottom>1pt</PaddingBottom></Style></Textbox>"""
def cell(t): return f"<TablixCell><CellContents>{t}</CellContents></TablixCell>"
money="#,##0.00;-#,##0.00;''"
cols=[("Description","Description","Left",11),("GenLed","Gen Led","Left",4),("Debit","Debit","Right",4),("Credit","Credit","Right",4)]
hdr="".join(cell(tb(f"Hdr{f}",t,bold=True,align=a,border="BottomBorder")) for f,t,a,w in cols)
det="".join(cell(tb(f"Val{f}", f"=Fields!{f}.Value" if f in("Description","GenLed") else f"=Sum(Fields!{f}.Value)", align=a, fmt=None if f in("Description","GenLed") else money)) for f,t,a,w in cols)
tot=cell(tb("TotLabel","Totals",bold=True,border="TopBorder"))+cell(tb("TotBlank","",border="TopBorder"))+"".join(cell(tb(f"Tot{f}",f'=Sum(Fields!{f}.Value, "PostingBlock")',bold=True,align="Right",fmt=money,border="TopBorder")) for f in("Debit","Credit"))
width=sum(c[3] for c in cols)
fields=[("Description","System.String"),("GenLed","System.String"),("Debit","System.Decimal"),("Credit","System.Decimal"),("Journal","System.String"),("Month","System.String")]
fx="".join(f"<Field Name=\"{n}\"><DataField>{n}</DataField><rd:TypeName>{t}</rd:TypeName></Field>" for n,t in fields)
def pos(t,top,left,w,h): return t.replace("<CanGrow>",f"<CanGrow>",1).replace("</Textbox>",f"<Top>{top}cm</Top><Left>{left}cm</Left><Height>{h}cm</Height><Width>{w}cm</Width></Textbox>")
# For positioned textboxes, Top/Left/Height/Width must come after Style? In RDL order within ReportItem: Name attr, then elements in any order is allowed (xs:choice unbounded). OK.
title=pos(tb("Title",'=Parameters!ReportTitle.Value &amp; " For " &amp; Parameters!MonthName.Value'.replace("&amp;","&"),size="14pt",bold=True),0,0,27.7,0.8)
printed=pos(tb("PrintedOn",'="Printed " & Format(Globals!ExecutionTime, "dd/MM/yyyy h:mm tt")',size="8pt"),0.1,0,10,0.5)
pageno=pos(tb("PageNumber",'="Page " & Globals!PageNumber & " of " & Globals!TotalPages',size="8pt",align="Right"),0.1,17.7,10,0.5)
rdl=f"""<?xml version="1.0" encoding="utf-8"?>
<Report xmlns="http://schemas.microsoft.com/sqlserver/reporting/2016/01/reportdefinition" xmlns:rd="http://schemas.microsoft.com/SQLServer/reporting/reportdesigner">
  <AutoRefresh>0</AutoRefresh>
  <DataSources><DataSource Name="EOM"><ConnectionProperties><DataProvider>System.Data.DataSet</DataProvider><ConnectString>/* Local Connection */</ConnectString></ConnectionProperties><rd:DataSourceID>{uuid.uuid4()}</rd:DataSourceID></DataSource></DataSources>
  <DataSets><DataSet Name="PostingBlock"><Query><DataSourceName>EOM</DataSourceName><CommandText>/* Local Query */</CommandText></Query><Fields>{fx}</Fields></DataSet></DataSets>
  <ReportSections>
    <ReportSection>
      <Body>
        <ReportItems>
          <Tablix Name="PostingTable">
            <TablixBody>
              <TablixColumns>{"".join(f"<TablixColumn><Width>{c[3]}cm</Width></TablixColumn>" for c in cols)}</TablixColumns>
              <TablixRows>
                <TablixRow><Height>0.6cm</Height><TablixCells>{hdr}</TablixCells></TablixRow>
                <TablixRow><Height>0.5cm</Height><TablixCells>{det}</TablixCells></TablixRow>
                <TablixRow><Height>0.6cm</Height><TablixCells>{tot}</TablixCells></TablixRow>
              </TablixRows>
            </TablixBody>
            <TablixColumnHierarchy><TablixMembers>{"<TablixMember />"*len(cols)}</TablixMembers></TablixColumnHierarchy>
            <TablixRowHierarchy>
              <TablixMembers>
                <TablixMember><KeepWithGroup>After</KeepWithGroup><RepeatOnNewPage>true</RepeatOnNewPage></TablixMember>
                <TablixMember>
                  <Group Name="Account"><GroupExpressions><GroupExpression>=Fields!Description.Value</GroupExpression><GroupExpression>=Fields!GenLed.Value</GroupExpression></GroupExpressions></Group>
                  <SortExpressions><SortExpression><Value>=Fields!Description.Value</Value></SortExpression><SortExpression><Value>=Fields!GenLed.Value</Value></SortExpression></SortExpressions>
                </TablixMember>
                <TablixMember><KeepWithGroup>Before</KeepWithGroup></TablixMember>
              </TablixMembers>
            </TablixRowHierarchy>
            <DataSetName>PostingBlock</DataSetName>
            <Top>0cm</Top><Left>0cm</Left><Height>1.7cm</Height><Width>{width}cm</Width>
            <Style><Border><Style>None</Style></Border></Style>
          </Tablix>
        </ReportItems>
        <Height>1.7cm</Height>
        <Style />
      </Body>
      <Width>27.7cm</Width>
      <Page>
        <PageHeader><Height>1.2cm</Height><PrintOnFirstPage>true</PrintOnFirstPage><PrintOnLastPage>true</PrintOnLastPage><ReportItems>{title}</ReportItems><Style /></PageHeader>
        <PageFooter><Height>0.7cm</Height><PrintOnFirstPage>true</PrintOnFirstPage><PrintOnLastPage>true</PrintOnLastPage><ReportItems>{printed}{pageno}</ReportItems><Style /></PageFooter>
        <PageHeight>21cm</PageHeight><PageWidth>29.7cm</PageWidth>
        <LeftMargin>1cm</LeftMargin><RightMargin>1cm</RightMargin><TopMargin>1cm</TopMargin><BottomMargin>1cm</BottomMargin>
        <Style />
      </Page>
    </ReportSection>
  </ReportSections>
  <ReportParameters>
    <ReportParameter Name="ReportTitle"><DataType>String</DataType><Nullable>true</Nullable><DefaultValue><Values><Value>Posting Block</Value></Values></DefaultValue><AllowBlank>true</AllowBlank><Prompt>Report title</Prompt></ReportParameter>
    <ReportParameter Name="MonthName"><DataType>String</DataType><Nullable>true</Nullable><DefaultValue><Values><Value></Value></Values></DefaultValue><AllowBlank>true</AllowBlank><Prompt>Month</Prompt></ReportParameter>
  </ReportParameters>
  <ReportParametersLayout><GridLayoutDefinition><NumberOfColumns>2</NumberOfColumns><NumberOfRows>1</NumberOfRows><CellDefinitions><CellDefinition><ColumnIndex>0</ColumnIndex><RowIndex>0</RowIndex><ParameterName>ReportTitle</ParameterName></CellDefinition><CellDefinition><ColumnIndex>1</ColumnIndex><RowIndex>0</RowIndex><ParameterName>MonthName</ParameterName></CellDefinition></CellDefinitions></GridLayoutDefinition></ReportParametersLayout>
  <rd:ReportUnitType>Cm</rd:ReportUnitType>
  <rd:ReportID>{uuid.uuid4()}</rd:ReportID>
</Report>
"""
open(sys.argv[1],'w').write(rdl)
