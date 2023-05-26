# download corpus for feverous
cd ./datasets/FEVEROUS
mkdir -p ./raw_data
cd ./raw_data
wget https://fever.ai/download/feverous/feverous_train_challenges.jsonl
wget https://fever.ai/download/feverous/feverous_dev_challenges.jsonl
wget https://fever.ai/download/feverous/feverous-wiki-pages.zip
wget https://fever.ai/download/feverous/feverous-wiki-pages-db.zip
unzip feverous-wiki-pages-db.zip

cd ..
mkdir -p ./corpus/jsonl_corpus

# build pyserini index from sqlite database
python build_jsonline_corpus_from_db.py \
    --db_path ./raw_data/feverous_wikiv1.db \
    --save_path ./corpus/jsonl_corpus/feverous_corpus.jsonl

python -m pyserini.index.lucene \
    --collection JsonCollection \
    --input ./corpus/jsonl_corpus \
    --index ./corpus/index \
    --generator DefaultLuceneDocumentGenerator \
    --threads 40 \
    --storePositions --storeDocvectors --storeRaw