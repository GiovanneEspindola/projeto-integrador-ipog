"""Preenche o sumario do .docx com o resultado ja calculado.

Por que existe: o sumario de um documento Word e um CAMPO, nao texto. O Word
calcula o conteudo dele ao abrir; qualquer outro leitor (LibreOffice, Google
Docs, visualizador do celular) mostra a pagina do sumario EM BRANCO, porque nao
executa campos. Como o documento vai ser aberto por outra pessoa, em um programa
que nao se sabe qual e, o campo precisa vir com o resultado dentro.

O que o script faz: converte o .docx em PDF, descobre em que pagina cada titulo
caiu, e grava essas linhas dentro do campo, entre o "separate" e o "end" — que e
exatamente onde o Word guarda o resultado que ele mesmo calcula. O campo continua
vivo: ao abrir no Word ele se recalcula sozinho e o numero se corrige se o
documento mudar.

Um detalhe que obriga a repetir o processo: preencher o sumario faz o proprio
sumario ocupar mais paginas, o que empurra todo o resto para a frente e muda os
numeros que acabaram de ser medidos. Por isso o script mede, preenche e mede de
novo, ate os numeros pararem de mudar.

    uv run --with pypdfium2 python entregas/preencher_sumario.py

Depende do LibreOffice do lado Windows apenas para medir as paginas.
"""
import pathlib
import re
import shutil
import subprocess
import sys
import unicodedata
import zipfile

import pypdfium2 as pdfium

RAIZ = pathlib.Path(__file__).resolve().parent.parent
assert (RAIZ / "pyproject.toml").exists(), f"raiz do projeto nao encontrada: {RAIZ}"
DOCX = RAIZ / "entregas" / "entrega-01" / "Projeto-Integrador-Banco-de-Dados.docx"

SOFFICE = pathlib.Path("/mnt/c/Program Files/LibreOffice/program/soffice.exe")
TRAB_WSL = pathlib.Path("/mnt/c/Users/giova/AppData/Local/Temp/pi-sumario")
TRAB_WIN = r"C:\Users\giova\AppData\Local\Temp\pi-sumario"

LARG = 9026          # posicao do tab a direita, em DXA (largura util da pagina)
MAX_VOLTAS = 5
FONTE = '<w:rFonts w:ascii="Calibri" w:cs="Calibri" w:eastAsia="Calibri" w:hAnsi="Calibri"/>'

# Os dois paragrafos vazios que o gerador deixa no lugar do resultado do campo.
# Os grupos capturam as marcas de abertura e de fechamento, que sao reaproveitadas
# dentro da primeira e da ultima linha do sumario.
CAMPO_VAZIO = re.compile(
    r"<w:p><w:r>(<w:fldChar w:fldCharType=\"begin\".*?<w:fldChar w:fldCharType=\"separate\"/>)"
    r"</w:r></w:p><w:p><w:r>(<w:fldChar w:fldCharType=\"end\"/>)</w:r></w:p>", re.S)


def normaliza(s):
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]", "", s)


def titulos(document_xml):
    """Extrai (nivel, texto) de cada paragrafo com estilo de titulo."""
    achados = []
    for par in re.findall(r"<w:p>.*?</w:p>", document_xml, re.S):
        m = re.search(r'<w:pStyle w:val="Heading(\d)"/>', par)
        if not m or int(m.group(1)) > 3:
            continue
        texto = "".join(re.findall(r"<w:t[^>]*>([^<]*)</w:t>", par))
        if texto.strip():
            achados.append((int(m.group(1)), texto.strip()))
    return achados


def paginas_do_pdf(pdf_path):
    pdf = pdfium.PdfDocument(pdf_path)
    return [pdf[i].get_textpage().get_text_range() for i in range(len(pdf))]


def paginas_do_sumario(paginas):
    """Quantas paginas o sumario ocupa, contadas pela linha pontilhada.

    A linha de um sumario termina em uma corrida de pontos ate o numero da
    pagina. Nenhuma pagina de texto corrido tem isso, entao contar paginas com
    varias corridas de ponto identifica exatamente o bloco do sumario.
    """
    n = 0
    for texto in paginas[1:]:                     # a capa nunca conta
        if len(re.findall(r"\.{5,}", texto)) < 5:
            break
        n += 1
    return n


def converte_pdf(docx_path):
    TRAB_WSL.mkdir(parents=True, exist_ok=True)
    for velho in TRAB_WSL.glob("medir.*"):
        velho.unlink()
    shutil.copyfile(docx_path, TRAB_WSL / "medir.docx")
    subprocess.run([str(SOFFICE), "--headless", "--norestore", "--convert-to", "pdf",
                    "--outdir", TRAB_WIN, rf"{TRAB_WIN}\medir.docx"],
                   capture_output=True, text=True)
    pdf = TRAB_WSL / "medir.pdf"
    if not pdf.exists():
        sys.exit("LibreOffice nao gerou o PDF de medicao")
    return pdf


