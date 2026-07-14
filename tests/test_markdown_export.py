from server.markdown_export import docspec_to_markdown

DOCSPEC = {
    "topic": "Estados físicos da água",
    "ageRange": "8-9 anos (3.º ano)",
    "duration": 40,
    "objectives": [
        "Identificar os três estados físicos da água",
        "Relacionar a temperatura com as mudanças de estado",
    ],
    "materials": ["Tablet com browser"],
    "memAlignment": {
        "modules": ["TEA (Trabalho de Estudo Autónomo)"],
        "socialOrganization": "individual → pares → turma",
    },
    "sessionFlow": "0-5min ativação → 5-35min exploração → 35-40min síntese",
    "curriculum": {
        "ae": [
            {
                "subject": "Estudo do Meio",
                "year": "3.º ano",
                "descriptor": "Identificar propriedades físicas da água",
            }
        ],
        "competencies": ["PA-I: Saber científico, técnico e tecnológico"],
    },
    "units": [
        {
            "summary": "Os três estados da água dependem da temperatura",
            "textDescription": "A temperatura determina o estado da água.",
            "interaction": {
                "constraint": "A água muda de estado a 0°C e 100°C",
                "assessment": "O aluno regista as temperaturas de mudança",
            },
            "differentiation": {
                "support": "Slider com 3 posições",
                "standard": "Slider contínuo",
                "challenge": "Gráfico de energia",
            },
            "maker": {
                "type": "minecraft",
                "challenge": "Constrói o ciclo da água",
                "groupSize": "3-4",
                "connection": "Reconstrói o ciclo em 3D",
                "communication": "Tour guiado ao mundo",
                "alternatives": ["Lego com etiquetas"],
            },
            "duration": 20,
        }
    ],
}


def test_markdown_contains_title_objectives_and_units():
    md = docspec_to_markdown(DOCSPEC)

    assert md.startswith("# Estados físicos da água")
    assert "## Objetivos de aprendizagem" in md
    assert "- Identificar os três estados físicos da água" in md
    assert "## Unit 1: Os três estados da água dependem da temperatura (20 min)" in md
    assert "**Constraint:** A água muda de estado a 0°C e 100°C" in md
    assert "- 🟢 Apoio: Slider com 3 posições" in md
    assert "### 🛠️ Maker — Minecraft" in md
    assert "- **Alternativas:** Lego com etiquetas" in md
    assert "**Duração:** 40 minutos" in md
    assert "## Alinhamento MEM" in md
    assert "## Fluxo da sessão" in md
    assert "### Aprendizagens Essenciais" in md
    assert "- **Estudo do Meio (3.º ano):** Identificar propriedades físicas da água" in md


def test_markdown_minimal_docspec_does_not_crash():
    md = docspec_to_markdown({"topic": "Teste", "units": []})
    assert md.startswith("# Teste")
    assert "## Objetivos de aprendizagem" in md
