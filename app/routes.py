from flask import Blueprint, render_template, request, flash, redirect, url_for, jsonify, send_file
from flask_login import login_required, current_user
from app.models import db, Ticket, Municipio, Usuario
from app.utils.pdf_generator import PDFGenerator
from app.utils.turno_manager import TurnoManager
from sqlalchemy import or_

main_bp = Blueprint('main', __name__)
turno_manager = TurnoManager()

@main_bp.route('/')
def index():
    municipios = Municipio.query.filter_by(activo=True).all()
    return render_template('public/solicitud.html', municipios=municipios)

@main_bp.route('/solicitar-turno', methods=['POST'])
def solicitar_turno():
    try:
        curp = request.form.get('curp')
        nombre = request.form.get('nombre')
        apellido_paterno = request.form.get('apellido_paterno')
        apellido_materno = request.form.get('apellido_materno')
        telefono = request.form.get('telefono')
        email = request.form.get('email')
        municipio_id = request.form.get('municipio_id')
        
        # Verificar si ya existe un turno para esta CURP en el municipio
        ticket_existente = turno_manager.validar_turno_existente(municipio_id, curp)
        if ticket_existente:
            flash('Ya existe un turno para esta CURP en el municipio seleccionado', 'warning')
            return redirect(url_for('main.modificar_turno'))
        
        # Obtener siguiente turno
        numero_turno = turno_manager.obtener_siguiente_turno(municipio_id)
        
        # Crear nuevo ticket
        nuevo_ticket = Ticket(
            curp=curp,
            nombre=nombre,
            apellido_paterno=apellido_paterno,
            apellido_materno=apellido_materno,
            telefono=telefono,
            email=email,
            municipio_id=municipio_id,
            numero_turno=numero_turno
        )
        
        db.session.add(nuevo_ticket)
        db.session.commit()
        
        flash(f'Turno asignado exitosamente. Su número de turno es: {numero_turno}', 'success')
        return redirect(url_for('main.descargar_comprobante', ticket_id=nuevo_ticket.id))
        
    except Exception as e:
        db.session.rollback()
        flash('Error al procesar la solicitud', 'error')
        return redirect(url_for('main.index'))

@main_bp.route('/modificar-turno')
def modificar_turno_form():
    return render_template('public/modificar_turno.html')

@main_bp.route('/modificar-turno', methods=['POST'])
def modificar_turno():
    curp = request.form.get('curp')
    numero_turno = request.form.get('numero_turno')
    
    ticket = Ticket.query.filter_by(curp=curp, numero_turno=numero_turno).first()
    
    if not ticket:
        flash('No se encontró ningún turno con los datos proporcionados', 'error')
        return redirect(url_for('main.modificar_turno_form'))
    
    municipios = Municipio.query.filter_by(activo=True).all()
    return render_template('public/editar_solicitud.html', ticket=ticket, municipios=municipios)

@main_bp.route('/actualizar-turno/<int:ticket_id>', methods=['POST'])
def actualizar_turno(ticket_id):
    ticket = Ticket.query.get_or_404(ticket_id)
    
    ticket.nombre = request.form.get('nombre')
    ticket.apellido_paterno = request.form.get('apellido_paterno')
    ticket.apellido_materno = request.form.get('apellido_materno')
    ticket.telefono = request.form.get('telefono')
    ticket.email = request.form.get('email')
    
    db.session.commit()
    flash('Solicitud actualizada exitosamente', 'success')
    return redirect(url_for('main.descargar_comprobante', ticket_id=ticket.id))

@main_bp.route('/comprobante/<int:ticket_id>')
def descargar_comprobante(ticket_id):
    ticket = Ticket.query.get_or_404(ticket_id)
    pdf_buffer = PDFGenerator.generar_comprobante(ticket)
    
    return send_file(
        pdf_buffer,
        as_attachment=True,
        download_name=f"comprobante_turno_{ticket.numero_turno}.pdf",
        mimetype='application/pdf'
    )

