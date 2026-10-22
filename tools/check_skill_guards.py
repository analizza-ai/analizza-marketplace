"""Guarda da skill yeroon-play-plug: impede que as anti-metas vazem."""
import re
import sys
from pathlib import Path

MARCADOR = re.compile(r"(?<!\$)\{[a-z][a-z0-9-]*\}")
MARCADORES_PERMITIDOS = {"{id}"}  # variável de rota do Spring, não é marcador
CHAVE_LITERAL = re.compile(r"(?:yk_|whsec_)[A-Za-z0-9_-]{8,}")
TERMOS_PRIVADOS = ("bjjdream", "yeroon-stream-poc", "analizza-tube")
CAMPOS_FRONTMATTER = {"name", "description"}


def _ler(arquivo: Path):
    try:
        return arquivo.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError):
        return None


def _frontmatter(texto: str):
    linhas = texto.splitlines()
    if not linhas or linhas[0].strip() != "---":
        return None
    for i in range(1, len(linhas)):
        if linhas[i].strip() == "---":
            return linhas[1:i]
    return None


def _vocabulario(texto: str) -> set[str]:
    """Marcadores da primeira coluna das tabelas sob um título com 'Vocabulário'."""
    declarados: set[str] = set()
    na_secao = False
    for linha in texto.splitlines():
        if linha.startswith("#"):
            na_secao = "vocabulário" in linha.lower()
            continue
        if na_secao and linha.lstrip().startswith("|"):
            celulas = linha.strip().strip("|").split("|")
            declarados.update(MARCADOR.findall(celulas[0]))
    return declarados


def verificar_skill(skill_dir: Path) -> list[str]:
    erros: list[str] = []
    skill_md = skill_dir / "SKILL.md"

    texto_skill = _ler(skill_md) if skill_md.is_file() else None
    if texto_skill is None:
        erros.append("SKILL.md: arquivo ausente ou ilegível")
        texto_skill = ""
    else:
        linhas = _frontmatter(texto_skill)
        if linhas is None:
            erros.append("SKILL.md: frontmatter ausente ou sem fechamento")
        else:
            chaves = {
                l.split(":", 1)[0].strip()
                for l in linhas
                if ":" in l and not l[:1].isspace()
            }
            for extra in sorted(chaves - CAMPOS_FRONTMATTER):
                erros.append(f"SKILL.md: campo de frontmatter não permitido: {extra}")
            for falta in sorted(CAMPOS_FRONTMATTER - chaves):
                erros.append(f"SKILL.md: campo de frontmatter ausente: {falta}")

    declarados = _vocabulario(texto_skill) | MARCADORES_PERMITIDOS
    templates = skill_dir / "templates"

    for arquivo in sorted(p for p in skill_dir.rglob("*") if p.is_file()):
        texto = _ler(arquivo)
        if texto is None:
            continue
        rel = arquivo.relative_to(skill_dir).as_posix()
        for m in sorted(set(CHAVE_LITERAL.findall(texto))):
            erros.append(f"{rel}: possível chave ou segredo literal ({m[:7]}...)")
        for termo in TERMOS_PRIVADOS:
            if termo in texto:
                erros.append(f"{rel}: referência privada proibida: {termo}")
        if templates.is_dir() and templates in arquivo.parents:
            for marcador in sorted(set(MARCADOR.findall(texto)) - declarados):
                erros.append(
                    f"{rel}: marcador {marcador} não declarado na tabela "
                    "Vocabulário do SKILL.md"
                )
    return erros


def main() -> int:
    raiz = Path(__file__).resolve().parents[1]
    pastas = [raiz / "plugins/analizza-skills/skills/yeroon-play-plug"]
    erros = []
    for pasta in pastas:
        erros += [f"{pasta.name}/{e}" for e in verificar_skill(pasta)]
    if erros:
        print("\n".join(erros))
        return 1
    print(f"guarda das skills ok ({len(pastas)} skill(s) verificada(s))")
    return 0


if __name__ == "__main__":
    sys.exit(main())
