# Riferimenti scientifici

Questo file raccoglie la letteratura peer-reviewed usata per fondare le scelte metodologiche di BearLens (in particolare la baseline territoriale, le covariate di enrichment, e il modo in cui il sito comunica bias e limiti). Ogni voce indica a quale/i milestone del progetto è collegata e perché.

Non è una bibliografia esaustiva sull'ecologia dell'orso bruno: è una selezione mirata a giustificare le scelte tecniche e comunicative di questo progetto. Va mantenuta aggiornata quando nuove decisioni metodologiche vengono prese.

---

## Orsi e interazioni uomo–orso

**Ditmer, M.A., Iannarilli, F., Tri, A.N., Garshelis, D.L. & Carter, N.H. (2021).** Artificial night light helps account for observer bias in citizen science monitoring of an expanding large mammal population. *Journal of Animal Ecology*, 90, 330–342. DOI: [10.1111/1365-2656.13338](https://doi.org/10.1111/1365-2656.13338)

- **Milestone:** M8c (enrichment luminosità artificiale notturna VIIRS/ALAN), M10 (caveat metodologici)
- Riferimento più diretto per BearLens: dimostra che la luminosità artificiale notturna è il predittore singolo più forte del tasso di segnalazione di orso nero (β=0.81), più forte di densità abitativa, copertura del suolo o densità stradale. Un'area idonea ma poco illuminata mostrava ~375% più orsi *predetti* che *osservati*. Motiva l'introduzione di ALAN come covariata di sforzo osservativo in M8c.

**Airst, J.I. & Fleming, T.B. (2024).** Spatial Predictors of Human–Black Bear Interactions in Nova Scotia, Canada. *Human–Wildlife Interactions*, 18(2), Article 8. DOI: [10.26077/2f07-828b](https://doi.org/10.26077/2f07-828b)

- **Milestone:** M9 (disegno baseline territoriale), M10 (confronto osservazioni/baseline)
- Confronta 3.278 segnalazioni di conflitto + 867 non-conflict report con 12.000 punti casuali (GAMM logistico). Precedente diretto per il rapporto segnalazioni/punti di controllo che BearLens adotta in M9; le interazioni risultano concentrate vicino a strade, in paesaggi frammentati a densità abitativa moderata.

**McFadden-Hiller, J.E., Beyer, D.E. Jr. & Belant, J.L. (2016).** Spatial Distribution of Black Bear Incident Reports in Michigan. *PLOS ONE*, 11(4), e0154474. DOI: [10.1371/journal.pone.0154474](https://doi.org/10.1371/journal.pone.0154474)

- **Milestone:** M8b (copertura del suolo/land cover), M10 (caveat sul confondimento ecologico), M10b (regressione logistica used-available)
- 1.800 incidenti vs 5.400 punti casuali (rapporto 3:1), GLM/regressione logistica con selezione di modello via AIC. Il segnale più forte è la copertura forestale e i margini agro-forestali frammentati, non la vicinanza agli insediamenti — un segnale ecologico reale, non un artefatto di osservazione. Base diretta per l'impianto statistico di M10b.

**Wilson, S.M., Madel, M.J., Mattson, D.J., Graham, J.M., Burchfield, J.A. & Belsky, J.M. (2005).** Natural landscape features, human-related attractants, and conflict hotspots: A spatial analysis of human-grizzly bear conflicts. *Ursus*, 16(1), 117–129. DOI: [10.2192/1537-6176(2005)016[0117:NLFHAA]2.0.CO;2](https://doi.org/10.2192/1537-6176(2005)016%5B0117:NLFHAA%5D2.0.CO;2)

- **Milestone:** M10 (caveat sul confondimento ecologico), M12 (analisi esplorative avanzate)
- Hotspot da kernel density + simulazione Monte Carlo su attrattori antropici (bestiame, arnie, discariche). Il 75% dei conflitti si concentra nell'8% dell'area di studio; gli attrattori protetti (es. arnie recintate) riducono i conflitti — pattern guidato dalla gestione del territorio, non dall'osservazione.

**Sıkdokur, E., Naderi, M., Çeltik, E., Kemahlı Aytekin, M.C., Kušak, J., Sağlam, I.K. & Şekercioğlu, Ç.H. (2024).** Human-brown bear conflicts in Türkiye are driven by increased human presence around protected areas. *Ecological Informatics*, 81, 102643. DOI: [10.1016/j.ecoinf.2024.102643](https://doi.org/10.1016/j.ecoinf.2024.102643)

- **Milestone:** M8b (distanza da aree protette), M10 (caveat sul confondimento ecologico — riferimento più importante)
- Ecological Niche Modeling su dati nazionali 2017–2022. La vicinanza a confini di aree protette e l'indice di impronta umana sono predittori rilevanti. **Punto chiave per BearLens**: gli autori interpretano la concentrazione dei conflitti vicino alle aree protette come comportamento reale dell'orso (attrazione verso cibo antropico, specialmente in iperfagia), non solo come maggiore probabilità di osservazione. Fonda la nuova categoria di bias "confondimento ecologico" in M10.

**Franchini, M., Raniolo, S., Corazzin, M., Zanghellini, P., Bragalanti, N. & Bovolenta, S. (2026).** Patterns of brown bear damages to agro-livestock activities in North-Eastern Italy across 15 years. *Scientific Reports*, 16, 7212. DOI: [10.1038/s41598-026-38371-4](https://doi.org/10.1038/s41598-026-38371-4)

- **Milestone:** M7 (bibliografia/UI metodologia), M10 (rimando al sistema ufficiale PAT)
- Dati ufficiali della Provincia Autonoma di Trento e Friuli-Venezia Giulia, 2009–2023, 3.180 eventi di danno verificati sul campo (tecnici faunistici, genetica). Hotspot analysis (Getis-Ord Gi*) su griglia 5×5 km: 46% delle celle hotspot in Trentino, stagionalità primavera-estate marcata, avvicinamento progressivo agli insediamenti dal 2018. **Riferimento diretto sul territorio di studio**: dimostra che esiste già un sistema di monitoraggio ufficiale e verificato, rispetto al quale il dataset crowdsourced di BearLens va esplicitamente differenziato nella comunicazione del sito.

**Sherman, W.C., Schell, C.J. & Wilkinson, C.E. (2025).** The wildlife nextdoor: Socioeconomics and race predict social media carnivore reports. *Science of the Total Environment*, 977, 179227. DOI: [10.1016/j.scitotenv.2025.179227](https://doi.org/10.1016/j.scitotenv.2025.179227)

- **Milestone:** M8b (covariate socioeconomiche/demografiche ISTAT), M10 (bias di reporting)
- 2.584 post Nextdoor, 52 quartieri di Los Angeles, include l'orso tra i carnivori studiati. Status socioeconomico e composizione demografica predicono il tasso di segnalazione sui social indipendentemente dalla probabile presenza reale dell'animale - meccanismo di bias distinto dalla semplice accessibilità del terreno.

---

## Citizen science, accessibilità e sampling bias

**Geldmann, J., Heilmann-Clausen, J., Holm, T.E., Levinsky, I., Markussen, B., Olsen, K., Rahbek, C. & Tøttrup, A.P. (2016).** What determines spatial bias in citizen science? Exploring four recording schemes with different proficiency requirements. *Diversity and Distributions*, 22, 1139–1149. DOI: [10.1111/ddi.12477](https://doi.org/10.1111/ddi.12477)

- **Milestone:** M8 (giustificazione covariate strade/uso del suolo), M9 (baseline territoriale)
- Quattro schemi di citizen science danesi confrontati con strade, popolazione, uso del suolo. Distanza da strade, densità di popolazione e suolo urbano guidano il bias spaziale; il bias si riduce quando aumenta la competenza richiesta all'osservatore. Motiva l'incrocio segnalazioni/infrastrutture come proxy di bias.

**Sicacha-Parada, J., Steinsland, I., Cretois, B. & Borgelt, J. (2019).** Accounting for spatial varying sampling effort due to accessibility in Citizen Science data: A case study of moose in Norway.

- **Milestone:** M10b (roadmap statistico avanzato), M12
- Log-Gaussian Cox Process bayesiano che tratta l'accessibilità (distanza da strade) come superficie di sforzo osservativo esplicita dentro il modello, invece che come semplice covariata di confronto. Le segnalazioni di alce sono sovrarappresentate vicino alle strade. Percorso di aggiornamento naturale oltre il confronto descrittivo di M10.

**Tang, B., Clark, J.S. & Gelfand, A.E. (2021).** Modeling spatially biased citizen science effort through the eBird database. *Environmental and Ecological Statistics*, 28(3), 609–630. DOI: [10.1007/s10651-021-00508-1](https://doi.org/10.1007/s10651-021-00508-1)

- **Milestone:** M10b, M12
- Modella congiuntamente "dove vanno gli osservatori" e "quanto cercano" con effetti spaziali casuali (dati eBird). Argomenta che entrambe le componenti vanno modellate per un'inferenza affidabile da dati citizen-science — rilevante per un'eventuale evoluzione statistica oltre l'MVP descrittivo.

**Kays, R., Lasky, M., Parsons, A.W., Pease, B. & Pacifici, K. (2021).** Evaluation of the Spatial Biases and Sample Size of a Statewide Citizen Science Project. *Citizen Science: Theory and Practice*, 6(1), 34. DOI: [10.5334/cstp.344](https://doi.org/10.5334/cstp.344)

- **Milestone:** M9 (disegno baseline territoriale — riferimento più diretto)
- Confronta 4.295 siti di camera-trapping (65% da volontari) con 9.586 punti casuali di riferimento su 7 variabili di uso del suolo/infrastrutture. Copertura "adeguata" per il 99,2% dell'area di studio; convalida l'uso di punti casuali come benchmark di rappresentatività descrittiva a livello di MVP, a condizione di segnalare esplicitamente le zone sotto-rappresentate.

**Guilbault, E., Renner, I.W., Beh, E.J. & Mahony, M. (2023).** A practical approach to making use of uncertain species presence-only data in ecology: Reclassification, regularization methods and observer bias. *Ecological Informatics*, 77, 102155. DOI: [10.1016/j.ecoinf.2023.102155](https://doi.org/10.1016/j.ecoinf.2023.102155)

- **Milestone:** M3 (classificazione del tipo di segnalazione), M12
- Tratta record presence-only incerti/con possibile errata identificazione tramite riclassificazione EM e regolarizzazione, affrontando insieme incertezza di identificazione e bias dell'osservatore. Rilevante se in futuro BearLens dovesse gestire segnalazioni con specie ambigua o bassa confidenza di classificazione in modo più sofisticato dei semplici livelli high/medium/low/unknown.

---

## Presence-only, background points e baseline

**Phillips, S.J., Dudík, M., Elith, J., Graham, C.H., Lehmann, A., Leathwick, J. & Ferrier, S. (2009).** Sample selection bias and presence-only distribution models: implications for background and pseudo-absence data. *Ecological Applications*, 19(1), 181–197. DOI: [10.1890/07-2153.1](https://doi.org/10.1890/07-2153.1)

- **Milestone:** M9 (limiti dichiarati della baseline uniforme), M12 (target-group background)
- Fondamentale: propone il "target-group background" (punti di controllo tratti da record di altri taxa/sforzi di rilevamento correlati) invece del background uniformemente casuale, così da ereditare lo stesso bias di accessibilità dei dati di presenza. Motiva la proposta di uno scenario di sensitivity analysis con un altro layer citizen-science locale in M12.

**VanDerWal, J., Shoo, L.P., Graham, C. & Williams, S.E. (2009).** Selecting pseudo-absence data for presence-only distribution modeling: How far should you stray from what you know? *Ecological Modelling*, 220(4), 589–594. DOI: [10.1016/j.ecolmodel.2008.11.010](https://doi.org/10.1016/j.ecolmodel.2008.11.010)

- **Milestone:** M9 (documentazione dei limiti/alternative della baseline)
- Il risultato cambia in funzione del raggio da cui vengono estratti i punti di background rispetto alle occorrenze note; un buffer intermedio è risultato ottimale su 12 specie testate.

**Whitford, A.M., Shipley, B.R. & McGuire, J.L. (2024).** The influence of the number and distribution of background points in presence-background species distribution models. *Ecological Modelling*, 488, 110604. DOI: [10.1016/j.ecolmodel.2023.110604](https://doi.org/10.1016/j.ecolmodel.2023.110604)

- **Milestone:** M9 (numero e distribuzione dei punti di baseline)
- Un'estensione di background limitata a piccoli buffer causa sovrastima; variare l'estensione del background tra modelli replicati riduce la sensibilità alla ponderazione del bias spaziale. Rilevante per giustificare/testare in futuro se 10.000 punti uniformi sull'intera area di studio siano sufficienti o necessitino di scenari alternativi.

**Steen, B., Broennimann, O., Maiorano, L. & Guisan, A. (2024).** How sensitive are species distribution models to different background point selection strategies? A test with species at various equilibrium levels. *Ecological Modelling*, 493, 110754. DOI: [10.1016/j.ecolmodel.2024.110754](https://doi.org/10.1016/j.ecolmodel.2024.110754)

- **Milestone:** M9, M12 (baseline stratificata come scenario di sensitivity analysis)
- Confronta strategie di background geografico-casuale, stratificato nello spazio ambientale e casuale nello spazio ambientale. Il background geografico-casuale puro (l'approccio MVP di BearLens) è risultato il meno accurato tra quelli testati; quello stratificato per ambiente il più accurato. Motiva l'introduzione di una baseline stratificata come scenario esplorativo aggiuntivo in M12, non come sostituto dell'MVP.

**Komori, O., Eguchi, S., Saigusa, Y., Kusumoto, B. & Kubota, Y. (2020).** Sampling bias correction in species distribution models by quasi-linear Poisson point process. *Ecological Informatics*, 55, 101015. DOI: [10.1016/j.ecoinf.2019.101015](https://doi.org/10.1016/j.ecoinf.2019.101015)

- **Milestone:** M12 (analisi esplorative avanzate, solo se si va oltre la statistica descrittiva)
- Non verificato in dettaglio (solo titolo/sede confermati in fase di revisione della letteratura): citato come possibile riferimento per separare esplicitamente processo ecologico e processo di campionamento, da validare con lettura integrale prima di un eventuale uso metodologico.

---

## Mappa riepilogativa riferimento → milestone

| Milestone | Riferimenti principali |
|---|---|
| M3 – classificazione tipo di segnalazione | Guilbault et al. 2023 |
| M7 – UI metodologia / bibliografia | Franchini et al. 2026 |
| M8 – enrichment OSM | Geldmann et al. 2016 |
| M8b – aree protette, popolazione, uso del suolo | Sıkdokur et al. 2024; Sherman et al. 2025; McFadden-Hiller et al. 2016 |
| M8c – luminosità artificiale notturna (VIIRS/ALAN) | Ditmer et al. 2021 |
| M9 – baseline territoriale | Airst & Fleming 2024; Kays et al. 2021; Phillips et al. 2009; VanDerWal et al. 2009; Whitford et al. 2024; Steen et al. 2024 |
| M10 – confronto osservazioni/baseline e caveat | Sıkdokur et al. 2024; Wilson et al. 2005; McFadden-Hiller et al. 2016; Franchini et al. 2026; Sherman et al. 2025 |
| M10b – regressione logistica used-available (roadmap avanzato) | McFadden-Hiller et al. 2016; Sicacha-Parada et al. 2019; Tang, Clark & Gelfand 2021 |
| M12 – analisi esplorative avanzate | Wilson et al. 2005; Phillips et al. 2009; Steen et al. 2024; Guilbault et al. 2023; Komori et al. 2020 |

---

*Nota sulla verifica delle fonti: la maggior parte di queste voci è stata verificata in full text (accesso aperto, es. PLOS ONE, Scientific Reports) o tramite abstract/dettagli metodologici pubblicamente accessibili sulla pagina dell'editore. La voce Komori et al. 2020 è confermata solo a livello di titolo e sede editoriale: va letta integralmente prima di citarne risultati specifici in qualunque testo pubblicato sul sito.*
