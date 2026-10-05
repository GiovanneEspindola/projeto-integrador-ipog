"""Confere o pacote final, seus códigos incorporados e evidências obrigatórias.

Uso: uv run --with pypdf python entregas/verificar_entrega03.py
"""
from pathlib import Path
from zipfile import ZipFile
from html.parser import HTMLParser
import hashlib,json,re,xml.etree.ElementTree as ET
from pypdf import PdfReader
ROOT=Path(__file__).resolve().parents[1]
EV=ROOT/'apresentacao/evidencias/entrega03'
OUT=ROOT/'entregas/entrega-03'

def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(p.read_text())
class HTMLAudit(HTMLParser):
 def __init__(self):super().__init__();self.ids=[];self.links=[];self.images=[];self.sources=0;self.details=0
 def handle_starttag(self,tag,attrs):
  a=dict(attrs)
  if 'id' in a:self.ids.append(a['id'])
  if tag=='a':self.links.append(a.get('href',''))
  if tag=='img':self.images.append(a.get('src',''))
  if tag=='details':
   self.details+=1
   if a.get('class')=='source':self.sources+=1

def main():
 old=load(EV/'anteriores.sha256.json')
 for f,h in old.items():assert digest(ROOT/f)==h,f
 for f,h in load(EV/'manifesto.json')['sha256'].items():assert digest(ROOT/f)==h,f
 results=load(EV/'resultados.json');assert len(results)==16
 py=load(EV/'conferencia-python.json');assert py['pares']==16 and not py['divergentes']
 assert all(x['equivalent'] for x in results.values())
 assert sum(x['linhas'] for x in load(EV/'migracao.json'))==3311
 tests=load(EV/'testes-fronteira.json');assert len(tests)==38
 perf=load(ROOT/'bench/results/entrega03/catalogo.json');assert len(perf)==16
 for banks in perf.values():
  for data in banks.values():assert len(data['amostras_ms'])==20
 assert len(load(ROOT/'bench/results/entrega03/otimizacoes.json'))==4
 ns={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
 docx=OUT/'Projeto-Integrador-Banco-de-Dados-Entrega-03.docx'
 with ZipFile(docx) as z:xml=ET.fromstring(z.read('word/document.xml'))
 paragraphs=[''.join(t.text or '' for t in p.findall('.//w:t',ns)) for p in xml.findall('.//w:p',ns)]
 text='\n'.join(paragraphs)
 scripts=list(ROOT.glob('sql/queries/Q*.sql'))+list(ROOT.glob('mongo/pipelines/P*.js'))
 scripts += [ROOT/p for p in ['sql/entrega03/00_views.sql','sql/entrega03/10_procedures.sql','sql/entrega03/11_exemplos_procedures.sql','mongo/entrega03/recursos_documentais.js','mongo/entrega03/mapreduce.js']]
 for p in scripts:assert p.read_text().rstrip() in text,'Código incompleto no Word: '+str(p)
 pdf=OUT/'Projeto-Integrador-Banco-de-Dados-Entrega-03.pdf';pages=PdfReader(pdf).pages
 mapping=load(OUT/'sumario.json');from finalizar_entrega03 import normal
 for title,page in mapping.items():
  lines=(pages[page-1].extract_text() or '').splitlines()
  spans={normal(' '.join(lines[i:i+n])) for i in range(len(lines)) for n in (1,2,3)}
  assert normal(title) in spans,(title,page)
 assert mapping['Referências']>mapping['18. Conclusões e reprodução']
 assert len(pages)==load(EV/'paginacao.json')['paginas']
 guide=ROOT/'docs/estudo/guia-completo.html';h=HTMLAudit();h.feed(guide.read_text())
 assert len(h.ids)==len(set(h.ids))
 for link in h.links:
  if link.startswith('#'):assert link[1:] in h.ids,link
 assert h.sources==32 and h.details>=50,(h.sources,h.details)
 assert all(src.startswith('data:image/png;base64,') for src in h.images)
 assert '<!-- lessons -->' not in guide.read_text()
 report={'status':'PASSOU','paginas_docx_renderizado':len(pages),'codigos_completos_no_word':len(scripts),
   'pares_equivalentes':16,'testes_adicionais':len(tests),'analises_performance':len(perf),
   'estudos_otimizacao':4,'guia_blocos_codigo':h.sources,'guia_exercicios_e_blocos':h.details,
   'anteriores_preservados':list(old),
   'arquivos':{str(p.relative_to(ROOT)):digest(p) for p in [docx,pdf,guide,ROOT/'docs/estudo/guia-completo.md']}}
 (EV/'verificacao-final.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
 print(json.dumps(report,ensure_ascii=False,indent=2))

if __name__=='__main__':main()
