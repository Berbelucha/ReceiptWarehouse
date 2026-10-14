import re

from docling.datamodel.base_models import Page
from docling_core.types import DoclingDocument
from docling_core.types.doc import DocItemLabel, TextCell


def rebuild_lines_from_cells(
    doc: DoclingDocument,
    page: Page,
    y_tol: float = 30.0,
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
    vertical = lambda c: min([c.rect.r_y0, c.rect.r_y1, c.rect.r_y2, c.rect.r_y3])
    horizontal = lambda c: min([c.rect.r_x0, c.rect.r_x1, c.rect.r_x2, c.rect.r_x3])
    arr = sorted(page.cells, key=lambda c: (vertical(c), horizontal(c)))
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
            if item_list_started and not re.search(
                "[0-9]+[,.][0-9]{2}", group[-1] if group else "", re.IGNORECASE
            ):
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
