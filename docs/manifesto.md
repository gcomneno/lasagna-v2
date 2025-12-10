# Brain-Inspired Compressor Manifesto
## (Lasagna v2 – Time Series Edition, MVP)
Non vogliamo solo schiacciare bit. Vogliamo lasciare al dato una forma che una macchina possa ancora capire.

## 1. Il problema: non basta “zippare”
Le serie temporali moderne – sensori, log, metriche, telemetria – sono:
- **ridondanti** (trend lenti, pattern che si ripetono),
- **rumorose**, ma con struttura,
- **consumate da macchine**, non solo da umani.

Uno ZIP tradizionale:
- vede solo **byte grezzi**,
- ignora il concetto di *tempo, trend, autocorrelazione*,
- non sa nulla di predizione, residui, segmenti.

Il risultato è accettabile come rapporto di compressione, ma **il significato temporale viene sepolto** dentro un blob opaco.

L’obiettivo di Lasagna v2 è diverso:
> comprimere *senza distruggere* la struttura temporale
> e, anzi, renderla più esplicita per una macchina a valle.

---

## 2. Principi “brain-inspired”
Lasagna v2 per serie temporali nasce da pochi principi semplici:

1. **Segmentare lo scorrere del tempo**
   Non tutto il segnale è uguale. Il compressore spezza la serie in **segmenti** con comportamento interno omogeneo (flat, trend, oscillazione locale…).

2. **Predire prima di memorizzare**
   Come il cervello “si aspetta” cosa verrà dopo, il codec non salva valori grezzi ma:
   - costruisce una **predizione locale**,
   - salva solo **l’errore** (residuo) rispetto a quella predizione.

3. **Multi-modello, non monolitico**
   Non esiste un modello unico buono per tutto.
   Per ogni segmento Lasagna può scegliere tra più strategie:
   - `mean`    → piatti/localmente costanti
   - `linear`  → trend lenti / rampette
   - `rw`      → random-walk, per serie molto autocorrelate

   Nel modo `auto`, il codec **valuta tutti e tre** e si sceglie quello che ricostruisce meglio *dopo* quantizzazione.

4. **Quantizzare in modo consapevole**
   L’errore non è rumore casuale: ha una scala.
   Per ogni segmento Lasagna stima la deviazione standard dei residui σ e fissa:

   [   Q = \max(C_Q \cdot \sigma,\ Q_{\min})   ]

   - Q piccolo → alta qualità, residui più “grossi” in modulo
   - Q grande  → più perdita, ma valori più concentrati intorno a 0

5. **Codifica entropica semplice ma intelligente**
   I residui (quantizzati) sono interi piccoli e spesso vicini a 0.
   Lasagna li codifica con:
   - **ZigZag** (per gestire segno),
   - **Varint** (più piccoli sono, meno byte costano).

   Risultato: segmenti con residui quasi nulli si comprimono in pochissimi byte.

6. **File ispezionabile, non blob opaco**
   Il formato `.lsg2` contiene header e tabella segmenti leggibili:
   - per ogni segmento: `[start, end]`, tipo di predittore, mean, slope, Q, seed
   - una CLI (`lasagna-info`) che stampa una tabella umana leggibile.

   Una macchina (o un analizzatore) può usare questi metadata **senza** dover decodificare tutto il flusso.

---

## 3. Architettura del Lasagna v2 – Time Series MVP

Pipeline di compressione per una serie temporale univariata:

1. **Segmentazione**

   Modalità:
   - `fixed`: segmenti di lunghezza fissa (es. 50, 64 campioni),
   - `adaptive`: partendo da `min_len`, estende il segmento finché il MSE del modello **resta sotto soglia** (`mse_threshold`), senza superare `max_len`.

   Questo fa sì che:
   - su un trend perfetto, i segmenti diventano **lunghi** (modellabile bene),
   - su una sinusoide rumorosa, i segmenti si adattano alle zone più difficili.

2. **Scelta del predittore**

   Per ogni segmento:
   - se l’utente chiede un modello specifico (`mean`, `linear`, `rw`) → viene usato quello;
   - con `predictor=auto`:
     * prova **mean, linear, rw**,
     * per ognuno simula *encode → quantizzazione → decode locale*,
     * misura l’MSE **post-decode**,
     * sceglie il modello con errore finale più basso.

3. **Calcolo residui e quantizzazione**

   Residui continui:
   [   r_i = x_i - \hat{x}_i   ]

   poi:
   [   q_i = \text{round}\left(\frac{r_i}{Q}\right)   ]

   con Q scelto per segmento come sopra.
   Il decoder farà l’operazione inversa: `r_i ≈ q_i * Q`.

