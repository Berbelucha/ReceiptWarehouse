import re
from datetime import datetime
from decimal import Decimal
from pathlib import Path

from markdown_it import MarkdownIt
from markdown_it.token import Token

from src.models import Receipt, ReceiptItem, Store


def parse_store(tokens: list[Token]) -> Store:
    lines: list[str] = []
    current_section: str = ''

    for i, token in enumerate(tokens):
        if token.type == "heading_open" and token.tag == "h3":
            heading = tokens[i+1].content.strip()
            current_section = heading

        elif current_section == "Sklep" and token.type == "inline" and token.children and len(token.children) > 1:
            for line in token.children:
                text = line.content.strip()
                if text:
                    lines.append(text)

    if not lines:
        raise ValueError("Nie znaleziono danych w sekcji 'Sklep'.")

    lines = [line.strip() for line in lines if line.strip()]
    name = lines[0].strip("*").strip()
    nip = None
    address = None
    extra = None

    for line in lines[1:]:
        line = line.strip()

        nip_match = re.match(r"^NIP:\s*(\d+)", line, re.IGNORECASE)
        if nip_match:
            nip = nip_match.group(1)
            continue

        if line == "Punkt sprzedaży":
            extra = line
            continue

        if line.startswith("ul. "):
            if extra == "Punkt sprzedaży":
                extra = f"{extra}: {line}"
            else:
                address = line

    return Store(
        name=name,
        address=address,
        extra=extra,
        NIP=nip,
    )

def parse_amount(value: str) -> Decimal:
    if value.lower().find("brak") >= 0:
        return Decimal(0)

    normalized = value.replace("\xa0", " ").strip()
    normalized = re.sub(r"\s*(PLN|zł|zl|g|kg)\s*$", "", normalized, flags=re.IGNORECASE)
    normalized = normalized.replace(" ", "").replace(",", ".")

    return Decimal(normalized)


def find_in_tokens(token: Token, query: str) -> Token | None:
    if token.children:
        results = []
        for child in token.children:
            check = find_in_tokens(child, query)
            if check:
                results.append(check)
        return results.pop() if results else None
    text = token.content.strip()
    if text.lower().startswith(query.lower()):
        return token
    return None


def parse_receipt(receipt_name: str, markdown: str) -> Receipt:
    parser = MarkdownIt("commonmark").enable("table")
    tokens = parser.parse(markdown)

    store = parse_store(tokens)
    purchase_date = None
    total = None
    items = []
    date_token = None
    total_token = None

    for token in tokens:
        if date_token is None:
            date_token = find_in_tokens(token, "Data:")
        if total_token is None:
            total_token = find_in_tokens(token, "Suma:")

    if date_token is not None:
        raw_date = date_token.content.strip().split(":", 1)[1].strip()
        if raw_date == "[brak danych]" or raw_date == "[Brak danych]":
            purchase_date = None
        else:
            try:
                purchase_date = datetime.strptime(raw_date, "%d-%m-%Y %H:%M")
            except Exception: #noqa: BLE001
                purchase_date = datetime.strptime(raw_date, "%Y-%m-%d %H:%M")

    if total_token is not None:
        total = parse_amount(total_token.content.strip().split(":", 1)[1])

    table_rows = []
    table_row = []
    inside_table = False
    inside_row = False

    for token in tokens:
        if token.type == "tbody_open":
            inside_table = True
            table_rows = []

        elif token.type == "tr_open" and inside_table:
            inside_row = True
            table_row = []

        elif token.type == "inline" and inside_table and inside_row and token.children:
            table_row.append(token.children[0].content.strip())

        elif token.type == "tr_close":
            inside_row = False
            if table_row:
                table_rows.append(table_row)

        elif token.type == "tbody_close":
            inside_table = False
            if not table_rows:
                continue

            for row in table_rows:
                items.append(
                    ReceiptItem(
                        name=row[0],
                        quantity=parse_amount(row[3]),
                        price=parse_amount(row[4]),
                        total=parse_amount(row[5]),
                        tags=row[6],
                    )
                )

    return Receipt(
        source_file=receipt_name,
        store=store,
        date=purchase_date,
        total=total,
        items=items,
    )


def generate_metadata_json(markdown: Path):
    return parse_receipt(markdown.name, markdown.read_text())
