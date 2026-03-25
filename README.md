# example-service-cpu

Минимальный Python HTTP-сервис для проверки CPU quota и resource limits.

## Что умеет

- `GET /healthz` - простой healthcheck
- `GET /cpu?seconds=10&workers=2` - запускает CPU-bound вычисления в отдельных процессах

Сервис специально считает простые числа в tight loop, чтобы держать CPU загруженным без внешних зависимостей.

## Локальный запуск

```bash
python3 app.py
```

Проверка:

```bash
curl http://localhost:8080/healthz
curl "http://localhost:8080/cpu?seconds=10&workers=2"
```

## Docker

```bash
docker build -t example-service-cpu .
docker run --rm -p 8080:8080 example-service-cpu
```

## Как использовать для проверки CPU quota

Если контейнеру выдано, например, `500m`, можно дать нагрузку:

```bash
curl "http://<service>/cpu?seconds=30&workers=4"
```

И потом смотреть:

- CPU usage в Grafana
- throttling / quota поведение
- не превышает ли сервис ожидаемую долю CPU при нескольких worker-процессах

Обычно удобнее всего играть параметрами:

- `seconds` - как долго держать нагрузку
- `workers` - сколько параллельных CPU-bound процессов запустить
