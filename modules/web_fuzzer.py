import asyncio
import aiohttp
import sys
import os
import shutil
import subprocess
from modules.base_module import BaseModule

if sys.platform == 'win32':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

class WebFuzzer(BaseModule):
    description = "Web Fuzzer Híbrido: Motor Python Asíncrono, Gobuster, ffuf, dirb o Nikto"
    
    def __init__(self):
        self.options = {
            'TARGET_URL': {'value': None, 'required': True, 'desc': 'URL base (Ej: http://example.com)'},
            'ENGINE': {'value': 'python', 'required': True, 'desc': 'Motores: python, gobuster, ffuf, dirb, nikto'},
            'WORDLIST': {'value': '', 'required': False, 'desc': 'Ruta al diccionario (Requerido excepto en Nikto)'},
            'EXTENSIONS': {'value': '', 'required': False, 'desc': 'Extensiones. Ej: php,txt (No aplica a Nikto)'},
            'CONCURRENCY': {'value': '50', 'required': False, 'desc': 'Hilos/Conexiones concurrentes'},
            'TIMEOUT': {'value': '5', 'required': False, 'desc': 'Tiempo de espera (Motor Python)'},
            'ENGINE_ARGS': {'value': '', 'required': False, 'desc': 'Argumentos extra para motores externos'}
        }

    # --- MOTOR NATIVO EN PYTHON ---
    async def fetch(self, session, url, semaphore):
        async with semaphore:
            try:
                async with session.get(url, allow_redirects=False, ssl=False) as response:
                    status = response.status
                    if status != 404:
                        location = response.headers.get('Location', '')
                        redirect_info = f" -> {location}" if location else ""
                        
                        if status == 200:
                            print(f"[+] {status:<5} | {url}")
                        elif status in [301, 302, 307]:
                            print(f"[*] {status:<5} | {url}{redirect_info}")
                        elif status in [401, 403]:
                            print(f"[-] {status:<5} | {url} (Acceso Denegado)")
                        else:
                            print(f"[!] {status:<5} | {url}")
            except Exception:
                pass

    async def run_python_engine(self, base_url, wordlist_path, extensions, concurrency, timeout):
        print(f"\n[*] Iniciando motor de Fuzzing nativo en Python para {base_url}...")
        
        payloads = []
        with open(wordlist_path, 'r', encoding='utf-8', errors='ignore') as f:
            for line in f:
                word = line.strip()
                if not word or word.startswith('#'): continue
                payloads.append(word)
                if extensions:
                    for ext in extensions.split(','):
                        if ext.strip(): payloads.append(f"{word}.{ext.strip()}")

        print(f"[*] Total de peticiones: {len(payloads)} | Concurrencia: {concurrency}")
        print("-" * 60)
        
        if not base_url.endswith('/'): base_url += '/'
        semaphore = asyncio.Semaphore(concurrency)
        timeout_config = aiohttp.ClientTimeout(total=float(timeout))
        
        async with aiohttp.ClientSession(timeout=timeout_config) as session:
            tasks = [asyncio.create_task(self.fetch(session, f"{base_url}{payload}", semaphore)) for payload in payloads]
            await asyncio.gather(*tasks)

    # --- MOTOR EXTERNO (BINARIOS DEL SISTEMA) ---
    def run_external_engine(self, engine, url, wordlist, extensions, threads, extra_args):
        print(f"\n[*] Iniciando motor externo '{engine}' para {url}...")
        
        # Validación de privilegios: A diferencia de Nmap, los fuzzers web raramente necesitan Root,
        # a menos que intenten saltarse WAFs alterando paquetes o usando proxys locales privilegiados.
        if "nikto" in engine and "-Tuning" in extra_args:
            print("[i] Nota: Has activado opciones de Tuning en Nikto. Algunos perfiles intrusivos pueden ser bloqueados agresivamente por IPS/WAFs.")

        cmd = []
        
        # Construcción dinámica del comando según el binario
        if engine == "gobuster":
            cmd = ["gobuster", "dir", "-u", url, "-w", wordlist, "-t", str(threads)]
            if extensions: cmd.extend(["-x", extensions])
                
        elif engine == "ffuf":
            # ffuf requiere la palabra clave FUZZ en la URL
            target_url = url if "FUZZ" in url else (f"{url}/FUZZ" if not url.endswith('/') else f"{url}FUZZ")
            cmd = ["ffuf", "-u", target_url, "-w", wordlist, "-t", str(threads)]
            if extensions: cmd.extend(["-e", extensions])
                
        elif engine == "dirb":
            cmd = ["dirb", url, wordlist]
            if extensions: cmd.extend(["-X", f".{extensions.replace(',', ',.')}"]) # dirb espera .php,.txt
                
        elif engine == "nikto":
            cmd = ["nikto", "-h", url]
            # Nikto no requiere wordlist obligatoriamente
            
        if extra_args:
            cmd.extend(extra_args.split())

        print(f"[*] Ejecutando: {' '.join(cmd)}\n")
        
        try:
            # Ejecución asíncrona a nivel de sistema para ver el stream en consola
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT, 
                text=True,
                bufsize=1
            )
            
            for line in iter(process.stdout.readline, ''):
                print(line, end='')
                
            process.stdout.close()
            process.wait()
            
        except Exception as e:
            print(f"[-] Error crítico al ejecutar {engine}: {e}")

    # --- ORQUESTADOR PRINCIPAL ---
    def run(self):
        if not self.check_requirements(): return
            
        target_url = self.options['TARGET_URL']['value']
        engine_choice = self.options['ENGINE']['value'].lower()
        wordlist = self.options['WORDLIST']['value']
        extensions = self.options['EXTENSIONS']['value']
        concurrency = int(self.options['CONCURRENCY']['value'])
        timeout = self.options['TIMEOUT']['value']
        extra_args = self.options['ENGINE_ARGS']['value']
        
        if not target_url.startswith('http://') and not target_url.startswith('https://'):
            print("[-] Error: TARGET_URL debe comenzar con http:// o https://")
            return

        valid_engines = ["python", "gobuster", "ffuf", "dirb", "nikto"]
        if engine_choice not in valid_engines:
            print(f"[-] Motor inválido. Opciones: {', '.join(valid_engines)}")
            return

        # Si no es Nikto, validar que el diccionario exista
        if engine_choice != "nikto" and not wordlist:
            print(f"[-] Error: El motor '{engine_choice}' requiere que configures WORDLIST.")
            return
        if engine_choice != "nikto" and not os.path.isfile(wordlist):
            print(f"[-] Error: No se encontró el diccionario en: {wordlist}")
            return

        # Si elige un motor externo, validar que esté instalado en el sistema
        if engine_choice != "python":
            bin_path = shutil.which(engine_choice)
            if not bin_path:
                print(f"\n[!] ADVERTENCIA: La aplicación '{engine_choice}' no está instalada en el sistema.")
                print(f"[*] Realizando fallback automático al motor asíncrono en Python...")
                engine_choice = "python"

        # Ejecución
        if engine_choice == "python":
            try:
                asyncio.run(self.run_python_engine(target_url, wordlist, extensions, concurrency, timeout))
                print("\n[*] Fuzzing en Python completado.")
            except KeyboardInterrupt:
                print("\n[-] Fuzzing interrumpido por el usuario.")
        else:
            self.run_external_engine(engine_choice, target_url, wordlist, extensions, concurrency, extra_args)