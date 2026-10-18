import argparse
import json
from pathlib import Path
import subprocess
import sys
from .backend import Platform, write_json


def main():
    parser = argparse.ArgumentParser(description='SONAR local RNA-editing reporter measurement platform')
    parser.add_argument('--reference',help='Explicit frozen scientific root')
    parser.add_argument('--workspace',help='Writable imports/models/output workspace')
    commands = parser.add_subparsers(dest='command',required=True)
    p = commands.add_parser('serve'); p.add_argument('--port',type=int,default=8765); p.add_argument('--open',action='store_true')
    commands.add_parser('verify'); commands.add_parser('reproduce'); commands.add_parser('list')
    p = commands.add_parser('import'); p.add_argument('source'); p.add_argument('--name',default='Imported experiment')
    p = commands.add_parser('validate'); p.add_argument('--dataset',default='reference')
    for name in ['analyze','example','export']:
        p = commands.add_parser(name); p.add_argument('--dataset',default='reference'); p.add_argument('--sample',default=None)
        p.add_argument('--mode',choices=['research','routine'],default='research')
        p.add_argument('--population',choices=['reporter','blue_positive_reporter','blue_negative_reporter'],default='reporter')
        p.add_argument('--bootstrap',type=int,default=0); p.add_argument('--output',required=True)
    p = commands.add_parser('fit'); p.add_argument('csv'); p.add_argument('--name',default='User reference fit'); p.add_argument('--output',required=True)
    p = commands.add_parser('pipeline-rerun'); p.add_argument('directory'); p.add_argument('--output',required=True)
    p = commands.add_parser('pipeline-export'); p.add_argument('run_id'); p.add_argument('--output',required=True)
    args = parser.parse_args()
    try:
        platform = Platform(args.reference,args.workspace)
        if args.command == 'serve':
            from .server import serve
            serve(platform,args.port,args.open); return
        if args.command in ['verify','reproduce']:
            if args.command == 'verify':
                print(json.dumps(platform.verify_release()))
            result = subprocess.run([sys.executable,str(platform.root/'science.py'),args.command],cwd=platform.root)
            raise SystemExit(result.returncode)
        if args.command == 'list':
            value = platform.datasets()
        elif args.command == 'import':
            path = Path(args.source)
            value = platform.import_zip(path.read_bytes(),args.name) if path.suffix.lower()=='.zip' else platform.import_directory(path,args.name)
        elif args.command == 'validate':
            value = platform.validate_dataset(args.dataset)
        elif args.command in ['analyze','example']:
            value = platform.analyze(args.sample or 'S7_90B',args.dataset,args.population,args.mode,args.bootstrap)
            write_json(args.output,value)
        elif args.command == 'export':
            from .export import export_bundle
            dest=Path(args.output);dest.parent.mkdir(parents=True,exist_ok=True)
            dest.write_bytes(export_bundle(platform,args.dataset,args.mode,[args.sample] if args.sample else None,args.population))
            value={'output':str(dest.resolve())}
        elif args.command == 'pipeline-rerun':
            from .measurement import MeasurementPipeline
            value=MeasurementPipeline(platform).rerun(args.directory);write_json(args.output,value)
        elif args.command == 'pipeline-export':
            from .measurement import MeasurementPipeline
            Path(args.output).write_bytes(MeasurementPipeline(platform).export(args.run_id));value={'output':args.output}
        else:
            value=platform.fit_references(Path(args.csv).read_text(encoding='utf-8-sig'),args.name);write_json(args.output,value)
        print(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False))
    except (ValueError,FileNotFoundError,KeyError) as exc:
        parser.exit(2,f'SONAR: {exc}\n')


if __name__=='__main__':
    main()
