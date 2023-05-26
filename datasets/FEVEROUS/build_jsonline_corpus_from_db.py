import argparse
import os
from feverous_db import FeverousDB
from utils.wiki_page import WikiPage

import re
import json
from tqdm import tqdm

def get_jsonline_corpus(db_path, save_path):
    db = FeverousDB(db_path)

    corpus = []
    doc_ids = db.get_doc_ids()

    for doc_id in tqdm(doc_ids):
        page_json = db.get_doc_json(doc_id)
        wiki_page = WikiPage(doc_id, page_json, mode = 'intro')
        title = wiki_page.get_title_content()
        # get all sentences
        all_sentence_ids = [element for element in wiki_page.page_order if element.startswith('sentence_')]
        # merge sentences into paragraph (create a paragraph-based corpus)
        paragraph = ' '.join([str(wiki_page.get_element_by_id(sentence_id)) for sentence_id in all_sentence_ids])
        paragraph = title + '\t' + paragraph
        rec = {"id": doc_id, "contents": paragraph}
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