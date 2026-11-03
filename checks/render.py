#!/usr/bin/env python3
"""Fill README.md and dashboard/index.html from dashboard/data/counts.json."""

import json
import sys
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COUNTS = ROOT / "dashboard" / "data" / "counts.json"
README_IN = ROOT / "README.md.in"
README = ROOT / "README.md"
DASHBOARD = ROOT / "dashboard" / "index.html"


def quantize(numerator, denominator, places):
    value = (Decimal(numerator) * Decimal(100) / Decimal(denominator)).quantize(
        Decimal(places), rounding=ROUND_HALF_UP
    )
    return value


def pct(numerator, denominator, comma=False):
    text = format(quantize(numerator, denominator, "0.1"), "f")
    return text.replace(".", ",") if comma else text


def rate(numerator, denominator):
    return float(quantize(numerator, denominator, "0.1"))


def mean_text(facts, level):
    value = Decimal(str(facts["admission"][level]["mean_grade"])).quantize(
        Decimal("0.01"), rounding=ROUND_HALF_UP
    )
    return format(value, "f")


def row(facts, name, level):
    for item in facts[name]:
        if item["level"] == level:
            return item
    raise KeyError(name + level)


def age_table(facts):
    order = ["<=20", "21-23", "24-26", "27+"]
    lines = [
        "| Возраст | Без стипендии, завершившие | Выпуск | Со стипендией, завершившие | Выпуск |",
        "|---|---:|---:|---:|---:|",
    ]
    for band in order:
        cells = []
        for level in ("0", "1"):
            found = [
                item
                for item in facts["age_scholarship"]
                if item["age_band"] == band and item["scholarship"] == level
            ][0]
            cells.append(str(found["n_resolved"]))
            cells.append(pct(found["n_graduate"], found["n_resolved"], comma=True) + "%")
        lines.append("| %s | %s |" % (band, " | ".join(cells)))
    return "\n".join(lines)


def age_html(facts):
    order = ["<=20", "21-23", "24-26", "27+"]
    rows = []
    for band in order:
        cells = ["<td>%s</td>" % band]
        for level in ("0", "1"):
            found = [
                item
                for item in facts["age_scholarship"]
                if item["age_band"] == band and item["scholarship"] == level
            ][0]
            cells.append("<td>%s</td>" % found["n_resolved"])
            cells.append(
                "<td>%s%%</td>" % pct(found["n_graduate"], found["n_resolved"], comma=True)
            )
        rows.append("<tr>%s</tr>" % "".join(cells))
    return (
        "<table><thead><tr><th>Возраст</th><th>Без стипендии</th><th>Выпуск</th>"
        "<th>Со стипендией</th><th>Выпуск</th></tr></thead><tbody>"
        + "".join(rows)
        + "</tbody></table>"
    )


