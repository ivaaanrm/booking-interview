# Booking System

## Ejecutar

```bash
docker compose up -d --build
```

La API estará disponible en **http://localhost:80**.

## Probar la API

Importa `booking_api.postman_collection.json` en Postman — todos los endpoints están preconfigurados con ejemplos.

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/resources` | Listar recursos |
| GET | `/resources/{id}/availability?date=YYYY-MM-DD` | Consultar disponibilidad |
| GET/POST | `/reservations` | Listar / crear reservas |
| GET/PUT/PATCH/DELETE | `/reservations/{id}` | Gestionar una reserva |

## Desarrollo local

Requiere [uv](https://github.com/astral-sh/uv) y Python 3.12.

```bash
uv sync && uv run manage.py migrate && uv run manage.py runserver
```
