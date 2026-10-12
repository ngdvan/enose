from pathlib import Path
from zipfile import ZipFile
from lxml import etree as E
import pymupdf,json
from PIL import Image,ImageDraw
r=Path(__file__).resolve().parents[1]
ns={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main','a':'http://schemas.openxmlformats.org/drawingml/2006/main','r':'http://schemas.openxmlformats.org/officeDocument/2006/relationships'}
trees=[]
for name in ['IEEE_Revision_3.0_Clean','IEEE_Revision_3.0_Highlighted']:
 with ZipFile(r/'submission'/f'{name}.docx') as z:
  tree=E.fromstring(z.read('word/document.xml'))
  assert len(tree.xpath('//a:blip[@r:embed="rId8"]',namespaces=ns))==1
  for h in tree.xpath('//w:highlight',namespaces=ns):h.getparent().remove(h)
  for node in tree.iter():
   if node.tag != '{'+ns['w']+'}t' and node.text and not node.text.strip():node.text=None
   if node.tail and not node.tail.strip():node.tail=None
  trees.append(E.tostring(tree,method='c14n'))
 d=pymupdf.open(r/'submission'/f'{name}.pdf')
 assert len(d)==10
 text='\n'.join(p.get_text() for p in d)
 assert 'We investigate' in text and '10 labeled pairs' in text
 (r/'proof'/f'{name}.txt').write_text(text,encoding='utf-8')
 sheet=Image.new('RGB',(1500,2800),'#dddddd')
 for i,p in enumerate(d):
  pix=p.get_pixmap(matrix=pymupdf.Matrix(1.5,1.5))
  img=Image.frombytes('RGB',[pix.width,pix.height],pix.samples)
  img.thumbnail((490,620))
  sheet.paste(img,((i%3)*500,(i//3)*700))
 sheet.save(r/'proof'/f'{name}_graphic_check.png')
 if name.endswith('Highlighted'):
  d[0].get_pixmap(matrix=pymupdf.Matrix(1.5,1.5)).save(r/'proof/highlight_graphic_restored.png')
assert trees[0]==trees[1], 'Clean/highlighted document mismatch'
p=r/'evidence/validation.json'
v=json.loads(p.read_text(encoding='utf-8'))
v['abstract_graphic_restored']=True
v['abstract_graphic_check']='2026-10-13: original V2.2 rId8 drawing restored; clean/highlighted XML equality verified after removing highlights; both PDFs retain 10 pages.'
p.write_text(json.dumps(v,indent=2),encoding='utf-8')
print('PASS: original graphic present, clean/highlighted equal, revised abstract retained, 10 pages each.')
