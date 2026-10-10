import json
import os
from pathlib import Path

def run():
    print("Generating report card...")
    results = {}
    
    # Load T1-T9 and ablations
    files = [
        'eval/t1_results.json', 'eval/t2_results.json', 'eval/t3_results.json',
        'eval/t4_results.json', 'eval/t5_results.json', 'eval/t6_results.json',
        'eval/t7_results.json', 'eval/t8_results.json', 'eval/t9_results.json',
        'eval/ablation_results.json'
    ]
    
    for f in files:
        if Path(f).exists():
            with open(f, 'r') as file:
                data = json.load(file)
                key = Path(f).stem
                results[key] = data
                
    with open('eval/report_card.json', 'w') as f:
        json.dump(results, f, indent=2, allow_nan=False)
        
    with open('docs/VALIDATION_FINAL_REPORT.md', 'w') as f:
        f.write("# SpeechProof Validation Final Report\n\n")
        f.write("## 1. Executive Summary\n")
        f.write("Validation sprint T4-T9 and A1-A5 executed. Due to N=1 (aryan_test.wav), most evaluations are marked INCONCLUSIVE or NOT RUN.\n\n")
        f.write("## 2. Project Problem and Scope\n")
        f.write("Evaluating automated speech scoring.\n\n")
        f.write("## 3. Scorer Architecture\n")
        f.write("SpeechProofScorer using large-v3 ASR.\n\n")
        f.write("## 4. Dataset Composition and Consent Status\n")
        f.write("Single authorized recording: aryan_test.wav. Consent for automated evaluation only.\n\n")
        f.write("## 5. Methodology and Results\n")
        f.write("Please see `eval/report_card.json` for full details.\n")
        for k, v in results.items():
            status = v.get('status', 'COMPLETED')
            if 'conclusion' in v:
                status = v['conclusion']
            if 'baseline' in v: # T3 format
                status = 'PILOT'
            f.write(f"- **{k.upper()}**: {status}\n")

if __name__ == '__main__':
    run()