def prose(facts):
    fee0 = row(facts, "tuition", "0")
    fee1 = row(facts, "tuition", "1")
    sch0 = row(facts, "scholarship", "0")
    sch1 = row(facts, "scholarship", "1")
    zero = facts["sem1"]["zero"]
    some = facts["sem1"]["some"]
    english = """**Summary.** Study on open data, not an employer mart. One snapshot of %(n)s undergraduates from a Portuguese polytechnic (UCI 697, CC BY 4.0). The file has no student id and no dates.

Of %(n)s students, %(n_graduate)s have graduated, %(n_dropout)s dropped out, and %(n_enrolled)s are still enrolled. Graduates divided by everyone: %(pct_all)s%%. Graduates divided by finished outcomes only (%(n_resolved)s): %(pct_res)s%%. The first denominator counts people who have not finished as if they had failed to graduate.

Among finished outcomes, scholarship holders graduate at %(sch1)s%% (%(sch1_g)s of %(sch1_n)s) and the others at %(sch0)s%% (%(sch0_g)s of %(sch0_n)s). Mean admission grade is %(adm1)s against %(adm0)s, so the gap is not the admission score. It remains in every age band.

Students whose tuition was not up to date graduate at %(fee0)s%% of finished outcomes (%(fee0_g)s of %(fee0_n)s), against %(fee1)s%% (%(fee1_g)s of %(fee1_n)s) when it was. This is a snapshot association, not an effect of collecting a debt.

Among finished students who took at least one first-semester unit, %(zero_d)s of %(zero_n)s with zero units approved dropped out (%(zero_pct)s%%), against %(some_d)s of %(some_n)s who had at least one approved (%(some_pct)s%%). There are no dates in the file, so this is not an early warning: the zero and the dropout status were stored together.""" % {
        "n": facts["n"],
        "n_graduate": facts["n_graduate"],
        "n_dropout": facts["n_dropout"],
        "n_enrolled": facts["n_enrolled"],
        "n_resolved": facts["n_resolved"],
        "pct_all": pct(facts["n_graduate"], facts["n"]),
        "pct_res": pct(facts["n_graduate"], facts["n_resolved"]),
        "sch1": pct(sch1["n_graduate"], sch1["n_resolved"]),
        "sch1_g": sch1["n_graduate"],
        "sch1_n": sch1["n_resolved"],
        "sch0": pct(sch0["n_graduate"], sch0["n_resolved"]),
        "sch0_g": sch0["n_graduate"],
        "sch0_n": sch0["n_resolved"],
        "adm1": mean_text(facts, "1"),
        "adm0": mean_text(facts, "0"),
        "fee0": pct(fee0["n_graduate"], fee0["n_resolved"]),
        "fee0_g": fee0["n_graduate"],
        "fee0_n": fee0["n_resolved"],
        "fee1": pct(fee1["n_graduate"], fee1["n_resolved"]),
        "fee1_g": fee1["n_graduate"],
        "fee1_n": fee1["n_resolved"],
        "zero_d": zero["n_dropout"],
        "zero_n": zero["n_resolved"],
        "zero_pct": pct(zero["n_dropout"], zero["n_resolved"]),
        "some_d": some["n_dropout"],
        "some_n": some["n_resolved"],
        "some_pct": pct(some["n_dropout"], some["n_resolved"]),
    }
    russian = """**Коротко.** Учебный разбор открытых данных, не витрина работодателя. Один снимок %(n)s студентов португальского политехникума (UCI 697, лицензия CC BY 4.0). В файле нет идентификатора студента и нет дат.

Из %(n)s человек %(n_graduate)s уже выпустились, %(n_dropout)s отчислены, %(n_enrolled)s ещё учатся. Выпускники, делённые на всех: %(pct_all)s%%. Делённые только на тех, у кого исход уже известен (%(n_resolved)s): %(pct_res)s%%. В первом знаменателе незавершившие стоят так, будто они не выпустились.

Среди завершивших стипендиаты выпускаются в %(sch1)s%% случаев (%(sch1_g)s из %(sch1_n)s), остальные в %(sch0)s%% (%(sch0_g)s из %(sch0_n)s). Средний балл поступления %(adm1)s против %(adm0)s: разрыв не объясняется баллом на входе. Он остаётся в каждой возрастной группе, таблица ниже.

Если плата на снимке не была погашена, среди завершивших выпустились %(fee0)s%% (%(fee0_g)s из %(fee0_n)s). Если была погашена — %(fee1)s%% (%(fee1_g)s из %(fee1_n)s). Это связь в одном снимке, не эффект взыскания долга.

Среди завершивших, кто записался хотя бы на один предмет первого семестра, при нуле зачтённых отчислены %(zero_d)s из %(zero_n)s (%(zero_pct)s%%), а при хотя бы одном зачтённом — %(some_d)s из %(some_n)s (%(some_pct)s%%). Дат в файле нет, поэтому это не ранний сигнал: ноль зачётов и статус «отчислен» записаны вместе.""" % {
        "n": facts["n"],
        "n_graduate": facts["n_graduate"],
        "n_dropout": facts["n_dropout"],
        "n_enrolled": facts["n_enrolled"],
        "n_resolved": facts["n_resolved"],
        "pct_all": pct(facts["n_graduate"], facts["n"], comma=True),
        "pct_res": pct(facts["n_graduate"], facts["n_resolved"], comma=True),
        "sch1": pct(sch1["n_graduate"], sch1["n_resolved"], comma=True),
        "sch1_g": sch1["n_graduate"],
        "sch1_n": sch1["n_resolved"],
        "sch0": pct(sch0["n_graduate"], sch0["n_resolved"], comma=True),
        "sch0_g": sch0["n_graduate"],
        "sch0_n": sch0["n_resolved"],
        "adm1": mean_text(facts, "1").replace(".", ","),
        "adm0": mean_text(facts, "0").replace(".", ","),
        "fee0": pct(fee0["n_graduate"], fee0["n_resolved"], comma=True),
        "fee0_g": fee0["n_graduate"],
        "fee0_n": fee0["n_resolved"],
        "fee1": pct(fee1["n_graduate"], fee1["n_resolved"], comma=True),
        "fee1_g": fee1["n_graduate"],
        "fee1_n": fee1["n_resolved"],
        "zero_d": zero["n_dropout"],
        "zero_n": zero["n_resolved"],
        "zero_pct": pct(zero["n_dropout"], zero["n_resolved"], comma=True),
        "some_d": some["n_dropout"],
        "some_n": some["n_resolved"],
        "some_pct": pct(some["n_dropout"], some["n_resolved"], comma=True),
    }
    return english, russian, age_table(facts)


