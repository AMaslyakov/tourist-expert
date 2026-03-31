# tourist-expert

Продукционная экспертная система "Консультант по путешествиям".

## Что умеет приложение

- Показывает веб-форму для ввода параметров поездки.
- Подбирает рекомендацию на основе продукционных правил `experta`.
- Выполняет прямой и обратный explain-вывод.
- Сохраняет каждую консультацию в JSON в каталог `consultation/`.

## Требования

- Python 3.9+
- `pip`

## Установка и запуск на Linux/macOS

1. Перейдите в директорию проекта:

```bash
cd /path/to/tourist-expert
```

2. Создайте виртуальное окружение:

```bash
python3 -m venv venv
```

3. Активируйте его:

```bash
source venv/bin/activate
```

4. Установите зависимости:

```bash
pip install -r requirements.txt
```

5. Запустите приложение:

```bash
python3 -m app
```

6. Откройте в браузере:

```text
http://127.0.0.1:5000
```

Если в вашей системе команда `python` уже указывает на нужный интерпретатор, вместо `python3` можно использовать `python`.

## Установка и запуск на Windows

1. Перейдите в директорию проекта:

```powershell
cd C:\path\to\tourist-expert
```

2. Создайте виртуальное окружение:

```powershell
py -m venv venv
```

3. Активируйте его:

```powershell
venv\Scripts\activate
```

4. Установите зависимости:

```powershell
pip install -r requirements.txt
```

5. Запустите приложение:

```powershell
py -m app
```

6. Откройте в браузере:

```text
http://127.0.0.1:5000
```

## Запуск тестов

Linux/macOS:

```bash
python3 -m unittest discover -s tests -v
```

Windows:

```powershell
py -m unittest discover -s tests -v
```

## Полезно

- Приложение поднимает один маршрут: `/`.
- Каталог `consultation/` создается автоматически при старте приложения.
- В JSON-сессии сохраняются исходные данные, итоговая рекомендация и explain-данные для forward/backward вывода.
- Значение `SECRET_KEY` можно переопределить через переменную окружения `SECRET_KEY`; без нее используется локальное dev-значение.
