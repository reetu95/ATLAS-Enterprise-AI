"""Sequential HTTP benchmark. Uses only the Python standard library."""
import argparse
import csv
import hashlib
import json
import math
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parent

def percentile(values, percent):
    if not values: return None
    ordered = sorted(values)
    return round(ordered[max(0, math.ceil(len(ordered)*percent/100)-1)], 2)

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base-url',default='http://127.0.0.1:8000')
    parser.add_argument('--split',choices=['development','heldout'],default='development')
    parser.add_argument('--repeats',type=int,default=1)
    parser.add_argument('--limit',type=int)
    parser.add_argument('--timeout',type=float,default=120)
    parser.add_argument('--label',required=True,help='Experiment name; e.g. baseline-modelname')
    parser.add_argument('--config-note',required=True,help='Non-secret model, region and retrieval settings')
    parser.add_argument('--dry-run',action='store_true',help='Validate and list counts without making requests')
    args = parser.parse_args()
    if args.repeats<1 or args.timeout<=0 or (args.limit is not None and args.limit<1):
        parser.error('repeats, timeout and limit must be positive')
    dataset = ROOT/f'{args.split}.jsonl'
    cases = [json.loads(line) for line in dataset.read_text().splitlines() if line.strip()]
    if args.limit: cases=cases[:args.limit]
    if args.dry_run:
        print(json.dumps({'requests':len(cases)*args.repeats,
                          'categories':dict(Counter(c['category'] for c in cases)),
                          'network_requests':0},indent=2)); return
    stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    output=ROOT/'results'/stamp; output.mkdir(parents=True)
    metadata={'started_at':stamp,'label':args.label,'config_note':args.config_note,
              'base_url':args.base_url,'split':args.split,'repeats':args.repeats,
              'dataset_sha256':hashlib.sha256(dataset.read_bytes()).hexdigest(),
              'concurrency':1,'warmup_requests':0,'history':'fresh conversation per request',
              'corpus_manifest':json.loads((ROOT/'corpus'/'manifest.json').read_text())}
    (output/'metadata.json').write_text(json.dumps(metadata,indent=2)+'\n')
    results=[]
    review_fields=['id','run','category','http_status','status','latency_ms','question',
                   'expected_answer','answer','sources','correctness','citation_supported',
                   'retrieval_hit','behavior_pass','review_notes']
    with (output/'responses.jsonl').open('w') as raw, (output/'review.csv').open('w',newline='') as review:
        writer=csv.DictWriter(review,fieldnames=review_fields); writer.writeheader()
        for repeat in range(1,args.repeats+1):
            for case in cases:
                request=Request(args.base_url.rstrip('/')+'/api/chat',
                                data=json.dumps({'question':case['question']}).encode(),
                                headers={'Content-Type':'application/json'},method='POST')
                start=time.perf_counter(); http_status=None; payload={}; error=None
                try:
                    with urlopen(request,timeout=args.timeout) as response:
                        http_status=response.status; payload=json.loads(response.read())
                except HTTPError as exc:
                    http_status=exc.code
                    try: payload=json.loads(exc.read())
                    except (ValueError,UnicodeError): payload={'detail':'Non-JSON HTTP error'}
                except (URLError,TimeoutError,OSError,ValueError) as exc:
                    error=f'{type(exc).__name__}: {exc}'
                latency=round((time.perf_counter()-start)*1000,2)
                if not isinstance(payload,dict): payload={}; error='Unexpected non-object response'
                valid_response=(http_status==200 and isinstance(payload.get('answer'),str)
                                and isinstance(payload.get('sources'),list))
                expected_block=(case['category'] in ('prompt_injection','unanswerable')
                                and http_status==400 and 'Input guardrail blocked' in str(payload.get('detail','')))
                outcome='response' if valid_response else 'guardrail_block' if expected_block else 'failure'
                row={'id':case['id'],'run':repeat,'category':case['category'],
                     'question':case['question'],'expected_answer':case['expected_answer'],
                     'evidence':case['evidence'],'http_status':http_status,
                     'status':payload.get('status',outcome),'outcome':outcome,
                     'latency_ms':latency,'answer':payload.get('answer',payload.get('detail','')),
                     'sources':payload.get('sources',[]),'error':error}
                results.append(row); raw.write(json.dumps(row,ensure_ascii=False)+'\n'); raw.flush()
                writer.writerow({**{k:row[k] for k in review_fields if k in row},
                                 'sources':json.dumps(row['sources'],ensure_ascii=False)})
                review.flush()
                print(f'{case["id"]} run={repeat} {outcome} {latency}ms',flush=True)
    responses=[r['latency_ms'] for r in results if r['outcome']=='response']
    answered=[r['latency_ms'] for r in results if r['outcome']=='response' and r['status']=='answered']
    summary={'requests':len(results),'outcomes':dict(Counter(r['outcome'] for r in results)),
             'statuses':dict(Counter(r['status'] for r in results)),
             'http_failure_rate':sum(r['outcome']=='failure' for r in results)/len(results),
             'successful_response_count':len(responses),
             'successful_response_p50_ms':percentile(responses,50),
             'successful_response_p95_ms':percentile(responses,95),
             'answered_count':len(answered),'answered_p50_ms':percentile(answered,50),
             'answered_p95_ms':percentile(answered,95),
             'quality_metrics':'Pending manual review; no automatic accuracy claims',
             'latency_scope':'Client HTTP round trip including API, database, retrieval, generation and persistence; no browser rendering',
             'not_measured':['ingestion','separate retrieval/model durations','cost','concurrent capacity']}
    (output/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    print(f'Results: {output}')

if __name__=='__main__': main()
