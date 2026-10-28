# Kaggle S6E10 Kompletan Izveštaj o Eksperimentima i Analiza Rezultata

## 1. Pregled Takmičenja
- **Naziv:** Kaggle Playground Series - Season 6, Episode 10 (`playground-series-s6e10`)
- **Problem:** Predviđanje zadovoljstva putnika avionskih kompanija (`satisfaction`: 0 = neutral/dissatisfied, 1 = satisfied)
- **Zvanična Metrika:** Area Under the ROC Curve (ROC-AUC)
- **Dimenzije Podataka:**
  - Trening skup: 699,635 redova x 23 kolone
  - Test skup: 299,844 redova x 22 kolone
  - Balans klasa: 55.64% nezadovoljnih (0), 44.36% zadovoljnih (1)
  - Nedostajuće vrednosti: Isključivo `Arrival Delay in Minutes` (292 u train, 130 u test)

---

## 2. Hronologija i Rezultati Sprovedenih Eksperimenata

| Ref Predaje | Naziv Eksperimenta / Arhitektura | 5-Fold OOF ROC-AUC | Kaggle Public LB | Ključne Odlike i Nalazi |
|:---|:---|:---|:---|:---|
| **57721912** | **Route-ID Tri-GBDT Master** (Bayesian $m=20$) | **0.96041** | **0.95991** | **Najbolji model u radnom prostoru.** In-fold Bayesian target encoding na `Flight Distance` bez ikakvog curenja podataka. |
| **57723036** | **Heterogeneous Tri-GBDT & PyTorch MLP** | 0.96030 | **0.95981** | Dodavanje duboke neuronske mreže sa Entity Embeddings; MLP OOF je bio 0.95697, pa je Nelder-Mead minimizovao težinu. |
| **57720118** | **Tri-GBDT Baseline** (Nelder-Mead Rank) | 0.95893 | **0.95821** | Prvi 5-fold ansambl (LightGBM 0.95868, CatBoost 0.95858, XGBoost 0.95858). Standardni listovi dostižu plafon. |
| **57679083** | **LightGBM 5-Fold Baseline** | 0.95852 | **0.95805** | Čista jednostruka GBDT osnova bez složenog inženjeringa ruta. |

---

## 3. Detaljni Inženjering Obeležja (Feature Engineering)

1. **Rute kao Diskretni Identifikatori (`Flight Distance`):**
   - Uočeno je oko 3,500 unikatnih diskretnih vrednosti u koloni `Flight Distance`.
   - Bayesian Smoothed M-estimate target encoding unutar svakog folda:
     $$S_i = \frac{n_i \cdot \bar{y}_i + m \cdot \bar{y}_{\text{global}}}{n_i + m}, \quad m=20$$
   - Učestalost rute (`fd_count`) na kombinovanom train+test skupu bez ciljne labele.
   - Donosi čist skok od +0.0015 ROC-AUC u odnosu na sirovu distancu.

2. **Dinamika Kašnjenja i Oporavak Leta:**
   - `total_delay = Departure Delay + Arrival Delay`
   - `delay_recovery = Arrival Delay - Departure Delay` (negativna vrednost znači da je posada ubrzala let i nadoknadila vreme)
   - `is_delayed = total_delay > 0`
   - `log_dep_delay = log1p(max(Departure Delay, 0))`
   - `log_arr_delay = log1p(max(Arrival Delay, 0))`

3. **Strukturne CTGAN Nule (N/A Survey Flags):**
   - Generator sintetičkih podataka koristi ocenu 0 da označi da usluga nije primenjiva (N/A).
   - Uvođenje binarnih indikatora `{col}_is_zero` za anketna pitanja i ukrštanja (`wifi_0_booking_0`, `food_0_entertainment_0`) omogućava stablima da prepoznaju strukturne obrasce generatora.

4. **Domenski Indeksi i Agregacije Anketa:**
   - `inflight_comfort_index`, `digital_exp_index`, `service_quality_index`, `ground_service_index`.
   - Statistika po putniku: `ratings_mean`, `ratings_std`, `ratings_min`, `ratings_max`, `low_rating_count` (broj ocena <= 2, asimetrični indikator frustracije).

---

## 4. Validacioni Protokol i Ansambl Optimizacija
- **Protokol:** 5-Fold Stratified K-Fold (seme 42) uz strogu izolaciju svih transformacija u okviru pojedinačnih foldova.
- **Optimizacija Ansambla:**
  - Pretvaranje verovatnoća u percentilne rangove:
    $$r = \frac{\text{rank}(p) - 0.5}{N}$$
  - Nelder-Mead simpleks algoritam sa Softmax ograničenjem težina direktno na OOF predikcijama radi maksimizacije zvanične ROC-AUC metrike.

---

## 5. Sledeći Koraci za Pobedu i Maksimizaciju Skora
1. Proširenje Tri-GBDT modela integracijom CatBoost GPU ordered target encoding-a i XGBoost hist algoritma sa većim brojem binova (`max_bin=512`).
2. Implementacija novih interakcija (npr. odnos kašnjenja i dužine leta `delay_per_distance`).
3. Formiranje konačnog optimizovanog ansambla treniranog od nule na punom 5-fold skupu.
