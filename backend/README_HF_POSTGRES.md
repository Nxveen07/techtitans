# TruthTrace Backend: Hugging Face + Postgres

## 1) Environment

Set `backend/.env`:

```env
DATABASE_URL="postgresql+psycopg://postgres:postgres@127.0.0.1:5432/truthtracedb"
HF_MODEL_ID="distilbert-base-uncased"
HF_INFERENCE_MODEL_ID="distilbert-base-uncased-finetuned-sst-2-english"
HF_MODEL_DIR="./models/current"
HF_METRICS_PATH="./models/current/metrics.json"
```

## 2) Install Dependencies

```powershell
cd "C:\Users\eshwa\OneDrive\Desktop\red shield\TruthTrace_Project\backend"
pip install -r requirements.txt
```

## 3) Start PostgreSQL

Make sure PostgreSQL is running on `127.0.0.1:5432` with:
- database: `truthtracedb`
- user: `postgres`
- password: `postgres`

Initialize tables (optional if backend startup auto-creates):

```powershell
psql -h 127.0.0.1 -U postgres -d truthtracedb -f ".\db\init.sql"
```

## 4) Start Backend

```powershell
.\start_backend.bat
```

or

```powershell
uvicorn main:app --host 127.0.0.1 --port 8000
```

## 5) Dataset APIs

- `POST /api/v1/datasets/samples`
- `GET /api/v1/datasets/samples`
- `POST /api/v1/datasets/split`

Sample insert:

```json
{
  "content": "A claim to classify",
  "label": "suspicious",
  "source_type": "text",
  "split": "unsplit"
}
```

## 6) Train Locally on CPU

1. Add enough samples.
2. Split dataset:
   - train/val/test ratios should sum to 1.0.
3. Run:

```powershell
python .\ml\train.py
```

Model artifacts are written to `HF_MODEL_DIR`.

## 7) Import Kaggle 79k Dataset

Download: https://www.kaggle.com/datasets/stevenpeutz/misinformation-fake-news-text-dataset-79k

Then run:

```powershell
python .\scripts\import_kaggle_79k.py --csv "C:\path\to\your\kaggle_file.csv"
```

Optional quick import for testing:

```powershell
python .\scripts\import_kaggle_79k.py --csv "C:\path\to\your\kaggle_file.csv" --limit 5000
```

After import:
1. Split data with `/api/v1/datasets/split`
2. Run `python .\ml\train.py`
3. Restart backend

## 8) Analyze Endpoint

`POST /api/v1/content/analyze` keeps the same frontend response contract:

- `classification`
- `fake_probability`
- `explanation`
- `bias_level`
- `sentiment`
- `claim`
- `fact`
- `source`
