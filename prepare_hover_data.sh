cd datasets/HOVER

# # download hover corpus
mkdir -p ./corpus
cd ./corpus
wget https://nlp.stanford.edu/projects/hotpotqa/enwiki-20171001-pages-meta-current-withlinks-abstracts.tar.bz2
tar -xjvf enwiki-20171001-pages-meta-current-withlinks-abstracts.tar.bz2
rm enwiki-20171001-pages-meta-current-withlinks-abstracts.tar.bz2
cd ..

# build sqlite database from hotpotQA raw corpus
python build_db_for_hotpotQA.py \
    --wiki_dir ./corpus/enwiki-20171001-pages-meta-current-withlinks-abstracts \
    --num-workers 16 \
    --hotpoqa_format \
    --save_path ./corpus/hotpotqa_corpus.db

mkdir -p ./corpus/jsonl_corpus

# build pyserini index from sqlite database
python build_jsonline_corpus_from_db.py \
    --db_path ./corpus/hotpotqa_corpus.db \
    --save_path ./corpus/jsonl_corpus/hotpotqa_corpus.jsonl

python -m pyserini.index.lucene \
    --collection JsonCollection \
    --input ./corpus/jsonl_corpus \
    --index ./corpus/index \
    --generator DefaultLuceneDocumentGenerator \
    --threads 40 \
    --storePositions --storeDocvectors --storeRaw

rm ./corpus/hotpotqa_corpus.db
rm -r ./corpus/enwiki-20171001-pages-meta-current-withlinks-abstracts