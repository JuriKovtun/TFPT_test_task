from RPA.PDF import PDF
from pathlib import Path
import time
import re
import sys


class EtlTools:
    def __init__(self, lib, logger):
        self.lib = lib
        self.logger = logger
        self.pdf = PDF()
        self.current = sys._getframe().f_code.co_name

    def wait_for_the_download(self, output_dir: Path, timeout=30) -> None:
        """wait until the browser finishes to download a file
        """
        started, finished = False, False
        self.logger.info(
            f'wait for the download, timeout: {timeout} seconds...')
        while not finished and timeout > 0:
            last_file = sorted([f for f in output_dir.iterdir()],
                               key=lambda f: f.stat().st_mtime)[-1]
            if last_file.suffix == '.crdownload':
                started = True
                time.sleep(1)
                timeout -= 1
            else:
                time.sleep(1)
                timeout -= 1
            if started and last_file.suffix != '.crdownload':
                finished = True
            if timeout == 0:
                raise Exception("download has not been finished")

    def download_pdf(self, url: str, output_dir: Path) -> None:
        """open link in new window, click Download Business Case PDF
        """
        lib = self.lib
        lib.execute_javascript('window.open()')
        lib.switch_window(locator='NEW')
        lib.go_to(url)
        locator = 'css:#business-case-pdf > a'
        lib.wait_until_element_is_visible(locator, 30)
        self.logger.info(f'click "Download Business Case PDF" at: {url}')
        lib.click_element(locator)
        self.wait_for_the_download(output_dir)
        lib.close_window()
        lib.switch_window(locator='MAIN')

    def extract_from_pdf(self, file: str) -> dict:
        """extract values from pdf
        return {Name of this Investment: value, Unique Investment Identifier: value}
        """
        pdf = self.pdf
        try:
            page = pdf.get_text_from_pdf(source_path=file, pages='1')[1]
            pattern_name = re.compile(
                r'Name of this Investment: (.*?)2', re.IGNORECASE)
            pattern_uii = re.compile(
                r'Unique Investment Identifier \(UII\): (.*?)Section B', re.IGNORECASE)
            name = pattern_name.findall(page)
            uii = pattern_uii.findall(page)
            if len(name) != 1 or len(uii) != 1:
                raise Exception(f'wrong number of data extracted from the file: {file}',
                                f'name: {name}', f'uii: {uii}')
            else:
                return {'name': name[0], 'UII': uii[0]}
        except Exception as error:
            self.logger.error('failed to extract from:', file, error)


if __name__ == '__main__':
    pass