4. **Codifica residui**

   Per ogni segmento:
   - i `q_i` (interi con segno) vengono trasformati con ZigZag in interi non negativi,
   - ogni valore viene codificato con varint (7 bit/payload, MSB=continuation).

   Il formato `.lsg2` memorizza:
   - `coding_type = 0` → int32 raw (debug / fallback),
   - `coding_type = 1` → ZigZag + varint (MVP attuale).

5. **Formato file `.lsg2`**

   Struttura:
   - **Header** binario (`LSG2`, versione, #punti, #segmenti,…)
   - **Context JSON**:
     * `sampling`: `dt`, `t0`,
     * `unit`: stringa simbolica (es. `kW`, `arbitrary`…)
   - **Tabella segmenti**:
     * `start_idx`, `end_idx`
     * `predictor_type` (`mean`/`linear`/`rw`)
     * `mean`, `slope`, `intercept`, `Q`, `seed_value`
   - **Sezione residui**:
     * `coding_type` (raw vs varint),
     * per ogni segmento: header + blob di residui codificati.

---

## 4. Che faccia ha un `.lsg2` reale?

### Caso 1 – Trend lineare perfetto

Serie sintetica:
[x_i = 0.1 \cdot i]

Risultato tipico (`lasagna-info`):
- 200 punti → 3 segmenti (**adaptive** tende a usare segmenti lunghi),
- tutti i segmenti con:
  * `pred = linear`,
  * `slope ≈ 0.1`,
  * `Q = 1e-6` (residui praticamente nulli),
- residuali quasi tutti 0 → varint compatta i residui in pochissimi byte.

Compressione:
- float64 raw: 1600 byte
- `.lsg2` varint: ~**478 byte** → ~**3.3x**
- errore praticamente nullo.

Il codec ha “capito” che la serie è una retta e memorizza solo **la retta + pochi zeri**.

---

### Caso 2 – Sinusoide + rumore

Serie sintetica:
[x_i = \sin\left(\frac{2\pi i}{50}\right) + \text{rumore gaussiano}]

Risultato tipico:
- 300 punti → 7 segmenti **adaptivi** (lunghezze 31–50),
- `predictor=auto` produce un mix:
  * segmenti `mean` su tratti quasi piatti,
  * segmenti `linear` dove la sinusoide si comporta localmente come una rampa,
  * segmenti `rw` dove la dinamica è molto autocorrelata.
- Q per segmento nell’intervallo ~0.08–0.26, scelto in base alla varianza dei residui.

Compressione:
- float64 raw: 2400 byte
- `.lsg2` adaptive+varint: ~**761 byte** → ~**3.15x**

Qualità:
- RMSE ≈ 0.065 rispetto all’originale,
- errore massimo ≈ 0.15 su un segnale con ampiezza ≈ 1 e rumore esplicito.

Il codec non fa solo “bit saving”:
**discretizza il comportamento locale** in termini di:
- tipo di modello (mean/linear/rw),
- forza del trend (slope),
- scala del rumore/residuo (Q),

con un file che una macchina può **leggere, interrogare, filtrare**.

---

## 5. Perché questo è “brain-inspired” e non solo “codec-inspired”

Il parallelo con il cervello (molto terra-terra, ma utile):
- **Segmentazione** → spezzare l’esperienza in “scene” (qui, finestre temporali omogenee).
- **Predizione** → il cervello anticipa cosa arriverà; qui il codec stima il valore atteso e guarda solo l’errore.
- **Errore come informazione** → quello che conta non è il dato assoluto, ma lo scarto dal modello interno.
- **Multi-modello locale** → il cervello non usa un singolo modello globale; attiva “strategie” diverse in contesti diversi.
  Qui ogni segmento può essere mean, linear o random-walk a seconda di cosa **funziona meglio dopo la distorsione**.
- **Rappresentazione leggibile per una macchina** → la corteccia non salva zlib; salva pattern con struttura.
  `.lsg2` conserva esplicitamente segmenti, pendenze, scale di errore.

Non stiamo simulando un neurone, ma stiamo rispettando la stessa intuizione di base:
> “Prima capisco *come si comporta* il pezzo di mondo,
> poi memorizzo solo lo scarto, in forma compatta e riutilizzabile.”

---

## 6. Roadmap naturale (oltre l’MVP)
L’MVP di Lasagna v2 per serie temporali è già:
- implementato,
- testato su esempi sintetici,
- misurabile in termini di compressione e RMSE,
- introspezionabile.