def render_readme(facts):
    english, russian, table = prose(facts)
    template = README_IN.read_text(encoding="utf-8")
    text = (
        template.replace("@@EN@@", english)
        .replace("@@RU@@", russian)
        .replace("@@AGE@@", table)
    )
    return text


def bar_chart(items, label_key, with_n=False):
    rows = []
    for item in items:
        shown = format(Decimal(str(item["rate"])), "f").replace(".", ",")
        width = format(Decimal(str(item["rate"])), "f")
        count = ""
        if with_n:
            count = "<span class=\"bar-n\">%s</span>" % item["n"]
        rows.append(
            "<div class=\"bar-row%s\">"
            "<span class=\"bar-label\">%s</span>"
            "<span class=\"bar-track\"><span class=\"bar-fill\" style=\"width: %s%%\"></span></span>"
            "<span class=\"bar-value\">%s%%</span>%s</div>"
            % (" course-row" if with_n else "", item[label_key], width, shown, count)
        )
    return "\n".join(rows)


def render_dashboard(facts):
    fee0 = row(facts, "tuition", "0")
    fee1 = row(facts, "tuition", "1")
    sch0 = row(facts, "scholarship", "0")
    sch1 = row(facts, "scholarship", "1")
    bars = [
        {"group": "Плата не погашена", "rate": rate(fee0["n_graduate"], fee0["n_resolved"])},
        {"group": "Плата погашена", "rate": rate(fee1["n_graduate"], fee1["n_resolved"])},
        {"group": "Без стипендии", "rate": rate(sch0["n_graduate"], sch0["n_resolved"])},
        {"group": "Стипендия", "rate": rate(sch1["n_graduate"], sch1["n_resolved"])},
    ]
    courses = [
        {
            "course": item["course"],
            "rate": rate(item["n_graduate"], item["n_resolved"]) if item["n_resolved"] else 0,
            "n": item["n_resolved"],
        }
        for item in facts["courses"]
        if item["n_resolved"]
    ]
    courses.sort(key=lambda item: (-item["rate"], int(item["course"])))
    zero = facts["sem1"]["zero"]
    some = facts["sem1"]["some"]
    html = """<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Исходы студентов · открытые данные</title>
<style>
  * { box-sizing: border-box; }
  body { margin: 0; background: #f4f1ea; color: #1c1c1c; font: 16px/1.45 Iowan Old Style, Palatino, Georgia, serif; overflow-x: hidden; }
  main { width: min(880px, 100%%); margin: 0 auto; padding: 32px 20px 64px; }
  h1 { font-size: 28px; line-height: 1.2; margin: 0 0 8px; }
  h2 { font-size: 18px; margin: 28px 0 8px; }
  p, li { max-width: 68ch; }
  .muted { color: #5e594f; }
  .nums { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; margin: 20px 0; }
  .num { background: #fff; border: 1px solid #e2dcd0; padding: 14px 16px; }
  .num b { display: block; font-size: 34px; letter-spacing: -0.03em; }
  table { border-collapse: collapse; width: 100%%; background: #fff; font-size: 14px; table-layout: fixed; }
  th, td { border-bottom: 1px solid #e2dcd0; text-align: right; padding: 6px 8px; }
  th:first-child, td:first-child { text-align: left; }
  .table-scroll { width: 0; min-width: 100%%; overflow-x: auto; }
  .bars { background: #fff; border: 1px solid #e2dcd0; padding: 10px 14px; margin-top: 8px; }
  .bar-row { display: grid; grid-template-columns: 11.5rem minmax(0, 1fr) 3.4rem; grid-template-areas: "label track value"; gap: 10px; align-items: center; margin: 8px 0; }
  .course-row { grid-template-columns: 3.6rem minmax(0, 1fr) 3.4rem 3rem; grid-template-areas: "label track value n"; }
  .bar-label { grid-area: label; min-width: 0; font-size: 14px; }
  .bar-track { grid-area: track; display: block; height: 16px; background: #f4f1ea; }
  .bar-fill { display: block; height: 16px; background: #1f4e5f; max-width: 100%%; }
  .bar-value { grid-area: value; text-align: right; font-size: 14px; font-variant-numeric: tabular-nums; }
  .bar-n { grid-area: n; text-align: right; color: #5e594f; font-size: 13px; font-variant-numeric: tabular-nums; }
  a { color: #1f4e5f; }
  @media (max-width: 640px) {
    .nums { grid-template-columns: 1fr; }
    .bar-row, .course-row { grid-template-columns: minmax(0, 1fr) auto auto; grid-template-areas: "label value n" "track track track"; }
  }
</style>
</head>
<body>
<main>
  <p class="muted">Учебный разбор открытых данных · не данные работодателя</p>
  <h1>Два знаменателя одной и той же когорты</h1>
  <p>Снимок %(n)s студентов португальского политехникума. %(n_enrolled)s ещё учатся, исход неизвестен. Слева выпускники разделены на всех. Справа — только на тех, у кого исход уже записан.</p>
  <div class="nums">
    <div class="num"><b>%(pct_all)s%%</b><span class="muted">%(n_graduate)s из %(n)s, включая ещё учащихся</span></div>
    <div class="num"><b>%(pct_res)s%%</b><span class="muted">%(n_graduate)s из %(n_resolved)s с известным исходом</span></div>
  </div>
  <h2>Плата и стипендия среди завершивших</h2>
  <p class="muted">Доля выпустившихся. Стипендия здесь не совпадает с более высоким баллом поступления: %(adm1)s против %(adm0)s.</p>
  <div class="bars">@@BARS@@</div>
  <h2>Выпуск по возрасту и стипендии</h2>
  <p class="muted">Только завершившие. Разрыв остаётся в каждой строке.</p>
  <div class="table-scroll">@@AGE_HTML@@</div>
  <h2>Первый семестр — не ранний сигнал</h2>
  <p>Среди завершивших, кто взял хотя бы один предмет: при нуле зачтённых отчислены %(zero_d)s из %(zero_n)s, при хотя бы одном зачтённом — %(some_d)s из %(some_n)s. Дат в файле нет, ноль и статус сняты одним снимком.</p>
  <h2>Программы</h2>
  <p class="muted">Код программы как в файле. Доля выпустившихся среди завершивших, в подписи — число завершивших. Расшифровку кодов не переписывал по памяти: она в статье Realinho и соавторов, 2022.</p>
  <div class="bars">@@COURSES@@</div>
  <p class="muted">Источник: UCI Machine Learning Repository, набор 697, CC BY 4.0. %(not_enrolled)s человек без записанных предметов первого семестра в сравнение семестра не входят.</p>
  <p class="muted"><a href="https://github.com/Grigorzelidze/portalegre-student-outcomes/blob/main/docs/decisions.md">Какие чтения этого файла неверны</a></p>
</main>
</body>
</html>
""" % {
        "n": facts["n"],
        "n_enrolled": facts["n_enrolled"],
        "n_graduate": facts["n_graduate"],
        "n_resolved": facts["n_resolved"],
        "pct_all": pct(facts["n_graduate"], facts["n"], comma=True),
        "pct_res": pct(facts["n_graduate"], facts["n_resolved"], comma=True),
        "adm1": mean_text(facts, "1").replace(".", ","),
        "adm0": mean_text(facts, "0").replace(".", ","),
        "zero_d": zero["n_dropout"],
        "zero_n": zero["n_resolved"],
        "some_d": some["n_dropout"],
        "some_n": some["n_resolved"],
        "not_enrolled": facts["sem1"]["not_enrolled"],
    }
    html = html.replace("@@AGE_HTML@@", age_html(facts))
    html = html.replace("@@BARS@@", bar_chart(bars, "group"))
    html = html.replace("@@COURSES@@", bar_chart(courses, "course", with_n=True))
    return html


def main():
    facts = json.loads(COUNTS.read_text(encoding="utf-8"))
    readme = render_readme(facts)
    dashboard = render_dashboard(facts)
    if "--check" in sys.argv:
        stale = []
        if not README.exists() or README.read_text(encoding="utf-8") != readme:
            stale.append(README.name)
        if not DASHBOARD.exists() or DASHBOARD.read_text(encoding="utf-8") != dashboard:
            stale.append(str(DASHBOARD.relative_to(ROOT)))
        if stale:
            raise SystemExit("out of date: " + ", ".join(stale))
        print("check ok")
        return
    README.write_text(readme, encoding="utf-8")
    DASHBOARD.parent.mkdir(parents=True, exist_ok=True)
    DASHBOARD.write_text(dashboard, encoding="utf-8")
    print("rendered", README.name, DASHBOARD.name)


if __name__ == "__main__":
    main()