def mapeia(docx_path, itens):
    """Descobre em que pagina cada titulo caiu, no documento como ele vai sair.

    As paginas do proprio sumario sao puladas: depois de preenchido, todo titulo
    aparece tambem la, e a busca acharia essa ocorrencia em vez da verdadeira.
    """
    brutas = paginas_do_pdf(converte_pdf(docx_path))
    paginas = [normaliza(t) for t in brutas]
    mapa, procura_de = [], 1 + paginas_do_sumario(brutas)
    for nivel, texto in itens:
        alvo = normaliza(texto)[:45]
        achou = next((p for p in range(procura_de, len(paginas)) if alvo in paginas[p]), None)
        if achou is None:      # titulo dividido pela quebra de linha do PDF
            achou = next((p for p in range(procura_de, len(paginas))
                          if alvo[:22] in paginas[p]), procura_de)
        mapa.append((nivel, texto, achou + 1))
        procura_de = achou
    return mapa


def linhas_xml(mapa, abre, fecha):
    """Monta as linhas do sumario, ja com as marcas de inicio e fim do campo.

    As marcas vao DENTRO da primeira e da ultima linha, e nao em paragrafos
    proprios: um paragrafo vazio a mais no fim do campo era suficiente para
    empurrar uma pagina em branco para dentro do documento.
    """
    saida = []
    ultimo = len(mapa) - 1
    for k, (nivel, texto, pagina) in enumerate(mapa):
        recuo = (nivel - 1) * 260
        negrito = "<w:b/><w:bCs/>" if nivel == 1 else ""
        cor = '<w:color w:val="1A3D5C"/>' if nivel == 1 else ""
        rpr = f"<w:rPr>{FONTE}{negrito}{cor}<w:sz w:val=\"20\"/><w:szCs w:val=\"20\"/></w:rPr>"
        esc = texto.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
        saida.append(
            "<w:p><w:pPr>"
            f'<w:tabs><w:tab w:val="right" w:leader="dot" w:pos="{LARG}"/></w:tabs>'
            f'<w:spacing w:before="{30 if nivel == 1 else 0}" w:after="0"/>'
            f'<w:ind w:left="{recuo}" w:right="0"/>'
            "</w:pPr>"
            + (f"<w:r>{abre}</w:r>" if k == 0 else "")
            + f'<w:r>{rpr}<w:t xml:space="preserve">{esc}</w:t></w:r>'
            + f"<w:r>{rpr}<w:tab/><w:t>{pagina}</w:t></w:r>"
            + (f"<w:r>{fecha}</w:r>" if k == ultimo else "")
            + "</w:p>")
    return "".join(saida)


def injeta(original_bytes, mapa, destino):
    with zipfile.ZipFile(destino, "w", zipfile.ZIP_DEFLATED) as saida:
        with zipfile.ZipFile(original_bytes) as origem:
            for item in origem.infolist():
                dado = origem.read(item.filename)
                if item.filename == "word/document.xml":
                    xml = dado.decode("utf-8")
                    m = CAMPO_VAZIO.search(xml)
                    if not m:
                        sys.exit("campo do sumario nao encontrado — o gerar_docx.js mudou?")
                    xml = xml[:m.start()] + linhas_xml(mapa, m.group(1), m.group(2)) + xml[m.end():]
                    dado = xml.encode("utf-8")
                saida.writestr(item, dado)


def main():
    if not SOFFICE.exists():
        sys.exit(f"LibreOffice nao encontrado em {SOFFICE}")
    if not DOCX.exists():
        sys.exit(f"{DOCX} nao existe — rode antes: cd entregas && npm run docx")

    limpo = TRAB_WSL / "sem-sumario.docx"
    TRAB_WSL.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(DOCX, limpo)

    with zipfile.ZipFile(limpo) as z:
        itens = titulos(z.read("word/document.xml").decode("utf-8"))
    print(f"{len(itens)} titulos no documento")

    # Chute inicial medido no documento de sumario vazio; a partir dai o ciclo
    # sempre mede o documento JA PREENCHIDO, que e o que vai ser entregue —
    # medir o vazio erra por uma pagina, porque ele pagina diferente.
    mapa, atual = mapeia(limpo, itens), None
    for volta in range(1, MAX_VOLTAS + 1):
        atual = TRAB_WSL / f"volta{volta}.docx"
        injeta(limpo, mapa, atual)
        conferido = mapeia(atual, itens)
        print(f"volta {volta}: capitulo 1 na pagina {conferido[0][2]}, "
              f"ultimo titulo na {conferido[-1][2]}")
        if conferido == mapa:
            break
        mapa = conferido
    else:
        sys.exit(f"os numeros nao estabilizaram em {MAX_VOLTAS} voltas")

    shutil.copyfile(atual, DOCX)
    print(f"\nsumario preenchido em {DOCX.relative_to(RAIZ)} "
          f"({len(itens)} linhas)")


if __name__ == "__main__":
    main()
