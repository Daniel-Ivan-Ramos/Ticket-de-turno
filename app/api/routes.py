from flask import Blueprint, request, jsonify
from app.models import db, Ticket, Municipio
from app.utils.turno_manager import TurnoManager

api_bp = Blueprint('api', __name__)
turno_manager = TurnoManager()

@api_bp.route('/tickets', methods=['GET'])
def obtener_tickets():
    municipio_id = request.args.get('municipio_id')
    estatus = request.args.get('estatus')
    
    query = Ticket.query
    
    if municipio_id:
        query = query.filter_by(municipio_id=municipio_id)
    if estatus:
        query = query.filter_by(estatus=estatus)
    
    tickets = query.all()
    
    return jsonify([{
        'id': ticket.id,
        'curp': ticket.curp,
        'nombre_completo': f"{ticket.nombre} {ticket.apellido_paterno} {ticket.apellido_materno}",
        'municipio': ticket.municipio.nombre,
        'numero_turno': ticket.numero_turno,
        'estatus': ticket.estatus,
        'fecha_creacion': ticket.fecha_creacion.isoformat()
    } for ticket in tickets])

@api_bp.route('/tickets', methods=['POST'])
def crear_ticket():
    data = request.get_json()
    
    try:
        if turno_manager.validar_turno_existente(data['municipio_id'], data['curp']):
            return jsonify({'error': 'Ya existe un turno para esta CURP en el municipio'}), 400
        
        numero_turno = turno_manager.obtener_siguiente_turno(data['municipio_id'])
        
        nuevo_ticket = Ticket(
            curp=data['curp'],
            nombre=data['nombre'],
            apellido_paterno=data['apellido_paterno'],
            apellido_materno=data['apellido_materno'],
            telefono=data['telefono'],
            email=data['email'],
            municipio_id=data['municipio_id'],
            numero_turno=numero_turno
        )
        
        db.session.add(nuevo_ticket)
        db.session.commit()
        
        return jsonify({
            'id': nuevo_ticket.id,
            'numero_turno': nuevo_ticket.numero_turno,
            'mensaje': 'Turno creado exitosamente'
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@api_bp.route('/estadisticas')
def obtener_estadisticas():
    municipio_id = request.args.get('municipio_id')
    
    query = Ticket.query
    if municipio_id:
        query = query.filter_by(municipio_id=municipio_id)
    
    total = query.count()
    pendientes = query.filter_by(estatus='Pendiente').count()
    resueltos = query.filter_by(estatus='Resuelto').count()
    
    return jsonify({
        'total': total,
        'pendientes': pendientes,
        'resueltos': resueltos,
        'porcentaje_resueltos': (resueltos / total * 100) if total > 0 else 0
    })