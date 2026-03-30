#import "@preview/modern-g7-32:0.2.0": custom-title-template

#let (
  per-line,
  if-present,
  fetch-field,
  sign-field,
  detailed-sign-field,
  agreed-field,
  approved-field,
  approved-and-agreed-fields,
) = custom-title-template.title-utils

#let unbreak-name(name) = {
  if name == none { return none }
  name.replace(" ", "\u{00A0}")
}

#let has-text(value) = value != none and value != ""

#let normalize-person(value, hint) = fetch-field(
  value,
  ("name", "position", "title", "part", "co-performer", "organization"),
  default: (
    name: none,
    position: none,
    title: none,
    part: none,
    co-performer: false,
    organization: none,
  ),
  hint: hint,
)

#let arguments(..args, year: auto) = {
  let args = args.named()
  args.organization = fetch-field(
    args.at("organization", default: none),
    ("full", "short"),
    default: (full: none, short: none),
    hint: "организации",
  )
  args.manager = normalize-person(args.at("manager", default: none), "руководителя")
  args.stage = fetch-field(
    args.at("stage", default: none),
    ("type", "num"),
    default: (type: none, num: none),
    hint: "этапа",
  )
  if "performer" in args.keys() {
    args.performer = normalize-person(args.at("performer", default: none), "исполнителя")
  }
  return args
}

#let template(
  ministry: none,
  organization: (
    full: "Московский авиационный институт",
    short: "Национальный исследовательский университет",
  ),
  institute: (number: none, name: none),
  department: (number: none, name: none),
  udk: none,
  research-number: none,
  report-number: none,
  approved-by: (name: none, position: none, year: auto),
  agreed-by: (name: none, position: none, year: none),
  report-type: "Отчёт",
  about: "О лабораторной работе",
  part: none,
  bare-subject: false,
  research: none,
  subject: none,
  stage: none,
  manager: (position: none, name: none, title: none),
  performer: none,
  year: auto,
  ..rest,
) = {
  let organization = fetch-field(
    organization,
    ("full", "short"),
    default: (full: none, short: none),
    hint: "организации",
  )
  let manager = normalize-person(manager, "руководителя")
  let performer = normalize-person(performer, "исполнителя")
  let stage = fetch-field(
    stage,
    ("type", "num"),
    default: (type: none, num: none),
    hint: "этапа",
  )

  let topic-lines = ()
  if has-text(report-type) {
    topic-lines.push(text(weight: "bold", upper(report-type)))
  }
  if has-text(about) {
    topic-lines.push([#about])
  }
  if has-text(research) {
    topic-lines.push([#research])
  }
  if has-text(subject) and not bare-subject {
    topic-lines.push([по теме:])
  }
  if has-text(subject) {
    topic-lines.push([*Тема:* #subject])
  }
  if has-text(stage.type) and stage.num == none {
    topic-lines.push([(#stage.type)])
  }
  if has-text(stage.type) and stage.num != none {
    topic-lines.push([(#stage.type, этап #stage.num)])
  }
  if has-text(part) {
    topic-lines.push([Книга #part])
  }

  let performer-role = if has-text(performer.title) {
    performer.title
  } else if has-text(performer.position) {
    performer.position
  } else {
    "Исполнитель"
  }

  let manager-role = if has-text(manager.title) {
    manager.title
  } else if has-text(manager.position) {
    manager.position
  } else {
    "Руководитель"
  }

  let sign-cells = ()
  if has-text(performer.name) {
    sign-cells.push([#performer-role:])
    sign-cells.push([])
    sign-cells.push([#unbreak-name(performer.name)])
  }
  if has-text(performer.name) and has-text(manager.name) {
    sign-cells.push([])
    sign-cells.push([])
    sign-cells.push([])
  }
  if has-text(manager.name) {
    sign-cells.push([#manager-role:])
    sign-cells.push([])
    sign-cells.push([#unbreak-name(manager.name)])
  }
  if has-text(manager.position) and manager.position != manager-role {
    sign-cells.push([])
    sign-cells.push([])
    sign-cells.push([#manager.position])
  }

  set par(justify: false, first-line-indent: 0pt, spacing: 0.2em)

  {
    set par(leading: 1em, spacing: 0em, first-line-indent: 0pt, justify: false)
    per-line(
      align: center,
      indent: 0pt,
      (value: [*#ministry*], when-present: ministry),
      (value: [#organization.full], when-present: organization.full),
      (value: [#organization.short], when-present: organization.short),
    )
  }

  v(50mm, weak: true)

  align(center)[
    #stack(
      spacing: 6mm,
      ..topic-lines,
    )
  ]

  v(65mm, weak: true)

  grid(
    columns: (auto, 48mm, auto),
    stroke: none,
    row-gutter: 0.5em,
    align: left + horizon,
    ..sign-cells,
  )

  v(0.5fr)
}
