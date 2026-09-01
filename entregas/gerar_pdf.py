"""Monta o PDF da Entrega 01 a partir dos Markdown de docs/ e dos diagramas.

Junta capa, sumario, os cinco documentos (docs/00 a docs/04), as tres figuras e
um apendice com a validacao da carga. O PDF sai em entregas/entrega-01/.

Roda sem sujar o ambiente do projeto, porque reportlab e pillow servem so para
isto e nao sao dependencias do trabalho:

    uv run --with reportlab --with pillow python entregas/gerar_pdf.py

O conversor de Markdown daqui e proposital e minimo: cobre exatamente o que os
documentos usam (titulos, tabelas, blocos de codigo, listas, citacoes e enfase).
Nao e um conversor de uso geral.
"""
import hashlib
import html as _html
import io, pathlib, re, sys

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (BaseDocTemplate, Frame, HRFlowable, Image,
                                KeepTogether, NextPageTemplate, PageBreak,
                                PageTemplate, Paragraph, Preformatted, Spacer,
                                Table, TableStyle)
from reportlab.platypus.tableofcontents import TableOfContents

RAIZ = pathlib.Path(__file__).resolve().parent.parent
assert (RAIZ / "pyproject.toml").exists(), f"raiz do projeto nao encontrada: {RAIZ}"
SAIDA = RAIZ / "entregas" / "entrega-01" / "Entrega-01-Projeto-Integrador-Banco-de-Dados.pdf"

pdfmetrics.registerFont(TTFont("Mono", "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"))
pdfmetrics.registerFont(TTFont("Mono-Bold", "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"))

# fora do WinAnsi das fontes internas; trocados pelo equivalente ASCII
TROCA = {"→": "->", "↔": "<->", "≥": ">=", "−": "-"}

LARG, ALT = A4
MARGEM = 2.2 * cm
UTIL = LARG - 2 * MARGEM

ss = getSampleStyleSheet()
def estilo(nome, **kw):
    base = kw.pop("parent", ss["Normal"])
    return ParagraphStyle(nome, parent=base, **kw)

E = {
    "corpo": estilo("corpo", fontName="Times-Roman", fontSize=10.2, leading=14.6,
                    alignment=TA_JUSTIFY, spaceAfter=7),
    "h1": estilo("h1", fontName="Helvetica-Bold", fontSize=19, leading=23,
                 spaceBefore=0, spaceAfter=14, textColor=colors.HexColor("#1a3d5c")),
    "h2": estilo("h2", fontName="Helvetica-Bold", fontSize=13.5, leading=17,
                 spaceBefore=16, spaceAfter=7, textColor=colors.HexColor("#1a3d5c")),
    "h3": estilo("h3", fontName="Helvetica-Bold", fontSize=11.2, leading=14,
                 spaceBefore=12, spaceAfter=5, textColor=colors.HexColor("#33526b")),
    "h4": estilo("h4", fontName="Helvetica-BoldOblique", fontSize=10.2, leading=13,
                 spaceBefore=9, spaceAfter=4),
    "cita": estilo("cita", fontName="Times-Italic", fontSize=9.6, leading=13.4,
                   leftIndent=14, rightIndent=8, spaceAfter=8,
                   textColor=colors.HexColor("#3d3d3d")),
    "lista": estilo("lista", fontName="Times-Roman", fontSize=10.2, leading=14.2,
                    leftIndent=16, bulletIndent=5, spaceAfter=3, alignment=TA_JUSTIFY),
    "codigo": estilo("codigo", fontName="Mono", fontSize=7.4, leading=9.6,
                     leftIndent=6, textColor=colors.HexColor("#1c1c1c")),
    "celula": estilo("celula", fontName="Times-Roman", fontSize=8.4, leading=11),
    "celula_th": estilo("celula_th", fontName="Helvetica-Bold", fontSize=8.4, leading=11,
                        textColor=colors.white),
    "legenda": estilo("legenda", fontName="Helvetica-Oblique", fontSize=8.6, leading=11,
                      alignment=TA_CENTER, spaceBefore=5, spaceAfter=4,
                      textColor=colors.HexColor("#444444")),
}

