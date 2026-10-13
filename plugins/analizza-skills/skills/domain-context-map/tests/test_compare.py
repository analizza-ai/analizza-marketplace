import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import fixtures

SCRIPTS = Path(__file__).resolve().parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS))

import guide_file  # noqa: E402
import inventory  # noqa: E402


class CompareTest(unittest.TestCase):

    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        fixtures.write(self.root, fixtures.KOTLIN_OPENSPEC)
        self.found = inventory.inventory(self.root)

    def guide(self, stamp):
        path = self.root / "docs" / "domain" / "domain-guide.md"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            f"{stamp}\n# Guia\n\n{guide_file.DESCRIPTION_TITLE}\n\nContas.\n\n{guide_file.GUIDE_TITLE}\n\n### O que é\n\nx\n",
            encoding="utf-8",
        )
        return path

    def without_remote(self):
        return {key: value for key, value in self.found.items() if key != "remote"}

    def run_script(self, *arguments):
        done = subprocess.run(
            [sys.executable, str(SCRIPTS / "inventory.py"), str(self.root), *arguments], capture_output=True, text=True,
        )
        self.assertEqual(0, done.returncode, done.stderr)
        return done.stdout

    def test_o_carimbo_volta_inteiro_pela_leitura(self):
        parsed = guide_file.parse(inventory.stamp(self.found, "2026-10-13") + "\n")

        self.assertEqual("2026-10-13", parsed.stamp["gerado"])
        self.assertEqual(self.without_remote(), parsed.stamp["inventario"])

    def test_o_carimbo_cabe_em_linhas_simples(self):
        lines = inventory.stamp(self.found, "2026-10-13").splitlines()

        self.assertEqual("<!-- olly-guide", lines[0])
        self.assertEqual("-->", lines[-1])
        self.assertEqual(5, len(lines))

    def test_inventario_igual_nao_tem_mudanca(self):
        self.assertEqual([], inventory.changes(self.found, copy.deepcopy(self.found)))

    def test_contagem_de_arquivos_nao_e_mudanca(self):
        new = copy.deepcopy(self.found)
        new["arquivos"] += 30
        new["rotas"][0]["arquivos"] += 5
        new["commit"] = "fffffff"

        self.assertEqual([], inventory.changes(self.found, new))

    def test_pastas_novas_e_sumidas_por_camada(self):
        new = copy.deepcopy(self.found)
        new["rotas"] = [{"pasta": "src/main/kotlin/app/api", "arquivos": 2}]
        new["migrations"].append({"pasta": "db/extra/migrations", "arquivos": 1})

        self.assertEqual(
            [
                "rotas: pasta nova src/main/kotlin/app/api",
                "rotas: pasta sumiu src/main/kotlin/app/presenter/routes",
                "migrations: pasta nova db/extra/migrations",
            ],
            inventory.changes(self.found, new),
        )

    def test_framework_de_specs_modulos_e_sufixos(self):
        new = copy.deepcopy(self.found)
        new["specs"]["frameworks"] = ["superpowers"]
        new["specs"]["pastas"] = ["docs/superpowers"]
        new["modulos"][0]["framework"] = "ktor"
        new["modulos"].append({"caminho": "web", "build": "package.json", "linguagem": "typescript", "framework": "nextjs"})
        new["sufixos"] = [{"sufixo": "UseCase", "arquivos": 4}]

        found = inventory.changes(self.found, new)

        self.assertIn("specs: framework mudou de openspec para superpowers", found)
        self.assertIn("specs: pasta nova docs/superpowers", found)
        self.assertIn("specs: pasta sumiu openspec", found)
        self.assertIn("módulos: novo web", found)
        self.assertIn("módulos: . mudou de spring para ktor", found)
        self.assertIn("sufixos: novo UseCase", found)
        self.assertIn("sufixos: sumiu Handler", found)

    def test_inventario_antigo_sem_uma_chave_nao_derruba(self):
        self.assertEqual(["rotas: pasta nova src/main/kotlin/app/presenter/routes"], inventory.changes({}, {"rotas": self.found["rotas"]}))

    def test_linha_de_comando_compara_com_o_carimbo_do_arquivo(self):
        guide = self.guide(inventory.stamp(self.found, "2026-10-01"))
        # Nome de uma palavra so: nao cria sufixo novo, a unica mudanca e a pasta.
        fixtures.write(self.root, {"src/main/kotlin/app/api/Health.kt": "@RestController\nclass Health\n"})

        result = json.loads(self.run_script("--compare", str(guide)))

        self.assertEqual(
            {"carimbo": True, "gerado": "2026-10-01", "commit": None, "mudancas": ["rotas: pasta nova src/main/kotlin/app/api"]},
            result,
        )

    def test_arquivo_sem_carimbo_ou_inexistente_diz_que_nao_ha_com_o_que_comparar(self):
        handwritten = self.guide("")

        self.assertEqual(
            {"carimbo": False, "gerado": None, "commit": None, "mudancas": []},
            json.loads(self.run_script("--compare", str(handwritten))),
        )
        self.assertFalse(json.loads(self.run_script("--compare", str(self.root / "nao-existe.md")))["carimbo"])

    def test_carimbo_com_inventario_fora_do_formato_nao_e_carimbo(self):
        whole = self.without_remote()
        for label, broken in (
            ("vazio", {}),
            ("sem modulos", {key: value for key, value in whole.items() if key != "modulos"}),
            ("rotas com numero", {**whole, "rotas": [1]}),
            ("rotas sem pasta", {**whole, "rotas": [{"arquivos": 2}]}),
            ("modulos com texto", {**whole, "modulos": ["a"]}),
            ("modulos com caminho lista", {**whole, "modulos": [{"caminho": ["a"]}]}),
            ("specs com texto", {**whole, "specs": "openspec"}),
            ("frameworks com numero", {**whole, "specs": {"frameworks": [1], "pastas": []}}),
            ("sufixos sem nome", {**whole, "sufixos": [{}]}),
            ("camada nula", {**whole, "dominio": None}),
        ):
            stamp = "<!-- olly-guide\ngerado: 2026-10-01\ncommit: abc1234\ninventario: " + json.dumps(broken) + "\n-->"
            with self.subTest(label):
                self.assertEqual(
                    {"carimbo": False, "gerado": None, "commit": None, "mudancas": []},
                    json.loads(self.run_script("--compare", str(self.guide(stamp)))),
                )

    def test_arquivo_novo_que_so_reordena_um_empate_nao_muda_os_sufixos(self):
        words = ["Alpha", "Bravo", "Charlie", "Delta", "Echo", "Foxtrot", "Golf", "Hotel", "India", "Juliet", "Kilo", "Lima"]
        fixtures.write(self.root, {
            f"src/main/kotlin/app/outros/Caso{index}{word}.kt": "class X\n" for word in words for index in range(3)
        })
        old = inventory.inventory(self.root)
        fixtures.write(self.root, {"src/main/kotlin/app/outros/Caso9Lima.kt": "class X\n"})

        self.assertEqual([], inventory.changes(old, inventory.inventory(self.root)))

    def test_linha_de_comando_emite_o_carimbo(self):
        parsed = guide_file.parse(self.run_script("--stamp"))

        self.assertRegex(parsed.stamp["gerado"], r"^\d{4}-\d{2}-\d{2}$")
        self.assertEqual(self.without_remote(), parsed.stamp["inventario"])


if __name__ == "__main__":
    unittest.main()
