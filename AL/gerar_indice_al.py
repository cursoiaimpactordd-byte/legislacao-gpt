#!/usr/bin/env python3
"""
Gera AL/indice.json automaticamente a partir dos arquivos da pasta AL do repositório.
Uso:
  python gerar_indice_al.py
Execute na raiz do repositório legislacao-gpt.
"""
import json
import re
from pathlib import Path

PASTA = Path("AL")
SAIDA = PASTA / "indice.json"

TIPOS = {
    "COM": "Comunicado",
    "DEC": "Decreto",
    "PORT": "Portaria",
    "IN": "Instrução Normativa",
    "INST": "Instrução Normativa"
}

IGNORAR_SUFIXOS = ("_faq.md", "_semantica.md", "_readme.txt")


def tipo_por_prefixo(prefixo: str) -> str:
    return TIPOS.get(prefixo.upper(), prefixo.upper())


def extrair_metadados(nome: str):
    # Exemplos esperados:
    # COM_001_2025.md
    # DEC_103586_2025.md
    base = nome.rsplit(".", 1)[0]
    partes = base.split("_")
    prefixo = partes[0].upper() if partes else "DOC"
    numero = partes[1] if len(partes) >= 2 else ""
    ano = partes[2] if len(partes) >= 3 and re.fullmatch(r"\d{4}", partes[2]) else ""
    tipo = tipo_por_prefixo(prefixo)
    return base, prefixo, tipo, numero, ano


def ler_assunto_ou_titulo(caminho: Path, tipo: str, numero: str, ano: str) -> str:
    try:
        texto = caminho.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return f"{tipo} nº {numero}/{ano} - Alagoas" if numero and ano else caminho.name

    for linha in texto.splitlines()[:80]:
        linha = linha.strip()
        if linha.startswith("#"):
            return linha.lstrip("#").strip()
        if linha.lower().startswith(("assunto:", "ementa:", "documento:")):
            return linha.split(":", 1)[1].strip()

    return f"{tipo} nº {numero}/{ano} - Alagoas" if numero and ano else caminho.name


def ler_resumo_semantico(base: str) -> str:
    sem = PASTA / f"{base}_semantica.md"
    readme = PASTA / f"{base}_readme.txt"
    for caminho in (sem, readme):
        if caminho.exists():
            texto = caminho.read_text(encoding="utf-8", errors="ignore").strip()
            linhas = [l.strip() for l in texto.splitlines() if l.strip()]
            if linhas:
                # Pega as primeiras linhas úteis sem criar um índice gigante.
                resumo = " ".join(linhas[:5])
                return resumo[:700]
    return "Consulte o arquivo completo para confirmação do conteúdo, vigência, obrigações e impactos."


def gerar_tags(tipo: str, assunto: str, texto_resumo: str):
    base = {"AL", "Alagoas", "SEFAZ/AL", tipo, "legislação estadual"}
    fonte = f"{assunto} {texto_resumo}".lower()
    palavras_chave = [
        "icms", "substituição tributária", "benefício fiscal", "incentivo fiscal",
        "prodesin", "nota fiscal", "nfe", "nf-e", "sped", "obrigação acessória",
        "prazo", "decreto", "portaria", "comunicado", "instrução normativa",
        "contribuinte", "sefaz", "difal", "fecoep", "regime especial"
    ]
    for p in palavras_chave:
        if p in fonte:
            base.add(p)
    return sorted(base)


def main():
    if not PASTA.exists():
        raise SystemExit("Pasta AL não encontrada. Execute o script na raiz do repositório.")

    entradas = []
    for caminho in sorted(PASTA.iterdir()):
        if not caminho.is_file():
            continue
        nome = caminho.name
        if nome == "indice.json":
            continue
        if nome.endswith(IGNORAR_SUFIXOS):
            continue
        if not nome.lower().endswith((".md", ".txt", ".json")):
            continue

        base, prefixo, tipo, numero, ano = extrair_metadados(nome)
        assunto = ler_assunto_ou_titulo(caminho, tipo, numero, ano)
        resumo = ler_resumo_semantico(base)
        relacionados = []
        for sufixo in ("_faq.md", "_readme.txt", "_semantica.md"):
            rel = f"{base}{sufixo}"
            if (PASTA / rel).exists():
                relacionados.append(rel)

        entradas.append({
            "id": base,
            "estado": "AL",
            "estado_nome": "Alagoas",
            "tipo": tipo,
            "numero": numero,
            "ano": ano,
            "assunto": assunto,
            "arquivo": nome,
            "arquivos_relacionados": relacionados,
            "resumo": resumo,
            "tags": gerar_tags(tipo, assunto, resumo),
            "origem": ""
        })

    SAIDA.write_text(json.dumps(entradas, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Índice gerado: {SAIDA} ({len(entradas)} documentos)")


if __name__ == "__main__":
    main()