def limpa(t):
    for a, b in TROCA.items():
        t = t.replace(a, b)
    return t

def inline(t, cor_codigo="#8a2b2b"):
    """Markdown de linha para as tags do reportlab.

    O codigo entre crases sai de cena antes de negrito e italico agirem: sem
    isso, um `docs/02-*` viraria abertura de italico e quebraria o parser.
    """
    t = limpa(t)
    t = _html.escape(t, quote=False)

    guardado = []
    def guarda(m):
        guardado.append(m.group(1))
        return f"\x00{len(guardado) - 1}\x00"
    t = re.sub(r"`([^`]+)`", guarda, t)

    t = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", t)
    t = re.sub(r"(?<![\w*])\*([^*\n]+)\*(?![\w*])", r"<i>\1</i>", t)
    t = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r"\1", t)
    t = re.sub(r"&lt;(https?://[^&]+)&gt;", r"\1", t)

    def devolve(m):
        corpo = guardado[int(m.group(1))]
        return f'<font face="Mono" size="8.6" color="{cor_codigo}">{corpo}</font>'
    return re.sub(r"\x00(\d+)\x00", devolve, t)

class Doc(BaseDocTemplate):
    def __init__(self, *a, **kw):
        super().__init__(*a, **kw)
        quadro = Frame(MARGEM, MARGEM, UTIL, ALT - 2 * MARGEM, id="n")
        self.addPageTemplates([
            PageTemplate(id="capa", frames=[quadro]),
            PageTemplate(id="miolo", frames=[quadro], onPage=self.rodape),
        ])
        self._n_tit = 0

    def rodape(self, canv, doc):
        canv.saveState()
        canv.setFont("Helvetica", 7.6)
        canv.setFillColor(colors.HexColor("#777777"))
        canv.drawString(MARGEM, 1.35 * cm,
                        "Projeto Integrador — Projeto 3: Banco de Dados · Entrega 01")
        canv.drawRightString(LARG - MARGEM, 1.35 * cm, str(canv.getPageNumber() - 1))
        canv.setStrokeColor(colors.HexColor("#cccccc"))
        canv.line(MARGEM, 1.7 * cm, LARG - MARGEM, 1.7 * cm)
        canv.restoreState()

    def afterFlowable(self, flow):
        if not isinstance(flow, Paragraph):
            return
        nome = flow.style.name
        if nome not in ("h1", "h2"):
            return
        if flow.getPlainText().strip() == "Sumário":
            return
        nivel = {"h1": 0, "h2": 1}[nome]
        texto = re.sub(r"<[^>]+>", "", flow.getPlainText())
        # a chave TEM de ser deterministica: um contador daria nomes diferentes
        # a cada passada do multiBuild e o sumario nunca convergiria
        chave = "tit_" + hashlib.md5(f"{nivel}|{texto}".encode()).hexdigest()[:12]
        self.canv.bookmarkPage(chave)
        self.notify("TOCEntry", (nivel, texto, self.page - 1, chave))


