from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

def workorder_pdf(workorder) -> bytes:
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    w, h = A4
    y = h - 50

    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, y, f"Акт выполненных работ / Заказ-наряд №{workorder.id}")
    y -= 30

    c.setFont("Helvetica", 10)
    c.drawString(50, y, f"Дата: {workorder.created_date.strftime('%d.%m.%Y %H:%M')}")
    y -= 15
    c.drawString(50, y, f"Клиент: {workorder.car.client.full_name}, тел.: {workorder.car.client.phone}")
    y -= 15
    c.drawString(50, y, f"Авто: {workorder.car.brand} {workorder.car.model}, гос.номер: {workorder.car.license_plate}, VIN: {workorder.car.vin}")
    y -= 15
    c.drawString(50, y, f"Статус: {workorder.get_status_display()}")
    y -= 20

    c.setFont("Helvetica-Bold", 11)
    c.drawString(50, y, "Услуги:")
    y -= 15
    c.setFont("Helvetica", 10)
    total_services = 0.0
    for ws in workorder.workorderservice_set.select_related("service").all():
        line = ws.line_total
        total_services += line
        c.drawString(60, y, f"- {ws.service.service_name} x{ws.qty} = {line:.2f}")
        y -= 12
        if y < 80:
            c.showPage()
            y = h - 50

    y -= 10
    c.setFont("Helvetica-Bold", 11)
    c.drawString(50, y, "Запчасти:")
    y -= 15
    c.setFont("Helvetica", 10)
    total_parts = 0.0
    for wp in workorder.workorderpart_set.select_related("part").all():
        line = wp.line_total
        total_parts += line
        c.drawString(60, y, f"- {wp.part.part_name} x{wp.qty} = {line:.2f}")
        y -= 12
        if y < 80:
            c.showPage()
            y = h - 50

    y -= 15
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y, f"Итого: {(total_services + total_parts):.2f}")
    y -= 40
    c.setFont("Helvetica", 10)
    c.drawString(50, y, "Подпись исполнителя: ____________________")
    y -= 20
    c.drawString(50, y, "Подпись клиента: ________________________")

    c.showPage()
    c.save()
    return buffer.getvalue()
