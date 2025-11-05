# Console App

Минималистичная утилита для работы с файлами и архивами.

## Установка
```bash
uv sync
```

## Запуск
```bash
uv run app --help
```

## Основные команды
- ls [-l] <path>
- cat [-b] <file>
- rm [--recursive] <path>
- cd <path>
- mkdir <path>
- touch <path>
- mv <src> <dst>
- cp [-r] <src> <dst>
- zip <src> <archive.zip>
- unzip <archive.zip> <dst>
- tar [--compress] <src> <archive.tar[.gz]>
- untar <archive.tar[.gz]> <dst>
- history [--limit N]
- undo

## Примеры
```bash
uv run app ls -l .
uv run app cp -r folder backup/
uv run app rm --recursive backup/
uv run app undo
```

## Примечания
- История команд: ~/.history
- Бэкапы для undo: ~/.trash