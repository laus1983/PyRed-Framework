# PyRed-Framework

Un framework modular, asíncrono y multiplataforma basado en Python, diseñado para centralizar herramientas de reconocimiento, escaneo y operaciones ofensivas de Red Team.

El toolkit proporciona una interfaz de línea de comandos (CLI) interactiva e intuitiva, similar a herramientas estándar de la industria (como Metasploit), permitiendo la carga dinámica de módulos y la orquestación de ataques o recolección de inteligencia sin depender de complejas interfaces gráficas.

## 🚀 Características Principales

- **Arquitectura Modular Dinámica:** Añade nuevos scripts de ataque o escaneo simplemente copiándolos en la carpeta `modules/`. El orquestador los cargará automáticamente (Plug & Play).
- **Consola Interactiva:** Interfaz CLI completa con soporte para configuración de variables al vuelo (`set`, `show options`).
- **Multiplataforma:** Compatible con Linux (ej. Arch Linux, Kali), Windows (incluye parches para bucles asíncronos nativos) y Android (vía Termux con soporte Root/tsu).
- **Conciencia de Privilegios:** Auto-detección de permisos de Administrador/Root al inicio, alertando sobre limitaciones en módulos que requieran _Raw Sockets_.
- **Ejecución Híbrida y Asíncrona:** Integración de motores ultrarrápidos nativos en Python (`asyncio`/`aiohttp`) con _wrappers_ que puentean herramientas robustas del sistema (Nmap, Gobuster, ffuf, etc.).

---

## 🛠️ Instalación y Configuración

### Prerrequisitos

- Python 3.8 o superior.
- Nmap (Recomendado para el módulo `hybrid_scanner`).
- Gobuster, ffuf, dirb o Nikto (Opcionales para el módulo `web_fuzzer`).

### 1. Clonar el repositorio

```bash
git clone [https://github.com/laus1983/PyRed-Framework.git](https://github.com/laus1983/PyRed-Framework.git)
cd PyRed-Framework
```

### 2. Instalación de dependencias

Se recomienda utilizar un entorno virtual, aunque no es estrictamente necesario si operas desde contenedores o Termux.

```bash
pip install -r requirements.txt
```

### 3. Configuración de API Keys (.env)

El framework utiliza un archivo `.env` en la raíz del proyecto para cargar automáticamente las credenciales necesarias en los módulos de OSINT. Crea el archivo `.env` con el siguiente formato:

```env
SHODAN_API_KEY=tu_clave_de_shodan
```

### 4. Ejecución en entornos móviles (Android / Termux)

Para operar el toolkit desde un smartphone rooteado y aprovechar módulos que requieran _Raw Sockets_:

```bash
pkg update && pkg upgrade
pkg install python git nmap tsu -y
pip install -r requirements.txt
# Ejecutar con privilegios root
sudo python main.py
# o alternativamente: tsu -c "python main.py"
```

---

## 📖 Guía de Uso

Para iniciar la consola interactiva, ejecuta el archivo principal:

```bash
# Inicio estándar
python main.py

# Inicio con privilegios (para escaneos avanzados)
sudo python main.py
```

### Comandos de la Consola (CLI)

Una vez dentro del prompt `rt-toolkit >`, tienes a disposición los siguientes comandos:

| Comando        | Descripción                                                     | Ejemplo de uso           |
| :------------- | :-------------------------------------------------------------- | :----------------------- |
| `help` o `?`   | Muestra el menú de ayuda y los comandos disponibles.            | `help`                   |
| `list`         | Muestra todos los módulos cargados dinámicamente en el sistema. | `list`                   |
| `use`          | Selecciona un módulo específico para interactuar con él.        | `use hybrid_scanner`     |
| `show options` | Lista las variables requeridas y opcionales del módulo activo.  | `show options`           |
| `set`          | Asigna un valor a una variable del módulo.                      | `set TARGET_IP 10.0.0.5` |
| `run`          | Ejecuta el módulo seleccionado con la configuración actual.     | `run`                    |
| `back`         | Deselecciona el módulo actual y vuelve al prompt principal.     | `back`                   |
| `exit`         | Cierra la consola y finaliza la aplicación.                     | `exit`                   |

---

## 🧩 Módulos Disponibles

### 1. `hybrid_scanner`

Un escáner de puertos y servicios que se adapta al entorno.

- Si Nmap está instalado, actúa como un orquestador en tiempo real que soporta todos los _flags_ nativos (ej. `-sS -O -sV -p-`).
- Si no está disponible, realiza un _fallback_ a un motor asíncrono puro en Python (`asyncio`) capaz de escanear miles de puertos por segundo.
- **Opciones principales:** `TARGET_IP`, `ENGINE` (`nmap` o `python`), `NMAP_ARGS`, `PORTS`.

### 2. `osint_recon`

Reconocimiento pasivo de dominios, DNS y subdominios sin alertar al objetivo.

- **Integraciones:** Certificate Transparency (`crt.sh`), HackerTarget, y Shodan.
- **Opciones principales:** `TARGET_DOMAIN`, `FIND_SUBDOMAINS`, `DNS_ENUM`, `USE_SHODAN`.

### 3. `web_fuzzer`

Fuzzer de directorios y archivos web híbrido y ultrarrápido.

- Capaz de orquestar herramientas de la industria como `gobuster`, `ffuf`, `dirb` y `nikto`.
- Incluye un motor de respaldo asíncrono nativo en Python (`aiohttp`) en caso de no contar con binarios externos.
- **Opciones principales:** `TARGET_URL`, `ENGINE`, `WORDLIST`, `EXTENSIONS`, `CONCURRENCY`.

### 4. `tcp_handler`

Listener TCP avanzado para atrapar conexiones entrantes (estilo Netcat).

- Utiliza multiplexación (`select`) para I/O asíncrono no bloqueante, permitiendo manejar el teclado y la red simultáneamente sin congelar la consola.
- Soporta la reutilización inmediata de puertos (`SO_REUSEADDR`) para prevenir errores en caso de cierres abruptos.
- **Opciones principales:** `LHOST`, `LPORT`.

---

## 🧑‍💻 Desarrollo y Creación de Módulos

El toolkit está diseñado para crecer. Para añadir una nueva herramienta, crea un archivo `.py` en la carpeta `modules/` que herede de `BaseModule`.

**Estructura básica de un nuevo módulo:**

```python
from modules.base_module import BaseModule

class MiNuevoModulo(BaseModule):
    description = "Descripción breve de lo que hace el script"

    options = {
        'OBJETIVO': {'value': None, 'required': True, 'desc': 'Descripción de la variable'},
    }

    def run(self):
        if not self.check_requirements():
            return

        objetivo = self.options['OBJETIVO']['value']
        print(f"[*] Ejecutando ataque contra {objetivo}...")
        # Lógica de tu código aquí
```

---

## ⚠️ Aviso Legal y Ética (Disclaimer)

Este proyecto y los módulos contenidos en él han sido desarrollados **estrictamente con fines educativos, de investigación académica y para la ejecución de auditorías de seguridad autorizadas**.

El uso de esta herramienta para atacar objetivos sin el consentimiento previo por escrito es ilegal. El autor no asume ninguna responsabilidad, ni se hace cargo de ningún daño causado por el mal uso o la utilización de este código para actividades maliciosas.

---

_Autor: Luis Alberto Urdaneta Salazar (CEH, E\|CSA)_
