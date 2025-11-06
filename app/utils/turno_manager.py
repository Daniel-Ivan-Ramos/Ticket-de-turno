class TurnoManager:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(TurnoManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            from app.models import db, Ticket, Municipio
            self.db = db
            self.Ticket = Ticket
            self.Municipio = Municipio
            self._initialized = True
    
    def obtener_siguiente_turno(self, municipio_id):
        try:
            ultimo_ticket = self.Ticket.query.filter_by(
                municipio_id=municipio_id
            ).order_by(self.Ticket.numero_turno.desc()).first()
            
            if ultimo_ticket:
                return ultimo_ticket.numero_turno + 1
            else:
                return 1
                
        except Exception as e:
            print(f"Error obteniendo siguiente turno: {e}")
            return 1
    
    def validar_turno_existente(self, municipio_id, curp):
        try:
            return self.Ticket.query.filter_by(
                municipio_id=municipio_id, 
                curp=curp
            ).first()
        except Exception as e:
            print(f"Error validando turno existente: {e}")
            return None