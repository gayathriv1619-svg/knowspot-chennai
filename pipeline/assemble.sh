cd "$(dirname "$0")" && python3 build3.py && python3 - <<'P'
import re
s=open('template.html').read();d=open('data.js').read()
out=s.replace('/*__DATA__*/',d);open('/Users/gayathri/zocket-tech/knowspot-ai/app/index.html','w').write(out)
open('app_check.js','w').write('\n'.join(re.findall(r'<script>([\s\S]*?)</script>',out)))
P
node --check app_check.js && echo SYNTAX_OK
