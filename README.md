# AuzolanApp

Plataforma web de ayuda vecinal altruista para comunidades pequenas.

## 1) Que es este proyecto
AuzolanApp conecta personas para pedir y ofrecer ayuda dentro de su comunidad.

Principios del producto:
- Sin dinero: no pagos, no propinas, no tarifas.
- Sin publicidad ni captacion profesional.
- Todo recurso vive dentro de una comunidad.
- Privacidad por defecto (zona aproximada, sin direccion publica).
- Chat solo tras aceptar una oferta de voluntariado.

## 2) Estado actual del desarrollo
El proyecto ya tiene backend y frontend funcionales para:
- Registro y login con JWT.
- Seleccion de comunidad en registro.
- Listado, creacion y gestion de peticiones.
- Ofertas de ayuda y aceptacion de voluntario.
- Chat entre participantes.
- Reportes y moderacion.
- Prestamos vecinales (publicar item, solicitar, aceptar/rechazar y marcar devolucion).
- Gestion de miembros por comunidad para moderador/superadmin.
- Edicion de perfil propio (sin editar email).

## 3) Stack tecnico
- Backend: Django + Django REST Framework + SimpleJWT
- DB: PostgreSQL
- Frontend: React (Vite) + React Router + React-Bootstrap
- Documentacion API: drf-spectacular (Swagger)

## 4) Roles y permisos
### Usuario normal (member)
- Opera en sus comunidades aprobadas.
- Puede crear/editar/cerrar sus propias peticiones (segun estado).
- Puede ofrecer ayuda en peticiones abiertas.
- Puede reportar contenido.
- Puede editar su perfil (`display_name`, `bio`) pero no su email.

### Moderador de comunidad (moderator)
- Todo lo anterior dentro de su comunidad.
- Puede listar miembros de su comunidad.
- Puede editar datos de usuarios de su comunidad (`display_name`, `bio`, `status` de membership).
- Puede moderar peticiones de su comunidad (cerrar/eliminar).
- Puede ver ofertas de peticiones de su comunidad.
- Puede listar y gestionar reportes de su comunidad.
- No puede cambiar el rol de otros usuarios (reservado a superadmin).

### Superadmin global (`is_superuser`)
- Permisos globales sobre todas las comunidades.
- Puede gestionar miembros en cualquier comunidad.
- Puede cambiar rol en comunidad (`member` <-> `moderator`).
- Puede usar Django admin para operativa global.

## 5) Requisitos
- Python 3.11+
- Node.js 18+
- PostgreSQL (local o Docker)
- Docker Desktop (opcional)

## 6) Arranque rapido (Windows + PowerShell)

### 6.1 Backend
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r backend/requirements.txt
```

### 6.2 Base de datos
Opcion recomendada (Docker):
```powershell
Copy-Item .env.example .env
docker compose up -d postgres
```

Si usas Postgres local, crea la BD `auzolanapp` y ajusta variables.

### 6.3 Variables de entorno backend
```powershell
$env:DJANGO_SECRET_KEY = "change_me"
$env:POSTGRES_DB = "auzolanapp"
$env:POSTGRES_USER = "postgres"
$env:POSTGRES_PASSWORD = "postgres"
$env:POSTGRES_HOST = "localhost"
$env:POSTGRES_PORT = "5432"
```

### 6.4 Migraciones + datos demo
```powershell
python backend/manage.py migrate
python backend/manage.py seed_demo
```

### 6.5 Arrancar backend
```powershell
python backend/manage.py runserver
```
Backend: `http://localhost:8000`

### 6.6 Arrancar frontend (otra terminal)
```powershell
cd frontend
npm install
npm run dev
```
Frontend: `http://localhost:5173`

## 7) Datos demo (`seed_demo`) `backend\apps\core\management\commands\seed_demo.py`
`python backend/manage.py seed_demo` deja un escenario estable para pruebas.

Incluye:
- Comunidades: `Obanos`, `Com. Vecinos`
- 12 usuarios demo
- 1 superadmin demo
- Moderador en cada comunidad
- Peticiones, ofertas, conversaciones, mensajes y reportes
- Prestamos con items en `available` y `loaned`, y solicitudes en `pending/accepted/rejected`

Importante:
- Limpia peticiones/ofertas/chat/reportes de las comunidades demo.
- Elimina comunidades sobrantes que no sean `Obanos` o `Com. Vecinos` para evitar datos legacy.

