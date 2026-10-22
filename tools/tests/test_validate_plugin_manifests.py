import json
from pathlib import Path

from tools.validate_plugin_manifests import (
    carregar_manifesto,
    validar_manifestos,
    validar_marketplace,
)


def manifestos_validos():
    claude = {"name": "analizza-skills", "version": "0.2.1"}
    codex = {
        "name": "analizza-skills",
        "version": "0.2.1",
        "skills": "./skills/",
        "interface": {
            "displayName": "Analizza Skills",
            "shortDescription": "Scaffolding e qualidade para projetos Kotlin/Java + Spring Boot",
            "longDescription": "Cria monorepos do zero e configura testes de integração.",
            "developerName": "Diego Lirio",
            "category": "Developer Tools",
            "capabilities": ["Read", "Write"],
        },
    }
    return claude, codex


def criar_skills(tmp_path: Path, nomes: list[str]) -> None:
    skills_dir = tmp_path / "skills"
    skills_dir.mkdir()
    for nome in nomes:
        pasta = skills_dir / nome
        pasta.mkdir()
        (pasta / "SKILL.md").write_text("# skill\n", encoding="utf-8")


def test_manifestos_compativeis_nao_produzem_erros(tmp_path: Path):
    criar_skills(tmp_path, ["a", "b", "c"])
    claude, codex = manifestos_validos()
    assert validar_manifestos(claude, codex, tmp_path) == []


def test_versao_divergente_e_reportada(tmp_path: Path):
    criar_skills(tmp_path, ["a"])
    claude, codex = manifestos_validos()
    codex["version"] = "0.3.0"
    assert "version diverge" in "\n".join(validar_manifestos(claude, codex, tmp_path))


def test_caminho_de_skills_diferente_e_reportado(tmp_path: Path):
    criar_skills(tmp_path, ["a"])
    claude, codex = manifestos_validos()
    codex["skills"] = "./codex-skills/"
    assert "skills deve ser './skills/'" in "\n".join(
        validar_manifestos(claude, codex, tmp_path)
    )


def test_diretorio_de_skills_ausente_e_reportado(tmp_path: Path):
    claude, codex = manifestos_validos()
    assert "diretório de skills não existe" in "\n".join(
        validar_manifestos(claude, codex, tmp_path)
    )


def test_interface_incompleta_e_reportada(tmp_path: Path):
    criar_skills(tmp_path, ["a"])
    claude, codex = manifestos_validos()
    del codex["interface"]["category"]
    assert "interface.category ausente" in "\n".join(
        validar_manifestos(claude, codex, tmp_path)
    )


def test_skill_md_faltando_e_reportado(tmp_path: Path):
    criar_skills(tmp_path, ["a", "b"])
    (tmp_path / "skills" / "c").mkdir()
    claude, codex = manifestos_validos()
    erros = "\n".join(validar_manifestos(claude, codex, tmp_path))
    assert "número de SKILL.md" in erros


def test_name_ausente_no_codex_e_reportado(tmp_path: Path):
    criar_skills(tmp_path, ["a"])
    claude, codex = manifestos_validos()
    del codex["name"]
    assert "codex: name ausente" in "\n".join(validar_manifestos(claude, codex, tmp_path))


def test_version_ausente_no_codex_e_reportada(tmp_path: Path):
    criar_skills(tmp_path, ["a"])
    claude, codex = manifestos_validos()
    del codex["version"]
    assert "codex: version ausente" in "\n".join(
        validar_manifestos(claude, codex, tmp_path)
    )


def test_manifesto_ausente_e_reportado(tmp_path: Path, capsys):
    caminho = tmp_path / "plugin.json"
    resultado = carregar_manifesto(caminho)
    assert resultado is None
    assert f"manifesto ausente ou inválido: {caminho}" in capsys.readouterr().out


def test_manifesto_json_valido_mas_nao_objeto_e_reportado(tmp_path: Path, capsys):
    caminho = tmp_path / "plugin.json"
    caminho.write_text("[]", encoding="utf-8")
    resultado = carregar_manifesto(caminho)
    assert resultado is None
    assert f"JSON inválido: {caminho}" in capsys.readouterr().out


def test_manifestos_reais_respeitam_o_contrato():
    raiz = Path(__file__).resolve().parents[2]
    assert validar_marketplace(raiz) == []

    marketplace = json.loads(
        (raiz / ".claude-plugin/marketplace.json").read_text(encoding="utf-8")
    )
    assert marketplace["plugins"]
    for entrada in marketplace["plugins"]:
        plugin_dir = raiz / entrada["source"]
        skills_dir = plugin_dir / "skills"
        assert skills_dir.is_dir()
        assert not skills_dir.is_symlink()
        pastas = [p for p in skills_dir.iterdir() if p.is_dir()]
        assert pastas
        assert len(list(skills_dir.glob("*/SKILL.md"))) == len(pastas)


def test_readme_documenta_claude_e_codex_sem_comando_inventado():
    raiz = Path(__file__).resolve().parents[2]
    readme = (raiz / "README.md").read_text(encoding="utf-8")
    assert "### Claude Code" in readme
    assert "### Codex" in readme
    assert "Plugins" in readme
    assert "codex plugin install" not in readme


def criar_plugin(raiz: Path, nome: str, version_codex: str, com_codex: bool = True) -> None:
    plugin_dir = raiz / "plugins" / nome
    (plugin_dir / ".claude-plugin").mkdir(parents=True)
    claude, codex = manifestos_validos()
    claude.update(name=nome, version="1.0.0")
    codex.update(name=nome, version=version_codex)
    (plugin_dir / ".claude-plugin" / "plugin.json").write_text(
        json.dumps(claude), encoding="utf-8"
    )
    if com_codex:
        (plugin_dir / ".codex-plugin").mkdir()
        (plugin_dir / ".codex-plugin" / "plugin.json").write_text(
            json.dumps(codex), encoding="utf-8"
        )
    criar_skills(plugin_dir, ["a"])


def escrever_marketplace(raiz: Path, nomes: list[str]) -> None:
    (raiz / ".claude-plugin").mkdir(exist_ok=True)
    plugins = [{"name": n, "source": f"./plugins/{n}"} for n in nomes]
    (raiz / ".claude-plugin" / "marketplace.json").write_text(
        json.dumps({"plugins": plugins}), encoding="utf-8"
    )


def test_marketplace_valida_todos_os_plugins(tmp_path: Path):
    criar_plugin(tmp_path, "p1", "1.0.0")
    criar_plugin(tmp_path, "p2", "2.0.0")
    escrever_marketplace(tmp_path, ["p1", "p2"])
    erros = validar_marketplace(tmp_path)
    assert erros == ["p2: version diverge entre os manifestos"]


def test_plugin_sem_codex_e_reportado(tmp_path: Path):
    criar_plugin(tmp_path, "p1", "1.0.0", com_codex=False)
    escrever_marketplace(tmp_path, ["p1"])
    assert any(e.startswith("p1: ") for e in validar_marketplace(tmp_path))
