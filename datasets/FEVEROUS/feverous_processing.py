from feverous_db import FeverousDB
from utils.wiki_page import WikiPage
import json
import os
from tqdm import tqdm

db =  FeverousDB("./raw_data/feverous_wikiv1.db")

def is_valid_sample(evidence):
    for content in evidence:
        for element in content['content']:
            if element.find('_sentence_') < 0:
                return False
    return True

def process_feverous_data(data_path, output_path, split, mode):
    with open(data_path, 'r') as f:
        dataset = [json.loads(line) for line in f]

    output_samples = []
    label_map = {'SUPPORTS': 'supports', 'REFUTES': 'refutes'}
    for sample in tqdm(dataset):
        # filter out samples with invalid evidence
        if sample['label'] not in label_map:
            continue
        if not is_valid_sample(sample['evidence']):
            continue

        evidence_set = []
        for content in sample['evidence']:
            for sentence in content['content']:
                wiki_id, sentence_id = sentence.split('_sentence_')
                page_json = db.get_doc_json(wiki_id)
                wiki_page = WikiPage(wiki_id, page_json)
                title = wiki_page.get_title_content()
                sentence = wiki_page.get_element_by_id(f'sentence_{sentence_id}') # Returns specific Wiki sentence
                evidence_set.append(f'{title}\t{str(sentence)}')

        evidence = '\n'.join(evidence_set)

        output_sample = {
            'id': sample['id'], 
            'claim': sample['claim'], 
            'label': label_map[sample['label']],
            'challenge': sample['challenge'],
            'evidence': evidence
        }
        output_samples.append(output_sample)

    print(len(output_samples))
    with open(os.path.join(output_path, f'{split}_{mode}.json'), 'w') as f:
        f.write(json.dumps(output_samples, indent=2))

if __name__ == "__main__":
    data_path = './raw_data/feverous_train_challenges.jsonl'
    output_path = './claims'
    process_feverous_data(data_path, output_path, split = 'train', mode = 'oracle')