### Credenciales demo
Usuarios demo (password comun): `Demo1234!`
- `maria.garcia@example.com`
- `juan.lopez@example.com`
- `ana.martinez@example.com`
- `pedro.sanchez@example.com`
- `carmen.ruiz@example.com`
- `luis.moreno@example.com`
- `laura.gomez@example.com`
- `carlos.navarro@example.com`
- `nuria.fernandez@example.com`
- `diego.perez@example.com`
- `ines.rodriguez@example.com`
- `miguel.santos@example.com`

Superadmin demo:
- `admin@example.com` / `AdminDemo1234!`

## 8) Flujos de uso recomendados
1. Usuario normal
- Login con `juan.lopez@example.com`
- Crear peticion, ofrecer ayuda y reportar contenido.
- Publicar un item de prestamo o solicitar uno disponible.

2. Moderador
- Login con `carlos.navarro@example.com` (Obanos) o `laura.gomez@example.com` (Com. Vecinos)
- Ir a `Mi comunidad` para listar/editar miembros.
- Ir a `Reportes` para revisar reportes de su comunidad y decidir si cierra/elimina peticiones reportadas.

3. Superadmin
- Login con `admin@example.com`
- Cambiar comunidad desde navbar y gestionar todo.
- Ir a `Reportes` para revisar reportes de cualquier comunidad.
- Acceder a `/admin` para operativa global.

4. Flujo de prestamos
- Ir a `/loans`.
- Publicar item con el mini formulario.
- Entrar al detalle del item para solicitar prestamo.
- Quien presta acepta/rechaza solicitudes y marca devolucion.

## 9) Rutas frontend principales
- `/` Home publica
- `/login`
- `/register`
- `/requests`
- `/requests/mine`
- `/requests/new`
- `/requests/:id`
- `/requests/:id/chat`
- `/reports` (moderador/superadmin)
- `/loans`
- `/loans/:id`
- `/profile`
- `/community/members` (moderador/superadmin)

## 10) Endpoints API principales
Prefijo: `/api`

Auth:
- `POST /api/auth/register` (requiere `community_id`)
- `POST /api/auth/token`
- `POST /api/auth/token/refresh`
- `GET /api/me`
- `GET/PATCH /api/profile`

Communities:
- `GET /api/communities`
- `POST /api/communities/{community_id}/join`
- `GET /api/communities/{community_id}/members`
- `PATCH /api/communities/{community_id}/members/{user_id}`

Requests/Offers:
- `GET/POST /api/requests`
- `GET/PATCH /api/requests/{request_id}`
- `POST /api/requests/{request_id}/close`
- `GET/POST /api/requests/{request_id}/offers`
- `POST /api/requests/{request_id}/accept-offer/{offer_id}`
- `POST /api/moderation/requests/{request_id}/close`
- `DELETE /api/moderation/requests/{request_id}`

Chat:
- `GET /api/requests/{request_id}/conversation`
- `GET/POST /api/conversations/{conversation_id}/messages`

Reports:
- `POST /api/requests/{request_id}/reports`
- `GET /api/reports`
- `POST /api/reports/{report_id}/status`

Loans:
- `GET /api/loans`
- `POST /api/loans`
- `GET /api/loans/{loan_id}`
- `PATCH /api/loans/{loan_id}`
- `GET /api/loans/{loan_id}/requests`
- `POST /api/loans/{loan_id}/requests`
- `POST /api/loans/{loan_id}/requests/{loan_request_id}/accept`
- `POST /api/loans/{loan_id}/requests/{loan_request_id}/reject`
- `POST /api/loans/{loan_id}/mark-returned`

## 11) Documentacion API y admin
- OpenAPI schema: `http://localhost:8000/api/schema`
- Swagger UI: `http://localhost:8000/api/docs`
- Django admin: `http://localhost:8000/admin`

## 12) Tests
Con entorno virtual activo:
```powershell
python backend/manage.py test
```

## 13) Errores comunes
- `No module named django`
  - Activa venv e instala `backend/requirements.txt`.
- Error de conexion a Postgres
  - Revisa variables `POSTGRES_*`.
- Frontend sin conectar al backend
  - Verifica backend en `http://localhost:8000`.
  - Si hace falta, define `VITE_API_URL`.
