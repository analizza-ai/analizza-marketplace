"""Le docs/domain/domain-guide.md: o carimbo, a descricao do alvo e o guia do alvo."""
from __future__ import annotations

import json
import re
from dataclasses import dataclass

DESCRIPTION_TITLE = "## Descrição do alvo"
GUIDE_TITLE = "## Guia do alvo"
STAMP = re.compile(r"\A\s*<!-- olly-guide\n(.*?)\n-->", re.S)


FOLDER_KEYS = ("rotas", "servicos", "dominio", "validacoes", "migrations")


def texts(value):
    return isinstance(value, list) and all(isinstance(item, str) for item in value)


def items(value, field):
    return isinstance(value, list) and all(isinstance(item, dict) and isinstance(item.get(field), str) for item in value)


def is_inventory(value):
    """O inventario do carimbo so vale inteiro e no formato que a comparacao le; editado a mao, nao e carimbo."""
    if not isinstance(value, dict):
        return False
    specs = value.get("specs")
    return (
        all(items(value.get(key), "pasta") for key in FOLDER_KEYS)
        and items(value.get("modulos"), "caminho")
        and items(value.get("sufixos"), "sufixo")
        and isinstance(specs, dict) and texts(specs.get("frameworks")) and texts(specs.get("pastas"))
    )


@dataclass
class Guide:
    stamp: dict | None
    description: str | None
    guide: str | None


def stamp(text):
    text = text.replace("\r\n", "\n")
    found = STAMP.search(text)
    if not found:
        return None
    fields = {}
    for line in found.group(1).splitlines():
        key, separator, value = line.partition(":")
        if separator:
            fields[key.strip()] = value.strip()
    try:
        inventory = json.loads(fields.get("inventario", ""))
    except ValueError:
        inventory = None
    return {
        "gerado": fields.get("gerado"),
        "commit": fields.get("commit"),
        "inventario": inventory if is_inventory(inventory) else None,
    }


def parse(text):
    text = text.replace("\r\n", "\n")
    lines = text.splitlines()
    try:
        first = lines.index(DESCRIPTION_TITLE)
        second = lines.index(GUIDE_TITLE, first + 1)
    except ValueError:
        return Guide(stamp(text), None, None)
    return Guide(
        stamp(text),
        "\n".join(lines[first + 1:second]).strip(),
        "\n".join(lines[second + 1:]).strip(),
    )
