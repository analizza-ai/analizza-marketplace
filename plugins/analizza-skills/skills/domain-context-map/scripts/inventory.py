#!/usr/bin/env python3
"""Inventario de um repositorio para a skill domain-context-map.

So le o disco: nao escreve nada e nao usa rede. Nunca falha por causa do que
encontra: o que nao reconhece volta vazio ou nulo, e quem interpreta e o modelo.
"""
import datetime
import json
import os
import re
import subprocess
import sys
from collections import Counter
from pathlib import Path

import guide_file

IGNORED = {".git", "node_modules", "build", "dist", "target", ".gradle", ".next", "out", ".idea", ".venv", "__pycache__"}
LANGUAGES = {
    ".kt": "kotlin", ".java": "java", ".ts": "typescript", ".tsx": "typescript",
    ".js": "javascript", ".jsx": "javascript",
}
# Extensions that count as source in "codigo". Layers, routes and suffixes are still
# detected only for LANGUAGES: in another language the map is made by hand.
SOURCE = set(LANGUAGES) | {
    ".mjs", ".cjs", ".vue", ".svelte", ".py", ".go", ".rb", ".cs", ".php", ".rs", ".swift", ".scala", ".groovy",
    ".c", ".h", ".cc", ".cpp", ".hpp", ".m", ".dart", ".ex", ".exs", ".erl", ".clj", ".fs", ".vb", ".lua", ".pl",
    ".r", ".jl", ".hs", ".ml", ".zig",
}
BUILD_FILES = ("build.gradle.kts", "build.gradle", "pom.xml", "package.json")
# Framework de specs e a pasta que o denuncia.
SPEC_FOLDERS = (
    ("openspec", "openspec"), ("superpowers", "docs/superpowers"), ("spec-kit", ".specify"),
    ("spec-kit", "specs"), ("adr", "docs/adr"), ("adr", "adr"),
)
SPRING_ROUTE = re.compile(
    r"@(RestController|Controller|RequestMapping|GetMapping|PostMapping|PutMapping|DeleteMapping|PatchMapping)\b"
)
KTOR_ROUTE = re.compile(r"\brouting\s*\{")
NEXT_ROUTE = re.compile(r"(^|/)app/(.*/)?route\.(ts|js)$|(^|/)pages/api/")
# A file that only exists inside a Next app/ router, and a folder that is a route parameter.
NEXT_ROUTER_FILE = re.compile(r"^(route|page|layout)\.[tj]sx?$")
ROUTE_SEGMENT = re.compile(r"^\[.*\]$")
# A route folder with one of these names is a folder of routes: what is below it is route too.
# Any other folder with a route file (a base package, the source root) hides nothing below it.
ROUTE_FOLDERS = {"routes", "route", "controllers", "controller", "api", "presenter", "web", "rest", "endpoints"}
LAYERS = {
    "servicos": {"application", "service", "services", "usecase", "usecases"},
    "dominio": {"domain", "model", "models", "entity", "entities"},
    "validacoes": {"rules", "validation", "validations", "validator", "validators"},
}
MIGRATIONS = re.compile(r"(^|/)(db/migration|migrations|prisma)(/|$)")
TEST_FOLDERS = {"test", "tests", "__tests__"}
TEST_FILE = re.compile(r"\.(test|spec)\.[tj]sx?$")
LAST_WORD = re.compile(r"[A-Z][a-z0-9]+$")
MAX_BYTES = 1_000_000


