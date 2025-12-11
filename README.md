# Lasagna v2 — Brain-Inspired Time-Series Compressor
> 🧠🍝 **Lasagna v2** è un codec sperimentale per serie temporali univariate:
> segmentazione adattiva, predittori multipli, quantizzazione percettiva e
> un primo strato di “pattern tagging” semi-cognitivo.

⚠️ **Stato del progetto:** MVP di ricerca, non ancora pensato per produzione.
Formato e API possono cambiare senza preavviso.

---

## Obiettivi
Lasagna v2 nasce da tre idee:

1. **Non comprimere solo i bit, ma anche la struttura temporale.**
   Segmenti “lunghi e tranquilli” vanno trattati in modo diverso da tratti rumorosi
   o oscillatori.

2. **Separare pattern e residuo.**
   Prima si cattura il pattern principale (trend, flat, oscillazione),
   poi si impacchetta l’errore con una quantizzazione controllata.

3. **Tenere un occhio al “cervello”, ma parlare con le macchine.**
   Non è un codec percettivo umano, ma prende spunto da concetti come:
   chunking, priming, multi-livello, salienza.

Per la parte concettuale vedi anche
📄 [`docs/manifesto.md`](docs/manifesto.md).

---

## Funzionalità principali (MVP v2)

- **Serie temporali univariate** (`TimeSeries`):
  - valori float,
  - `dt` (passo temporale), `t0` (timestamp di inizio), `unit`.

- **Segmentazione:**
  - `fixed`: segmenti di lunghezza costante,
  - `adaptive`: segmenti variabili in base al MSE del modello.

- **Predittori per segmento:**
  - `mean` — livello costante,
  - `linear` — retta (trend),
  - `rw` — random-walk (dipendenza forte dal punto precedente),
  - `auto` — selezione automatica per segmento (MSE post-decode).

- **Codifica dei residui:**
  - `raw` — interi 32 bit,
  - `varint` — ZigZag + varint (più compatto quando i residui sono piccoli).

- **Pattern tagging per segmento:**
  - `patt ∈ {flat, trend, oscillation, noisy}`,
  - `sal ∈ {0, 1, 2}` (salienza “energetica” del segmento).

- **Formato binario `.lsg2`:**
  - header con meta-info (JSON compresso),
  - tabella segmenti,
  - sezione residui con blocchi per segmento.

---

## Installazione

Consigliato usare una virtualenv.

```bash
git clone https://github.com/<TUO_USER>/lasagna-v2.git
cd lasagna-v2
python3 -m venv .venv
source .venv/bin/activate

# installa runtime + strumenti di sviluppo
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

La installazione in modalità editable ti dà:

- il package `lasagna2`,
- lo script CLI `lasagna2`,
- gli strumenti dev (`black`, `ruff`, `pre-commit`, `pytest`, `detect-secrets`, …).

---

## Quickstart

### 1. Esempio `trend` (CSV → LSG2 → CSV)

Encode (trend quasi perfettamente lossless):

```bash
lasagna2 encode   --dt 1   --t0 0   --unit step   data/examples/trend.csv   data/tmp/trend.lsg2
```

Ispeziona il file `.lsg2`:

```bash
lasagna2 info data/tmp/trend.lsg2 -v
```

Output tipico (estratto):

```text
Time series :
  points    : 200
  dt        : 60.0 s
  t0        : 2025-01-01T00:00:00Z
  unit      : kW
  segments  : 3

Segments overview:
  id  start   end   len  pred  patt  sal   mean        slope       Q
  --- ------- ----- ---- ----- ----- --- ----------- ----------- -----------
    0       0    79   80 linear trend  2    3.950000    0.100000       1e-06
    1      80   159   80 linear trend  2   11.950000    0.100000       1e-06
    2     160   199   40 linear trend  1   17.950001    0.100000       1e-06
```

Decode:

```bash
lasagna2 decode   data/tmp/trend.lsg2   data/tmp/trend_decoded.csv
```

Il file CSV risultante contiene l’header `# value` e 200 valori ricostruiti, uno per riga.

---

### 2. Esempio `sine_noise` (codec lossy controllato)

Encode (sinusoide + rumore, con soglia MSE più alta):

```bash
lasagna2 encode   --dt 1   --t0 0   --unit step   data/examples/sine_noise.csv   data/tmp/sine_noise.lsg2
```

Decode:

