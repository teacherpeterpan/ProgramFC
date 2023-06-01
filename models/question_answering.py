import argparse
import torch

class T5_Question_Answering:
    def __init__(self, model, tokenizer):
        self.model = model
        self.tokenizer = tokenizer

    def generate(self, input_string, **generator_args):
        device = "cuda:0" if torch.cuda.is_available() else "cpu"
        input_ids = self.tokenizer.encode(input_string, return_tensors="pt").to(device)
        with torch.no_grad():
            res = self.model.generate(input_ids, **generator_args)
        return self.tokenizer.batch_decode(res, skip_special_tokens=True)

    def get_answer_from_rationale(self, rationale):
        # method 1: string matching
        indicators = ['final answer:', 'the answer is', 'the final answer is']
        split_text = ""
        for indicator in indicators:
            if rationale.find(indicator) >= 0:
                split_text = indicator

        if split_text == "":
            return None
        
        answer = rationale.split(split_text)[-1].strip()
        answer = answer[:-1] if answer.endswith('.') else answer
        return answer
        # method 2: ask question based on rationale. 

    # def answer_question(self, question):
    #     predict_answer = {}
    #     example = f'Answer the following question by reasoning step-by-step.\nQ: {question}'
    #     out = self.generate(example, 
    #                 max_length = None, 
    #                 max_new_tokens = 128)[0].strip()
    #     predict_answer['rationale'] = out
        
    #     predict_answer['answer_text'] = self.get_answer_from_rationale(predict_answer['rationale'])

    #     if predict_answer['answer_text'] is None:
    #         example = '{}\nQ: {}\n The answer is:'.format(predict_answer['rationale'], question)
    #         out = self.generate(example, 
    #                 max_length = None, 
    #                 max_new_tokens = 32)[0].strip()
    #         predict_answer['answer_text'] = out

    #     return predict_answer

    def answer_question(self, question):
        predict_answer = {}
        example = f'Answer the following question by reasoning step-by-step.\nQ: {question}'
        out = self.generate(example, 
                    max_length = None, 
                    max_new_tokens = 128)[0].strip()
        predict_answer['rationale'] = out
        
        predict_answer['answer_text'] = self.get_answer_from_rationale(predict_answer['rationale'])

        if predict_answer['answer_text'] is None:
            example = '{}\nQ: {}\n The answer is:'.format(predict_answer['rationale'], question)
            out = self.generate(example, 
                    max_length = None, 
                    max_new_tokens = 32)[0].strip()
            predict_answer['answer_text'] = out

        return predict_answer

    def answer_question_directly(self, question, evidence, claim_only = False):
        if claim_only == True:
            example = f"Question: {question}\nThe answer is:"
        else:
            example = f"{evidence}\nQuestion: {question}\nThe answer is:"

        # answer question with FLAN-T5
        predict_answer = {}
        answer_text = self.generate(example, 
                    max_length = None, 
                    max_new_tokens = 32)[0].strip()
        
        predict_answer['rationale'] = ""
        predict_answer['answer_text'] = answer_text
        return predict_answer

    def answer_verify_question(self, claim, evidence, claim_only = False):
        claim = claim[:-1] if claim.endswith('.') else claim
        example = None
        if claim_only == True:
            example = f"Is it true that {claim}? True or false? The answer is: "
        else:
            example = f"{evidence}\nBased on the above information, is it true that {claim}? True or false? The answer is: "

        # answer question with FLAN-T5
        predict_answer = {}
        answer_text = self.generate(example, 
                    max_length = None, 
                    max_new_tokens = 8)[0].strip()
        
        predict_answer['rationale'] = ""
        predict_answer['answer_text'] = answer_text
        return predict_answer


