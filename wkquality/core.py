"""Deterministic content checks. Heuristics flag review opportunities, not factual verdicts."""
from __future__ import annotations
from dataclasses import dataclass, asdict
from pathlib import Path
from urllib.parse import urlparse
from collections import Counter
import json, re, datetime

HEAD = re.compile(r'^(#{1,6})\s+(.+?)\s*$', re.M)
LINK = re.compile(r'(?<!!)\[([^\]]+)\]\((https?://[^)]+)\)')
URL = re.compile(r'https?://[^\s)>]+')
NUM = re.compile(r'(?<!\w)(?:\$?\d+(?:[.,]\d+)?\s?(?:%|percent|hours?|days?|x|million|billion|k|m)?)\b',re.I)
STRONG = re.compile(r'\b(always|never|guarantee[ds]?|eliminates?|proves?|every|no risk|zero risk|best|only|all companies|fully autonomous)\b',re.I)
ATTR = re.compile(r'\b(according to|source:|study by|reported by|data from|research from|measured|benchmark(?:ed)?|in our test|we observed)\b',re.I)
FENCE = re.compile(r'```.*?```',re.S)
INLINE = re.compile(r'`[^`]*`')
FRONT = re.compile(r'\A---\n.*?\n---\n',re.S)
STOP = set('the and this that with from will have your their there what when into about using more than these those does were been being where while they them then our for are not can you its but how who why has had was said says also each such own onto work'.split())
JARGON = {'leverage':'use','utilize':'use','synergy':'specific collaboration','seamless':'describe the integration','robust':'name the failure mode or capacity','cutting-edge':'name the technical advance','revolutionize':'state the measurable change','game-changing':'state the measurable change','unlock':'describe the capability','transformative':'state the changed workflow','next-generation':'specify the version or technical difference','best-in-class':'provide comparison criteria','single pane of glass':'name the consolidated views','at scale':'supply scale and load','agentic':'specify the agent, tools, and boundaries','empower':'state who can do what'}
AI_PATTERNS={'automation without boundaries':r'\b(?:autonomous|agentic|self-driving)\b','productivity without denominator':r'\b(?:save[s]? time|boost[s]? productivity|improve[s]? efficiency|faster)\b','governance handwave':r'\b(?:responsible AI|trustworthy AI|human in the loop|governed AI)\b'}
OPERATIONAL = r'\b(?:owner|approver|rollback|audit|evaluation|test(?:ing)?|permission|cost|budget|review|exception|threshold|fallback|version|metric|baseline|workflow|SLA|observability|monitoring)\b'

@dataclass
class Finding:
    tool: str
    severity: str
    rule: str
    line: int
    message: str
    excerpt: str = ''
    def dict(self):return asdict(self)

def clean(text):
    return INLINE.sub(' ',FENCE.sub(' ',FRONT.sub('',text)))
def words(text): return re.findall(r"\b[\w]+(?:['’-][\w]+)*\b",text.lower())
def line_of(text,offset):return text.count('\n',0,offset)+1
def passages(text):
    """Sentence-ish units with offset, preserving line numbers; avoids code and frontmatter."""
    masked=mask(text)
    for m in re.finditer(r'[^.!?\n]+(?:[.!?]+|(?=\n|\Z))',masked):
        s=m.group().strip()
        if len(s)>15 and not s.lstrip().startswith('#'):
            yield s,line_of(text,m.start()),m.start()
def mask(text):
    for rex in (FENCE,FRONT,INLINE):
        text=rex.sub(lambda m:''.join('\n' if c=='\n' else ' ' for c in m.group()),text)
    return text

def claims(text,ledger):
    out=[]
    for sentence,ln,_ in passages(text):
        if not (NUM.search(sentence) or STRONG.search(sentence)):continue
        supported=bool(ATTR.search(sentence) or URL.search(sentence) or LINK.search(sentence))
        ledger_hit=any(item.get('claim','').lower() in sentence.lower() and item.get('status')=='verified' and item.get('source_url') for item in ledger if len(item.get('claim',''))>12)
        if not (supported or ledger_hit):
            out.append(Finding('claim-sentinel','warning','unsupported_high_stakes_claim',ln,'Quantified or absolute claim needs a traceable source or claim-ledger match.',sentence[:180]))
    return out

def jargon(text):
    out=[]; masked=mask(text)
    for phrase,replacement in JARGON.items():
        for m in re.finditer(r'(?<!\w)'+re.escape(phrase)+r'(?!\w)',masked,re.I):
            out.append(Finding('jargon-tax','info','vague_language',line_of(text,m.start()),f'“{phrase}”: {replacement}.',phrase))
    return out

def ai_theater(text):
    out=[]; masked=mask(text)
    evidence=len(re.findall(OPERATIONAL,masked,re.I))
    for name,pattern in AI_PATTERNS.items():
        for m in re.finditer(pattern,masked,re.I):
            if evidence<3:
                out.append(Finding('ai-theater','warning','operational_gap',line_of(text,m.start()),f'{name}: name owners, controls, evaluation, exceptions and measurable workflow outcomes.',m.group()))
    return out

