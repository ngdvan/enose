from zipfile import ZipFile
from lxml import etree as E
from pathlib import Path
import pymupdf
r=Path(__file__).resolve().parents[2]
ns={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main','a':'http://schemas.openxmlformats.org/drawingml/2006/main'}
for f in [r/'v2.2/author_review/full_revision_001/IEEE_Full_Revision_Clean.docx',r/'V3.0/submission/IEEE_Revision_3.0_Clean.docx']:
 print(f)
 xml=E.fromstring(ZipFile(f).read('word/document.xml'))
 for i,p in enumerate(xml.xpath('//w:p',namespaces=ns)):
  if p.xpath('.//a:blip',namespaces=ns):
   print(i,''.join(p.xpath('.//w:t/text()',namespaces=ns))[:100],[dict(b.attrib) for b in p.xpath('.//a:blip',namespaces=ns)])
d=pymupdf.open(r/'V3.0/Base v2.2/IEEE_Full_Revision_Clean.pdf')
d[0].get_pixmap(matrix=pymupdf.Matrix(1.5,1.5)).save(str(r/'V3.0/proof/v22_abstract_compare.png'))
