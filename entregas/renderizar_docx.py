"""Converte uma cópia temporária do Word para inspeção, sem alterar o original.

Uso: python3 entregas/renderizar_docx.py ARQUIVO.docx /tmp/destino
Usa LibreOffice local ou, no WSL, a instalação disponível no Windows.
"""
import pathlib
import shutil
import subprocess
import sys
import tempfile

source=pathlib.Path(sys.argv[1]).resolve()
output=pathlib.Path(sys.argv[2]).resolve()
output.mkdir(parents=True,exist_ok=True)
soffice=shutil.which('libreoffice') or shutil.which('soffice')
if soffice:
    with tempfile.TemporaryDirectory(prefix='pi-render-') as tmp:
        profile=pathlib.Path(tmp)/'profile'
        subprocess.run([soffice,'-env:UserInstallation='+profile.as_uri(),'--headless','--convert-to','pdf','--outdir',str(output),str(source)],check=True)
else:
    soffice='/mnt/c/Program Files/LibreOffice/program/soffice.exe'
    if not pathlib.Path(soffice).exists():
        raise SystemExit('LibreOffice não encontrado. Abra o documento no Word e exporte para PDF para conferir.')
    tmp=pathlib.Path('/mnt/c/Users/giova/AppData/Local/Temp/pi-revisao-entrega01')
    tmp.mkdir(exist_ok=True)
    shutil.copyfile(source,tmp/'revisado.docx')
    pdf=tmp/'revisado.pdf'
    if pdf.exists(): pdf.unlink()
    subprocess.run([soffice,'-env:UserInstallation=file:///C:/Users/giova/AppData/Local/Temp/pi-revisao-lo-profile','--headless','--norestore','--convert-to','pdf','--outdir',r'C:\Users\giova\AppData\Local\Temp\pi-revisao-entrega01',r'C:\Users\giova\AppData\Local\Temp\pi-revisao-entrega01\revisado.docx'],check=True,timeout=90)
    if not pdf.exists(): raise SystemExit('A conversão não produziu PDF.')
    shutil.copyfile(pdf,output/(source.stem+'.pdf'))
print(output/(source.stem+'.pdf'))
