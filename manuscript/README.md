# NSGA-III Nutrition Optimization Manuscript

This directory contains the LaTeX source files for the academic paper "Multi-Objective Nutrition Optimization Using NSGA-III: A Comprehensive Approach to Dietary Planning".

## Files

- `main.tex` - Main LaTeX document
- `algorithm.tex` - Detailed algorithm description
- `Makefile` - Build automation
- `README.md` - This file

## Prerequisites

To build the manuscript, you need:

1. **LaTeX Distribution**: Install a LaTeX distribution such as:
   - TeX Live (Linux/macOS)
   - MiKTeX (Windows)
   - MacTeX (macOS)

2. **Required Packages**: The following LaTeX packages are used:
   - `amsmath`, `amsfonts`, `amssymb` - Mathematical symbols
   - `graphicx` - Image inclusion
   - `booktabs` - Professional tables
   - `hyperref` - Hyperlinks
   - `geometry` - Page layout
   - `float` - Figure placement
   - `subcaption` - Subfigures
   - `algorithm`, `algorithmic` - Algorithm pseudocode
   - `listings` - Code listings
   - `xcolor` - Color support

## Building the Manuscript

### Using Make (Recommended)

```bash
# Build the complete PDF
make all

# Clean auxiliary files
make clean

# Clean everything except source files
make distclean

# Open the PDF (platform dependent)
make view

# Check if all required files exist
make check

# Show help
make help
```

### Manual Build

If you prefer to build manually:

```bash
# First pass
pdflatex main

# Bibliography
bibtex main

# Second pass
pdflatex main

# Third pass (for references)
pdflatex main
```

## Figures

The manuscript includes figures from the `../results/figures/` directory:

- `pareto_fronts_*.png` - Pareto front comparisons
- `objective_correlations_*.png` - Objective correlation matrix
- `solution_diversity_*.png` - Solution diversity analysis
- `convergence_*.png` - Convergence analysis
- `food_categories_*.png` - Food category usage
- `nutrient_achievement_*.png` - Nutrient achievement heatmap

## Content Overview

### Abstract
Brief overview of the NSGA-III approach to nutrition optimization.

### Introduction
- Motivation for multi-objective nutrition optimization
- Limitations of current approaches
- Contributions of this work

### Related Work
- Multi-objective optimization in nutrition
- NSGA-III and many-objective optimization
- Computational nutrition

### Problem Formulation
- Decision variables (7,083 foods)
- 8 objective functions with mathematical formulations
- Multi-objective optimization problem

### NSGA-III Algorithm
- Algorithm overview and pseudocode
- Reference point generation
- Selection mechanisms
- Genetic operations

### Experimental Setup
- Dataset description (7,083 foods, 31 nutrients)
- Experimental design (4 different objective combinations)
- Algorithm parameters

### Results and Analysis
- Solution quality statistics
- Pareto front analysis
- Objective correlations
- Food category analysis
- Nutrient achievement assessment

### Discussion
- Algorithm performance evaluation
- Solution quality assessment
- Limitations and future work

### Conclusion
Summary of contributions and future research directions.

## Customization

### Adding New Sections

To add new sections, edit `main.tex` and add:

```latex
\section{New Section Title}
\input{new_section}
```

Then create `new_section.tex` with your content.

### Modifying Figures

To use different figures, update the figure paths in `main.tex`:

```latex
\includegraphics[width=0.8\textwidth]{../results/figures/your_figure.png}
```

### Adding References

Add new references to the bibliography section in `main.tex`:

```latex
\bibitem{key}
Author, A.
\newblock Title of the paper.
\newblock \emph{Journal Name}, volume(issue):pages, year.
```

## Troubleshooting

### Common Issues

1. **Missing figures**: Ensure all figure files exist in `../results/figures/`
2. **LaTeX errors**: Check for missing packages or syntax errors
3. **Bibliography issues**: Run `bibtex` and multiple `pdflatex` passes

### Debug Mode

To see detailed LaTeX output:

```bash
pdflatex -interaction=nonstopmode main.tex
```

## Citation

If you use this work in your research, please cite:

```bibtex
@article{nsga3_nutrition_2024,
  title={Multi-Objective Nutrition Optimization Using NSGA-III: A Comprehensive Approach to Dietary Planning},
  author={Author Name},
  journal={Journal Name},
  year={2024},
  volume={X},
  number={Y},
  pages={Z}
}
```

## License

This manuscript is provided for academic and research purposes. Please respect the intellectual property rights of the authors.

## Contact

For questions or suggestions regarding this manuscript, please contact the authors. 