def tabela(linhas):
    """Converte um bloco de tabela markdown num flowable Table."""
    def celulas(l):
        l = l.strip()
        if l.startswith("|"): l = l[1:]
        if l.endswith("|"): l = l[:-1]
        return [c.strip() for c in re.split(r"(?<!\\)\|", l)]

    cab = celulas(linhas[0])
    alinh = celulas(linhas[1])
    corpo = [celulas(l) for l in linhas[2:] if l.strip()]
    n = len(cab)

    dados = [[Paragraph(inline(c, cor_codigo="#ffffff"), E["celula_th"]) for c in cab]]
    for linha in corpo:
        linha = (linha + [""] * n)[:n]
        dados.append([Paragraph(inline(c.replace("\\|", "|")), E["celula"]) for c in linha])

    # largura proporcional ao conteudo, com piso e teto
    peso = []
    for i in range(n):
        m = max([len(re.sub(r"[*`]", "", cab[i]))] +
                [len(re.sub(r"[*`]", "", (l + [""] * n)[i])) for l in corpo] or [1])
        peso.append(max(4, min(m, 46)))
    total = sum(peso)
    larguras = [UTIL * p / total for p in peso]

    t = Table(dados, colWidths=larguras, repeatRows=1, hAlign="LEFT")
    estilos = [
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1a3d5c")),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#b8c4cc")),
        ("LEFTPADDING", (0, 0), (-1, -1), 4),
        ("RIGHTPADDING", (0, 0), (-1, -1), 4),
        ("TOPPADDING", (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1),
         [colors.white, colors.HexColor("#f2f5f7")]),
    ]
    for i, a in enumerate(alinh):
        if a.endswith(":") and a.startswith(":"):
            estilos.append(("ALIGN", (i, 0), (i, -1), "CENTER"))
        elif a.endswith(":"):
            estilos.append(("ALIGN", (i, 0), (i, -1), "RIGHT"))
    t.setStyle(TableStyle(estilos))
    return t


def bloco_codigo(linhas):
    txt = limpa("\n".join(linhas)).replace("\t", "    ")
    p = Preformatted(txt, E["codigo"])
    caixa = Table([[p]], colWidths=[UTIL], hAlign="LEFT")
    caixa.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f4f4f2")),
        ("BOX", (0, 0), (-1, -1), 0.4, colors.HexColor("#d5d5d0")),
        ("LEFTPADDING", (0, 0), (-1, -1), 7),
        ("RIGHTPADDING", (0, 0), (-1, -1), 7),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    return caixa


def figura(caminho, legenda, altura_max=20.2 * cm):
    from PIL import Image as PILImage
    with PILImage.open(caminho) as im:
        lp, ap = im.size
    larg = UTIL
    alt = larg * ap / lp
    if alt > altura_max:
        alt = altura_max
        larg = alt * lp / ap
    img = Image(str(caminho), width=larg, height=alt)
    img.hAlign = "CENTER"
    return [img, Paragraph(legenda, E["legenda"])]


def converte(md, figuras=None):
    """Markdown -> lista de flowables. figuras: {texto_do_h2: [flowables]}"""
    figuras = figuras or {}
    fl = []
    linhas = md.splitlines()
    i = 0
    lista_num = 0
    while i < len(linhas):
        ln = linhas[i]
        cru = ln.rstrip()

        if not cru.strip():
            i += 1; lista_num = 0; continue

        if cru.startswith("```"):
            j = i + 1
            buf = []
            while j < len(linhas) and not linhas[j].startswith("```"):
                buf.append(linhas[j]); j += 1
            fl.append(bloco_codigo(buf)); fl.append(Spacer(1, 7))
            i = j + 1; continue

        if cru.startswith("|") and i + 1 < len(linhas) and re.match(r"^\|[\s:|-]+\|?$", linhas[i + 1].strip()):
            j = i
            buf = []
            while j < len(linhas) and linhas[j].strip().startswith("|"):
                buf.append(linhas[j]); j += 1
            fl.append(Spacer(1, 3)); fl.append(tabela(buf)); fl.append(Spacer(1, 9))
            i = j; continue

        if re.match(r"^(---+|\*\*\*+)$", cru.strip()):
            fl.append(Spacer(1, 4))
            fl.append(HRFlowable(width="100%", thickness=0.5,
                                 color=colors.HexColor("#cccccc")))
            fl.append(Spacer(1, 8))
            i += 1; continue

        m = re.match(r"^(#{1,4})\s+(.*)$", cru)
        if m:
            nivel = len(m.group(1))
            texto = m.group(2).strip()
            chave = {1: "h1", 2: "h2", 3: "h3", 4: "h4"}[nivel]
            if nivel == 2:
                for gatilho, flows in figuras.items():
                    if gatilho and texto.startswith(gatilho):
                        fl.extend(flows); figuras[gatilho] = []
            fl.append(Paragraph(inline(texto), E[chave]))
            i += 1; continue

        if cru.lstrip().startswith(">"):
            buf = []
            while i < len(linhas) and linhas[i].lstrip().startswith(">"):
                buf.append(re.sub(r"^\s*>\s?", "", linhas[i])); i += 1
            fl.append(Paragraph(inline(" ".join(x.strip() for x in buf if x.strip())),
                                E["cita"]))
            continue

        m = re.match(r"^(\s*)[-*]\s+(.*)$", cru)
        if m:
            texto, i = junta_item(linhas, i, m.group(2))
            fl.append(Paragraph(inline(texto), E["lista"], bulletText="•"))
            continue

        m = re.match(r"^(\s*)(\d+)\.\s+(.*)$", cru)
        if m:
            lista_num += 1
            texto, i = junta_item(linhas, i, m.group(3))
            fl.append(Paragraph(inline(texto), E["lista"], bulletText=f"{lista_num}."))
            continue

        buf = [cru]
        i += 1
        while i < len(linhas) and linhas[i].strip() and not re.match(
                r"^(#{1,4}\s|```|\||>|\s*[-*]\s|\s*\d+\.\s|---+$)", linhas[i]):
            buf.append(linhas[i].strip()); i += 1
        fl.append(Paragraph(inline(" ".join(buf)), E["corpo"]))
    return fl


