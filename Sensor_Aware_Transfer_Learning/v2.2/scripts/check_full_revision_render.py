"""Check rendered PDFs and create page contact sheets for visual proofreading."""
from pathlib import Path
import json
import re
import pymupdf
from PIL import Image,ImageDraw
from zipfile import ZipFile
from lxml import etree

OUT=Path(__file__).resolve().parents[1]/'author_review/full_revision_001'
PROOF=OUT/'proof'

def main():
    PROOF.mkdir(exist_ok=True);records={}
    clean_zip=ZipFile(OUT/'IEEE_Full_Revision_Clean.docx')
    high_zip=ZipFile(OUT/'IEEE_Full_Revision_Highlighted.docx')
    parts=highlights=0
    for name in clean_zip.namelist():
        if name.startswith('word/') and name.endswith('.xml'):
            a,b=etree.fromstring(clean_zip.read(name)),etree.fromstring(high_zip.read(name))
            nodes=b.findall('.//{http://schemas.openxmlformats.org/wordprocessingml/2006/main}highlight');highlights+=len(nodes)
            for node in nodes:node.getparent().remove(node)
            assert not a.findall('.//{http://schemas.openxmlformats.org/wordprocessingml/2006/main}highlight')
            assert etree.tostring(a,method='c14n')==etree.tostring(b,method='c14n'),name
            parts+=1
    clean_zip.close();high_zip.close()
    path=OUT/'document_validation.json';validation=json.loads(path.read_text());validation.update(all_word_xml_parts_match_except_highlight=parts,total_highlights_including_headers=highlights);path.write_text(json.dumps(validation,indent=2),encoding='utf-8')
    for name in ['IEEE_Full_Revision_Clean','IEEE_Full_Revision_Highlighted','RESPONSE_TO_REVIEWERS','SUPPLEMENTARY_EVIDENCE']:
        doc=pymupdf.open(OUT/(name+'.pdf'));thumbs=[];outside=[];texts=[]
        for i,page in enumerate(doc):
            text=page.get_text();texts.append(text)
            assert len(text.strip())>60,(name,i,'blank/nearly blank page')
            for word in page.get_text('words'):
                if word[0]<-1 or word[1]<-1 or word[2]>page.rect.width+1 or word[3]>page.rect.height+1:outside.append([i+1,list(word[:5])])
            pix=page.get_pixmap(matrix=pymupdf.Matrix(.48,.48),alpha=False)
            im=Image.frombytes('RGB',[pix.width,pix.height],pix.samples)
            canvas=Image.new('RGB',(310,405),'#dddddd');canvas.paste(im,((310-im.width)//2,16));ImageDraw.Draw(canvas).text((8,2),str(i+1),fill='black');thumbs.append(canvas)
        assert not outside,(name,outside)
        text='\n'.join(texts)
        if name.startswith('IEEE'):
            assert not re.search(r'XXXX|VOL\.\s*XX|\bSYST\b',text)
            assert '13.9%' in text and '21.5%' in text and '27.5%' in text and '25.7%' in text
            assert 'no clear improvement' in text
        (PROOF/(name+'.txt')).write_text(text,encoding='utf-8')
        for start in range(0,len(thumbs),12):
            subset=thumbs[start:start+12];sheet=Image.new('RGB',(1240,405*((len(subset)+3)//4)),'white')
            for j,im in enumerate(subset):sheet.paste(im,((j%4)*310,(j//4)*405))
            sheet.save(PROOF/(name+'_'+str(start+1)+'.png'))
        records[name]=dict(pages=len(doc),blank_pages=0,text_outside_page=0)
    clean=(PROOF/'IEEE_Full_Revision_Clean.txt').read_text(encoding='utf-8')
    high=(PROOF/'IEEE_Full_Revision_Highlighted.txt').read_text(encoding='utf-8')
    assert re.sub(r'\s+','',clean)==re.sub(r'\s+','',high),'PDF text differs beyond highlight'
    report=dict(status='PASS: rendered PDF checks and page proof',renderer='LibreOffice 25.2.7.2, isolated local administrative extraction; PyMuPDF',
        documents=records,clean_highlighted_pdf_text_identical=True,
        proof='Contact sheets for all pages; detailed checks of front matter, figures and results tables. Original Word PDF automation stalled; alternate renderer succeeded.',
        limitations='PDFs are proofs from LibreOffice; exact pagination can vary in Microsoft Word or publisher typesetting.')
    (OUT/'render_validation.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    print(json.dumps(report,indent=2))

if __name__=='__main__':main()
