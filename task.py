import time
from pathlib import Path
from RPA.Browser.Selenium import Selenium
from RPA.Excel.Files import Files
from etl_tools import get_values


lib = Selenium()
xl = Files()
URL = 'https://itdashboard.gov/'
AGENCY_NAME = 'National Science Foundation'
output_dir = 'output'
prefs = {
    'download.default_directory': str(Path(Path.cwd(), output_dir))
}


def open_the_website(url):
    lib.open_chrome_browser(url=url)


def click_dive_in():
    """Click "DIVE IN" on the homepage
    to reveal the spending amounts for each agency
    """
    locator = 'css:.btn-lg-2x'
    print('click_dive_in')
    lib.click_element(locator)


def extract_spending_amounts() -> list:
    """extract spending amounts for each agency
    return [(agency, amount), ...]
    """
    locator = 'xpath: //*[contains(text(), "Total FY2021 Spending:")]'
    elements = lib.get_webelements(locator)
    data = [lib.get_text(e).split('\n') for e in elements]
    return [(e[0], e[-1]) for e in data]


def write_xls_file(data: list):
    """Write the amounts to an excel file and call the sheet "Agencies"
    """
    xl.create_workbook('output/spending_amounts.xlsx')
    xl.rename_worksheet('Sheet', 'Agencies')
    xl.set_cell_value(1, 1, 'Agencie')
    xl.set_cell_value(1, 2, 'Total FY2021 Spending')
    xl.append_rows_to_worksheet(data)
    xl.save_workbook()


def click_agency(name: str):
    """select one of the agencies, for example, National Science Foundation    
    """
    locator = f'partial link:{name}'
    lib.click_element(locator)


def get_cell_webelements() -> list:
    """scrape table with all "Individual Investments" and write it to a new sheet in excel
    return list of webelements
    """
    print('waiting for Individual Investments table')
    locator_1 = 'id:investments-table-object_wrapper'
    locator_2 = 'name:investments-table-object_length'
    locator_3 = 'css:#investments-table-object > tbody > tr > td'
    lib.wait_until_element_is_visible(locator_1, 30)
    lib.select_from_list_by_value(locator_2, '-1')
    # wait for all table elements to be rendered
    time.sleep(30)
    return lib.get_webelements(locator_3)


def extract_text(cells) -> list:
    """iterate over clee elements, extract text, return by rows
    return [[cell[0], cell[1], ...], [...]]
    """
    txt = [lib.get_text(cell) for cell in cells]
    row_length = 7
    return [txt[i:i+row_length] for i in range(0, len(txt), row_length)]


def write_table_to_workbook(data: list, agency_name: str = AGENCY_NAME):
    """write table to a new sheet in excel
    """
    xl.create_worksheet(agency_name)
    xl.append_rows_to_worksheet(data)
    xl.save_workbook()


def get_links_from_uii() -> list:
    """capture UII cells links
    return [str, str, ...]
    """
    locator = 'css:#investments-table-object > tbody > tr > td:nth-child(7n+1) > a'
    anchors = lib.get_webelements(locator)
    return [lib.get_element_attribute(a, 'href') for a in anchors]


def download_pdf(links):
    """open link, download pdf
    """
    locator = 'css:#business-case-pdf > a'
    if links:
        lib.open_chrome_browser(url=None, preferences=prefs)
        for link in links:
            lib.go_to(link)
            lib.click_element_when_visible(locator)
            time.sleep(20)
        lib.close_browser()
    else:
        print('there are no links to download pdf')


def match_values_to_table(values):
    xl.open_workbook('output/spending_amounts.xlsx')
    table = xl.read_worksheet(AGENCY_NAME)

    for value in values:
        for row in table:
            if row['A'] == value[1] and row['C'] == value[0]:
                print('the values match: ', *value)


def main():
    try:
        open_the_website(URL)

        # get agencies total spendings
        click_dive_in()
        lib.wait_until_element_is_visible('id:agency-tiles-widget')
        amounts = extract_spending_amounts()
        write_xls_file(amounts)

        # extract table content
        click_agency(AGENCY_NAME)
        cells = get_cell_webelements()
        txt = extract_text(cells)
        write_table_to_workbook(txt)

        # if UII cell contains a link open it and download pdf
        links = get_links_from_uii()
        download_pdf(links)

        # extract from pdf
        pdf_files = [p for p in map(
            str, Path(output_dir).iterdir()) if '.pdf' in p]
        pdf_values = get_values(pdf_files)
        match_values_to_table(pdf_values)

    finally:
        lib.close_all_browsers()


# Call the main() function, checking that we are running as a stand-alone script:
if __name__ == "__main__":
    main()