```bash
lasagna2 decode   data/tmp/sine_noise.lsg2   data/tmp/sine_noise_decoded.csv
```

In questo caso il codec è intenzionalmente **lossy**: la serie ricostruita ha la stessa lunghezza e la stessa forma globale,
ma i valori non coincidono esattamente punto per punto (RMSE moderata).

---

## Utilizzo da codice Python

```python
from pathlib import Path
from lasagna2 import TimeSeries, encode_timeseries, decode_timeseries

# Costruisci una piccola serie
values = [0.1 * i for i in range(200)]
ts = TimeSeries(
    values=values,
    dt=60.0,
    t0="2025-01-01T00:00:00Z",
    unit="kW",
)

# Encode in memoria
encoded = encode_timeseries(
    ts,
    segment_mode="adaptive",
    min_segment_length=30,
    max_segment_length=80,
    mse_threshold=0.01,
    predictor="auto",
    residual_coding="varint",
)

Path("trend.lsg2").write_bytes(encoded)

# Decode
decoded = decode_timeseries(encoded)
print(len(decoded.values), decoded.dt, decoded.unit)
```

### Esportare i tag dei segmenti

```bash
lasagna2 export-tags data/tmp/trend.lsg2 data/tmp/trend_tags.csv
head data/tmp/trend_tags.csv
```

Output:
```bash
seg_id,start,end,len,pred,patt,sal,energy,mean,slope,Q
0,0,63,64,linear,trend,2,6.40006,3.15,0.1,1e-06
```

---

## Struttura del progetto

```bash
lasagna-v2/
  lasagna2/
    __init__.py        # API pubblica (TimeSeries, encode_timeseries, decode_timeseries)
    core.py            # motore del codec (formato .lsg2, segmentazione, predittori, quantizzazione)
    cli.py             # implementazione CLI

  lasagna_mvp.py       # wrapper CLI compatibile: python lasagna_mvp.py ...

  data/
    examples/          # esempi di serie (trend, sin+noise, ...)

  docs/
    manifesto.md       # “Brain-Inspired Compressor Manifesto”
    examples-trend-sine.md

  tests/
    test_core_roundtrip.py
    test_cli_encode_decode_info.py
    test_decode_malicious.py

  .github/workflows/
    ci.yml             # lint + test (runner hardened)
    security.yml       # CodeQL, dependency-review
    supply-chain.yml   # Scorecard, pip-audit

  pyproject.toml
  requirements-dev.txt
  .pre-commit-config.yaml
  .secrets.baseline
  LICENSE
  README.md
```

---

## Strumenti ausiliari (`tools/`)
Nella cartella `tools/` trovi alcuni script di supporto:

- `batch_profile.py`
  Profilazione semantica batch di file `.lsg2`:
    python tools/batch_profile.py data/tmp -o data/tmp/profiles.csv

- `lasagna_viewer.py`
  Visualizza i segmenti (output di lasagna2 export-tags) con grafici semplici:
    python tools/lasagna_viewer.py data/tmp/sine_noise_tags.csv

- `semantic_events.py`
  Estrae “eventi” semantici da un profiles.csv:
    python tools/semantic_events.py data/tmp/profiles.csv data/tmp/events.csv

---

## Qualità & Sicurezza

- **Pre-commit**:
  - `black`, `ruff`, `detect-secrets`, controlli standard su YAML / whitespace / file grossi.
- **Test**:
  - roundtrip encode/decode su serie sintetiche,
  - CLI encode/info/decode,
  - test su file `.lsg2` corrotti / malevoli (decode deve fallire con `ValueError` e non esplodere).
- **CI (GitHub Actions)**:
  - runner hardened con egress policy e allowlist stretta,
  - actions pinmate a SHA,
  - `pre-commit` + `pytest` su ogni push/PR.
- **Security pipeline**:
  - CodeQL per Python,
  - dependency-review su PR,
  - pip-audit sulle dipendenze dev,
  - OpenSSF Scorecard periodico.

---

## Roadmap
MVP attuale copre **solo univariato**.
Idee per le prossime iterazioni:
- supporto multivariato (più serie correlate),
- pattern tagging più ricco (eventualmente supervisionato),
- livelli di “profilo” (`--profile=human`, `--profile=machine`),
- strumenti di visualizzazione per segmenti, residui e pattern,
- specifica del formato `.lsg2` più formale / “da paper”.

Contributi, discussioni e idee sono benvenuti, ma il progetto resta dichiaratamente sperimentale.