def junta_item(linhas, i, primeiro):
    """Junta as linhas de continuacao de um item de lista."""
    buf = [primeiro]
    i += 1
    while (i < len(linhas) and linhas[i].strip()
           and re.match(r"^[ \t]+\S", linhas[i])
           and not re.match(r"^\s*([-*]|\d+\.)\s", linhas[i])
           and not linhas[i].lstrip().startswith(("|", ">", "```", "#"))):
        buf.append(linhas[i].strip()); i += 1
    return " ".join(buf), i


def capa():
    c_tit = estilo("c_tit", fontName="Helvetica-Bold", fontSize=25, leading=31,
                   alignment=TA_CENTER, textColor=colors.HexColor("#1a3d5c"))
    c_sub = estilo("c_sub", fontName="Helvetica", fontSize=14, leading=19,
                   alignment=TA_CENTER, textColor=colors.HexColor("#33526b"))
    c_lin = estilo("c_lin", fontName="Times-Roman", fontSize=12, leading=19,
                   alignment=TA_CENTER)
    c_peq = estilo("c_peq", fontName="Helvetica", fontSize=10, leading=15,
                   alignment=TA_CENTER, textColor=colors.HexColor("#555555"))
    return [
        Spacer(1, 2.4 * cm),
        Paragraph("CURSO DE BANCO DE DADOS", c_peq),
        Paragraph("PROJETO INTEGRADOR", c_peq),
        Spacer(1, 1.9 * cm),
        HRFlowable(width="62%", thickness=1.1, color=colors.HexColor("#1a3d5c")),
        Spacer(1, 0.9 * cm),
        Paragraph("Projeto 3 — Banco de Dados", c_tit),
        Spacer(1, 0.5 * cm),
        Paragraph("Modelagem Híbrida: SQL <i>vs</i> NoSQL", c_sub),
        Spacer(1, 0.3 * cm),
        Paragraph("sobre o dataset Northwind Traders", c_sub),
        Spacer(1, 0.9 * cm),
        HRFlowable(width="62%", thickness=1.1, color=colors.HexColor("#1a3d5c")),
        Spacer(1, 1.6 * cm),
        Paragraph("<b>Entrega 01</b> — Análise de Negócio, Modelo Conceitual,", c_lin),
        Paragraph("Plano Híbrido e Modelo Relacional", c_lin),
        Spacer(1, 3.6 * cm),
        Paragraph("<b>Aluno</b>", c_peq),
        Paragraph("Giovanne Espindola", c_lin),
        Spacer(1, 0.8 * cm),
        Paragraph("<b>Professora</b>", c_peq),
        Paragraph("Fabiana Rocha", c_lin),
        Spacer(1, 2.6 * cm),
        Paragraph("06 de setembro de 2026", c_peq),
        NextPageTemplate("miolo"),
        PageBreak(),
    ]


