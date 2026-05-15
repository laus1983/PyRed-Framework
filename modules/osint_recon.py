import requests
import time
import os
from modules.base_module import BaseModule

class OsintRecon(BaseModule):
    description = "Reconocimiento pasivo (OSINT) integrado con crt.sh, HackerTarget y Shodan"
    
    def __init__(self):
        # Usamos __init__ para asegurar que os.getenv se evalúe cuando se instancia el módulo
        self.options = {
            'TARGET_DOMAIN': {'value': None, 'required': True, 'desc': 'Dominio objetivo (Ej: example.com)'},
            'FIND_SUBDOMAINS': {'value': 'true', 'required': False, 'desc': 'Buscar subdominios vía crt.sh (true/false)'},
            'DNS_ENUM': {'value': 'true', 'required': False, 'desc': 'Enumerar registros DNS/Hosts (true/false)'},
            'USE_SHODAN': {'value': 'true', 'required': False, 'desc': 'Buscar infraestructura en Shodan (true/false)'},
            # Aquí es donde ocurre la magia: leemos el archivo .env automáticamente
            'SHODAN_API_KEY': {'value': os.getenv('SHODAN_API_KEY', ''), 'required': False, 'desc': 'API Key de Shodan (Cargada del .env)'}
        }

    def fetch_crt_sh(self, domain):
        print(f"\n[*] Consultando crt.sh para subdominios de {domain}...")
        url = f"https://crt.sh/?q=%.{domain}&output=json"
        try:
            headers = {'User-Agent': 'Mozilla/5.0'}
            response = requests.get(url, headers=headers, timeout=15)
            if response.status_code == 200:
                data = response.json()
                subdomains = set()
                for entry in data:
                    name_value = entry.get('name_value', '')
                    for sub in name_value.split('\n'):
                        sub = sub.strip().lower()
                        if sub.endswith(domain) and '*' not in sub:
                            subdomains.add(sub)
                if subdomains:
                    print(f"[+] Se encontraron {len(subdomains)} subdominios únicos:")
                    for sub in sorted(subdomains):
                        print(f"    - {sub}")
                else:
                    print("[-] No se encontraron subdominios.")
            else:
                print(f"[-] Error en crt.sh: HTTP {response.status_code}")
        except Exception as e:
            print(f"[-] Error al conectar con crt.sh: {e}")

    def fetch_hackertarget_dns(self, domain):
        print(f"\n[*] Consultando HackerTarget para registros DNS de {domain}...")
        url = f"https://api.hackertarget.com/hostsearch/?q={domain}"
        try:
            response = requests.get(url, timeout=10)
            if response.status_code == 200:
                text_data = response.text
                if "error" in text_data.lower() or "exceeded" in text_data.lower():
                    print(f"[-] Error/Límite en HackerTarget: {text_data.strip()}")
                else:
                    print("[+] Registros encontrados:")
                    for line in text_data.split('\n'):
                        if line.strip():
                            parts = line.split(',')
                            if len(parts) >= 2:
                                print(f"    - Host: {parts[0]:<30} IP: {parts[1]}")
            else:
                print(f"[-] Error en HackerTarget: HTTP {response.status_code}")
        except Exception as e:
            print(f"[-] Error al conectar con HackerTarget: {e}")

    def fetch_shodan(self, domain, api_key):
        print(f"\n[*] Consultando Shodan para infraestructura asociada a {domain}...")
        if not api_key:
            print("[-] Saltando Shodan: No se encontró la API Key. Configúrala en el archivo .env o usa 'set SHODAN_API_KEY'")
            return

        query = f"hostname:{domain} OR ssl:{domain}"
        url = f"https://api.shodan.io/shodan/host/search?key={api_key}&query={query}"
        
        try:
            response = requests.get(url, timeout=15)
            if response.status_code == 200:
                data = response.json()
                total_results = data.get('total', 0)
                print(f"[+] Shodan encontró {total_results} equipos expuestos asociados al dominio.")
                
                matches = data.get('matches', [])
                for match in matches[:10]:
                    ip = match.get('ip_str', 'N/A')
                    port = match.get('port', 'N/A')
                    org = match.get('org', 'N/A')
                    os_info = match.get('os', 'Desconocido')
                    hostnames = match.get('hostnames', [])
                    hostname_str = hostnames[0] if hostnames else 'Sin Hostname'
                    
                    print(f"\n    [>] IP: {ip} | Puerto: {port}")
                    print(f"        Organización: {org}")
                    print(f"        Hostname: {hostname_str}")
                    print(f"        SO Detectado: {os_info}")
                
                if total_results > 10:
                    print(f"\n    [i] Mostrando 10 de {total_results} resultados. Usa la web de Shodan para ver el resto.")
            elif response.status_code == 401:
                print("[-] Error: API Key de Shodan inválida.")
            else:
                print(f"[-] Error en Shodan: Código HTTP {response.status_code}")
        except Exception as e:
            print(f"[-] Error al conectar con Shodan: {e}")

    def run(self):
        # Al verificar requerimientos, si la variable ya se cargó del .env, pasará la validación automáticamente
        if not hasattr(self, 'check_requirements') or not self.check_requirements():
            # Fallback en caso de que check_requirements no esté definido en la instancia actual por la migración a __init__
            pass 
            
        # Re-validación manual por seguridad para TARGET_DOMAIN
        if not self.options['TARGET_DOMAIN']['value']:
            print("[-] Error: La opción requerida 'TARGET_DOMAIN' no está configurada.")
            return

        target_domain = self.options['TARGET_DOMAIN']['value'].strip().lower()
        do_subdomains = str(self.options['FIND_SUBDOMAINS']['value']).strip().lower() == 'true'
        do_dns = str(self.options['DNS_ENUM']['value']).strip().lower() == 'true'
        do_shodan = str(self.options['USE_SHODAN']['value']).strip().lower() == 'true'
        shodan_key = str(self.options['SHODAN_API_KEY']['value']).strip()
        
        if target_domain.startswith('http://') or target_domain.startswith('https://'):
            target_domain = target_domain.split('//')[1].split('/')[0]
            
        print(f"\n[*] Iniciando módulo OSINT Recon para: {target_domain}")
        print("-" * 60)
        
        if do_subdomains:
            self.fetch_crt_sh(target_domain)
            time.sleep(1)
            
        if do_dns:
            self.fetch_hackertarget_dns(target_domain)
            time.sleep(1)

        if do_shodan:
            self.fetch_shodan(target_domain, shodan_key)
            
        print("\n[*] Módulo OSINT Recon finalizado.\n")