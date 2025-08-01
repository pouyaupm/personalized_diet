# Nutrigenomic Day-Planner 🧬

A **genotype-aware nutrition optimization system** that designs personalized daily menus based on your DNA and optimizes them using multi-objective optimization (MOO).

## 🚀 Features

- **DNA Parsing**: Parse 23andMe/Ancestry raw data files locally (no upload required)
- **Genotype Rules**: Apply nutrition adjustments based on genetic variants (BCMO1, APOE, FADS1, TCF7L2)
- **Nutrient Enrichment**: Enhance food database with EPA/DHA and folate data via USDA FDC API
- **Multi-Objective Optimization**: Generate Pareto-optimal nutrition plans using NSGA-II
- **Personalized Recommendations**: Genotype-specific nutrition advice and food suggestions

## 🧬 Supported Genetic Variants

| Gene | SNPs | Effect | Nutrition Adjustment |
|------|------|--------|---------------------|
| **BCMO1** | rs12934922, rs7501331 | Vitamin A conversion efficiency | Higher beta-carotene conversion factor (24 vs 12) |
| **APOE** | rs429358, rs7412 | Saturated fat sensitivity | Increased saturated fat penalty (1.3x multiplier) |
| **FADS1** | rs174546 | Omega-3 metabolism | Minimum EPA/DHA requirement (300mg) |
| **TCF7L2** | rs7903146 | Carbohydrate metabolism | Higher fiber target (+5g), lower sugar cap (-10g) |

## 📋 Requirements

- Python 3.8+
- 23andMe or Ancestry raw DNA data file
- USDA FDC API key (optional, for nutrient enrichment)

## 🛠️ Installation

1. **Clone the repository**:
```bash
git clone <your-repo-url>
cd personalized_diet
```

2. **Install dependencies**:
```bash
pip install -r requirements.txt
```

3. **Set up FDC API key** (optional):
```bash
export FDC_API_KEY="your_api_key_here"
```
Get your free API key from: https://fdc.nal.usda.gov/api-guide/

## 🚀 Quick Start

### 1. Basic Usage (with sample data)

```bash
python nutrigenomic_pipeline.py --dna sample_dna.txt --calories 2000
```

This will:
- Parse the sample DNA file
- Apply genotype rules
- Run optimization with 2000 calorie target
- Generate personalized recommendations

### 2. With Your DNA Data

```bash
python nutrigenomic_pipeline.py \
  --dna your_23andme_data.txt \
  --calories 1800 \
  --protein 60 \
  --fat 65 \
  --carbs 200 \
  --fdc-key YOUR_FDC_API_KEY
```

### 3. Advanced Options

```bash
python nutrigenomic_pipeline.py \
  --dna your_dna.txt \
  --calories 2000 \
  --population 200 \
  --generations 300 \
  --output my_results.json \
  --no-enrich
```

## 📊 Output

The pipeline generates a comprehensive JSON report with:

- **Genotype Analysis**: SNPs found and rules applied
- **Optimization Results**: Pareto-optimal solutions
- **Food Recommendations**: Top recommended foods with quantities
- **Personalized Advice**: Genotype-specific nutrition recommendations

### Example Output Structure

```json
{
  "knee_point": {
    "solution_idx": 42,
    "objectives": [0.15, -0.85, -0.72, 0.08, -0.91, 0.23, -0.68, 1250.5],
    "food_quantities": [150.2, 75.8, 200.1, ...]
  },
  "food_analysis": {
    "significant_foods": [
      {"name": "Salmon, Atlantic", "category": "Proteins", "amount_g": 150.2},
      {"name": "Spinach, raw", "category": "Vegetables", "amount_g": 100.5}
    ],
    "category_breakdown": {"Proteins": 250.3, "Vegetables": 300.1, ...},
    "total_weight_g": 1250.5
  },
  "recommendations": {
    "genotype_specific": [
      "BCMO1 variant detected: Your body converts beta-carotene to vitamin A less efficiently. Consider including more pre-formed vitamin A sources (liver, eggs, dairy)."
    ],
    "food_suggestions": [
      "Salmon, Atlantic (Proteins): 150.2g",
      "Spinach, raw (Vegetables): 100.5g"
    ]
  }
}
```

