# AuzolanApp (MVP A)

Plataforma web de ayuda vecinal altruista para comunidades pequeñas.

## Requisitos
- Python 3.11+
- Node.js 18+
- PostgreSQL

python -m venv .venv
.\.venv\Scripts\Activate.ps1

## Backend (Django + DRF)

### Configuración rápida
1. Crea y activa un entorno virtual.
2. Instala dependencias:

```bash
pip install -r backend/requirements.txt
```

3. Variables de entorno (ejemplo):

```bash
set DJANGO_SECRET_KEY="1234"
set POSTGRES_DB=auzolanapp
set POSTGRES_USER=postgres
set POSTGRES_PASSWORD=postgres
set POSTGRES_HOST=localhost
set POSTGRES_PORT=5432
```

4. Migraciones y servidor:

```bash
python backend/manage.py migrate
python backend/manage.py runserver
```

### PostgreSQL con Docker (opcional)
1. Copia el archivo de ejemplo:

```bash
copy .env.example .env
```

2. Levanta Postgres:

```bash
docker compose up -d postgres
```

3. Exporta las variables (o usa tus valores):

```bash
set DJANGO_SECRET_KEY=change_me
set POSTGRES_DB=auzolanapp
set POSTGRES_USER=postgres
set POSTGRES_PASSWORD=postgres
set POSTGRES_HOST=localhost
set POSTGRES_PORT=5432
```

### pgAdmin (UI visual) con Docker
Si quieres ver la base de datos de forma visual:
```bash
docker compose up -d postgres pgadmin
```
Luego abre: `http://localhost:5050`
- Email: `admin@example.com` (o `PGADMIN_DEFAULT_EMAIL`)
- Password: `admin1234` (o `PGADMIN_DEFAULT_PASSWORD`)

#### Cómo ver la base de datos en pgAdmin
1. En el panel izquierdo, clic derecho en **Servers** → **Register** → **Server...**
2. Pestaña **General**:
   - Name: `AuzolanApp`
3. Pestaña **Connection**:
   - Host name/address: `postgres`
   - Port: `5432`
   - Maintenance database: `auzolanapp`
   - Username: `postgres`
   - Password: `postgres`
   - Marca **Save password**
4. Guardar.

Ahora podrás navegar en:
`Servers > AuzolanApp > Databases > auzolanapp > Schemas > public > Tables`

### Cargar datos demo

```bash
python backend/manage.py seed_demo
```

Incluye:
- Comunidad "Comunidad Demo"
- 12 usuarios demo (password `Demo1234!`)
- Peticiones en estados open, in_progress, resolved y cancelled, con ofertas y chat
- Datos anteriores de la comunidad demo se reemplazan para dejar un escenario realista

## Frontend (React + Vite)

```bash
cd frontend
npm install
npm run dev
```

Por defecto el frontend usa `http://localhost:8000/api`. Para cambiarlo:

```bash
set VITE_API_URL=http://localhost:8000/api
```

## Arranque desde cero (paso a paso)
Guía pensada para Windows + PowerShell.

### 0) Prerrequisitos
- Instala Python 3.11+ y Node.js 18+
- Instala Docker Desktop **o** PostgreSQL local

### 1) Clonar/abrir proyecto y preparar venv
```bash
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 2) Instalar dependencias de backend
```bash
pip install -r backend/requirements.txt
```

### 3) Levantar PostgreSQL
Opción A (Docker recomendado):
```bash
copy .env.example .env
docker compose up -d postgres
```

Opción B (PostgreSQL local):
1. Asegúrate de que el servicio de PostgreSQL está encendido.
2. Crea la base de datos:
```bash
createdb -U postgres auzolanapp
```

### 4) Variables de entorno (backend)
```bash
set DJANGO_SECRET_KEY="cambia_esta_clave"
set POSTGRES_DB=auzolanapp
set POSTGRES_USER=postgres
set POSTGRES_PASSWORD=postgres
set POSTGRES_HOST=localhost
set POSTGRES_PORT=5432
```

### 5) Migraciones
```bash
python backend/manage.py makemigrations
python backend/manage.py migrate
```

### 6) Cargar datos demo
```bash
python backend/manage.py seed_demo
```
AuzolanApp\backend\apps\core\management\commands\seed_demo.py

Usuarios demo (password `Demo1234!`):
- maria.garcia@example.com
- juan.lopez@example.com
- ana.martinez@example.com
- pedro.sanchez@example.com
- carmen.ruiz@example.com
- luis.moreno@example.com
- laura.gomez@example.com
- carlos.navarro@example.com
- nuria.fernandez@example.com
- diego.perez@example.com
- ines.rodriguez@example.com
- miguel.santos@example.com

### 7) Levantar backend
```bash
python backend/manage.py runserver
```

Backend en: `http://localhost:8000`

### 8) Levantar frontend
En otra terminal:
```bash
cd frontend
npm install
npm run dev
```

Frontend en: `http://localhost:5173`

### 9) Probar la app
1. Entra a `http://localhost:5173`
2. Inicia sesión con `maria.garcia@example.com / Demo1234!`
3. Revisa “Peticiones” y “Mis peticiones”

### 10) Si algo falla
- Comprueba que PostgreSQL está activo.
- Verifica las variables `POSTGRES_*`.
- Repite migraciones si cambiaste modelos.

## Notas MVP
- No pagos ni monetización.
- Privacidad por defecto, ubicación aproximada.
- Chat solo tras aceptación de voluntario.
- Moderación y reportes en Django Admin.

## Swagger / Documentación visual de API
Se habilitó Swagger con drf-spectacular:
- Esquema: `http://localhost:8000/api/schema`
- Swagger UI: `http://localhost:8000/api/docs`

Si no te abre, instala dependencias y reinicia el backend:
```bash
pip install -r backend/requirements.txt
python backend/manage.py runserver
```
