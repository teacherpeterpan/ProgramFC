import argparse
import os
from doc_db import DocDB
import json
from tqdm import tqdm

def get_jsonline_corpus(db_path, save_path):
    db = DocDB(db_path)
    corpus = []
    doc_ids = db.get_doc_ids()
    for doc_id in tqdm(doc_ids):
        text = db.get_doc_text(doc_id)
        title = doc_id.split("_0")[0]
        rec = {"id": title, "contents": text}
        corpus.append(rec)

    with open(save_path, "w") as f:
        for rec in corpus:
            f.write(json.dumps(rec) + "\n")
    
    print(f'Successfully processed {len(corpus)} wiki paragraphs')

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--db_path', type=str, required=True,
                        help='Path to sqlite db holding document texts')
    parser.add_argument('--save_path', type=str, required=True, 
                        help='Path to save jsonline corpus')
    args = parser.parse_args()

    if not os.path.exists(args.save_path):
        print(f'Creating jsonline corpus at {args.save_path}')
        get_jsonline_corpus(args.db_path, args.save_path)
    else:
        print(f'Jsonline corpus already exists at {args.save_path}')