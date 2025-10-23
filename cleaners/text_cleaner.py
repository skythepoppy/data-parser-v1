import re

def clean_text(text): 

    """ basic cleanup for whitespace, links, and special char"""

    text=re.sub(r"http\S+", "", text)     #urls
    text=re.sub(r"\s+", " ", text)    # whitepsace
    text = re.sub(r"[^A-Za-z0-9.,!?;:'\"()\s-]", "", text)   #special char
    return text.strip()
    
    