def structure(text):
    out=[]; heads=[(len(m.group(1)),m.group(2),line_of(text,m.start())) for m in HEAD.finditer(mask(text))]
    if not any(level==1 for level,_,_ in heads):out.append(Finding('reader-first','warning','missing_h1',1,'Add a descriptive H1 heading.'))
    for (a,_,_),(b,title,line) in zip(heads,heads[1:]):
        if b>a+1:out.append(Finding('reader-first','warning','heading_jump',line,f'Heading level jumps from H{a} to H{b}: {title}.'))
    for m in re.finditer(r'(?m)^([^\n]+(?:\n(?!\n|#|[-*] |\d+\. )[^\n]+){0,})',mask(text)):
        block=m.group().strip()
        if len(words(block))>150:out.append(Finding('reader-first','info','dense_paragraph',line_of(text,m.start()),f'Paragraph contains {len(words(block))} words; consider splitting.'))
    for m in re.finditer(r'!\[([^\]]*)\]\([^)]+\)',text):
        if not m.group(1).strip():out.append(Finding('reader-first','warning','empty_image_alt',line_of(text,m.start()),'Image has empty alt text. Decorative images are an exception.'))
    for m in LINK.finditer(text):
        if m.group(1).strip().lower() in ('here','click here','read more','link'):
            out.append(Finding('reader-first','info','generic_link',line_of(text,m.start()),'Use destination-specific link text.',m.group(0)[:150]))
    return out

def content_debt(text,path,asof):
    out=[]; masked=mask(text)
    for m in re.finditer(r'\b(?:in )?(20(?:1\d|2\d))\b',masked):
        year=int(m.group(1));
        if asof.year-year>=3:
            out.append(Finding('decay-radar','info','dated_reference',line_of(text,m.start()),f'Check whether {year} is historical context or a stale current claim.',m.group()))
    for m in re.finditer(r'\b(?:currently|today|recently|latest|now|this year|newly released)\b',masked,re.I):
        out.append(Finding('decay-radar','info','temporal_claim',line_of(text,m.start()),'Time-relative wording requires a review date and current verification.',m.group()))
    return out

def evidence_links(text):
    out=[]
    for m in LINK.finditer(text):
        u=m.group(2)
        if urlparse(u).netloc.lower() in {'example.com','www.example.com','localhost','127.0.0.1'}:
            out.append(Finding('evidence-trail','warning','placeholder_link',line_of(text,m.start()),'Replace placeholder citation before publishing.',u))
        if re.search(r'(?i)(utm_source|utm_medium|utm_campaign)=',u):
            out.append(Finding('evidence-trail','info','tracking_url',line_of(text,m.start()),'Consider a canonical evidence URL without tracking parameters.',u[:150]))
    return out

def repetition(text):
    out=[]; paras=[(a.strip(),line_of(text,m.start())) for m in re.finditer(r'(?ms)(?:\A|\n\s*\n)(.+?)(?=\n\s*\n|\Z)',mask(text)) if (a:=m.group(1)).strip()]
    seen={}
    for para,line in paras:
        tokens=[w for w in words(para) if w not in STOP]
        if len(tokens)<12:continue
        trigrams=set(zip(tokens,tokens[1:],tokens[2:]))
        for prior,prior_line in seen.values():
            union=len(trigrams|prior); similarity=len(trigrams&prior)/union if union else 0
            if similarity>=.55:
                out.append(Finding('echo-chamber','info','repeated_paragraph',line,f'Paragraph substantially overlaps content at line {prior_line} (trigram Jaccard {similarity:.0%}).'))
                break
        seen[line]=(trigrams,line)
    return out

def inspect(text,path='content.md',ledger=None,asof=None):
    ledger=ledger or []; asof=asof or datetime.date.today()
    checks=(claims(text,ledger)+jargon(text)+ai_theater(text)+structure(text)+content_debt(text,path,asof)+evidence_links(text)+repetition(text))
    return {'file':str(path),'word_count':len(words(clean(text))),'findings':[f.dict() for f in sorted(checks,key=lambda f:(f.line,f.tool))], 'counts':dict(Counter(f.severity for f in checks))}

def validate_ledger(items):
    if not isinstance(items,list):raise ValueError('Claim ledger must be a JSON list.')
    required={'id','claim','status','source_url','owner','reviewed_on'}
    ids=set(); errors=[]
    for n,item in enumerate(items,1):
        if not isinstance(item,dict):errors.append(f'Entry {n}: expected object');continue
        missing=required-item.keys()
        if missing:errors.append(f'Entry {n}: missing {sorted(missing)}')
        if item.get('id') in ids:errors.append(f'Entry {n}: duplicate id {item.get("id")}')
        ids.add(item.get('id'))
        if item.get('status') not in {'verified','pending','rejected','expired'}:errors.append(f'Entry {n}: invalid status')
        if item.get('status')=='verified' and not str(item.get('source_url','')).startswith('https://'):errors.append(f'Entry {n}: verified claim needs HTTPS source')
        date=item.get('reviewed_on','')
        try:datetime.date.fromisoformat(date)
        except (ValueError,TypeError):errors.append(f'Entry {n}: reviewed_on must be YYYY-MM-DD')
    return errors
