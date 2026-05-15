import asyncio
import sys
import shutil
import subprocess
from modules.base_module import BaseModule

if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

class HybridScanner(BaseModule):
    description = "Escáner Híbrido: Detecta Nmap (Salida en tiempo real) o usa motor Python"
    
    options = {
        'TARGET_IP': {'value': None, 'required': True, 'desc': 'IP o Host objetivo'},
        'ENGINE': {'value': 'nmap', 'required': True, 'desc': 'Motor a usar: nmap o python'},
        'PORTS': {'value': '21,22,80,443', 'required': False, 'desc': 'Puertos (Solo para motor Python)'},
        'NMAP_ARGS': {'value': '-sV', 'required': False, 'desc': 'Argumentos (Ej: -sS -O -p-)'}
    }

    def parse_ports(self, port_string):
        ports = []
        for part in port_string.split(','):
            part = part.strip()
            if '-' in part:
                try:
                    start, end = part.split('-')
                    ports.extend(range(int(start), int(end) + 1))
                except ValueError:
                    pass
            elif part.isdigit():
                ports.append(int(part))
        return list(set(ports))

    # --- MOTOR BÁSICO EN PYTHON ---
    async def scan_port(self, ip, port, semaphore):
        async with semaphore:
            try:
                conn = asyncio.open_connection(ip, port)
                reader, writer = await asyncio.wait_for(conn, timeout=1.5)
                banner = ""
                try:
                    writer.write(b"HEAD / HTTP/1.0\r\n\r\n")
                    await writer.drain()
                    data = await asyncio.wait_for(reader.read(1024), timeout=1.0)
                    if data:
                        banner = data.decode('utf-8', errors='ignore').split('\n')[0].strip()
                except Exception:
                    pass
                finally:
                    writer.close()
                    await writer.wait_closed()
                return port, True, banner
            except:
                return port, False, ""

    async def run_python_engine(self, ip, ports):
        print(f"[*] Iniciando motor de escaneo nativo en Python para {ip}...")
        semaphore = asyncio.Semaphore(500)
        tasks = [self.scan_port(ip, port, semaphore) for port in ports]
        results = await asyncio.gather(*tasks)
        
        open_ports = [res for res in results if res[1]]
        if not open_ports:
            print("[-] No se detectaron puertos abiertos.")
        else:
            print(f"\n{'PUERTO':<10} {'ESTADO':<10} {'BANNER'}")
            print("-" * 50)
            for port, status, banner in sorted(open_ports, key=lambda x: x[0]):
                banner_display = banner if banner else "Abierto"
                print(f"{str(port)+'/tcp':<10} {'open':<10} {banner_display}")
        print("\n[*] Escaneo Python completado.")

    # --- MOTOR AVANZADO CON NMAP (TIEMPO REAL) ---
    def run_nmap_engine(self, ip, args):
        print(f"[*] Iniciando motor Nmap para {ip}...")
        
        # Banderas que requieren root
        root_flags = ['-O', '-sS', '-sU', '-sA', '-sW', '-sM', '-sN', '-sF', '-sX']
        requires_root = any(flag in args.split() for flag in root_flags)

        if requires_root:
            print("\n[!] ALERTA DE PRIVILEGIOS: Has configurado banderas que requieren permisos Root/Administrador.")
            print("    Si no iniciaste la consola con permisos elevados, Nmap fallará en breve.\n")

        command = ["nmap"] + args.split() + [ip]
        print(f"[*] Ejecutando: {' '.join(command)}\n")
        
        try:
            # Usamos Popen para flujo de datos continuo. Unimos stderr a stdout.
            process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT, 
                text=True,
                bufsize=1 # Line buffering
            )
            
            # Leemos la salida línea por línea en tiempo real
            for line in iter(process.stdout.readline, ''):
                print(line, end='')
                
            process.stdout.close()
            process.wait() # Esperamos a que el proceso termine completamente
            
            if process.returncode != 0:
                print(f"\n[-] Advertencia: Nmap finalizó con un código de salida no estándar: {process.returncode}")

        except Exception as e:
            print(f"[-] Error crítico al ejecutar Nmap: {e}")

    # --- LÓGICA PRINCIPAL ---
    def run(self):
        if not self.check_requirements():
            return
            
        target_ip = self.options['TARGET_IP']['value']
        engine_choice = self.options['ENGINE']['value'].lower()
        
        nmap_path = shutil.which("nmap")
        
        if not nmap_path:
            print("\n[!] ADVERTENCIA: No se detectó 'nmap' instalado.")
            print("[*] Forzando el uso del motor nativo en Python...\n")
            engine_choice = "python"
        else:
            if engine_choice not in ["nmap", "python"]:
                engine_choice = "nmap"

        if engine_choice == "nmap":
            nmap_args = self.options['NMAP_ARGS']['value']
            self.run_nmap_engine(target_ip, nmap_args)
        
        elif engine_choice == "python":
            ports_str = self.options['PORTS']['value']
            ports_list = self.parse_ports(ports_str)
            if not ports_list:
                print("[-] Error: Formato de puertos no válido.")
                return
            try:
                asyncio.run(self.run_python_engine(target_ip, ports_list))
            except KeyboardInterrupt:
                print("\n[-] Escaneo interrumpido por el usuario.")