def sumario():
    toc = TableOfContents()
    toc.levelStyles = [
        estilo("t0", fontName="Helvetica-Bold", fontSize=10.6, leading=19,
               textColor=colors.HexColor("#1a3d5c")),
        estilo("t1", fontName="Times-Roman", fontSize=9.8, leading=14.4, leftIndent=16),
    ]
    return [Paragraph("Sumário", E["h1"]),
            HRFlowable(width="100%", thickness=0.6, color=colors.HexColor("#1a3d5c")),
            Spacer(1, 10), toc, PageBreak()]


def apendice():
    ev = RAIZ / "apresentacao" / "evidencias" / "03-validacao-carga-nw.txt"
    txt = ev.read_text(encoding="utf-8")
    fl = [Paragraph("Apêndice A — Validação da carga <font size=13>public → nw</font>",
                    E["h1"]),
          Paragraph(
              "Saída bruta de <font face='Mono' size='8.6'>sql/21_validacao_carga.sql</font>, "
              "executada contra o banco. É a prova de que a migração para o schema do projeto "
              "não perdeu linha, centavo nem coluna. As outras treze evidências do trabalho "
              "estão no repositório, em <font face='Mono' size='8.6'>apresentacao/evidencias/</font>.",
              E["corpo"]),
          Spacer(1, 8)]
    # o cabecalho de tres linhas ja esta explicado no paragrafo acima
    corpo = "\n".join(txt.splitlines()[4:])
    for pedaco in re.split(r"\n(?=={3,})", corpo):
        pedaco = pedaco.strip("\n")
        if pedaco.strip():
            fl.append(bloco_codigo(pedaco.splitlines()))
            fl.append(Spacer(1, 7))
    return fl


DOCS = [
    ("docs/00-definicao-do-trabalho.md", {}),
    ("docs/01-analise-negocio.md", {}),
    ("docs/02-modelo-conceitual.md",
     {"1. O arquivo do diagrama": figura(
         RAIZ / "docs/diagramas/er-conceitual.png",
         "<b>Figura 1</b> — Modelo Entidade-Relacionamento conceitual do Northwind Traders.")}),
    ("docs/03-plano-hibrido.md",
     {"3. A arquitetura escolhida": figura(
         RAIZ / "docs/diagramas/arquitetura-hibrida.png",
         "<b>Figura 2</b> — Arquitetura híbrida: PostgreSQL como fonte, MongoDB como cópia documental.")}),
    ("docs/04-modelo-relacional.md",
     {"2. O que o banco passou a impedir": figura(
         RAIZ / "docs/diagramas/er-logico.png",
         "<b>Figura 3</b> — Modelo Entidade-Relacionamento lógico do schema <b>nw</b>, gerado do banco.")}),
]


def main():
    hist = []
    hist += capa()
    hist += sumario()
    for i, (rel, figs) in enumerate(DOCS):
        md = (RAIZ / rel).read_text(encoding="utf-8")
        hist += converte(md, figs)
        hist.append(PageBreak())
    hist += apendice()

    SAIDA.parent.mkdir(parents=True, exist_ok=True)
    doc = Doc(str(SAIDA), pagesize=A4,
              leftMargin=MARGEM, rightMargin=MARGEM,
              topMargin=MARGEM, bottomMargin=2.3 * cm,
              title="Entrega 01 — Projeto Integrador, Projeto 3: Banco de Dados",
              author="Giovanne Espindola",
              subject="Modelagem Híbrida SQL vs NoSQL sobre o dataset Northwind Traders")
    doc.multiBuild(hist, maxPasses=20)
    print(f"gerado: {SAIDA.relative_to(RAIZ)}")


if __name__ == "__main__":
    main()
