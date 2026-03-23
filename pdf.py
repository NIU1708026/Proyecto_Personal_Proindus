from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML
import io

def generar_pdf_binario(presupuesto_obj):
    # Cargar la plantilla
    env = Environment(loader=FileSystemLoader('templates'))
    template = env.get_template('factura.html')
    
    # Renderizar HTML con los datos del objeto Presupuesto
    html_content = template.render(p=presupuesto_obj)
    
    # Convertir a PDF en memoria (binario)
    pdf_file = io.BytesIO()
    HTML(string=html_content).write_pdf(pdf_file)
    pdf_file.seek(0)
    return pdf_file
