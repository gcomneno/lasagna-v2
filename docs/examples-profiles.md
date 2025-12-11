# Lasagna v2 – Esempi di profili semantici
Questa pagina mostra tre esempi sintetici che coprono i casi base:
- trend lineare “pulito”
- sinusoide con rumore
- plateau con “gradino” centrale (flat + spike)

Per ogni esempio ci sono:
- i comandi CLI per generare `.lsg2`, profilo e eventi,
- uno spezzone dell’output di `info -v`,
- il contenuto di `export-profile` e degli `eventi` derivati.

---

## 1. Trend lineare (`trend.csv`)
Serie: `x[i] = 0.1 * i` per 200 punti, dt=1, unit=step.

```bash
# encode
lasagna2 encode --dt 1 --t0 0 --unit step \
  data/examples/trend.csv \
  data/tmp/trend.lsg2

# profilo singolo
lasagna2 export-profile data/tmp/trend.lsg2 data/tmp/trend_profile.csv

# eventi (usando gli strumenti in tools/)
python tools/semantic_events.py \
  data/tmp/trend_profile.csv \
  data/tmp/trend_events.csv
```

Estratto da `lasagna2 info -v data/tmp/trend.lsg2`:

```bash
Time series :
  points    : 200
  dt        : 1.0 s
  t0        : 0
  unit      : step
  segments  : 2

Segments overview:
  id  start   end   len  pred  patt  sal   energy      mean        slope       Q
  --- ------- ----- ---- ----- ----- --- ---------- ----------- ----------- -----------
    0       0   127  128 linear trend  2     12.800    6.350000    0.100000       1e-06
    1     128   199   72 linear trend  2      7.200   16.350000    0.100000       1e-06

Profile:
  pattern       points   frac_pts   segs  motifs
  ----------- -------- ---------- ----- -------
  trend            200      1.000     2       1
```

`data/tmp/trend_profile.csv`:
```bash
file,n_points,dt,unit,n_segments,frac_flat,frac_trend,frac_oscillation,frac_noisy,sal_min,sal_max,sal_avg,energy_min,energy_max,energy_avg,n_motifs_flat,n_motifs_trend,n_motifs_oscillation,n_motifs_noisy
trend.lsg2,200,1,step,2,0.000000,1.000000,0.000000,0.000000,2.000,2.000,2.000,7.200072,12.800128,10.000100,0,1,0,0
```

`data/tmp/trend_events.csv`:
```bash
file,event_type
trend.lsg2,single_trend_regime
trend.lsg2,high_energy
```

Interpretazione:
-* quasi tutti i punti sono `trend` → profilo dominato da un unico regime lineare,
- `single_trend_regime` indica un unico motif di trend su tutta la serie,
- `high_energy` segnala che l’energia media non è trascurabile.

---

## 2. Sine + noise (`sine_noise.csv`)
Serie: sinusoide con rumore gaussiano, 300 punti, dt=1, unit=step.

```bash
lasagna2 encode --dt 1 --t0 0 --unit step \
  data/examples/sine_noise.csv \
  data/tmp/sine_noise.lsg2

lasagna2 export-tags data/tmp/sine_noise.lsg2 data/tmp/sine_noise_tags.csv
lasagna2 export-profile data/tmp/sine_noise.lsg2 data/tmp/sine_noise_profile.csv

python tools/semantic_events.py \
  data/tmp/sine_noise_profile.csv \
  data/tmp/sine_noise_events.csv
```

Estratto da `lasagna2 info -v`:
```bash
Time series :
  points    : 300
  dt        : 1.0 s
  t0        : 0
  unit      : step
  segments  : 6

Segments overview (esempio):
  id  start  end  len  pred    patt         sal  energy   mean        slope       Q
  0   ...          ... linear  oscillation  2    22.9003  0.140094   -0.006768   0.35105
  1   ...          ... linear  oscillation  2    17.9071  0.012336    0.004847   0.35330
  2   ...          ... linear  oscillation  2    16.8498 -0.020204    0.000587   0.35045
  3   ...          ... linear  oscillation  2    17.6559 -0.005213   -0.008138   0.35219
  4   ...          ... linear  trend        2    17.4445 -0.023513   -0.015318   0.34811
  5   ...          ... linear  trend        2    10.5215 -0.111979   -0.051661   0.20496
```

