"""Gera o Word, calcula sumário estático pela renderização e confere estabilidade.

Uso: uv run --with pypdf python entregas/finalizar_entrega04.py
Requer o LibreOffice usado por renderizar_docx.py. O DOCX final contém os
números calculados, sem depender de atualização de campos pelo avaliador.
"""
from pathlib import Path
import json,re,subprocess,sys,unicodedata,shutil
from pypdf import PdfReader
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'entregas/entrega-04'
DOCX=OUT/'Projeto-Integrador-Banco-de-Dados-Entrega-04.docx'
PREVIEW=Path('/tmp/pi-entrega04-preview')

def normal(s):
 s=unicodedata.normalize('NFKD',s).encode('ascii','ignore').decode().lower()
 return re.sub('[^a-z0-9]','',s)

def main():
 for iteration in range(1,5):
  subprocess.run(['node','entregas/gerar_docx.js','--entrega=4'],cwd=ROOT,check=True)
  subprocess.run([sys.executable,'entregas/renderizar_docx.py',str(DOCX),str(PREVIEW)],cwd=ROOT,check=True)
  pdf=PREVIEW/(DOCX.stem+'.pdf');pages=PdfReader(pdf).pages
  texts=[p.extract_text() or '' for p in pages]
  titles=json.loads((OUT/'titulos.json').read_text())
  mapping={}
  # Os capítulos começam após capa e sumário; não selecionar a entrada no sumário.
  for title in titles:
   candidates=[]
   for i,t in enumerate(texts):
    if i<2: continue
    lines=t.splitlines()
    spans={normal(' '.join(lines[j:j+size])) for j in range(len(lines)) for size in (1,2,3)}
    if normal(title) in spans: candidates.append(i+1)
   if not candidates:raise RuntimeError('Título não encontrado na renderização: '+title)
   mapping[title]=candidates[0]
  old=json.loads((OUT/'sumario.json').read_text()) if (OUT/'sumario.json').exists() else {}
  if mapping==old:
   shutil.copyfile(pdf,OUT/pdf.name)
   evidence={'paginas':len(pages),'iteracoes_nesta_execucao':iteration,'sumario':mapping,
             'pdf':str((OUT/pdf.name).relative_to(ROOT)),
             'criterio':'Números calculados em renderizações consecutivas e estáveis.'}
   (ROOT/'apresentacao/evidencias/entrega04/paginacao.json').write_text(json.dumps(evidence,ensure_ascii=False,indent=2))
   print(f'PASSOU: sumário estável; {len(pages)} páginas.');return
  (OUT/'sumario.json').write_text(json.dumps(mapping,ensure_ascii=False,indent=2))
 raise RuntimeError('Sumário não estabilizou; revisar a paginação antes de entregar.')

if __name__=='__main__':main()
