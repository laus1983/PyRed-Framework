class BaseModule:
    description = "Módulo base genérico"
    
    # Diccionario de opciones: 'NOMBRE': {'value': valor, 'required': True/False, 'desc': 'Descripción'}
    options = {}

    def run(self):
        raise NotImplementedError("Cada módulo debe implementar su propio método run()")

    def check_requirements(self):
        """Verifica que todas las opciones requeridas tengan un valor asignado."""
        for key, config in self.options.items():
            # Validación estricta para evitar errores de sintaxis
            if config['required'] and not config['value']:
                print(f"[-] Error: La opción requerida '{key}' no está configurada.")
                return False
        return True