`data/tmp/sine_noise_profile.csv`:
```bash
file,n_points,dt,unit,n_segments,frac_flat,frac_trend,frac_oscillation,frac_noisy,sal_min,sal_max,sal_avg,energy_min,energy_max,energy_avg,n_motifs_flat,n_motifs_trend,n_motifs_oscillation,n_motifs_noisy
sine_noise.lsg2,300,1,step,6,0.000000,0.296667,0.703333,0.000000,2.000,2.000,2.000,10.521464,22.900306,17.213185,0,1,1,0
```

`data/tmp/sine_noise_events.csv` (tipico):
```bash
file,event_type
sine_noise.lsg2,oscillation_dominated
sine_noise.lsg2,trend_oscillation_mix
sine_noise.lsg2,high_energy
```

Interpretazione:
- ~70% dei punti sono `oscillation`, il resto `trend`,
- `oscillation_dominated` indica che la dinamica principale è oscillatoria,
- `trend_oscillation_mix` segnala la coesistenza di pattern lenti (trend) e oscillatori,
- anche qui `high_energy` per l’energia media elevata.

---

## 3. Plateau + spike centrale (`flat_spike.csv`)
Serie sintetica:
- inizio e fine quasi piatti (0.0 + rumore leggero),
- blocco centrale con valori intorno a 5.0 + rumore più forte.

```bash
# generazione (esempio, vedi script nel README o nei tuoi appunti)
# python <script che crea data/examples/flat_spike.csv>

lasagna2 encode --dt 1 --t0 0 --unit arb \
  data/examples/flat_spike.csv \
  data/tmp/flat_spike.lsg2

lasagna2 export-tags data/tmp/flat_spike.lsg2 data/tmp/flat_spike_tags.csv
lasagna2 export-profile data/tmp/flat_spike.lsg2 data/tmp/flat_spike_profile.csv

python tools/semantic_events.py \
  data/tmp/flat_spike_profile.csv \
  data/tmp/flat_spike_events.csv
```

Estratto da `lasagna2 info -v`:
```bash
Time series :
  points    : 300
  dt        : 1.0 s
  t0        : 0
  unit      : arb
  segments  : 4

Segments overview:
  id  start   end   len  pred  patt  sal   energy      mean        slope       Q
  --- ------- ----- ---- ----- ----- --- ---------- ----------- ----------- -----------
    0       0   127  128 linear flat   1      1.128    0.000503    0.000027  0.00878316
    1     128   159   32 linear trend  2     31.873    1.722146    0.225924     0.77012
    2     160   191   32 linear trend  2     33.557    3.331940   -0.205545    0.843116
    3     192   299  108 linear flat   1      1.143    0.001697    0.000012   0.0105689

Profile:
  pattern       points   frac_pts   segs  motifs
  ----------- -------- ---------- ----- -------
  flat             236      0.787     2       2
  trend             64      0.213     2       1
```

`data/tmp/flat_spike_profile.csv`:
```bash
file,n_points,dt,unit,n_segments,frac_flat,frac_trend,frac_oscillation,frac_noisy,sal_min,sal_max,sal_avg,energy_min,energy_max,energy_avg,n_motifs_flat,n_motifs_trend,n_motifs_oscillation,n_motifs_noisy
flat_spike.lsg2,300,1,arb,4,0.786667,0.213333,0.000000,0.000000,1.000,2.000,1.500,1.127709,33.557145,16.925257,2,1,0,0
```

`data/tmp/flat_spike_events.csv`:
```bash
file,event_type
flat_spike.lsg2,flat_with_trend_bump
flat_spike.lsg2,high_energy
```

