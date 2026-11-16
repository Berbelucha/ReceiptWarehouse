import re
from collections.abc import Callable
from itertools import chain, groupby

from docling.datamodel.base_models import Page
from docling_core.types import DoclingDocument
from docling_core.types.doc import DocItemLabel, TextCell


def rebuild_lines_from_cells(
    doc: DoclingDocument,
    page: Page,
    y_tol: float = 25.0,
) -> DoclingDocument:
    """Split merged TextItems into per-line TextItems using page.cells.

    Each visual line becomes a GroupItem containing one TextItem whose
    text is the member cells joined by spaces and whose prov.bbox is the
    union of the member cell rects. Non-text items (pictures, tables,
    section headers) and items on other pages are kept as-is.

    Requires pipeline_options.generate_parsed_pages = True so that
    page.cells survives conversion.

    Args:
        doc:     conv_res.document (DoclingDocument, NOT ConversionResult)
        page:    conv_res.pages[page_no - 1] (internal Page object)
        y_tol:   vertical tolerance in page units for grouping cells
                 into one line (compare against median cell height)
    """

    result = DoclingDocument(name=doc.name)
    vertical: Callable[[TextCell], float] = lambda cell: min(
        [cell.rect.r_y0, cell.rect.r_y1, cell.rect.r_y2, cell.rect.r_y3]
    )
    horizontal: Callable[[TextCell], float] = lambda cell: min(
        [cell.rect.r_x0, cell.rect.r_x1, cell.rect.r_x2, cell.rect.r_x3]
    )
    middle_v: Callable[[TextCell], float] = lambda cell: (
        sum([cell.rect.r_y0, cell.rect.r_y1, cell.rect.r_y2, cell.rect.r_y3]) / 4
    )
    arr = sorted(page.cells, key=lambda cell: vertical(cell))

    grouped_items = []
    i = 0
    last_cell: TextCell | None = None

    def grouper(cell: TextCell):
        nonlocal last_cell
        nonlocal i

        if last_cell and abs(middle_v(last_cell) - middle_v(cell)) <= y_tol:
            last_cell = cell
            return i
        else:
            last_cell = cell
            i += 1
            return i

    for key, group in groupby(arr, lambda x: grouper(x)):
        grouped_items.append(sorted(group, key=lambda c: horizontal(c)))

    arr: list[TextCell] = list(chain.from_iterable(grouped_items))
    last_item: TextCell | None = None
    group: list[str] = []
    grouped: list[list[str]] = []
    item_list_started = False

    for item in arr:
        if (
            last_item
            and re.search("(p[a-z]r[a-z]gon|fiskalny)", item.text, re.IGNORECASE)
            is None
            and re.search("(p[a-z]r[a-z]gon|fiskalny)", last_item.text, re.IGNORECASE)
        ):
            item_list_started = True
            grouped.append(group)
            group = []
        elif re.search("sprzeda[zżź]|ptu|suma|sp\\.o", item.text, re.IGNORECASE):
            item_list_started = False

        if last_item and abs(vertical(item) - vertical(last_item)) > y_tol:
            regex = "[ \\-=]?[0-9]+[,.][0-9]{2} ?\\w?$"
            find_price = re.search(regex, " ".join(group), re.IGNORECASE)
            last_item = item
            if item_list_started and not find_price:
                group.append(item.text)
                last_item = item
                continue
            grouped.append(group)
            group = []

        group.append(item.text)
        last_item = item

    for group in grouped:
        group_ref = result.add_inline_group()
        result.add_text(DocItemLabel.TEXT, text=" ".join(group), parent=group_ref)
    return result
