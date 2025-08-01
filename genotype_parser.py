import json
import pandas as pd
from pathlib import Path
from typing import Dict, List, Any, Optional
import gzip

class GenotypeParser:
    """Parser for 23andMe and Ancestry raw DNA data files"""
    
    def __init__(self, rules_file: str = "rules.genome.json"):
        """Initialize parser with genotype rules"""
        self.rules = self._load_rules(rules_file)
        
    def _load_rules(self, rules_file: str) -> List[Dict]:
        """Load genotype rules from JSON file"""
        try:
            with open(rules_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            print(f"Warning: Rules file {rules_file} not found. Using default rules.")
            return self._get_default_rules()
    
    def _get_default_rules(self) -> List[Dict]:
        """Default genotype rules for nutrition optimization"""
        return [
            {
                "gene": "BCMO1",
                "refs": ["rs12934922", "rs7501331"],
                "any_of": {"rs12934922": ["T"], "rs7501331": ["T"]},
                "effect": {
                    "vitamin_a_conversion_factor": 24
                },
                "note": "WT=12; carriers use higher factor (24–36) to convert beta-carotene to retinol equivalents."
            },
            {
                "gene": "APOE",
                "refs": ["rs429358", "rs7412"],
                "any_of": {"rs429358": ["C"], "rs7412": ["C"]},
                "effect": {
                    "sat_fat_penalty_multiplier": 1.3
                },
                "note": "ε4+ increases penalty on saturated fat."
            },
            {
                "gene": "FADS1",
                "refs": ["rs174546"],
                "any_of": {"rs174546": ["T"]},
                "effect": {
                    "epa_dha_min_mg": 300
                },
                "note": "Require some direct EPA/DHA for minor allele carriers."
            },
            {
                "gene": "TCF7L2",
                "refs": ["rs7903146"],
                "any_of": {"rs7903146": ["T"]},
                "effect": {
                    "fiber_target_bonus_g": 5,
                    "added_sugar_max_delta_g": -10
                },
                "note": "Higher fiber target and lower added-sugar cap."
            }
        ]
    
    def load_genotypes(self, raw_path: str) -> Dict[str, str]:
        """Load genotypes from raw DNA file (23andMe or Ancestry format)"""
        genotypes = {}
        
        # Handle gzipped files
        if raw_path.endswith('.gz'):
            opener = gzip.open
        else:
            opener = open
            
        with opener(raw_path, 'rt', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith('#'):
                    continue
                    
                parts = line.split('\t')
                if len(parts) < 4:
                    continue
                    
                rsid, chrom, pos, genotype = parts[0], parts[1], parts[2], parts[3]
                
                # Handle different genotype formats
                if len(genotype) == 1:
                    # Single allele (e.g., 'A')
                    genotypes[rsid] = genotype
                elif len(genotype) == 2:
                    # Two alleles (e.g., 'CT', 'AA')
                    genotypes[rsid] = genotype
                elif len(genotype) == 3 and genotype[1] in ['/', '-']:
                    # Separated format (e.g., 'C/T', 'A-A')
                    genotypes[rsid] = genotype[0] + genotype[2]
                else:
                    # Unknown format, skip
                    continue
                    
        return genotypes
    
    def apply_rules(self, genotypes: Dict[str, str]) -> Dict[str, Any]:
        """Apply genotype rules to generate nutrition adjustments"""
        adjustments = {
            "vitamin_a_conversion_factor": 12,  # default WT
            "sat_fat_penalty_multiplier": 1.0,
            "epa_dha_min_mg": 0,
            "fiber_target_bonus_g": 0,
            "added_sugar_max_delta_g": 0,
            "applied_rules": []
        }
        
        for rule in self.rules:
            # Check if any of the rule's conditions are met
            if self._check_rule_conditions(rule, genotypes):
                # Apply the rule effects
                for key, value in rule["effect"].items():
                    if key.endswith("_multiplier"):
                        adjustments[key] *= value
                    elif key.endswith("_delta_g"):
                        adjustments[key] += value
                    else:
                        adjustments[key] = value
                
                # Record which rules were applied
                adjustments["applied_rules"].append({
                    "gene": rule["gene"],
                    "note": rule["note"]
                })
        
        return adjustments
    
    def _check_rule_conditions(self, rule: Dict, genotypes: Dict[str, str]) -> bool:
        """Check if a rule's conditions are met by the user's genotypes"""
        any_of = rule.get("any_of", {})
        
        if not any_of:
            return False
            
        # Check if any of the "any_of" conditions are met
        for rsid, alleles in any_of.items():
            if rsid in genotypes:
                user_genotype = genotypes[rsid]
                # Check if any of the specified alleles are present
                for allele in alleles:
                    if allele in user_genotype:
                        return True
        
        return False
    
    def get_genotype_summary(self, genotypes: Dict[str, str]) -> Dict[str, Any]:
        """Generate a summary of the user's genotypes for display"""
        summary = {
            "total_snps": len(genotypes),
            "relevant_snps": {},
            "gene_summary": {}
        }
        
        # Check which SNPs from our rules are present
        for rule in self.rules:
            gene = rule["gene"]
            if gene not in summary["gene_summary"]:
                summary["gene_summary"][gene] = {
                    "snps": [],
                    "status": "not_found"
                }
            
            for rsid in rule["refs"]:
                if rsid in genotypes:
                    summary["relevant_snps"][rsid] = {
                        "genotype": genotypes[rsid],
                        "gene": gene
                    }
                    summary["gene_summary"][gene]["snps"].append({
                        "rsid": rsid,
                        "genotype": genotypes[rsid]
                    })
        
        # Determine gene status
        for gene, info in summary["gene_summary"].items():
            if info["snps"]:
                # Check if any rules were applied for this gene
                rule = next((r for r in self.rules if r["gene"] == gene), None)
                if rule and self._check_rule_conditions(rule, genotypes):
                    info["status"] = "variant_detected"
                else:
                    info["status"] = "wild_type"
        
        return summary

def parse_dna_file(file_path: str, rules_file: str = "rules.genome.json") -> Dict[str, Any]:
    """Convenience function to parse DNA file and return adjustments"""
    parser = GenotypeParser(rules_file)
    genotypes = parser.load_genotypes(file_path)
    adjustments = parser.apply_rules(genotypes)
    summary = parser.get_genotype_summary(genotypes)
    
    return {
        "genotypes": genotypes,
        "adjustments": adjustments,
        "summary": summary
    }

if __name__ == "__main__":
    # Example usage
    parser = GenotypeParser()
    
    # Create a sample genotype file for testing
    sample_genotypes = {
        "rs12934922": "TT",  # BCMO1 variant
        "rs7501331": "CT",   # BCMO1 variant
        "rs429358": "CC",    # APOE variant
        "rs7412": "CT",      # APOE variant
        "rs174546": "TT",    # FADS1 variant
        "rs7903146": "CT"    # TCF7L2 variant
    }
    
    adjustments = parser.apply_rules(sample_genotypes)
    summary = parser.get_genotype_summary(sample_genotypes)
    
    print("Sample Genotype Analysis:")
    print(json.dumps(adjustments, indent=2))
    print("\nSummary:")
    print(json.dumps(summary, indent=2)) 