Interpretazione:
- la serie è dominata da segmenti `flat` (plateau iniziale/finale),
- il blocco centrale è visto come un unico motif di `trend`,
- l’evento `flat_with_trend_bump` descrive proprio questo pattern:
  plateau + uno “scalino” energetico ben localizzato.

---

## Eventi semantici attualmente supportati
La logica in `tools/semantic_events.py` oggi può emettere:
- `single_trend_regime` – quasi tutto trend, un unico motif di trend,
- `mixed_trend_regime` – trend significativo ma non dominante al 100%,
- `oscillation_dominated` – oscillazione predominante, almeno un motif oscillation,
- `trend_oscillation_mix` – coesistenza significativa di trend e oscillazione,
- `flat_with_trend_bump` – serie per lo più piatta con un unico blocco di trend,
- `noisy_segments_present` – presenza forte di segmenti marcati come noisy,
- `high_energy` – energia media sopra una certa soglia,
- `none` – nessuna delle condizioni precedenti soddisfatta.

Queste regole sono volutamente euristiche e pensate per l’MVP:
l’idea è poter costruire in futuro profili più ricchi e, se serve, collegarli a livelli semantici più alti.

## Come leggere `lasagna2 info`
Una volta ottenuto un `.lsg2`, il comando:
```bash
lasagna2 info data/tmp/trend.lsg2 -v
```

mostra:
    - metadata globali (n. punti, dt, t0, unit, n. segmenti),
    - rapporto di compressione,
    - una tabella con un segmento per riga, più qualche statistica riassuntiva.

Le colonne principali:
    pred – predittore usato nel segmento:
        mean → media costante locale,
        linear → retta (trend),
        rw → random-walk (x[i] ≈ x[i-1]).

    patt – pattern qualitativo (stimato on-the-fly):
        flat → segmento quasi piatto, poco movimento,
        trend → segmento con pendenza significativa,
        oscillation → dinamica oscillante ma strutturata,
        noisy → residuo più sporco / difficile da modellare.

    sal – salienza grezza (0, 1, 2):
        0 → poco interessante (bassa variazione),
        1 → medio,
        2 → molto “energetico” (tanto trend o tanta oscillazione/rumore).

    energy – energia grezza del segmento (somma delle varianze / ampiezza).
    mean, slope – parametri principali del modello lineare locale.
    Q – errore medio quadratico (MSE) del modello sul segmento.

Esempio (trend lineare):
```bash
Segments overview:
  id  start   end   len  pred  patt  sal   energy      mean        slope       Q
  --- ------- ----- ---- ----- ----- --- ---------- ----------- ----------- -----------
    0       0   127  128 linear trend  2     12.800    6.350000    0.100000       1e-06
    1     128   199   72 linear trend  2      7.200   16.350000    0.100000       1e-06

Esempio (sinusoide + rumore):

Segments overview:
  id  start  end  len  pred    patt         sal  energy   mean        slope       Q
  --- ----- ---- ---- ----- -----------    --- -------- ----------- ----------- ---------
    0     …   63   64 linear oscillation    2   22.9003  0.140094   -0.006768   0.35105
    1     …  113   50 linear oscillation    2   17.9071  0.012337    0.004847   0.35330
    2     …  161   48 linear oscillation    2   16.8498 -0.020204    0.000587   0.35045
    3     …  210   49 linear oscillation    2   17.6559 -0.005213   -0.008138   0.35219
    4     …  258   48 linear trend          2   17.4445 -0.023513   -0.015318   0.34811
    5     …  299   41 linear trend          2   10.5215 -0.111979   -0.051661   0.20496
```

In pratica, lasagna2 info non è solo un “dump del file”:
    ti fa vedere dove la serie:
        - è piatta vs in salita/discesa,
        - oscilla vs è rumorosa,
        - concentra più energia,
    senza bisogno di decodificare tutti i campioni.

È il modo più rapido per farsi un’idea “cognitiva” della serie prima ancora di guardare il CSV decodificato.
