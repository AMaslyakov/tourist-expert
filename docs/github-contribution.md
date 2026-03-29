# Инструкция по внесению изменений через fork в репозиторий организации

Этот документ описывает единый процесс работы с репозиторием организации через личный fork.
Ссылки на репозитории подставляются вручную.

## Обозначения

- `git@github.com:student-projects-40916/tourist-expert.git`:ssh URL репозитория организации (upstream).
- `git@github.com:<YorGitHub>/tourist-expert.git`: ssh Url участника организации <YorGitHub> - название твоего GitHub
- `<task-branch>`: имя рабочей ветки под задачу, например `feature/add-season-rules`.

## 1. Сделать fork репозитория организации

1. Откройте страницу репозитория организации на GitHub.
2. Нажмите `Fork`.
3. Убедитесь, что fork создан в вашем аккаунте.

Результат:
- В организации остается исходный репозиторий.
- В вашем аккаунте появляется копия (fork), с которой вы работаете.

## 2. Клонировать fork к себе локально

```bash
git clone git@github.com:<YorGitHub>/tourist-expert.git
cd tourist-expert
```

Проверка:

```bash
git remote -v
```

Ожидается, что `origin` указывает на ваш fork.

## 3. Добавить `upstream` по HTTPS, только для fetch 

```bash
git remote add upstream https://github.com/student-projects-40916/tourist-expert.git
git remote -v
```

Ожидается:
- `origin` - ваш fork;
- `upstream` - репозиторий организации.

## 4. Синхронизировать локальный `main` с `upstream/main`

Перед началом каждой новой задачи обновляйте локальный `main` из `upstream`.

```bash
git checkout main
git fetch upstream
git pull --ff-only upstream main
```

Ветку main в локальном репозитории обнавляем через `git pull upsream main`(только main)
Ветку main в origin (форк на твоем аккаунте) обнавляем `git push origin main`(только main)

```bash
git push origin main
```

## 5. Создать новую ветку под изменения

Изменения выполняются только в новой ветке, не в `main`.

```bash
git checkout -b <task-branch>
```

Рекомендации(опционально) по именам веток:
- `feature/...` для нового функционала
- `fix/...` для исправлений
- `docs/...` для документации
- `test/...` для тестов

## 6. Внести изменения, закоммитить

После изменений проверьте статус и сделайте commit:

```bash
git status
git add .
git commit -m "Краткое описание изменений"
```

Рекомендуется делать несколько небольших осмысленных commit, если задача большая.

## 7. Запушить ветку в ваш fork на GitHub

```bash
git push -u origin <task-branch>
```

Результат:
- На GitHub в вашем fork появляется новая ветка с изменениями.

## 8. Создать Pull Request из новой ветки

1. Откройте ваш fork на GitHub.
2. Перейдите в ветку `<task-branch>`.
3. Нажмите `Compare & pull request`.
4. Проверьте направления PR:
   - `base repository`: репозиторий организации
   - `base branch`: `main`
   - `head repository`: ваш fork
   - `compare branch`: `<task-branch>`
5. Заполните заголовок и описание PR.
6. Создайте PR.

Важно: PR создается **из вашей новой ветки**, не из `main`.

## 9. Обновлять PR, если попросили правки

Вносите правки в ту же ветку `<task-branch>`, затем:

```bash
git add .
git commit -m "Исправления по ревью"
git push
```

PR обновится автоматически.

## 10. Поддерживать ветку актуальной, если `upstream/main` изменился

Если во время ревью `main` в организации ушел вперед:

```bash
git fetch upstream
git checkout <task-branch>
git merge upstream/main
```

Решите конфликты (если есть), затем:

```bash
git add .
git commit
git push
```

Допустимый альтернативный вариант в команде: `rebase` вместо `merge` (по внутренним правилам проекта).

## 11. После merge PR обновить локальный `main`

Когда PR принят и влит в `upstream/main`:

```bash
git checkout main
git fetch upstream
git pull --ff-only upstream main
git push origin main
```

## 12. Очистка старой рабочей ветки (опционально)

Локально:

```bash
git branch -d <task-branch>
```

В fork на GitHub:

```bash
git push origin --delete <task-branch>
```

## Краткий ежедневный сценарий

1. Обновить `main` из `upstream`.
2. Создать новую ветку от свежего `main`.
3. Сделать изменения и commit.
4. Запушить ветку в `origin`.
5. Создать PR в `upstream/main`.
6. Внести правки по ревью и допушить в ту же ветку.