## 🔧 Technical Details

### Architecture

```
User DNA (raw txt) ─┐
                    │  parse → {rsid: genotype} → apply "rules.json" → user-specific targets/penalties
                    └─────────────────────────────────────────────────────────────────────────────────┐
                                                                                                      │
`food.csv` (base nutrients) + FDC API enrichment (Folate DFE, EPA/DHA, etc.) → food table (normalized)┤
                                                                                                      │
optimizer (NSGA-II) → Pareto menus → UI (with "Genotype‑aware" badges)                                ┘
```

### Optimization Objectives

1. **Macro Deviation**: Minimize deviation from calorie/protein/fat/carb targets
2. **Micronutrient Completeness**: Maximize RDA achievement for 20+ nutrients
3. **Antioxidant Diversity**: Maximize variety and total antioxidant power
4. **Sugar-Fiber Ratio**: Optimize ratio, favor whole foods over processed
5. **Fat Quality**: Maximize Mediterranean-style fat ratios
6. **Electrolyte Balance**: Optimize sodium:potassium ratio
7. **Food Diversity**: Maximize variety across food categories
8. **Total Weight**: Minimize total food weight for practical portions

### Genotype Adjustments

- **BCMO1**: Vitamin A conversion factor (12 → 24 for variants)
- **APOE**: Saturated fat penalty multiplier (1.0 → 1.3 for variants)
- **FADS1**: EPA/DHA minimum requirement (0 → 300mg for variants)
- **TCF7L2**: Fiber target bonus (+5g) and sugar cap reduction (-10g)

## 🔬 DNA File Format

The system accepts 23andMe/Ancestry raw data files with tab-separated format:

```
rsid    chromosome    position    genotype
rs12934922        16    8103952    TT
rs7501331         16    8103245    CT
rs429358          19    45411941   CC
```

## 🌐 FDC API Integration

The USDA FoodData Central API enriches your food database with:

- **Folate DFE** (µg DFE) - for BCMO1 variants
- **EPA** (20:5 n-3) and **DHA** (22:6 n-3) - for FADS1 variants
- **Added sugars** - for TCF7L2 variants

### API Setup

1. Visit: https://fdc.nal.usda.gov/api-guide/
2. Click "Get an API Key"
3. Set environment variable: `export FDC_API_KEY="your_key"`
4. Rate limit: 1,000 requests/hour/IP

## 📈 Performance

- **Optimization**: NSGA-II with 100-200 population, 200-300 generations
- **Typical runtime**: 2-5 minutes for 7k foods
- **Solution quality**: 50-100 Pareto-optimal solutions
- **Memory usage**: ~500MB for full dataset

## 🔒 Privacy & Ethics

- **Local Processing**: DNA files parsed locally, never uploaded
- **Non-Medical**: Educational/research purposes only
- **Transparency**: All genotype rules and adjustments clearly documented
- **Export**: Users can download complete analysis logs

## 🧪 Testing

### Test with Sample Data

```bash
# Test genotype parser
python genotype_parser.py

# Test FDC API (requires API key)
python fdc_api.py

# Test optimizer
python nutrigenomic_optimizer.py

# Test complete pipeline
python nutrigenomic_pipeline.py --dna sample_dna.txt --calories 2000
```

### Expected Results

With the sample DNA file, you should see:
- BCMO1 variant detected (rs12934922: TT, rs7501331: CT)
- APOE variant detected (rs429358: CC, rs7412: CT)
- FADS1 variant detected (rs174546: TT)
- TCF7L2 variant detected (rs7903146: CT)

## 📚 References

- **FDC API**: https://fdc.nal.usda.gov/api-guide/
- **Genotype Rules**: Based on published nutrigenomic research
- **Optimization**: NSGA-II algorithm from pymoo library
- **Food Database**: USDA SR Legacy and Foundation Foods

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Submit a pull request

## 📄 License

This project is for educational and research purposes. Please ensure compliance with local regulations regarding genetic data processing.

## ⚠️ Disclaimer

This tool is for **educational and research purposes only**. It is not intended for medical diagnosis, treatment, or advice. Always consult with healthcare professionals for medical decisions.

---

**Built with ❤️ for personalized nutrition research** 