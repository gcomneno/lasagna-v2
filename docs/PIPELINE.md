# Lasagna v2 – Demo Pipeline

Questa pagina documenta la pipeline completa, dalla serie temporale in CSV
fino agli output semantici e alle immagini dei segmenti.

Pipeline logica:

```text
CSV → .lsg2 → profiles.csv → events.csv + clusters.csv → PNG
```

La demo usa tre serie sintetiche in `data/demo/`:

- `trend.csv`        → regime a trend quasi puro
- `sine_noise.csv`   → sinusoide + trend + rumore
- `flat_spike.csv`   → plateau con gradino centrale (spike)

---

## 1. Generazione dati demo

I CSV demo vengono generati da:

```bash
python tools/generate_demo_data.py
```

Output attesi:

- `data/demo/trend.csv`
- `data/demo/sine_noise.csv`
- `data/demo/flat_spike.csv`

Il formato è una singola colonna:

```text
value
1.234
1.235
...
```

---

## 2. Encoding → formato binario `.lsg2`

Per passare dai CSV al formato binario Lasagna:

```bash
lasagna2 encode --dt 1 --t0 0 --unit step   data/demo/trend.csv   data/demo/trend.lsg2

lasagna2 encode --dt 1 --t0 0 --unit step   data/demo/sine_noise.csv   data/demo/sine_noise.lsg2

lasagna2 encode --dt 1 --t0 0 --unit step   data/demo/flat_spike.csv   data/demo/flat_spike.lsg2
```

`--dt`, `--t0`, `--unit` sono parametri di metadato (sampling, origine tempo, unità).

---

## 3. Profilo globale: `profiles.csv`

Il tool `batch_profile.py` scorre una directory, legge tutti i `.lsg2`
e produce un `profiles.csv` con:

- frazioni di punti per pattern (`frac_flat`, `frac_trend`, `frac_oscillation`, `frac_noisy`)
- statistiche di energia e salienza
- numero di motifs per pattern

Comando demo:

```bash
python tools/batch_profile.py data/demo -o data/demo/profiles.csv
```

Output:

- `data/demo/profiles.csv`

---

## 4. Eventi semantici + cluster

### 4.1 Eventi semantici

`semantic_events.py` prende `profiles.csv` e produce un `events.csv`
con una o più etichette di “evento semantico” per file:

Eventi possibili:

- `single_trend_regime`
- `mixed_trend_regime`
- `oscillation_dominated`
- `trend_oscillation_mix`
- `flat_with_trend_bump`
- `noisy_segments_present`
- `high_energy`
- `none`

Demo:

```bash
python tools/semantic_events.py data/demo/profiles.csv data/demo/events.csv
```

Output:

- `data/demo/events.csv`

### 4.2 Cluster di profilo

`cluster_profiles.py` aggiunge una colonna `cluster` a `profiles.csv`:

Cluster possibili (oggi):

- `trend_dominated`
- `oscillation_dominated`
- `flat_with_trend_bump`
- `mostly_flat`
- `noisy_dominated`
- `trend_oscillation_mix`
- `high_energy_mixed`
- `mixed_other`

Demo:

```bash
python tools/cluster_profiles.py data/demo/profiles.csv data/demo/clusters.csv
```

Output:

- `data/demo/clusters.csv`

---

## 5. Export dei tag di segmento

Per ogni `.lsg2` è possibile esportare i tag di segmento in CSV:

- `pred ∈ {mean, linear, rw}`
- `patt ∈ {flat, trend, oscillation, noisy}`
- `sal ∈ {0, 1, 2}`
- `energy, mean, slope, Q (MSE)`

Demo:

```bash
lasagna2 export-tags data/demo/trend.lsg2       data/demo/trend_tags.csv
lasagna2 export-tags data/demo/sine_noise.lsg2  data/demo/sine_noise_tags.csv
lasagna2 export-tags data/demo/flat_spike.lsg2  data/demo/flat_spike_tags.csv
```

---

## 6. Viewer: immagini dei segmenti e dell’energia

Il tool `lasagna_viewer.py` prende un CSV di export-tags
e genera due immagini PNG:

- `*.segments.png` → segmenti nel tempo, colorati per pattern
- `*.energy.png`   → energia per segmento

Nella demo usiamo la serie `flat_spike`:

```bash
python tools/lasagna_viewer.py data/demo/flat_spike_tags.csv
```

Output attesi (accanto al CSV):

- `data/demo/flat_spike_tags.segments.png`
- `data/demo/flat_spike_tags.energy.png`

Queste immagini mostrano:

- segmenti `flat` ai lati,
- segmento centrale “attivo” (tipicamente classificato `noisy`)
- energia concentrata sul segmento centrale (dove c’è lo spike).

---

## 7. Demo completa

Quando il `Makefile` è configurato, è possibile lanciare l’intera demo con:

```bash
make demo
```

che esegue in sequenza:

1. generazione CSV demo,
2. encoding in `.lsg2`,
3. `profiles.csv` + `events.csv` + `clusters.csv`,
4. export dei tag,
5. generazione delle PNG per `flat_spike`.
