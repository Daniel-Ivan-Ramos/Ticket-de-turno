from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
import base64
from io import BytesIO
from datetime import datetime

class PDFGenerator:
    @staticmethod
    def generar_comprobante(ticket):
        buffer = BytesIO()
        c = canvas.Canvas(buffer, pagesize=letter)
        width, height = letter
        
        # Encabezado
        c.setFont("Helvetica-Bold", 16)
        c.drawString(100, height - 100, "COMPROBANTE DE TURNO")
        c.line(100, height - 105, 500, height - 105)
        
        # Información del ticket
        c.setFont("Helvetica", 12)
        y = height - 150
        c.drawString(100, y, f"Nombre: {ticket.nombre} {ticket.apellido_paterno} {ticket.apellido_materno}")
        y -= 25
        c.drawString(100, y, f"CURP: {ticket.curp}")
        y -= 25
        c.drawString(100, y, f"Municipio: {ticket.municipio.nombre}")
        y -= 25
        c.drawString(100, y, f"Número de Turno: {ticket.numero_turno}")
        y -= 25
        c.drawString(100, y, f"Fecha: {ticket.fecha_creacion.strftime('%d/%m/%Y %H:%M')}")
        y -= 25
        c.drawString(100, y, f"Estatus: {ticket.estatus}")
        
        # Código QR
        qr_data = ticket.generar_qr_base64()
        qr_image = ImageReader(BytesIO(base64.b64decode(qr_data)))
        c.drawImage(qr_image, 400, height - 300, width=100, height=100)
        
        c.showPage()
        c.save()
        
        buffer.seek(0)
        return buffer