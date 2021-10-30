from RPA.PDF import PDF

pdf = PDF()


def extract_values_from_pdf(file: str) -> tuple:
    """extract values from pdf
    return Name of this Investment, Unique Investment Identifier
    """
    page = pdf.get_text_from_pdf(file)[1]
    a, b = 'Name of this Investment: ', 'Section B:'
    sub = page[page.find(a)+len(a):page.find(b)]
    return sub.split('2.')[0], sub.split()[-1]


def get_values(files: list) -> list:
    return [extract_values_from_pdf(f) for f in files]


if __name__ == '__main__':
    pass
