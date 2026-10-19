from __future__ import annotations
import argparse, json, sys, datetime
from pathlib import Path
from .core import inspect, validate_ledger
EXTS={'.md','.mdx','.markdown'}
def main(argv=None):
    p=argparse.ArgumentParser(prog='wkq',description='Will Kelly Content Lab: evidence-first publication checks')
    sub=p.add_subparsers(dest='command',required=True)
    scan=sub.add_parser('scan',help='Inspect a Markdown file or directory recursively')
    scan.add_argument('path',type=Path)
    scan.add_argument('--ledger',type=Path)
    scan.add_argument('--format',choices=['text','json','sarif'],default='text')
    scan.add_argument('--out',type=Path)
    scan.add_argument('--fail-on',choices=['none','warning','info'],default='warning')
    scan.add_argument('--as-of',type=datetime.date.fromisoformat)
    led=sub.add_parser('ledger',help='Validate a JSON claim ledger')
    led.add_argument('path',type=Path)
    args=p.parse_args(argv)
    try:
        if args.command=='ledger':
            errors=validate_ledger(json.loads(args.path.read_text(encoding='utf-8')))
            print('\n'.join(errors) if errors else 'Claim ledger valid.')
            return 1 if errors else 0
        if args.path.is_file():paths=[args.path]
        elif args.path.is_dir():paths=sorted(x for x in args.path.rglob('*') if x.suffix.lower() in EXTS and '.git' not in x.parts and 'node_modules' not in x.parts)
        else:raise ValueError('Path is not a file or directory')
        if not paths:raise ValueError('No Markdown files found')
        ledger=json.loads(args.ledger.read_text(encoding='utf-8')) if args.ledger else []
        errors=validate_ledger(ledger) if args.ledger else []
        if errors:raise ValueError('Invalid ledger:\n'+'\n'.join(errors))
        reports=[inspect(x.read_text(encoding='utf-8'),str(x),ledger,args.as_of) for x in paths]
        if args.format=='json':output=json.dumps({'schema_version':'1.0','reports':reports},indent=2)
        elif args.format=='sarif':
            results=[]
            for report in reports:
                for f in report['findings']:
                    results.append({'ruleId':f['tool']+'/'+f['rule'],'level':'warning' if f['severity']=='warning' else 'note','message':{'text':f['message']},'locations':[{'physicalLocation':{'artifactLocation':{'uri':report['file']},'region':{'startLine':f['line']}}}]})
            output=json.dumps({'version':'2.1.0','$schema':'https://json.schemastore.org/sarif-2.1.0.json','runs':[{'tool':{'driver':{'name':'Will Kelly Content Lab','rules':[]}},'results':results}]},indent=2)
        else:
            chunks=[]
            for report in reports:
                chunks.append(f"\n{report['file']} ({report['word_count']} words; {report['counts']})")
                for f in report['findings']:chunks.append(f"  {f['line']}: [{f['severity']}] {f['tool']}/{f['rule']}: {f['message']}")
            output='\n'.join(chunks)
        if args.out:
            args.out.parent.mkdir(parents=True,exist_ok=True);args.out.write_text(output+'\n',encoding='utf-8')
            print(f'Wrote {args.out}')
        else:print(output)
        levels={'none':set(),'warning':{'warning'},'info':{'warning','info'}}
        return 2 if any(f['severity'] in levels[args.fail_on] for r in reports for f in r['findings']) else 0
    except (ValueError,OSError,json.JSONDecodeError) as e:
        print(f'wkq: {e}',file=sys.stderr);return 1
if __name__=='__main__':sys.exit(main())