# Panel de Administración
@main_bp.route('/dashboard')
@login_required
def dashboard():
    if not current_user.es_admin:
        flash('No tienes permisos para acceder a esta página', 'error')
        return redirect(url_for('main.index'))
    
    # Estadísticas básicas
    total_tickets = Ticket.query.count()
    tickets_pendientes = Ticket.query.filter_by(estatus='Pendiente').count()
    tickets_resueltos = Ticket.query.filter_by(estatus='Resuelto').count()
    
    # Estadísticas por municipio
    municipios_stats = db.session.query(
        Municipio.nombre,
        db.func.count(Ticket.id).label('total_tickets'),
        db.func.sum(db.case((Ticket.estatus == 'Pendiente', 1), else_=0)).label('pendientes'),
        db.func.sum(db.case((Ticket.estatus == 'Resuelto', 1), else_=0)).label('resueltos')
    ).join(Ticket, Municipio.id == Ticket.municipio_id)\
     .group_by(Municipio.id, Municipio.nombre)\
     .all()
    
    # Estadísticas por fecha (últimos 7 días)
    from datetime import datetime, timedelta
    fecha_limite = datetime.utcnow() - timedelta(days=7)
    
    tickets_por_fecha = db.session.query(
        db.func.date(Ticket.fecha_creacion).label('fecha'),
        db.func.count(Ticket.id).label('cantidad')
    ).filter(Ticket.fecha_creacion >= fecha_limite)\
     .group_by(db.func.date(Ticket.fecha_creacion))\
     .order_by(db.func.date(Ticket.fecha_creacion))\
     .all()
    
    # Preparar datos para las gráficas
    municipios_nombres = [stat.nombre for stat in municipios_stats]
    municipios_totales = [stat.total_tickets for stat in municipios_stats]
    municipios_pendientes = [stat.pendientes for stat in municipios_stats]
    municipios_resueltos = [stat.resueltos for stat in municipios_stats]
    
    fechas = [stat.fecha.strftime('%d/%m') for stat in tickets_por_fecha]
    tickets_por_dia = [stat.cantidad for stat in tickets_por_fecha]
    
    return render_template('admin/dashboard.html',
                         total_tickets=total_tickets,
                         pendientes=tickets_pendientes,
                         resueltos=tickets_resueltos,
                         municipios_stats=municipios_stats,
                         municipios_nombres=municipios_nombres,
                         municipios_totales=municipios_totales,
                         municipios_pendientes=municipios_pendientes,
                         municipios_resueltos=municipios_resueltos,
                         fechas=fechas,
                         tickets_por_dia=tickets_por_dia)

@main_bp.route('/admin/tickets')
@login_required
def administrar_tickets():
    if not current_user.es_admin:
        flash('No tienes permisos para acceder a esta página', 'error')
        return redirect(url_for('main.index'))
    
    query = request.args.get('q', '')
    if query:
        tickets = Ticket.query.filter(
            or_(
                Ticket.curp.contains(query),
                Ticket.nombre.contains(query),
                Ticket.apellido_paterno.contains(query)
            )
        ).order_by(Ticket.fecha_creacion.desc()).all()
    else:
        tickets = Ticket.query.order_by(Ticket.fecha_creacion.desc()).all()
    
    return render_template('admin/tickets.html', tickets=tickets, query=query)

@main_bp.route('/admin/tickets/<int:ticket_id>/eliminar', methods=['POST'])
@login_required
def eliminar_ticket(ticket_id):
    if not current_user.es_admin:
        return jsonify({'error': 'No autorizado'}), 403
    
    ticket = Ticket.query.get_or_404(ticket_id)
    db.session.delete(ticket)
    db.session.commit()
    
    flash('Ticket eliminado exitosamente', 'success')
    return redirect(url_for('main.administrar_tickets'))

@main_bp.route('/admin/tickets/<int:ticket_id>/estatus', methods=['POST'])
@login_required
def cambiar_estatus(ticket_id):
    if not current_user.es_admin:
        return jsonify({'error': 'No autorizado'}), 403
    
    ticket = Ticket.query.get_or_404(ticket_id)
    ticket.estatus = 'Resuelto' if ticket.estatus == 'Pendiente' else 'Pendiente'
    db.session.commit()
    
    return jsonify({'nuevo_estatus': ticket.estatus})

