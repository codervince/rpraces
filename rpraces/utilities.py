import re
from fractions import Fraction

def try_int(value):
    try:
        return int(value)
    except:
        return 0

def isFavorite(winodds):
    if winodds is None:
        return None
    return "F" or "J" or "C" in winodds

def decimalizeodds(winodds):
    '''Assume format \d\d/\d'''
    if winodds is None:
        return None
    if "Evens" in winodds:
        return 2.0
    if "/" in winodds:
        num, denom = winodds.split("/")
        dec = Fraction(int(num), int(denom)) + Fraction(1,1)
        return float(dec)
#imperialtofurlongs
def imperialtofurlongs(idist):
    '''ex 2m2f50y'''
    miles = 0
    furlongs = 0
    yards = 0
    if "f" in idist and "m" in idist:
        miles, furlongs = try_int(idist.split("m")[0]), try_int(idist.split("f")[0].split("m")[1])
    if "f" in idist and "m" not in idist:
        furlongs = try_int(idist.split("f")[0])
    return miles*8 + furlongs

def rcnametocode(racecoursename):
    return {
    'Chelmsford (AW)': 'Cfd',

    }.get(racecoursename, None)

def getgoingcode(goingname):
    return {
    'Standard': 'St',
    'Good': 'Gd',
    'Soft': 'Sft',
    'Heavy': 'Hy',
    'Good to Soft': 'GS',
    'Good to Firm': 'GF',
    'Very Soft': 'VSft',
    }.get(goingname, None)

def getraceclassLn(raceconditions):
    # C3NvHcCh 7K
    cpat1 = re.compile(r'.*C(\d+)\w+.*')

    regexes = [cpat1]
    res = ""
    for regex in regexes:
        if re.match(regex, raceconditions):
            res += re.match(regex, raceconditions).group(1)
    return res

def getracetyperacename(racename):
    # NHF|NHFL|HcCh|Ch|HL|H|HcHL|NvChG2|NvChG1|NvHG2|NvCh|ChL
    pass
def getracetypeLn(raceconditions):
    # C3NvHcCh 7K
    rtpat1 = re.compile(r'.*C[0-9]{1}(2yM|2yHc|3yHc|2yL|2yG3|3y|L|3y|2y|NHF|NHFL|HcCh|Ch|HL|H|HcHL|NvChG2|NvChG1|NvHG2|NvCh|ChL)\s.*')
    rtpat2 = re.compile(r'(2yM|2yHc|3yHc|2yL|2yG3|3y|L|3y|2y|NHF|NHFL|HcCh|Ch|HL|H|HcHL|NvChG2|NvChG1|NvHG2|NvCh|ChL)\s(\d+)K.*')
    regexes = [rtpat1, rtpat2]
    res = ""
    for regex in regexes:
        if re.match(regex, raceconditions):
            res += re.match(regex, raceconditions).group(1)
    return res

def tf(values, encoding="utf-8"):
    value = ""
    for v in values:
        if v is not None and v != "":
            value = v
            break
    return value.encode(encoding).strip()

'''2m2f50y'''
def getdistance(distancegoing):
    '''2 cases: case1: has dot then decimal'''
    res = ""
    if '.' in distancegoing:
        d1 = ''.join( ''.join([ i for i in distancegoing.split(".")[0]if i.isdigit() ])   )
        d2 = ''.join( ''.join([ i for i in distancegoing.split(".")[1]if i.isdigit() ])   )
        res = d1 + '.' + d2
    else:
        res =''.join( ''.join([ i for i in distancegoing if i.isdigit() ])   )
    return res

def getracetype(racename):
     hh_regex = re.compile('.*?Handicap.*?', re.IGNORECASE)
     stakes_regex = re.compile('.*?Stakes.*?', re.IGNORECASE)
     if hh_regex.findall(racename):
         return "Handicap"
     if stakes_regex.findall(racename):
             return "Stakes"

def getraceclass(racename):
    class_regex = re.compile('.*?CLASS\((\d{1})\).*?', re.IGNORECASE)
    if class_regex.findall(racename):
        return class_regex.findall(racename).group(1)

def mynormalize(str):
    import unicodedata
    from unicodedata import normalize
    return str.replace(u'\xb4', u'\u0301')
