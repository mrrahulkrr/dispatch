from fastmcp import FastMCP

# US Tools
from tools.congress import search_bills, get_bill_detail
from tools.regulations import search_regulations, get_docket_comments
from tools.federal_register import search_federal_register, search_presidential_documents
from tools.arxiv import search_arxiv
from tools.sec import search_sec_filings

# UK Tools
from tools.uk_parliament import search_uk_bills, get_uk_bill_detail
from tools.uk_legislation import search_uk_legislation, search_uk_statutory_instruments
from tools.companies_house import search_companies_house

# Canada, EU, India Tools
from tools.canada_parliament import search_canada_bills
from tools.eu_journal import search_eu_official_journal
from tools.india_markets import search_nse_announcements

# Create a FastMCP server
mcp = FastMCP("dispatch-tools")

# ---- US Tools ----
# Register Congress tools
mcp.add_tool(search_bills)
mcp.add_tool(get_bill_detail)

# Register Regulations tools
mcp.add_tool(search_regulations)
mcp.add_tool(get_docket_comments)

# Register Federal Register tools
mcp.add_tool(search_federal_register)
mcp.add_tool(search_presidential_documents)

# Register ArXiv tools
mcp.add_tool(search_arxiv)

# Register SEC tools
mcp.add_tool(search_sec_filings)

# ---- UK Tools ----
# Register UK Parliament tools
mcp.add_tool(search_uk_bills)
mcp.add_tool(get_uk_bill_detail)

# Register UK Legislation tools
mcp.add_tool(search_uk_legislation)
mcp.add_tool(search_uk_statutory_instruments)

# Register UK Companies House tools
mcp.add_tool(search_companies_house)

# ---- Canada Tools ----
mcp.add_tool(search_canada_bills)

# ---- EU Tools ----
mcp.add_tool(search_eu_official_journal)

# ---- India Tools ----
mcp.add_tool(search_nse_announcements)

if __name__ == "__main__":
    mcp.run(transport="stdio")
