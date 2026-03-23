from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML
import io

# Añadimos 'tipo' a los argumentos de la función
def generar_pdf_binario(presupuesto_obj, tipo: str):
    """
    Toma el objeto del presupuesto y la etiqueta (Factura/Presupuesto)
    y genera el archivo PDF final.
    """
    # 1. Configuramos dónde están las plantillas
    env = Environment(loader=FileSystemLoader('templates'))
    template = env.get_template('factura.html')
    
    # 2. Renderizamos pasando tanto el objeto 'p' como el 'tipo'
    # Ahora Jinja2 podrá leer {{ tipo }} en el HTML
    html_content = template.render(
        p=presupuesto_obj, 
        tipo=tipo
    )
    
    # 3. Generamos el binario con WeasyPrint
    pdf_file = io.BytesIO()
    HTML(string=html_content).write_pdf(pdf_file)
    pdf_file.seek(0)
    
    return pdf_file