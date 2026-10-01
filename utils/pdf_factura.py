import os
from io import BytesIO
from datetime import datetime

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
)


def generar_pdf_factura(factura, detalles, pagos, total_pagado):
    """
    Genera un PDF de la factura y devuelve un BytesIO listo para enviar.

    Parámetros:
        factura: dict con datos de la factura (incluye JOIN con estudiante y usuario)
        detalles: lista de dicts con los productos facturados
        pagos: lista de dicts con las cuotas/pagos
        total_pagado: float con la suma de pagos realizados
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=40,
        leftMargin=40,
        topMargin=40,
        bottomMargin=40,
    )

    elementos = []
    styles = getSampleStyleSheet()

    # ============================================================
    # ESTILOS PERSONALIZADOS
    # ============================================================
    estilo_titulo = ParagraphStyle(
        'Titulo',
        parent=styles['Heading1'],
        fontSize=20,
        textColor=colors.HexColor('#1a4a8a'),
        alignment=1,  # Centrado
        spaceAfter=6,
    )

    estilo_subtitulo = ParagraphStyle(
        'Subtitulo',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.HexColor('#666666'),
        alignment=1,
        spaceAfter=15,
    )

    estilo_seccion = ParagraphStyle(
        'Seccion',
        parent=styles['Heading2'],
        fontSize=11,
        textColor=colors.HexColor('#1a4a8a'),
        spaceBefore=10,
        spaceAfter=6,
    )

    # ============================================================
    # ENCABEZADO: LOGO + TÍTULO
    # ============================================================
    logo_path = os.path.join('static', 'img', 'estudio.png')

    if os.path.exists(logo_path):
        try:
            logo = Image(logo_path, width=0.9 * inch, height=0.9 * inch)
            encabezado_data = [
                [logo, Paragraph(
                    '<b>ESTUDIA MEJOR</b><br/>'
                    '<font size=9 color="#666666">Sistema de Gestión Académica</font>',
                    styles['Normal']
                )]
            ]
            encabezado = Table(encabezado_data, colWidths=[1.1 * inch, 5.4 * inch])
            encabezado.setStyle(TableStyle([
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ]))
            elementos.append(encabezado)
        except Exception:
            # Si falla el logo, solo texto
            elementos.append(Paragraph("ESTUDIA MEJOR", estilo_titulo))
    else:
        elementos.append(Paragraph("ESTUDIA MEJOR", estilo_titulo))

    elementos.append(Spacer(1, 10))

    # Línea separadora
    linea = Table([['']], colWidths=[6.5 * inch], rowHeights=[2])
    linea.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#1a4a8a')),
    ]))
    elementos.append(linea)
    elementos.append(Spacer(1, 15))

    # Título de la factura
    elementos.append(Paragraph(
        f'FACTURA N° {factura["id"]:04d}',
        estilo_titulo
    ))
    fecha_str = factura['fecha_emision'].strftime('%d/%m/%Y %H:%M')
    elementos.append(Paragraph(
        f'Fecha de emisión: {fecha_str}',
        estilo_subtitulo
    ))

    # ============================================================
    # DATOS DEL ESTUDIANTE Y DEL EMISOR
    # ============================================================
    elementos.append(Paragraph('DATOS DEL CLIENTE', estilo_seccion))

    datos_cliente = [
        ['Nombre:', factura.get('estudiante_nombre', '—')],
        ['Email:', factura.get('estudiante_email', '—')],
        ['Teléfono:', factura.get('estudiante_telefono', '—') or '—'],
        ['Carrera:', factura.get('estudiante_carrera', '—')],
    ]
    tabla_cliente = Table(datos_cliente, colWidths=[1.2 * inch, 5.3 * inch])
    tabla_cliente.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
    ]))
    elementos.append(tabla_cliente)
    elementos.append(Spacer(1, 10))

    # Datos de la emisión
    datos_emision = [
        ['Emitida por:', factura.get('usuario_emisor', '—')],
        ['Tipo de pago:', 'Contado' if factura['tipo_pago'] == 'contado'
                          else f'{factura["num_cuotas"]} cuotas'],
        ['Estado:', factura['estado'].upper()],
    ]
    tabla_emision = Table(datos_emision, colWidths=[1.2 * inch, 5.3 * inch])
    tabla_emision.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
    ]))
    elementos.append(tabla_emision)
    elementos.append(Spacer(1, 20))

    # ============================================================
    # TABLA DE PRODUCTOS
    # ============================================================
    elementos.append(Paragraph('DETALLE DE PRODUCTOS Y SERVICIOS', estilo_seccion))

    tabla_productos_data = [
        ['Producto', 'Cant.', 'Precio Unit.', 'Subtotal']
    ]
    for d in detalles:
        tabla_productos_data.append([
            d['producto_nombre'],
            str(d['cantidad']),
            f'${d["precio_unitario"]:.2f}',
            f'${d["subtotal"]:.2f}',
        ])

    # Fila del total
    tabla_productos_data.append(['', '', 'TOTAL:', f'${float(factura["total"]):.2f}'])
    tabla_productos = Table(
        tabla_productos_data,
        colWidths=[3.5 * inch, 0.7 * inch, 1.2 * inch, 1.1 * inch]
    )
    tabla_productos.setStyle(TableStyle([
        # Encabezado
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a4a8a')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('ALIGN', (1, 0), (-1, 0), 'CENTER'),

        # Filas
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('ALIGN', (1, 1), (1, -1), 'CENTER'),
        ('ALIGN', (2, 1), (-1, -1), 'RIGHT'),

        # Fila del total
        ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#e8e8e8')),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, -1), (-1, -1), 11),

        # Bordes
        ('GRID', (0, 0), (-1, -2), 0.5, colors.HexColor('#cccccc')),
        ('BOX', (0, -1), (-1, -1), 0.5, colors.HexColor('#999999')),
    ]))
    elementos.append(tabla_productos)
    elementos.append(Spacer(1, 20))

    # ============================================================
    # TABLA DE CUOTAS / PAGOS
    # ============================================================
    if factura['tipo_pago'] == 'cuotas':
        elementos.append(Paragraph('PLAN DE CUOTAS', estilo_seccion))
    else:
        elementos.append(Paragraph('PAGO', estilo_seccion))

    tabla_pagos_data = [
        ['#', 'Vencimiento', 'Monto', 'Estado', 'Fecha de pago']
    ]
    for p in pagos:
        numero = '—' if factura['tipo_pago'] == 'contado' else str(p['numero_cuota'])
        fecha_pago_str = p['fecha_pago'].strftime('%d/%m/%Y') if p['fecha_pago'] else '—'
        tabla_pagos_data.append([
            numero,
            p['fecha_vencimiento'].strftime('%d/%m/%Y'),
            f'${p["monto"]:.2f}',
            'Pagado' if p['estado'] == 'pagado' else 'Pendiente',
            fecha_pago_str,
        ])

    tabla_pagos = Table(
        tabla_pagos_data,
        colWidths=[0.5 * inch, 1.4 * inch, 1.2 * inch, 1.5 * inch, 1.9 * inch]
    )
    tabla_pagos.setStyle(TableStyle([
        # Encabezado
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a4a8a')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),

        # Filas
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('ALIGN', (0, 1), (0, -1), 'CENTER'),
        ('ALIGN', (2, 1), (2, -1), 'RIGHT'),

        # Bordes
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cccccc')),
    ]))
    elementos.append(tabla_pagos)
    elementos.append(Spacer(1, 20))

    # ============================================================
    # RESUMEN FINAL
    # ============================================================
    total_float = float(factura['total'])
    saldo = total_float - total_pagado

    resumen_data = [
        ['Total pagado:', f'${total_pagado:.2f}'],
        ['Saldo pendiente:', f'${saldo:.2f}'],
    ]
    tabla_resumen = Table(resumen_data, colWidths=[5.5 * inch, 1.0 * inch])
    tabla_resumen.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 11),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('TEXTCOLOR', (1, 0), (1, 0), colors.HexColor('#0a7d35')),  # verde
        ('TEXTCOLOR', (1, 1), (1, 1), colors.HexColor('#a02020')),  # rojo
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
    ]))
    elementos.append(tabla_resumen)
    elementos.append(Spacer(1, 15))

    # Mensaje de estado
    if factura['estado'] == 'pagada':
        mensaje = '<b>✓ FACTURA TOTALMENTE PAGADA</b>'
        color = colors.HexColor('#d4edda')
    elif factura['estado'] == 'parcial':
        mensaje = '<b>⏳ FACTURA CON PAGOS PARCIALES</b>'
        color = colors.HexColor('#fff3cd')
    else:
        mensaje = '<b>⏳ FACTURA PENDIENTE DE PAGO</b>'
        color = colors.HexColor('#f8d7da')

    estilo_mensaje = ParagraphStyle(
        'Mensaje',
        parent=styles['Normal'],
        fontSize=12,
        alignment=1,
        textColor=colors.black,
    )
    tabla_mensaje = Table([[Paragraph(mensaje, estilo_mensaje)]],
                          colWidths=[6.5 * inch])
    tabla_mensaje.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), color),
        ('TOPPADDING', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
    ]))
    elementos.append(tabla_mensaje)
    elementos.append(Spacer(1, 25))

    # Pie
    estilo_pie = ParagraphStyle(
        'Pie',
        parent=styles['Normal'],
        fontSize=8,
        textColor=colors.HexColor('#888888'),
        alignment=1,
    )
    elementos.append(Paragraph(
        'Gracias por su preferencia — Estudia Mejor © 2026',
        estilo_pie
    ))

    # Generar PDF
    doc.build(elementos)
    buffer.seek(0)
    return buffer