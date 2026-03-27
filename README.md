# tourist-expert

Продукционная экспертная система "Консультант по путешествиям".

## Требования

- Python 3.10+ (рекомендуется 3.14)
- `pip`

## Установка и запуск (Linux)

1. Перейдите в директорию проекта:

```bash
cd /path/to/tourist-expert
```

2. Создайте виртуальное окружение:

```bash
python -m venv venv
```

3. Активируйте виртуальное окружение:

```bash
source venv/bin/activate
```

4. Установите зависимости:

```bash
pip install -r requirements.txt
```

5. Запустите приложение:

```bash
python -m app
```

6. Откройте в браузере:

```text
http://127.0.0.1:5000
```

## Установка и запуск (Windows)

1. Перейдите в директорию проекта:

```powershell
cd C:\path\to\tourist-expert
```

2. Создайте виртуальное окружение:

```powershell
py -m venv venv
```

3. Активируйте виртуальное окружение:

```powershell
venv\Scripts\activate
```

4. Установите зависимости:

```powershell
pip install -r requirements.txt
```

5. Запустите приложение:

```powershell
python -m app
```

6. Откройте в браузере:

```text
http://127.0.0.1:5000
```

## Полезно

- После консультации JSON-файлы сессий сохраняются в папку `consultation/`.
- Папка `consultation/` исключена из Git и используется только для локальной отладки.
