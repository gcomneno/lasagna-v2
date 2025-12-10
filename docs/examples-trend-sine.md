## How to read `lasagna-info`
Una volta ottenuto un `.lsg2`, il comando:
```bash
python3 lasagna_mvp.py info data.lsg2 -v
```

mostra:
- metadata globali (n. punti, dt, t0, unit, n. segmenti),
- rapporto di compressione,
- una tabella con **un segmento per riga**.

Le colonne principali:
- `pred`  – predittore usato nel segmento:
  * `mean`   → media costante locale,
  * `linear` → retta (trend),
  * `rw`     → random-walk (x[i] ≈ x[i-1]).
- `patt`  – pattern qualitativo (stimato on-the-fly):
  * `flat`        → segmento quasi piatto, poco movimento,
  * `trend`       → segmento con pendenza significativa,
  * `oscillation` → dinamica oscillante ma strutturata,
  * `noisy`       → residuo più sporco / difficile da modellare.
- `sal`   – salienza grezza (0, 1, 2):
  * 0 → poco interessante (bassa variazione),
  * 1 → medio,
  * 2 → molto “energetico” (tanto trend o tanto rumore).

Esempio (trend lineare):
```bash
id  start   end   len  pred  patt  sal   mean        slope       Q
--- ------- ----- ---- ----- ----- --- ----------- ----------- -----------
  0       0    79   80 linear trend  2    3.950000    0.100000       1e-06
  1      80   159   80 linear trend  2   11.950000    0.100000       1e-06
  2     160   199   40 linear trend  1   17.950001    0.100000       1e-06
```

Esempio (sinusoide + rumore):
```bash
id  start   end   len  pred  patt        sal   mean        slope       Q
--- ------- ----- ---- ----- ---------  --- ----------- ----------- -----------
  0       0    31   32 mean  noisy       2    0.417923   -0.030223    0.259765
  1      32    75   44 linear trend      2    0.061683    0.048782    0.215818
  2      76   125   50 rw    oscillation 2    0.007987    0.037898   0.080597
  3     126   172   47 linear trend      2    0.022447    0.044643    0.219240
  4     173   203   31 rw    oscillation 1   -0.461656    0.006847    0.089976
  5     204   250   47 linear trend      2   -0.017318   -0.044554    0.219958
  6     251   299   49 linear trend      2    0.004515   -0.041851    0.212018
```

In pratica:
- `lasagna-info` non è solo un “dump del file”:
  ti fa vedere **dove** la serie:
  * è piatta vs in salita/discesa,
  * oscilla vs è rumorosa,
  * concentra più energia,
- senza bisogno di decodificare tutti i campioni.
