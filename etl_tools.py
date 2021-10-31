from RPA.PDF import PDF
import time

pdf = PDF()


def download_pdf(url: str, lib) -> None:
    """open link in new window, click Download Business Case PDF      
    """
    lib.execute_javascript('window.open()')
    lib.switch_window(locator='NEW')
    lib.go_to(url)
    locator = 'css:#business-case-pdf > a'
    lib.click_element_when_visible(locator)
    print(f'download pdf from: {url}')
    time.sleep(20)
    lib.close_window()
    lib.switch_window(locator='MAIN')


def extract_from_pdf(file: str) -> dict:
    """extract values from pdf
    return {Name of this Investment: value, Unique Investment Identifier: value}
    """
    page = pdf.get_text_from_pdf(source_path=file, pages='1')[1]
    a, b = 'Name of this Investment: ', 'Section B:'
    sub = page[page.find(a)+len(a):page.find(b)]
    return {'name': sub.split('2.')[0], 'UII': sub.split()[-1]}


if __name__ == '__main__':
    pass
