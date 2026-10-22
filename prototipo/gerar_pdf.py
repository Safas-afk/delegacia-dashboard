"""Gera um PDF ficticio de inquerito policial para testar o pipeline de extracao.
Documento inventado (nomes, numeros e fatos sao ficticios). Nenhum dado real.
"""
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER

SAIDA = "pdfs/inquerito_ficticio.pdf"

styles = getSampleStyleSheet()
corpo = ParagraphStyle("corpo", parent=styles["Normal"], fontSize=11,
                       leading=16, alignment=TA_JUSTIFY, spaceAfter=10)
titulo = ParagraphStyle("titulo", parent=styles["Title"], fontSize=13, alignment=TA_CENTER)
cab = ParagraphStyle("cab", parent=styles["Normal"], fontSize=10, alignment=TA_CENTER)

doc = SimpleDocTemplate(SAIDA, pagesize=A4, topMargin=2*cm, bottomMargin=2*cm,
                        leftMargin=2.5*cm, rightMargin=2.5*cm)

el = []
el.append(Paragraph("ESTADO DA BAHIA", cab))
el.append(Paragraph("SECRETARIA DA SEGURANCA PUBLICA", cab))
el.append(Paragraph("POLICIA CIVIL - DELEGACIA DE TOXICOS E ENTORPECENTES (DTE)", cab))
el.append(Paragraph("COMARCA DE VITORIA DA CONQUISTA", cab))
el.append(Spacer(1, 0.6*cm))
el.append(Paragraph("PORTARIA DE INSTAURACAO DE INQUERITO POLICIAL", titulo))
el.append(Paragraph("INQUERITO POLICIAL N. 2026.0101.000457-3", cab))
el.append(Paragraph("SEGREDO DE JUSTICA", cab))
el.append(Spacer(1, 0.6*cm))

el.append(Paragraph(
    "A autoridade policial que esta subscreve, Dr. Mariana Teixeira de Almeida, "
    "Delegada de Policia titular da Delegacia de Toxicos e Entorpecentes de Vitoria "
    "da Conquista/BA, no uso de suas atribuicoes legais, RESOLVE instaurar o presente "
    "inquerito policial para apurar os fatos a seguir narrados.", corpo))

el.append(Paragraph(
    "Consta dos autos que, no dia 14 de fevereiro de 2026, por volta das 22h30, "
    "durante cumprimento de mandado de busca e apreensao expedido pelo Juizo da Vara "
    "de Entorpecentes, equipe policial compareceu a residencia situada no Bairro "
    "Patagonia, nesta cidade, onde foi efetuada a prisao em flagrante de JOSE CARLOS "
    "DOS SANTOS PEREIRA, brasileiro, 29 anos.", corpo))

el.append(Paragraph(
    "No interior do imovel foram apreendidos: 1,2 kg (um quilo e duzentos gramas) de "
    "substancia analoga a cocaina, 340 g de maconha, uma balanca de precisao, alem de "
    "01 (uma) pistola calibre .40 de uso restrito, com numeracao suprimida, e 28 "
    "municoes do mesmo calibre. O auto de prisao em flagrante foi lavrado na mesma data.", corpo))

el.append(Paragraph(
    "O conduzido foi autuado em flagrante e permanece PRESO. Figura ainda como "
    "investigada MARIA EDUARDA LIMA SOUZA, companheira do conduzido, atualmente foragida. "
    "Atuou como condutor o 3o Sgt PM Ricardo Alves Nunes, tendo presenciado os fatos as "
    "testemunhas Antonio Ferreira da Silva e Joana Dias Carvalho.", corpo))

el.append(Paragraph(
    "Os fatos, em tese, configuram os crimes de trafico ilicito de drogas (art. 33 da "
    "Lei n. 11.343/2006) e posse ilegal de arma de fogo de uso restrito com numeracao "
    "suprimida (art. 16 da Lei n. 10.826/2003). Diante da presenca de duas ou mais "
    "pessoas, apura-se tambem a associacao para o trafico (art. 35 da Lei n. 11.343/2006).", corpo))

el.append(Paragraph(
    "DETERMINO as seguintes diligencias: (a) requisicao de laudo de constatacao "
    "preliminar da substancia apreendida ao Departamento de Policia Tecnica; (b) "
    "requisicao de laudo definitivo (toxicologico); (c) requisicao de exame pericial "
    "da arma e das municoes; (d) oitiva das testemunhas; (e) comunicacao da instauracao "
    "ao Ministerio Publico no prazo legal.", corpo))

el.append(Spacer(1, 0.8*cm))
el.append(Paragraph("Vitoria da Conquista/BA, 15 de fevereiro de 2026.", corpo))
el.append(Spacer(1, 0.6*cm))
el.append(Paragraph("Dra. Mariana Teixeira de Almeida<br/>Delegada de Policia - DTE", cab))

doc.build(el)
print("PDF gerado:", SAIDA)
