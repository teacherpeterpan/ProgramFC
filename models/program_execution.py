import argparse
from transformers import T5Tokenizer, T5ForConditionalGeneration
import random
from tqdm import tqdm
import re
import os
import json

from question_answering import T5_Question_Answering
from retriever import PyseriniRetriever
from evaluate import print_evaluation_results

def parse_args():
    parser = argparse.ArgumentParser()
    # dataset args
    parser.add_argument('--dataset_name', type=str)
    parser.add_argument('--FV_data_path', type=str)
    parser.add_argument('--setting', help='[gold | open-book | close-book]', type=str)
    parser.add_argument('--num_eval_samples', default=2000, type=int)
    parser.add_argument('--program_dir', type=str)
    parser.add_argument('--program_file_name', type=str)
    parser.add_argument('--output_dir', type=str)
    # fact checker args
    parser.add_argument("--model_name", default = 'google/flan-t5-xl', type=str)
    parser.add_argument("--cache_dir", type=str)
    parser.add_argument('--corpus_index_path', default=None, type=str)
    parser.add_argument('--num_retrieved', default=5, type=int)
    parser.add_argument('--max_evidence_length', default=3000, help = 'to avoid exceeding GPU memory', type=int)
    args = parser.parse_args()
    return args

class Program_Execution:
    def __init__(self, args) -> None:
        # load model
        self.args = args
        CACHE_DIR = args.cache_dir
        self.model_name = args.model_name
        self.dataset_name = args.dataset_name
        print(f"Loading model {self.model_name}...")
        self.tokenizer = T5Tokenizer.from_pretrained(self.model_name, cache_dir= CACHE_DIR)
        self.model = T5ForConditionalGeneration.from_pretrained(self.model_name, cache_dir= CACHE_DIR)
        self.model.parallelize()
        print(f"Model {self.model_name} loaded.")

        self.QA_module = T5_Question_Answering(self.model, self.tokenizer)

        # load retriever
        if self.args.setting == 'open-book':
            self.searcher = PyseriniRetriever(self.args.corpus_index_path, use_bm25=True, k1=0.9, b=0.4)
        else:
            self.searcher = None

        # load dataset
        with open(os.path.join(args.FV_data_path, args.dataset_name, 'claims', f'dev.json'), 'r') as f:
            dataset = json.load(f)
        self.gold_evidence_map = {sample['id']:sample['evidence'] for sample in dataset}

    def map_direct_answer_to_label(self, predict):
        predict = predict.lower().strip()
        label_map = {'true': True, 'false': False, 'yes': True, 'no': False, "it's impossible to say": False}
        if predict in label_map:
            return label_map[predict]
        else:
            print(f"Alert!!! wrong answer mapping: {predict}")
            return random.sample([True, False], 1)[0]

    def parse_verify_command(self, command, variable_map):
        return_var, tmp = command.split('= Verify')
        return_var = return_var.strip()
        # claim = tmp.replace("\")", "").strip()

        p1 = re.compile(f'Verify\([f]?\"(.*)\"\)', re.S)
        matching = re.findall(p1, command)
        claim = matching[0] if len(matching)>0 else tmp

        # replace variable
        for variable_name, variable_value in variable_map.items():
            replace_var = "{" + str(variable_name) + "}"
            if claim.find(replace_var) >=0:
                claim = claim.replace(replace_var, variable_value)

        return return_var, claim

    def parse_question_command(self, command, variable_map):
        return_var, tmp = command.split('= Question')
        return_var = return_var.strip()
        # question = tmp.replace("\")", "").strip()

        p1 = re.compile(f'Question\([f]?\"(.*)\"\)', re.S)
        matching = re.findall(p1, command)
        question = matching[0] if len(matching)>0 else tmp

        # replace variable
        for variable_name, variable_value in variable_map.items():
            replace_var = "{" + str(variable_name) + "}"
            if question.find(replace_var) >=0:
                question = question.replace(replace_var, variable_value)

        return return_var, question

    def get_command_type(self, command):
        if command.find("label = ")>=0:
            return "FINAL"
        elif command.find('= Verify')>=0:
            return "VERIFY"
        elif command.find('= Question')>=0:
            return "QUESTION"
        else:
            return "UNKNOWN"

    def derive_final_answer(self, command, variable_map):
        final_label = True
        command = command.replace('label =', '').strip()
        p1 = re.compile(r'Predict[(](.*?)[)]', re.S)
        command_arg = re.findall(p1, command)[0]
        verify_subs = command_arg.split(" and ")
        arguments = [arg.strip() for arg in verify_subs]
        for argument in arguments:
            if argument in variable_map:
                final_label = variable_map[argument] and final_label
            else:
                print(f"Alert!!! wrong argument: {argument}")
        return final_label

    def retrieve_evidence(self, query):
        hits = self.searcher.retrieve(query, self.args.num_retrieved)
        evidence = '\n'.join([hit['text'].strip() for hit in hits])
        # cut overlong evidence
        if len(evidence.split()) > self.args.max_evidence_length:
            print('evidence is too long, cut it to max_evidence_length')
            evidence = ' '.join(evidence.split()[:self.args.max_evidence_length])
        
        # save retrieval results (can comment out if not needed)
        retrieved_results = []
        for hit in hits:
            retrieved_results.append({'id': hit['doc_id'], 'score': hit['score'], 'query': query})
        
        return evidence, retrieved_results
    
    def parse_program(self, ID, program, evidence):
        variable_map = {}
        claim_only = True if self.args.setting == 'close-book' else False
        retrieved_evidence = []
        # for each command
        for command in program:
            c_type = self.get_command_type(command)
            final_answer = None
            # verify a claim
            if c_type == "VERIFY":
                return_var, claim = self.parse_verify_command(command, variable_map)
                # if open-book setting, then retrieve evidence from the corpus
                if self.args.setting == 'open-book':
                    evidence, retrieved_results = self.retrieve_evidence(claim)
                    retrieved_evidence += retrieved_results
                
                answer = self.QA_module.answer_verify_question(claim, evidence, claim_only)['answer_text']
                variable_map[return_var] = self.map_direct_answer_to_label(answer)
            # ask a question
            elif c_type == "QUESTION":
                return_var, question = self.parse_question_command(command, variable_map)
                # if open-book setting, then retrieve evidence from the corpus
                if self.args.setting == 'open-book':
                    evidence, retrieved_results = self.retrieve_evidence(question)
                    retrieved_evidence += retrieved_results
                
                answer = self.QA_module.answer_question_directly(question, evidence, claim_only)['answer_text']
                variable_map[return_var] = answer
            elif c_type == 'FINAL':
                try:
                    final_answer = self.derive_final_answer(command, variable_map)
                except:
                    print(f"Alert!!! parsing error: {ID}")
                    final_answer = random.sample([True, False], 1)[0]
        
        return final_answer, retrieved_evidence

    def execute_on_dataset(self):
        # load generated program
        with open(os.path.join(self.args.program_dir, self.args.program_file_name), 'r') as f:
            dataset = json.load(f)
        dataset = dataset if self.args.num_eval_samples < 0 else dataset[:self.args.num_eval_samples]

        gt_labels, predictions = [], []
        results = []
        for sample in tqdm(dataset):
            program = sample['predicted_programs']
            gt_labels.append(sample['gold'])
            # get evidence
            evidence = self.gold_evidence_map[sample['id']] if self.args.setting == 'gold' else None
            
            # execute program
            sample_predictions = []
            for sample_program in program:
                try:
                    single_prediction, retrieved_evidence = self.parse_program(sample['id'], sample_program, evidence)
                except Exception as e:
                    print(f"Alert!!! execution error: {sample['id']}")
                    single_prediction = random.sample([True, False], 1)[0]
                sample_predictions.append(single_prediction)
            
            true_count = len([pred for pred in sample_predictions if pred == True])
            false_count = len([pred for pred in sample_predictions if pred == False])
            final_prediction = True if true_count > false_count else False
            predictions.append('supports' if final_prediction == True else 'refutes')
            results.append({'id': sample['id'], 
                            'claim': sample['claim'],
                            'gold': sample['gold'], 
                            'prediction': 'supports' if final_prediction == True else 'refutes'})
        
        # evaluate
        self.evaluation(predictions, gt_labels)

        # save results to file
        output_path = os.path.join(self.args.output_dir, '{}_{}'.format(self.model_name.split('/')[-1], self.args.setting))
        if not os.path.exists(output_path):
            os.makedirs(output_path)

        output_file_name = f'{self.args.dataset_name}.program.json'
        with open(os.path.join(output_path, output_file_name), 'w') as f:
           f.write(json.dumps(results, indent = 2))

    def evaluation(self, predictions, gt_labels):
        print_evaluation_results(predictions, gt_labels, num_of_classes=2)

if __name__ == "__main__":
    args = parse_args()
    program_executor = Program_Execution(args)
    program_executor.execute_on_dataset()