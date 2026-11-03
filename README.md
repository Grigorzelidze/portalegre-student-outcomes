# Исходы студентов политехникума Порталегре

[![build](https://github.com/Grigorzelidze/portalegre-student-outcomes/actions/workflows/build.yml/badge.svg)](https://github.com/Grigorzelidze/portalegre-student-outcomes/actions/workflows/build.yml)

Учебный разбор открытого набора [UCI 697](https://archive.ics.uci.edu/dataset/697/predict+students+dropout+and+academic+success). Это не витрина работодателя и не рабочий контур: сырьё публичное, логика разрезов выбрана вручную, цифры ниже пишет пайплайн, а не черновик.

**Коротко.** Учебный разбор открытых данных, не витрина работодателя. Один снимок 4424 студентов португальского политехникума (UCI 697, лицензия CC BY 4.0). В файле нет идентификатора студента и нет дат.

Из 4424 человек 2209 уже выпустились, 1421 отчислены, 794 ещё учатся. Выпускники, делённые на всех: 49,9%. Делённые только на тех, у кого исход уже известен (3630): 60,9%. В первом знаменателе незавершившие стоят так, будто они не выпустились.

Среди завершивших стипендиаты выпускаются в 86,2% случаев (835 из 969), остальные в 51,6% (1374 из 2661). Средний балл поступления 127,45 против 126,82: разрыв не объясняется баллом на входе. Он остаётся в каждой возрастной группе, таблица ниже.

Если плата на снимке не была погашена, среди завершивших выпустились 6,0% (29 из 486). Если была погашена — 69,3% (2180 из 3144). Это связь в одном снимке, не эффект взыскания долга.

Среди завершивших, кто записался хотя бы на один предмет первого семестра, при нуле зачтённых отчислены 493 из 495 (99,6%), а при хотя бы одном зачтённом — 851 из 2983 (28,5%). Дат в файле нет, поэтому это не ранний сигнал: ноль зачётов и статус «отчислен» записаны вместе.

## Возраст и стипендия

Только студенты с уже известным исходом: выпуск или отчисление. В ячейке «выпуск» — доля выпустившихся внутри этой ячейки.

| Возраст | Без стипендии, завершившие | Выпуск | Со стипендией, завершившие | Выпуск |
|---|---:|---:|---:|---:|
| <=20 | 1345 | 65,9% | 735 | 88,6% |
| 21-23 | 351 | 50,7% | 122 | 84,4% |
| 24-26 | 213 | 31,5% | 35 | 74,3% |
| 27+ | 752 | 32,2% | 77 | 71,4% |

## English

**Summary.** Study on open data, not an employer mart. One snapshot of 4424 undergraduates from a Portuguese polytechnic (UCI 697, CC BY 4.0). The file has no student id and no dates.

Of 4424 students, 2209 have graduated, 1421 dropped out, and 794 are still enrolled. Graduates divided by everyone: 49.9%. Graduates divided by finished outcomes only (3630): 60.9%. The first denominator counts people who have not finished as if they had failed to graduate.

Among finished outcomes, scholarship holders graduate at 86.2% (835 of 969) and the others at 51.6% (1374 of 2661). Mean admission grade is 127.45 against 126.82, so the gap is not the admission score. It remains in every age band.

Students whose tuition was not up to date graduate at 6.0% of finished outcomes (29 of 486), against 69.3% (2180 of 3144) when it was. This is a snapshot association, not an effect of collecting a debt.

Among finished students who took at least one first-semester unit, 493 of 495 with zero units approved dropped out (99.6%), against 851 of 2983 who had at least one approved (28.5%). There are no dates in the file, so this is not an early warning: the zero and the dropout status were stored together.

## Что открывается

- [Дашборд](https://grigorzelidze.github.io/portalegre-student-outcomes/) — те же два знаменателя, плата, стипендия, возраст и коды программ. Числа, таблица и столбцы собраны в HTML, страница не ждёт внешний скрипт. Исходник: [dashboard/index.html](dashboard/index.html).
- [`docs/decisions.md`](docs/decisions.md) — три чтения, которые файл не подтверждает: один знаменатель, стипендия как балл поступления, ноль зачётов как ранний сигнал.
- [`dashboard/data/counts.json`](dashboard/data/counts.json) — счётчики, из которых собраны этот файл и страница.

## Сборка останавливается

Пределы зашиты под этот zip и в dbt-тестах, и в `qa.assert_all()`. Сборка падает, а не рисует новые проценты, если:

- строк не 4424;
- статус вне Graduate, Dropout и Enrolled, статусов не три или кодов программ не 17;
- флаг не 0 и не 1;
- зачтённых или перезачтённых больше, чем взятых предметов;
- оценка вне 0–20;
- витрина не сходится сама с собой: выпуск, отчисление и «ещё учится» не дают всех, либо выпуск и отчисление не дают завершивших.

`make test` подменяет одну строку тремя способами и ждёт, что проверка упадёт. Правка не сохраняется.

## Как посчитать заново

Нужны `psql`, Python 3.9+ и пакеты из `requirements.txt` (pandas и dbt). Если `PGHOST` не задан, `scripts/pg_local.sh` поднимает локальный кластер на `127.0.0.1:54332` с trust-доступом только с этой машины. Каталог данных — `.pgdata`, в git он не входит. В CI кластер не поднимается: workflow уже указывает на Postgres 16. SQL написан так, чтобы его принимал Postgres 16.

```bash
make data
make build
make test
make check
```

`make data` скачивает zip UCI, сверяет SHA-256 из [`data/SHA256SUMS`](data/SHA256SUMS) и снимает BOM в копию для `\copy`. Pandas читает исходный `data.csv` и проверяет, что BOM и таб в имени колонки на месте.

`make build` грузит строки в `raw`. Дальше dbt: модель `student` приводит типы в `clean`, витрины собираются в `mart`, dbt-тесты останавливают сборку. Затем `qa.assert_all()` повторяет те же пределы, pandas сверяет витрины независимо, README и страница записываются заново.

`make test` портит одну строку тремя способами и ждёт, что проверка упадёт. Соединение при этом обрывается, правка не сохраняется. Затем JSON выгружается дважды и сравнивается побайтно.

`make check` ещё раз пересчитывает JSON и собирает README и страницу в памяти. Если текст разошёлся с файлами в git, команда завершается с ошибкой.

Сырой CSV в git не входит.

## Файлы

| Путь | Зачем |
|---|---|
| `sql/00_schemas.sql` | схемы `raw`, `clean`, `mart`, `qa` |
| `sql/10_raw.sql` | 37 текстовых колонок в порядке файла |
| `models/staging/student.sql` | dbt-модель: типы, таблица `clean.student` |
| `models/marts/` | dbt-витрины в схеме `mart` |
| `tests/` | dbt-тесты, которые останавливают `dbt build` |
| `sql/40_checks.sql` | те же пределы ещё раз, функцией `qa.assert_all()` |
| `checks/recompute.py` | второй путь: pandas против SQL |
| `checks/render.py` | README и страница из JSON |
| `checks/test_controls.py` | сломанная строка должна уронить проверку |
| `scripts/` | скачивание, локальный кластер, сборка |

## Данные и лицензия

Набор: Predict Students' Dropout and Academic Success, UCI Machine Learning Repository, id 697.

Авторы данных: Valentim Realinho, Mónica Vieira Martins, Jorge Machado, Luís Baptista.

Статья: Realinho, V.; Machado, J.; Baptista, L.; Martins, M.V. Predicting Student Dropout and Academic Success. *Data* 2022, 7, 146. [doi:10.3390/data7110146](https://doi.org/10.3390/data7110146).

Лицензия данных — CC BY 4.0. Код этого репозитория — MIT, см. [LICENSE](LICENSE).

Коды программ на странице не переведены в названия. Названия есть в статье; в репозиторий я их не переписывал.
