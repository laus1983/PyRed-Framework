from modules.base_module import BaseModule

class RedteamRefs(BaseModule):
    description = "Biblioteca de referencias rápidas y Cheat Sheets para Red Team"
    
    def __init__(self):
        self.options = {
            'CATEGORY': {'value': 'all', 'required': True, 'desc': 'Categoría: shells, privesc, wordlists, ad, all'}
        }
        
        # Base de datos interna de referencias
        self.references = {
            'shells': [
                {"name": "Reverse Shell Generator", "url": "https://www.revshells.com/", "desc": "Generador interactivo (La evolución moderna de PentestMonkey)."},
                {"name": "PentestMonkey", "url": "https://pentestmonkey.net/cheat-sheet/shells/reverse-shell-cheat-sheet", "desc": "El clásico cheat sheet de reverse shells."},
                {"name": "PayloadsAllTheThings (Shells)", "url": "https://github.com/swisskyrepo/PayloadsAllTheThings/blob/master/Methodology%20and%20Resources/Reverse%20Shell%20Cheatsheet.md", "desc": "Colección masiva de metodologías y comandos."}
            ],
            'privesc': [
                {"name": "GTFOBins", "url": "https://gtfobins.github.io/", "desc": "Bypass de restricciones locales y escalada en Linux usando binarios legítimos."},
                {"name": "LOLBAS", "url": "https://lolbas-project.github.io/", "desc": "El equivalente a GTFOBins pero para Windows (Living Off The Land)."},
                {"name": "HackTricks", "url": "https://book.hacktricks.xyz/", "desc": "La biblia moderna del pentesting y escalada de privilegios."}
            ],
            'wordlists': [
                {"name": "SecLists", "url": "https://github.com/danielmiessler/SecLists", "desc": "La colección de diccionarios más completa para Fuzzing y cracking."},
                {"name": "Trickest Wordlists", "url": "https://github.com/trickest/wordlists", "desc": "Diccionarios modernos generados y actualizados por la comunidad."}
            ],
            'ad': [
                {"name": "WADComs", "url": "https://wadcoms.github.io/", "desc": "Buscador interactivo de comandos para Active Directory."},
                {"name": "SANS AD Cheat Sheet", "url": "https://www.sans.org/posters/windows-and-active-directory-attacks/", "desc": "Poster oficial de ataques a Windows/AD."}
            ]
        }

    def print_category(self, cat_key, cat_title):
        print(f"\n=== {cat_title.upper()} ===")
        for item in self.references.get(cat_key, []):
            print(f"[*] {item['name']}")
            print(f"    URL : {item['url']}")
            print(f"    Info: {item['desc']}\n")

    def run(self):
        # Validación de la clase base
        if not hasattr(self, 'check_requirements') or not self.check_requirements():
            pass
            
        category = str(self.options['CATEGORY']['value']).strip().lower()
        
        valid_categories = list(self.references.keys()) + ['all']
        if category not in valid_categories:
            print(f"[-] Error: Categoría '{category}' inválida.")
            print(f"[*] Categorías disponibles: {', '.join(valid_categories)}")
            return

        print("\n[*] Cargando Biblioteca de Referencias Red Team...")
        print("-" * 60)

        if category == 'all':
            self.print_category('shells', 'Reverse Shells & Payloads')
            self.print_category('privesc', 'Escalada de Privilegios (PrivEsc)')
            self.print_category('wordlists', 'Diccionarios & Fuzzing (Wordlists)')
            self.print_category('ad', 'Active Directory')
        else:
            titles = {
                'shells': 'Reverse Shells & Payloads',
                'privesc': 'Escalada de Privilegios (PrivEsc)',
                'wordlists': 'Diccionarios & Fuzzing (Wordlists)',
                'ad': 'Active Directory'
            }
            self.print_category(category, titles[category])

        print("-" * 60)
        print("[*] Tip: En muchas terminales (como VSCode o Termux), puedes hacer Ctrl+Click (o mantener presionado) sobre la URL para abrirla directamente.")