def git(root, *args):
    try:
        # errors="replace": a file name or a remote that is not UTF-8 must not raise.
        done = subprocess.run(
            ["git", "-C", str(root), *args], capture_output=True, encoding="utf-8", errors="replace", timeout=30,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    return done.stdout.strip() if done.returncode == 0 else None


def files(root):
    """Caminhos relativos, com barra, do que nao e ignorado. Com git vale o .gitignore."""
    # -z: NUL-separated and unquoted, so accented names are not escaped by core.quotepath.
    listed = git(root, "ls-files", "-z", "-co", "--exclude-standard")
    if listed is not None:
        paths = [path for path in listed.split("\0") if path]
    else:
        paths = []
        for base, folders, names in os.walk(root):
            folders[:] = [folder for folder in folders if folder not in IGNORED]
            for name in names:
                paths.append(os.path.relpath(os.path.join(base, name), root).replace(os.sep, "/"))
    return sorted(
        path for path in paths
        if not (set(path.split("/")[:-1]) & IGNORED) and (root / path).is_file()
    )


def read(path):
    try:
        if path.stat().st_size > MAX_BYTES:
            return ""
        return path.read_text(encoding="utf-8", errors="ignore")
    except OSError:
        return ""


def extension(path):
    return os.path.splitext(path)[1]


def is_test(path):
    return bool(set(path.split("/")[:-1]) & TEST_FOLDERS) or bool(TEST_FILE.search(path))


def grouped(paths):
    counts = Counter(os.path.dirname(path) or "." for path in paths)
    return [{"pasta": folder, "arquivos": count} for folder, count in sorted(counts.items())]


def framework(build):
    text = read(build)
    if build.name == "package.json":
        try:
            package = json.loads(text)
        except ValueError:
            return None
        if not isinstance(package, dict):
            return None
        fields = (package.get("dependencies"), package.get("devDependencies"))
        return "nextjs" if any(isinstance(field, dict) and "next" in field for field in fields) else None
    if "springframework" in text or "spring-boot" in text:
        return "spring"
    if "io.ktor" in text:
        return "ktor"
    return None


def modules(root, paths):
    known = set(paths)
    folders = sorted({os.path.dirname(path) or "." for path in paths if os.path.basename(path) in BUILD_FILES})
    found = []
    for folder in folders:
        prefix = "" if folder == "." else folder + "/"
        build = next(name for name in BUILD_FILES if prefix + name in known)
        languages = Counter(
            LANGUAGES[extension(path)] for path in paths
            if path.startswith(prefix) and extension(path) in LANGUAGES
        )
        found.append({
            "caminho": folder,
            "build": build,
            "linguagem": languages.most_common(1)[0][0] if languages else None,
            "framework": framework(root / (prefix + build)),
        })
    return found


def specs(paths):
    frameworks, folders = [], []
    for name, folder in SPEC_FOLDERS:
        if any(path.startswith(folder + "/") for path in paths):
            folders.append(folder)
            if name not in frameworks:
                frameworks.append(name)
    markdown = Counter(os.path.dirname(path) or "." for path in paths if path.lower().endswith(".md"))
    return {
        "frameworks": frameworks,
        "pastas": folders,
        "markdown": [{"pasta": folder, "arquivos": count} for folder, count in markdown.most_common(5)],
    }


def routes(root, code):
    found = []
    for path in code:
        if NEXT_ROUTE.search(path):
            found.append(path)
        elif extension(path) in (".kt", ".java"):
            text = read(root / path)
            if SPRING_ROUTE.search(text) or KTOR_ROUTE.search(text):
                found.append(path)
    return grouped(found)


def next_routers(code):
    """As pastas app/ que sao roteador do Next: tudo abaixo delas e rota ou tela, nao camada."""
    found = set()
    for path in code:
        parts = path.split("/")
        if NEXT_ROUTER_FILE.match(parts[-1]) and "app" in parts[:-1]:
            found.add("/".join(parts[: parts.index("app") + 1]))
    return found


def inside(folder, parents):
    return any(folder == parent or folder.startswith(parent + "/") for parent in parents)


def is_route_area(folder, route_folders, routers):
    """A pasta e de rota, esta abaixo de uma pasta feita so para rotas, ou tem um [parametro] no caminho."""
    dedicated = {route for route in route_folders if route.split("/")[-1].lower() in ROUTE_FOLDERS}
    if folder in route_folders or inside(folder, dedicated | routers):
        return True
    return any(ROUTE_SEGMENT.match(part) for part in folder.split("/"))


def layers(code, route_folders):
    """Por camada, a pasta mais alta do caminho cujo nome a denuncia, com os arquivos abaixo dela.

    Entre servicos e dominio vale o primeiro nome a partir da raiz: application/models e caso de
    uso de um recurso chamado "model", nao dominio. Validacao e contada a parte, porque a pasta
    de regras costuma morar dentro do dominio. Pasta de rota nao e camada, tenha o nome que tiver;
    mas um arquivo de rota no pacote base nao esconde as camadas que ficam abaixo dele.
    """
    counts = {key: Counter() for key in LAYERS}
    route_folders, routers = set(route_folders), next_routers(code)
    for path in code:
        parts = path.split("/")[:-1]
        lowered = [part.lower() for part in parts]
        found = {}
        for index, part in enumerate(lowered):
            if part in LAYERS["servicos"] or part in LAYERS["dominio"]:
                found["servicos" if part in LAYERS["servicos"] else "dominio"] = index
                break
        for index, part in enumerate(lowered):
            if part in LAYERS["validacoes"]:
                found["validacoes"] = index
                break
        for key, index in found.items():
            folder = "/".join(parts[: index + 1])
            if not is_route_area(folder, route_folders, routers):
                counts[key][folder] += 1
    return {
        key: [{"pasta": folder, "arquivos": count} for folder, count in sorted(counter.items())]
        for key, counter in counts.items()
    }


def suffixes(code):
    counts = Counter()
    for path in code:
        stem, ext = os.path.splitext(os.path.basename(path))
        if ext in (".kt", ".java"):
            word = LAST_WORD.search(stem)
            # Nome de uma palavra so nao tem sufixo: "Account" nao e convencao.
            if word and word.group(0) != stem:
                counts[word.group(0)] += 1
        else:
            parts = re.split(r"[-.]", stem)
            if len(parts) > 1:
                counts[parts[-1]] += 1
    # No cut at the top N: with a cut, a tie at the edge makes one new file swap two suffixes.
    ordered = sorted(counts.items(), key=lambda item: (-item[1], item[0]))
    return [{"sufixo": name, "arquivos": count} for name, count in ordered if count >= 3]


def without_credential(url):
    """A URL do remote sem o que pode ser segredo: usuario e senha, ?consulta e #fragmento."""
    # The credential goes first: a password may hold ? or #, and cutting there first would leave half of it.
    url = url.strip()
    if "://" in url:
        # Up to the last @: a password may hold @ or /. A path with @ loses its start, and that is the safe side.
        scheme, rest = url.split("://", 1)
        url = scheme + "://" + rest.rsplit("@", 1)[-1]
    else:
        user, separator, rest = url.rpartition("@")
        # scp style: git@host:path has no secret; user:token@host:path has.
        if separator and ":" in user:
            url = rest
    return re.split(r"[?#]", url, maxsplit=1)[0]


def remote(root):
    url = git(root, "config", "--get", "remote.origin.url")
    return without_credential(url) if url else None


def inventory(root):
    paths = files(root)
    code = [path for path in paths if extension(path) in LANGUAGES and not is_test(path)]
    source = [path for path in paths if extension(path).lower() in SOURCE and not is_test(path)]
    found_routes = routes(root, code)
    found_layers = layers(code, [item["pasta"] for item in found_routes])
    return {
        "commit": git(root, "rev-parse", "--short", "HEAD"),
        "remote": remote(root),
        "arquivos": len(paths),
        "codigo": len(source),
        "modulos": modules(root, paths),
        "specs": specs(paths),
        "rotas": found_routes,
        "servicos": found_layers["servicos"],
        "dominio": found_layers["dominio"],
        "validacoes": found_layers["validacoes"],
        "migrations": grouped([path for path in paths if MIGRATIONS.search(os.path.dirname(path))]),
        "sufixos": suffixes(code),
    }


LAYER_KEYS = ("rotas", "servicos", "dominio", "validacoes", "migrations")


def stamp(found, today):
    """O bloco que abre docs/domain/domain-guide.md. O inventario vai numa linha so, para a leitura achar.

    O remote fica de fora: a comparacao nao o usa, e o arquivo vai para o repositorio.
    """
    kept = {key: value for key, value in found.items() if key != "remote"}
    return "\n".join([
        "<!-- olly-guide",
        f"gerado: {today}",
        f"commit: {found.get('commit') or ''}",
        "inventario: " + json.dumps(kept, ensure_ascii=False),
        "-->",
    ])


def names(found, key, field):
    return [item[field] for item in (found.get(key) or [])]


def added_and_removed(label, old, new, added, removed):
    return [f"{label}: {added} {name}" for name in new if name not in old] + \
        [f"{label}: {removed} {name}" for name in old if name not in new]


def changes(old, new):
    """O que mudou na forma do projeto. Contagem de arquivos e commit nao contam."""
    found = []
    for key in LAYER_KEYS:
        found += added_and_removed(key, names(old, key, "pasta"), names(new, key, "pasta"), "pasta nova", "pasta sumiu")

    old_specs, new_specs = old.get("specs") or {}, new.get("specs") or {}
    before, after = old_specs.get("frameworks") or [], new_specs.get("frameworks") or []
    if before != after:
        found.append(f"specs: framework mudou de {'+'.join(before) or 'nenhum'} para {'+'.join(after) or 'nenhum'}")
    found += added_and_removed(
        "specs", old_specs.get("pastas") or [], new_specs.get("pastas") or [], "pasta nova", "pasta sumiu",
    )

    old_modules = {module["caminho"]: module for module in (old.get("modulos") or [])}
    new_modules = {module["caminho"]: module for module in (new.get("modulos") or [])}
    found += added_and_removed("módulos", list(old_modules), list(new_modules), "novo", "sumiu")
    for path, module in new_modules.items():
        previous = old_modules.get(path)
        if previous and previous.get("framework") != module.get("framework"):
            found.append(
                f"módulos: {path} mudou de {previous.get('framework') or 'nenhum'} para {module.get('framework') or 'nenhum'}"
            )

    found += added_and_removed("sufixos", names(old, "sufixos", "sufixo"), names(new, "sufixos", "sufixo"), "novo", "sumiu")
    return found


def compare(root, guide):
    try:
        parsed = guide_file.parse(Path(guide).read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError):
        parsed = None
    if parsed is None or parsed.stamp is None or parsed.stamp["inventario"] is None:
        return {"carimbo": False, "gerado": None, "commit": None, "mudancas": []}
    return {
        "carimbo": True,
        "gerado": parsed.stamp["gerado"],
        "commit": parsed.stamp["commit"] or None,
        "mudancas": changes(parsed.stamp["inventario"], inventory(root)),
    }


def main(arguments):
    options = [argument for argument in arguments if argument.startswith("--")]
    positional = [argument for argument in arguments if not argument.startswith("--")]
    root = Path(positional[0] if positional else ".").resolve()
    if "--compare" in options:
        # O arquivo vem logo depois da raiz: inventory.py <raiz> --compare <arquivo>.
        guide = positional[1] if len(positional) > 1 else str(root / "docs" / "domain" / "domain-guide.md")
        print(json.dumps(compare(root, guide), ensure_ascii=False, indent=2))
    elif "--stamp" in options:
        print(stamp(inventory(root), datetime.date.today().isoformat()))
    else:
        print(json.dumps(inventory(root), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
