# Makefile for NSGA-III Nutrition Optimization Manuscript

# LaTeX compiler
LATEX = pdflatex
BIBTEX = bibtex

# Main document
MAIN = main
TARGET = $(MAIN).pdf

# Source files
TEX_FILES = $(MAIN).tex algorithm.tex
BIB_FILES = references.bib
FIGURES = ../results/figures/*.png

# Default target
all: $(TARGET)

# Build the PDF
$(TARGET): $(TEX_FILES) $(BIB_FILES)
	$(LATEX) $(MAIN)
	$(BIBTEX) $(MAIN)
	$(LATEX) $(MAIN)
	$(LATEX) $(MAIN)

# Clean auxiliary files
clean:
	rm -f *.aux *.log *.out *.toc *.bbl *.blg *.fdb_latexmk *.fls *.synctex.gz

# Clean everything except source files
distclean: clean
	rm -f $(TARGET)

# View the PDF (platform dependent)
view: $(TARGET)
	@if command -v xdg-open > /dev/null; then \
		xdg-open $(TARGET); \
	elif command -v open > /dev/null; then \
		open $(TARGET); \
	else \
		echo "Please open $(TARGET) manually"; \
	fi

# Check if all required files exist
check:
	@echo "Checking required files..."
	@for file in $(TEX_FILES); do \
		if [ -f $$file ]; then \
			echo "✓ $$file"; \
		else \
			echo "✗ $$file (missing)"; \
		fi; \
	done
	@echo "Checking figures..."
	@for fig in $(FIGURES); do \
		if [ -f $$fig ]; then \
			echo "✓ $$fig"; \
		else \
			echo "✗ $$fig (missing)"; \
		fi; \
	done

# Help
help:
	@echo "Available targets:"
	@echo "  all        - Build the complete PDF"
	@echo "  clean      - Remove auxiliary files"
	@echo "  distclean  - Remove all generated files"
	@echo "  view       - Open the PDF"
	@echo "  check      - Check if all required files exist"
	@echo "  help       - Show this help message"

.PHONY: all clean distclean view check help 