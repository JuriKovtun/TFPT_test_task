from pathlib import Path
from RPA.Browser.Selenium import Selenium
from RPA.Excel.Files import Files
from etl_tools import EtlTools
from logger import logger, ctx_message


lib = Selenium()
xl = Files()
logger = logger('task.log', Path(__file__).name)
etl = EtlTools(lib, logger)
URL = 'https://itdashboard.gov/'
AGENCY_NAME = 'National Science Foundation'
WORKBOOK = 'spending_amounts.xlsx'
output_dir = 'output'
output_dir = Path(Path.cwd(), output_dir)
prefs = {
    'download.default_directory': str(output_dir)
}


def open_the_website(url: str) -> None:
    lib.open_chrome_browser(url=url, preferences=prefs)


def click_dive_in() -> None:
    """Click "DIVE IN" on the homepage
    to reveal the spending amounts for each agency
    """
    locator = 'link:DIVE IN'
    logger.info(ctx_message('click on "DIVE IN" button'))
    lib.click_link(locator)


def extract_spending_amounts() -> list:
    """wait untill all widget elements appear
    extract spending amounts for each agency
    return [(agency, amount), ...]
    """
    widget = 'css:#agency-tiles-widget .col-sm-12 > div:nth-child(2) > a'
    number_of_widgets = 26
    lib.wait_until_page_contains_element(
        locator=widget, timeout=30, limit=number_of_widgets)
    elements = lib.get_webelements(widget)
    data = [lib.get_text(e).split('\n') for e in elements]
    logger.info(ctx_message(f'number of entries: {len(data)}'))
    return [(e[0], e[-1]) for e in data]


def write_xls_file(data: list) -> None:
    """Write the amounts to an excel file and call the sheet "Agencies"
    """
    xl.create_workbook(Path(output_dir, WORKBOOK).resolve())
    xl.rename_worksheet('Sheet', 'Agencies')
    xl.set_cell_value(1, 1, 'Agencie')
    xl.set_cell_value(1, 2, 'Total FY2021 Spending')
    xl.append_rows_to_worksheet(data)
    xl.save_workbook()


def click_agency(name: str) -> None:
    """select one of the agencies, for example, National Science Foundation
    """
    logger.info(ctx_message(f'click on {name}'))
    locator = f'partial link:{name}'
    lib.click_element(locator)


def get_row_webelements() -> list:
    """scrape table with all "Individual Investments", capture table rows
    return list of webelements
    """
    url = lib.get_location()
    logger.info(ctx_message(
        f'processing Individual Investments table at {url}'))
    locator_1 = 'id:investments-table-object_wrapper'
    locator_2 = 'name:investments-table-object_length'
    locator_3 = 'css:#investments-table-object > tbody > tr'

    lib.wait_until_element_is_visible(locator_1, 30)
    max_number = int(''.join(lib.get_text(
        'css:#investments-table-object_info').split()[-2].split(',')))
    last_row = f'css:tr:nth-child({max_number})'
    lib.select_from_list_by_value(locator_2, '-1')

    # wait either until the exact number of entries is displayed,
    # or the timeout expires before they all appear.
    lib.wait_until_element_is_visible(last_row, 30)
    data = lib.get_webelements(locator_3)
    received_rows = len(data)
    if received_rows != max_number:
        logger.warning('wrong number of rows extracted: expected: {}, received: {}'.format(
            url, max_number, received_rows))
    logger.info(ctx_message(f'extracted {received_rows} rows'))
    return data


def get_link_from_uii(cell) -> str:
    """capture UII cell link
    recieve <class 'selenium.webdriver.remote.webelement.WebElement'> as argument
    return 'link to the summary page' or '--' as an empty cell character
    """
    a = cell.find_elements_by_tag_name('a')
    return a[0].get_attribute('href') if a else '--'


def create_worksheet(agency_name: str) -> None:
    """create new sheet in excel
    """
    column_names = [['UII', 'Bureau', 'Investment Title',
                     'Total FY2021 Spending ($M)', 'Type', 'CIO Rating',
                     '# of Projects', 'Link to Summary']]
    xl.create_worksheet(agency_name)
    xl.append_rows_to_worksheet(column_names)


def write_table_to_workbook(data: list) -> None:
    """write table
    """
    xl.append_rows_to_worksheet(data)
    xl.save_workbook()


def compare_pdf_to_table(pdf_values: dict, table_row: list) -> None:
    """compare the value "Name of this Investment" with the column "Investment Title",
    and the value "Unique Investment Identifier (UII)" with the column "UII"
    """
    a = pdf_values['name'] == table_row[2]
    b = pdf_values['UII'] == table_row[0]
    if not a or not b:
        logger.warning(ctx_message('values did not match'))
    message = [f'"Name of this Investment" is expected to match "Investment Title": {a}',
               f'"Unique Investment Identifier (UII)" is expected to match "UII": {b}']
    logger.info(ctx_message('\n'.join(message)))


def main():
    logger.info('Started')
    try:
        open_the_website(URL)

        # get agencies total spendings
        click_dive_in()
        amounts = extract_spending_amounts()
        write_xls_file(amounts)

        # extract table content
        create_worksheet(AGENCY_NAME)
        click_agency(AGENCY_NAME)
        rows = get_row_webelements()

        # iterate over the table by rows, get text from every cell,
        # get link from UII cell, use link to download pdf, compare values, write xlsx file
        table_content = []
        for row in rows:
            row = row.find_elements_by_tag_name('td')
            row_content = [lib.get_text(cell) for cell in row]
            link = get_link_from_uii(row[0])
            row_content.append(link)
            table_content.append(row_content)
            if link != '--':
                etl.download_pdf(link, output_dir)
                # the pdf filename corresponds to a unique number known as the first column of the table
                file_name = row_content[0] + '.pdf'
                # open pdf, extract data
                pdf_values = etl.extract_from_pdf(
                    Path(output_dir, file_name).resolve())
                compare_pdf_to_table(pdf_values, row_content)

        write_table_to_workbook(table_content)
        logger.info('Finished')

    finally:
        lib.close_all_browsers()


# Call the main() function, checking that we are running as a stand-alone script:
if __name__ == "__main__":
    main()
