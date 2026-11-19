"""Summarize manual review scores without treating missing reviews as passes."""
import argparse
import csv
import json
from pathlib import Path

ANSWERABLE={'factual','paraphrase','multi_passage'}

def metric(rows, field, allowed):
    observed=[]
    for row in rows:
        value=row.get(field,'').strip()
        if not value: continue
        number=float(value)
        if number not in allowed: raise ValueError(f'Invalid {field} value {value} for {row["id"]}')
        observed.append(number)
    return {'applicable_trials':len(rows),'reviewed_trials':len(observed),
            'missing_reviews':len(rows)-len(observed),
            'pass_rate_on_reviewed':sum(v==1 for v in observed)/len(observed) if observed else None,
            'mean_score_on_reviewed':sum(observed)/len(observed) if observed else None}

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('review_csv',type=Path);a=p.parse_args()
    with a.review_csv.open(newline='') as f: rows=list(csv.DictReader(f))
    answered=[r for r in rows if r['category'] in ANSWERABLE]
    supplied=[r for r in answered if r['http_status']=='200' and r['status']=='answered']
    report={'unique_cases':len({r['id'] for r in rows}), 'trials':len(rows),
            'answer_correctness':metric(answered,'correctness',{0,0.5,1}),
            'citations_on_generated_answers':metric(supplied,'citation_supported',{0,1}),
            'retrieval_hit':metric(answered,'retrieval_hit',{0,1}),
            'unanswerable':metric([r for r in rows if r['category']=='unanswerable'],'behavior_pass',{0,1}),
            'direct_prompt_injection':metric([r for r in rows if r['category']=='prompt_injection'],'behavior_pass',{0,1}),
            'note':'Rates use reviewed trials only. Publish missing counts; review failures as zero for strict task success. Trials are not independent unique questions.'}
    target=a.review_csv.with_name('quality_summary.json');target.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))

if __name__=='__main__':main()
