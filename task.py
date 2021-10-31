import time
from pathlib import Path
from RPA.Browser.Selenium import Selenium
from RPA.Excel.Files import Files
from etl_tools import download_pdf, extract_from_pdf

lib = Selenium()
xl = Files()
URL = 'https://itdashboard.gov/'
AGENCY_NAME = 'National Science Foundation'
WORKBOOK = 'spending_amounts.xlsx'
output_dir = 'output'
prefs = {
    'download.default_directory': str(Path(Path.cwd(), output_dir))
}


def open_the_website(url) -> None:
    lib.open_chrome_browser(url=url, preferences=prefs)


def click_dive_in() -> None:
    """Click "DIVE IN" on the homepage
    to reveal the spending amounts for each agency
    """
    locator = 'xpath:/html/body/main/div[1]/div/div/div[3]/div/div/div/div/div/div/div/div/div/a'
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


def write_xls_file(data: list) -> None:
    """Write the amounts to an excel file and call the sheet "Agencies"
    """
    xl.create_workbook(str(Path(output_dir, WORKBOOK)))
    xl.rename_worksheet('Sheet', 'Agencies')
    xl.set_cell_value(1, 1, 'Agencie')
    xl.set_cell_value(1, 2, 'Total FY2021 Spending')
    xl.append_rows_to_worksheet(data)
    xl.save_workbook()


def click_agency(name: str) -> None:
    """select one of the agencies, for example, National Science Foundation    
    """
    locator = f'partial link:{name}'
    lib.click_element(locator)


def get_row_webelements() -> list:
    """scrape table with all "Individual Investments", capture table rows
    return list of webelements
    """
    print('wait for Individual Investments table')
    locator_1 = 'id:investments-table-object_wrapper'
    locator_2 = 'name:investments-table-object_length'
    locator_3 = 'css:#investments-table-object > tbody > tr'
    lib.wait_until_element_is_visible(locator_1, 30)
    lib.select_from_list_by_value(locator_2, '-1')
    # wait for all table elements to be rendered
    time.sleep(30)
    return lib.get_webelements(locator_3)


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
    column_names = [['UII'], ['Bureau'], ['Investment Title'],
                    ['Total FY2021 Spending ($M)'], ['Type'], ['CIO Rating'],
                    ['# of Projects'], ['Link to Summary']]
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
    message = [f'"Name of this Investment" is expected to match "Investment Title": {a}',
               f'"Unique Investment Identifier (UII)" is expected to match "UII": {b}']
    print(*message, sep='\n')


def main():
    try:
        open_the_website(URL)

        # get agencies total spendings
        click_dive_in()
        lib.wait_until_element_is_visible('id:agency-tiles-widget')
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
                download_pdf(link, lib)
                # the pdf filename corresponds to a unique number known as the first column of the table
                file_name = row_content[0] + '.pdf'
                # open pdf, extract data
                pdf_values = extract_from_pdf(str(Path(output_dir, file_name)))
                compare_pdf_to_table(pdf_values, row_content)

        write_table_to_workbook(table_content)
        print('done')

    finally:
        lib.close_all_browsers()


# Call the main() function, checking that we are running as a stand-alone script:
if __name__ == "__main__":
    main()