# CRUD COMPLETO PARA TICKETS - ADMIN
@main_bp.route('/admin/tickets/crear', methods=['GET', 'POST'])
@login_required
def crear_ticket_admin():
    if not current_user.es_admin:
        flash('No tienes permisos para acceder a esta página', 'error')
        return redirect(url_for('main.index'))
    
    municipios = Municipio.query.filter_by(activo=True).all()
    
    if request.method == 'POST':
        try:
            curp = request.form.get('curp')
            nombre = request.form.get('nombre')
            apellido_paterno = request.form.get('apellido_paterno')
            apellido_materno = request.form.get('apellido_materno')
            telefono = request.form.get('telefono')
            email = request.form.get('email')
            municipio_id = request.form.get('municipio_id')
            estatus = request.form.get('estatus', 'Pendiente')
            
            # Verificar si ya existe un turno para esta CURP en el municipio
            ticket_existente = turno_manager.validar_turno_existente(municipio_id, curp)
            if ticket_existente:
                flash('Ya existe un turno para esta CURP en el municipio seleccionado', 'warning')
                return redirect(url_for('main.crear_ticket_admin'))
            
            # Obtener siguiente turno
            numero_turno = turno_manager.obtener_siguiente_turno(municipio_id)
            
            # Crear nuevo ticket
            nuevo_ticket = Ticket(
                curp=curp,
                nombre=nombre,
                apellido_paterno=apellido_paterno,
                apellido_materno=apellido_materno,
                telefono=telefono,
                email=email,
                municipio_id=municipio_id,
                numero_turno=numero_turno,
                estatus=estatus
            )
            
            db.session.add(nuevo_ticket)
            db.session.commit()
            
            flash(f'Ticket creado exitosamente. Número de turno: {numero_turno}', 'success')
            return redirect(url_for('main.administrar_tickets'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Error al crear el ticket: {str(e)}', 'error')
    
    return render_template('admin/crear_ticket.html', municipios=municipios)

@main_bp.route('/admin/tickets/<int:ticket_id>/editar', methods=['GET', 'POST'])
@login_required
def editar_ticket(ticket_id):
    if not current_user.es_admin:
        flash('No tienes permisos para acceder a esta página', 'error')
        return redirect(url_for('main.index'))
    
    ticket = Ticket.query.get_or_404(ticket_id)
    municipios = Municipio.query.filter_by(activo=True).all()
    
    if request.method == 'POST':
        try:
            ticket.nombre = request.form.get('nombre')
            ticket.apellido_paterno = request.form.get('apellido_paterno')
            ticket.apellido_materno = request.form.get('apellido_materno')
            ticket.telefono = request.form.get('telefono')
            ticket.email = request.form.get('email')
            ticket.municipio_id = request.form.get('municipio_id')
            ticket.estatus = request.form.get('estatus')
            
            db.session.commit()
            flash('Ticket actualizado exitosamente', 'success')
            return redirect(url_for('main.administrar_tickets'))
            
        except Exception as e:
            db.session.rollback()
            flash('Error al actualizar el ticket', 'error')
    
    return render_template('admin/editar_ticket.html', ticket=ticket, municipios=municipios)

# CRUD COMPLETO PARA MUNICIPIOS
@main_bp.route('/admin/municipios')
@login_required
def administrar_municipios():
    if not current_user.es_admin:
        flash('No tienes permisos para acceder a esta página', 'error')
        return redirect(url_for('main.index'))
    
    municipios = Municipio.query.all()
    return render_template('admin/municipios.html', municipios=municipios)

@main_bp.route('/admin/municipios/crear', methods=['GET', 'POST'])
@login_required
def crear_municipio():
    if not current_user.es_admin:
        flash('No tienes permisos para acceder a esta página', 'error')
        return redirect(url_for('main.index'))
    
    if request.method == 'POST':
        try:
            nombre = request.form.get('nombre')
            codigo = request.form.get('codigo')
            
            # Validar que no exista el municipio
            municipio_existente = Municipio.query.filter(
                (Municipio.nombre == nombre) | (Municipio.codigo == codigo)
            ).first()
            
            if municipio_existente:
                flash('Ya existe un municipio con ese nombre o código', 'error')
                return redirect(url_for('main.crear_municipio'))
            
            nuevo_municipio = Municipio(
                nombre=nombre,
                codigo=codigo.upper(),
                activo=True
            )
            
            db.session.add(nuevo_municipio)
            db.session.commit()
            flash('Municipio creado exitosamente', 'success')
            return redirect(url_for('main.administrar_municipios'))
            
        except Exception as e:
            db.session.rollback()
            flash('Error al crear el municipio', 'error')
    
    return render_template('admin/crear_municipio.html')

@main_bp.route('/admin/municipios/<int:municipio_id>/editar', methods=['GET', 'POST'])
@login_required
def editar_municipio(municipio_id):
    if not current_user.es_admin:
        flash('No tienes permisos para acceder a esta página', 'error')
        return redirect(url_for('main.index'))
    
    municipio = Municipio.query.get_or_404(municipio_id)
    
    if request.method == 'POST':
        try:
            nombre = request.form.get('nombre')
            codigo = request.form.get('codigo')
            activo = request.form.get('activo') == 'on'
            
            # Validar que no exista otro municipio con el mismo nombre o código
            municipio_existente = Municipio.query.filter(
                (Municipio.nombre == nombre) | (Municipio.codigo == codigo)
            ).filter(Municipio.id != municipio_id).first()
            
            if municipio_existente:
                flash('Ya existe otro municipio con ese nombre o código', 'error')
                return redirect(url_for('main.editar_municipio', municipio_id=municipio_id))
            
            municipio.nombre = nombre
            municipio.codigo = codigo.upper()
            municipio.activo = activo
            
            db.session.commit()
            flash('Municipio actualizado exitosamente', 'success')
            return redirect(url_for('main.administrar_municipios'))
            
        except Exception as e:
            db.session.rollback()
            flash('Error al actualizar el municipio', 'error')
    
    return render_template('admin/editar_municipio.html', municipio=municipio)

@main_bp.route('/admin/municipios/<int:municipio_id>/eliminar', methods=['POST'])
@login_required
def eliminar_municipio(municipio_id):
    if not current_user.es_admin:
        return jsonify({'error': 'No autorizado'}), 403
    
    try:
        municipio = Municipio.query.get_or_404(municipio_id)
        
        # Verificar si hay tickets asociados
        if municipio.tickets:
            return jsonify({
                'error': 'No se puede eliminar el municipio porque tiene tickets asociados'
            }), 400
        
        db.session.delete(municipio)
        db.session.commit()
        
        return jsonify({'success': True})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500