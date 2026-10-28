# ✈️ Kaggle Playground Series s6e10 — Airline Passenger Satisfaction Setup

Ovaj repozitorijum sadrži kompletan, modularan i testiran setup za Kaggle takmičenje **[Playground Series Season 6 Episode 10](https://www.kaggle.com/competitions/playground-series-s6e10)**.

---

## 🎯 Pregled Takmičenja
- **Zadatak:** Binarna klasifikacija zadovoljstva putnika (`satisfaction`: `1` za zadovoljne, `0` za neutralne/nezadovoljne).
- **Metrika evaluacije:** **ROC-AUC** (Area Under the ROC Curve) nad predikcijama verovatnoće.
- **Dataset:**
  - `train.csv`: 699,635 redova, 23 kolone
  - `test.csv`: 299,844 redova, 22 kolone
  - `sample_submission.csv`: 299,844 redova (kolone: `id`, `satisfaction`)

---

## 🧠 NotebookLM Integracija
Za istraživanje domena, literature i optimalnih strategija kreirana je NotebookLM beležnica:
- **Notebook Naziv:** `Kaggle S6E10 - Airline Passenger Satisfaction (ROC-AUC Strategy)`
- **Notebook ID:** `65e928ad-ef50-4449-b972-043b73be0d39`
- **URL:** [https://notebooklm.google.com/notebook/65e928ad-ef50-4449-b972-043b73be0d39](https://notebooklm.google.com/notebook/65e928ad-ef50-4449-b972-043b73be0d39)
- **Izvori u beležnici:**
  - Pregled šeme podataka, rangirani prediktori, strategije agregacije anketa (pain points count, domain group scores).
  - Validacioni protokol (5-Fold Stratified K-Fold) i ROC-AUC ensembling (Rank Averaging & SLSQP soft blending).

---

## 📂 Struktura Projekta

```text
├── .gitignore
├── README.md                      # Kompletna dokumentacija projekta
├── WORK_LOG.md                    # JudgeGuard work log praćenje
├── judge_guard.py                 # Sigurnosni i paritetni gejt (pre-action verification)
├── requirements.txt               # Definisane biblioteke (LightGBM, XGBoost, CatBoost, Polars, Optuna, itd.)
├── pytest.ini                     # Konfiguracija za pytest
├── .venv/                         # Virtuelno okruženje kreirano preko uv (Python 3.12)
├── data/
│   ├── raw/                       # train.csv, test.csv, sample_submission.csv
│   └── processed/                 # Keširani obrađeni podaci
├── eda/
│   ├── run_eda.py                 # Automatizovana skripta za analizu podataka
│   └── eda_report.txt             # Izveštaj raspodele, korelacija i nedostajućih vrednosti
├── src/
│   ├── config.py                  # Putevi, hiperparametri, seed (42), definicije kolona
│   ├── data_loader.py             # Učitavanje podataka uz smanjenje memorije (downcasting)
│   ├── preprocessing.py           # Feature engineering (kašnjenja, ankete, unakrsne kolone)
│   ├── models/
│   │   ├── baseline.py            # 5-Fold Stratified CV za LightGBM, XGBoost i CatBoost
│   │   └── ensemble.py            # Rank Averaging i SLSQP optimizacija težina (ROC-AUC)
│   └── train.py                   # Glavna CLI skripta za pokretanje treniranja i čuvanje predikcija
├── notebooks/
│   └── exploration.ipynb          # Jupyter sveska za interaktivnu eksploraciju
├── scripts/
│   └── submit.sh                  # Skripta za brzu predaju putem Kaggle CLI
├── tests/
│   └── test_pipeline.py           # Unit i integracioni testovi
└── submissions/                   # Generisani submission fajlovi sa CV skorom i timestampom
```

---

## ⚙️ Brzo Pokretanje (Quickstart)

### 1. Aktivacija okruženja
```bash
source .venv/bin/activate
```

### 2. Pokretanje EDA (Exploratory Data Analysis)
```bash
python eda/run_eda.py
```
Pregled rezultata se nalazi u `eda/eda_report.txt`.

### 3. Pokretanje testova
```bash
pytest tests/ -v
```

### 4. Treniranje modela

- **Brzi test na malom uzorku (npr. 5,000 redova):**
  ```bash
  python src/train.py --model lgb --nrows 5000
  ```

- **Puno treniranje LightGBM modela sa 5-Fold CV i generisanjem predaje:**
  ```bash
  python src/train.py --model lgb --folds 5 --save-submission
  ```

- **Puno treniranje svih modela (LightGBM + XGBoost + CatBoost) i ansambliranje:**
  ```bash
  python src/train.py --model all --folds 5 --save-submission
  ```

---

## 🚀 Slanje Rešenja na Kaggle (Kaggle CLI)

Nakon što se generiše `.csv` fajl u `submissions/`, rešenje se može poslati jednom komandom:

```bash
./scripts/submit.sh submissions/sub_lgb_cv_0.9610_20261028_120000.csv "LightGBM 5-fold baseline"
```

Ili direktno kroz Kaggle CLI:
```bash
kaggle competitions submit -c playground-series-s6e10 -f submissions/<fajl>.csv -m "Opis predaje"
```

Provera statusa na leaderboardu:
```bash
kaggle competitions submissions -c playground-series-s6e10
kaggle competitions leaderboard -c playground-series-s6e10 --show
```
