from sklearn.metrics import classification_report, confusion_matrix
import json
import argparse
import os

def print_evaluation_results(predictions, gt_labels, num_of_classes=3):
    if num_of_classes == 3:
        target_names = ['refutes', 'supports', 'not enough info']
        label_map = {'refutes': 0, 'supports': 1, 'not enough info': 2}
        labels = [label_map[e] for e in gt_labels]
        predictions = [label_map[e] for e in predictions]
        print(classification_report(labels, predictions, target_names=target_names, digits=4))
        print(confusion_matrix(labels, predictions))
        print()
    elif num_of_classes == 2:
        target_names = ['refutes', 'supports']
        label_map = {'refutes': 0, 'supports': 1}
        labels = [label_map[e] for e in gt_labels]
        predictions = [label_map[e] for e in predictions]
        print(classification_report(labels, predictions, target_names=target_names, digits=4))
        print(confusion_matrix(labels, predictions))
        print()

def evaluate_hover_by_hops(args, result_file):
    with open(result_file, 'r') as f:
        results = json.load(f)

    with open(os.path.join(args.FV_data_path, args.dataset_name, 'claims', 'dev.json'), 'r') as f:
        dataset = json.load(f)
    
    id_num_hops_map = {sample['id']:sample['num_hops'] for sample in dataset}

    predictions = {'2_hop': [], '3_hop': [], '4_hop': []}
    gt_labels = {'2_hop': [], '3_hop': [], '4_hop': []}
    for sample in results:
        key = f"{id_num_hops_map[sample['id']]}_hop"
        gt_labels[key].append(sample['gold'].strip())
        predictions[key].append(sample['prediction'].strip())
    
    for key in predictions:
        print(key)
        print_evaluation_results(predictions[key], gt_labels[key], num_of_classes=2)
        print()

def evaluate_feverous(result_file):
    with open(result_file, 'r') as f:
        results = json.load(f)

    predictions = []
    gt_labels = []
    for sample in results:
        gt_labels.append(sample['gold'].strip())
        predictions.append(sample['prediction'].strip())
    
    print_evaluation_results(predictions, gt_labels, num_of_classes=2)

def parse_args():
    parser = argparse.ArgumentParser()
    # dataset args
    parser.add_argument('--dataset_name', type=str)
    parser.add_argument('--FV_data_path', type=str)
    parser.add_argument('--result_file', type=str)
    args = parser.parse_args()
    return args

if __name__ == "__main__":
    args = parse_args()
    if args.dataset_name == 'FEVEROUS':
        evaluate_feverous(args.result_file)
    elif args.dataset_name == 'HOVER':
        evaluate_hover_by_hops(args, args.result_file)
    else:
        raise NotImplementedError