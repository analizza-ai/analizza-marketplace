#!/usr/bin/env python3
"""Confere docs/domain/domain-guide.md contra os limites do cadastro do Olly e contra o disco."""
import re
import subprocess
import sys
from pathlib import Path

import guide_file

MAX_DESCRIPTION = 200
MAX_GUIDE = 8000
MAX_GLOSSARY = 40
SECTIONS = [
    "O que é", "Specs e documentação", "Onde está cada coisa no código", "Como seguir uma regra",
    "Como buscar", "Glossário", "Armadilhas",
]
REQUIRED = ["O que é", "Onde está cada coisa no código"]
GLOSSARY = "Glossário"
QUOTED = re.compile(r"`([^`\n]+)`")
POSITION = re.compile(r"(:\d+(-\d+)?|#L\d+(-L?\d+)?)$")
FILE_NAME = re.compile(r"^[\w.-]+\.\w+$")
NOT_A_PATH = set("*<>{}$|")
URLS = ("http://", "https://")
# Cheap net, not a scanner: the shapes a person pastes by accident.
SECRETS = [
    ("URL com usuário e senha", re.compile(r"://[^/\s:@]+:[^/\s@]+@")),
    ("token do GitHub", re.compile(r"(?<![A-Za-z0-9])(ghp_|github_pat_)[A-Za-z0-9_]{20,}")),
    ("chave de API", re.compile(r"(?<![A-Za-z0-9])sk-[A-Za-z0-9_-]{20,}")),
    ("chave da AWS", re.compile(r"(?<![A-Za-z0-9])AKIA[0-9A-Z]{16}(?![A-Za-z0-9])")),
    ("token do Slack", re.compile(r"(?<![A-Za-z0-9])xox[bap]-[A-Za-z0-9-]{10,}")),
    ("chave privada", re.compile(r"-----BEGIN [A-Z ]*PRIVATE KEY")),
]


def path_of(token):
    """O caminho citado no trecho, ou None quando o trecho nao e um caminho do repositorio."""
    if any(char.isspace() for char in token) or NOT_A_PATH & set(token):
        return None
    if token.startswith(("/", "@") + URLS) or "/" not in token:
        return None
    return token.rstrip("/")


def is_line_number(token):
    """O sufixo :N ou #LN so conta quando o resto e um caminho do repositorio ou um nome de arquivo com extensao."""
    if token.startswith(URLS) or not POSITION.search(token):
        return False
    rest = POSITION.sub("", token)
    return path_of(rest) is not None or bool(FILE_NAME.match(rest))


def secrets(text):
    """O que no texto parece segredo. Devolve o tipo, nunca o valor: a saida do script tambem e lida e colada."""
    return [label for label, pattern in SECRETS if pattern.search(text)]


def description_problems(description):
    if not description:
        return ["descrição vazia"]
    found = [f"descrição: parece segredo ({label}); tire do texto" for label in secrets(description)]
    if "\n" in description:
        found.append("descrição com quebra de linha: o cadastro aceita uma linha só")
    if len(description) > MAX_DESCRIPTION:
        found.append(f"descrição com {len(description)} caracteres: o limite é {MAX_DESCRIPTION}")
    return found


def section_problems(lines):
    titles = [line[4:].strip() for line in lines if line.startswith("### ")]
    found = [f"falta a seção '### {title}': todo guia tem" for title in REQUIRED if title not in titles]
    found += [f"seção desconhecida: {title}" for title in titles if title not in SECTIONS]
    known = [SECTIONS.index(title) for title in titles if title in SECTIONS]
    if known != sorted(known) or len(known) != len(set(known)):
        found.append("seção fora de ordem ou repetida: a ordem é " + ", ".join(SECTIONS))
    return found


def glossary_problems(lines):
    items, inside = 0, False
    for line in lines:
        if line.startswith("### "):
            inside = line[4:].strip() == GLOSSARY
        elif inside and line.startswith(("- ", "* ")):
            items += 1
    return [f"glossário com {items} itens: o limite é {MAX_GLOSSARY}"] if items > MAX_GLOSSARY else []


def line_problems(lines, root):
    found = []
    for number, line in enumerate(lines, 1):
        if line.startswith("# "):
            found.append(f"guia, linha {number}: título de primeiro nível")
        if line.startswith("## "):
            found.append(f"guia, linha {number}: título de segundo nível: as seções do guia usam ###")
        for label in secrets(line):
            found.append(f"guia, linha {number}: parece segredo ({label}); tire do texto")
        for token in QUOTED.findall(line):
            token = token.strip()
            if is_line_number(token):
                found.append(f"guia, linha {number}: número de linha em `{token}`")
                token = POSITION.sub("", token)
            path = path_of(token)
            if path is None:
                continue
            if ".." in path.split("/"):
                found.append(f"guia, linha {number}: caminho fora do repositório: {token}")
            elif not (root / path).exists():
                found.append(f"guia, linha {number}: caminho não existe: {token}")
    return found


def problems(text, root):
    parsed = guide_file.parse(text)
    found = []
    if parsed.stamp is None or parsed.stamp["inventario"] is None:
        found.append("carimbo ausente ou ilegível: o arquivo não foi gerado pela skill")
    if parsed.description is None or parsed.guide is None:
        found.append(f"faltam os títulos '{guide_file.DESCRIPTION_TITLE}' e '{guide_file.GUIDE_TITLE}'")
        return found
    found += description_problems(parsed.description)
    if not parsed.guide:
        return found + ["guia vazio"]
    if len(parsed.guide) > MAX_GUIDE:
        found.append(f"guia com {len(parsed.guide)} caracteres: o limite é {MAX_GUIDE}")
    lines = parsed.guide.splitlines()
    return found + section_problems(lines) + glossary_problems(lines) + line_problems(lines, root)


def commits_since(root, commit):
    if not commit:
        return "desconhecido"
    try:
        done = subprocess.run(
            ["git", "-C", str(root), "rev-list", "--count", f"{commit}..HEAD"],
            capture_output=True, encoding="utf-8", errors="replace", timeout=30,
        )
    except (OSError, subprocess.SubprocessError):
        return "desconhecido"
    return done.stdout.strip() if done.returncode == 0 else "desconhecido"


def main(arguments):
    guide = Path(arguments[0] if arguments else "docs/domain/domain-guide.md")
    root = Path(arguments[1] if len(arguments) > 1 else ".").resolve()
    try:
        text = guide.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        print(f"ERRO: não consegui ler {guide} como UTF-8")
        return 1
    found = problems(text, root)
    for problem in found:
        print(f"ERRO: {problem}")
    if found:
        return 1
    parsed = guide_file.parse(text)
    print(
        f"OK: descrição {len(parsed.description)}/{MAX_DESCRIPTION}, guia {len(parsed.guide)}/{MAX_GUIDE}, "
        f"commits desde o carimbo: {commits_since(root, parsed.stamp['commit'])}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
