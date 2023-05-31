# ProgramFC
Codes for ACL 2023 Paper ["Fact-Checking Complex Claims with Program-Guided Reasoning"](https://arxiv.org/abs/2305.12744)

## Introduction

We present Program-Guided Fact-Checking (ProgramFC), a novel fact-checking model that decomposes complex claims into simpler sub-tasks that can be solved using a shared library of specialized functions. We first leverage the in-context learning ability of large language models to generate reasoning programs to guide the verification process. Afterward, we execute the program by delegating each sub-task to the corresponding sub-task handler. This process makes our model both explanatory and data-efficient, providing clear explanations of its reasoning process and requiring minimal training data. We evaluate ProgramFC on two challenging fact-checking datasets and show that it outperforms seven fact-checking baselines across different settings of evidence availability, with explicit output programs that benefit human debugging. 

![The general framework of ProgramFC](./framework.png)

**Note: The results reported in our paper are mostly based on Codex. However, in light of OpenAI's decision to discontinue support for the Codex API from March 23rd, 2023, we have transitioned to using GPT-3.5 (`text-davinci-003`) for the code implementation provided here.**

First, install all the required packages:

```bash
pip install -r requirements.txt
```

## Dataset Preparation

To prepare the claims and corpus for **HOVER**, please run the following command:

```bash
bash prepare_hover_data.sh
```

To prepare the claims and corpus for **FEVEROUS-S**, please run the following command:

```bash
bash prepare_feverous_data.sh
```

The claims and the indexed corpus will be saved in the `datasets/[DATASET_NAME]/claims` and `datasets/[DATASET_NAME]/corpus` folder, respectively.

## Program Generation

To generate reasoning programs for each dataset, please run the following commands:

```bash
python ./models/program_generator.py \
    --data_path ./datasets \
    --dataset_name "Dataset Name [HOVER | FEVEROUS]" \
    --num_programs_per_example "Number of reasoning programs for each sample." \
    --model_name text-davinci-003 \
    --num_eval_samples "Number of testing examples. -1 for the whole test set." \
    --api_key "Your OpenAI API Key" \
    --save_path ./results/programs
```

Example of each sample with generated programs: 
```json
{
    "idx": 0,
    "id": "042339bf-0374-4ab3-ab49-6df5f12d868e",
    "claim": "The song recorded by Fergie that was produced by Polow da Don and was followed by Life Goes On was M.I.L.F.$.",
    "gold": "supports",
    "predicted_programs": [
      [
        [
          "fact_1 = Verify(\"M.I.L.F.$ was recorded by Fergie that was produced by Polow da Don.\")",
          "fact_2 = Verify(\"M.I.L.F.$ was was followed by Life Goes On.\")",
          "label = Predict(fact_1 and fact_2)"
        ]
      ]
    ]
}
```

## Program Execution

Releaseing soon...

## Reference
Please cite the paper in the following format if you use this dataset during your research.

```
@article{pan2023factchecking,
    title = {Fact-Checking Complex Claims with Program-Guided Reasoning},
    author = {Liangming Pan and Xiaobao Wu and Xinyuan Lu and Anh Tuan Luu and William Yang Wang and Min-Yen Kan and Preslav Nakov},
    booktitle = {Proceedings of the 61th Annual Meeting of the Association for Computational Linguistics (ACL)},
    url = {https://arxiv.org/abs/2305.12744},
    year = {2023}
}
```

## Q&A
If you encounter any problem, please either directly contact the [Liangming Pan](liangmingpan@ucsb.edu) or leave an issue in the github repo.
