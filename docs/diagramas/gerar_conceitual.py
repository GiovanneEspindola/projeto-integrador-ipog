"""Gera a figura conceitual vetorial e sua versão PNG para o relatório."""
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle

OUT=Path(__file__).resolve().parent
fig,ax=plt.subplots(figsize=(6.5,7.1))
ax.set_xlim(-12,600); ax.set_ylim(680,-12); ax.axis('off')
fig.subplots_adjust(0,0,1,1)
BLUE='#214761'; LINE='#456071'

def node(x,y,title,fields,color='#e8f0f5'):
 ax.add_patch(Rectangle((x,y),160,65,facecolor='white',edgecolor=LINE,lw=.8,zorder=3))
 ax.add_patch(Rectangle((x,y),160,23,facecolor=color,edgecolor=LINE,lw=.8,zorder=3))
 ax.text(x+80,y+12,title,ha='center',va='center',fontsize=9,fontweight='bold',color=BLUE,zorder=4)
 for i,f in enumerate(fields): ax.text(x+7,y+35+i*15,f,fontsize=8,va='center',zorder=4)

def label(x,y,t,size=8):
 ax.text(x,y,t,ha='center',va='center',fontsize=size,color=BLUE,bbox=dict(facecolor='white',edgecolor='none',pad=.7),zorder=5)

def edge(points,verb,vpos,a,apos,b,bpos):
 ax.plot([p[0] for p in points],[p[1] for p in points],color=LINE,lw=.8,zorder=1)
 label(*vpos,verb);label(*apos,a);label(*bpos,b)

node(5,0,'FORNECEDOR',['ID: fornecedor','nome da empresa'],'#e7efe3')
node(420,0,'CATEGORIA',['ID: categoria','nome da categoria'],'#e7efe3')
node(212,110,'PRODUTO',['ID: produto','nome; preço de catálogo'],'#e7efe3')
node(212,220,'ITEM DO PEDIDO',['ID: pedido + produto','qtd.; preço; desconto'])
node(212,340,'PEDIDO',['ID: pedido','datas; frete; endereço'])
node(5,340,'CLIENTE',['ID: cliente','empresa; contato'])
node(420,340,'TRANSPORTADORA',['ID: transportadora','nome; telefone'])
node(5,490,'FUNCIONÁRIO',['ID: funcionário','nome; cargo'],'#f5eddd')
node(212,490,'ATUAÇÃO',['ID: funcionário','      + território'],'#ede7f2')
node(420,490,'TERRITÓRIO',['ID: território','nome'],'#f5eddd')
node(420,600,'REGIÃO',['ID: região','nome'],'#f5eddd')
edge([(85,65),(85,140),(212,140)],'fornece',(132,123),'1',(85,79),'0..N',(192,140))
edge([(500,65),(500,140),(372,140)],'classifica',(450,122),'1',(500,79),'0..N',(395,140))
edge([(292,175),(292,220)],'aparece em',(349,197),'1',(281,181),'0..N',(277,214))
edge([(292,285),(292,340)],'contém',(335,311),'1..N',(273,292),'1',(281,333))
edge([(165,372),(212,372)],'faz',(188,352),'1',(173,372),'0..N',(198,387))
edge([(420,372),(372,372)],'indicada em',(397,344),'1',(413,372),'0..N',(387,387))
edge([(140,490),(140,441),(245,441),(245,405)],'registra',(198,441),'1',(151,477),'0..N',(245,419))
edge([(165,524),(212,524)],'possui',(188,502),'1',(173,524),'0..N',(200,538))
edge([(420,524),(372,524)],'vincula',(397,502),'1',(413,524),'0..N',(387,538))
edge([(500,600),(500,555)],'agrupa',(545,579),'1',(488,592),'1..N',(482,564))
edge([(35,490),(35,440),(70,440),(70,490)],'supervisiona',(45,423),'0..1',(20,461),'0..N',(89,470))
fig.savefig(OUT/'er-conceitual-relatorio.svg',transparent=False)
fig.savefig(OUT/'er-conceitual-relatorio.png',dpi=240)
print(OUT/'er-conceitual-relatorio.png')
