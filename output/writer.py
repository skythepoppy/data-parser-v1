import json 

def write_json(records, filepath): 

    """writes records to json file config"""

    with open(filepath, "a", encoding="utf-8") as f: 
        for rec in records: 
            json.dump(rec, f, ensure_ascii=False)
            f.write("\n")