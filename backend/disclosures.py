"""Local keyword screening for passages requiring human accounting review."""
import re
from itertools import islice

PATTERNS = {
    'Possible restatement': r'\brestat(?:e|ed|ement|ements|ing)\b|\brevis(?:ed|ion|ions)\s+(?:of\s+)?prior\s+period',
    'Possible audit-opinion issue': r'\b(?:opinion|opinions)\b.{0,180}\b(?:withdrawn|withdrawal|no longer|not be relied)\b|\b(?:qualified|adverse|disclaimer of)\s+opinion\b',
    'Possible control weakness': r'\bmaterial\s+weakness(?:es)?\b',
    'Possible going-concern uncertainty': r'\b(?:material uncertainty|substantial doubt)\b.{0,180}\bgoing\s+concern\b|\bgoing\s+concern\b.{0,180}\b(?:material uncertainty|substantial doubt)\b',
}


def screen_passages(pages):
    """Return at most 20 bounded excerpts. Negation/context requires human review."""
    findings=[]
    for page, text in pages.items():
        normalized=re.sub(r'\s+', ' ', text)
        for category, pattern in PATTERNS.items():
            for match in islice(re.finditer(pattern,normalized,re.I),2):
                excerpt=normalized[max(0,match.start()-110):min(len(normalized),match.end()+180)]
                findings.append({'category':category,'source_page':page,'excerpt':excerpt,
                    'screening_note':'Keyword match only; may describe a historical, resolved, hypothetical or negated issue. Review the full disclosure.'})
                if len(findings)>=20:
                    return findings
    return findings
