import cmd
import importlib
import os
import sys
import ctypes

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def check_privileges():
    """Verifica si el usuario actual es Administrador o Root."""
    try:
        # Para Linux / Termux
        is_admin = os.getuid() == 0
    except AttributeError:
        # Para Windows
        is_admin = ctypes.windll.shell32.IsUserAnAdmin() != 0
    return is_admin

class RedTeamConsole(cmd.Cmd):
    prompt = "rt-toolkit > "

    def __init__(self):
        super().__init__()
        # Verificación de privilegios al arrancar
        self.is_admin = check_privileges()
        self.intro = "\n=== RedTeam Toolkit Core ===\n"
        if self.is_admin:
            self.intro += "[+] Privilegios detectados: ROOT / ADMINISTRADOR.\n"
        else:
            self.intro += "[-] Privilegios detectados: USUARIO ESTÁNDAR.\n"
            self.intro += "[!] Advertencia: Módulos avanzados podrían fallar sin permisos elevados.\n"
        self.intro += "Escribe 'help' o '?' para ver los comandos.\n"

        self.modules = {}
        self.current_module = None
        self.load_modules()

    # ... (Mantén aquí el resto de las funciones: load_modules, do_list, do_use, do_show, do_set, do_run, do_back, do_exit que ya tenías) ...
    def load_modules(self):
        module_dir = 'modules'
        if not os.path.exists(module_dir):
            os.makedirs(module_dir)
            
        print("[*] Cargando módulos dinámicamente...")
        for filename in os.listdir(module_dir):
            if filename.endswith(".py") and filename not in ["__init__.py", "base_module.py"]:
                module_name = filename[:-3]
                try:
                    mod = importlib.import_module(f"{module_dir}.{module_name}")
                    class_name = "".join(word.capitalize() for word in module_name.split("_"))
                    
                    if hasattr(mod, class_name):
                        self.modules[module_name] = getattr(mod, class_name)()
                        print(f"  [+] Cargado: {module_name}")
                except Exception as e:
                    print(f"  [-] Error al cargar {module_name}: {e}")

    def do_list(self, arg):
        print("\nMódulos disponibles:")
        for name, instance in self.modules.items():
            print(f"  - {name}: {getattr(instance, 'description', 'Sin descripción')}")
        print()

    def do_use(self, arg):
        if arg in self.modules:
            self.current_module = self.modules[arg]
            self.prompt = f"rt-toolkit ({arg}) > "
        else:
            print(f"[-] Módulo '{arg}' no encontrado.")

    def do_show(self, arg):
        if arg == "options" and self.current_module:
            print(f"\nOpciones para {self.current_module.__class__.__name__}:")
            print(f"{'Nombre':<15} {'Valor Actual':<20} {'Requerido':<10} {'Descripción'}")
            print("-" * 65)
            for key, config in self.current_module.options.items():
                val = str(config['value']) if config['value'] else ""
                req = "Sí" if config['required'] else "No"
                print(f"{key:<15} {val:<20} {req:<10} {config['desc']}")
            print()
        elif not self.current_module:
            print("[-] Selecciona un módulo primero.")

    def do_set(self, arg):
        if not self.current_module:
            print("[-] Selecciona un módulo primero.")
            return

        parts = arg.split(maxsplit=1)
        if len(parts) == 2:
            key, value = parts[0].upper(), parts[1]
            if key in self.current_module.options:
                self.current_module.options[key]['value'] = value
                print(f"[*] {key} => {value}")
            else:
                print(f"[-] Opción '{key}' inválida.")
        else:
            print("[-] Uso incorrecto. Ej: set PORTS 1-1000")

    def do_run(self, arg):
        if self.current_module:
            print(f"[*] Lanzando {self.current_module.__class__.__name__}...\n")
            self.current_module.run()
        else:
            print("[-] Ningún módulo seleccionado.")

    def do_back(self, arg):
        self.current_module = None
        self.prompt = "rt-toolkit > "

    def do_exit(self, arg):
        print("Saliendo...")
        return True

if __name__ == '__main__':
    RedTeamConsole().cmdloop()