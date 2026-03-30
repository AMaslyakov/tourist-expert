SOURCE = report.typ
PDF = report.pdf
VIEWER = epdfview
FINISH_FILE = Практикум_3_Команда_7_Отчет.pdf

all: pdf

show: $(PDF)
	$(VIEWER) $(PDF)

pdf: $(SOURCE)
	typst compile --open $(VIEWER) $(SOURCE) $(PDF)

clean:
	rm $(PDF)

watch: $(SOURCE)
	typst watch --open $(VIEWER) $(SOURCE)

finish: $(SOURCE)
	typst compile --open $(VIEWER) $(SOURCE) $(FINISH_FILE)

.PHONY: clean show watch

