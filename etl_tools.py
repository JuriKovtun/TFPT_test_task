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

    @staticmethod
    def get_last_file(dir: Path) -> str:
        """return name of the last modified file/directory or 'empty dir'
        """
        file_list = sorted([f for f in dir.iterdir()],
                           key=lambda f: f.stat().st_mtime)
        return file_list[-1].name if file_list else 'empty dir'

    def wait_for_the_download(self, output_dir: Path, last_file: Path, timeout=30) -> None:
        """wait until the browser finishes to download a file
        """
        started, finished = False, False
        self.logger.info(f'wait for the download...')
        while not finished and timeout > 0:
            new_file = EtlTools.get_last_file(output_dir)
            if '.crdownload' in new_file:
                started = True
                time.sleep(1)
                timeout -= 1
            else:
                time.sleep(1)
                timeout -= 1
            if not '.crdownload' in new_file and started:
                finished = True
            if not '.crdownload' in new_file and new_file != last_file:
                finished = True
            if timeout == 0:
                raise Exception("download has not been finished")

    def download_pdf(self, url: str, output_dir: Path) -> None:
        """open link in new window, click Download Business Case PDF
        """
        lib = self.lib
        last_file = EtlTools.get_last_file(output_dir)
        lib.execute_javascript('window.open()')
        lib.switch_window(locator='NEW')
        lib.go_to(url)
        locator = 'css:#business-case-pdf > a'
        lib.wait_until_element_is_visible(locator, 30)
        self.logger.info(f'click "Download Business Case PDF" at: {url}')
        lib.click_element(locator)
        self.wait_for_the_download(output_dir, last_file)
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
