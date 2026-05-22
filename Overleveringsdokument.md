# Overleveringsdokument - Dynamic Risk Prediction Kursus

## Projektoversigt

Dette dokument beskriver strukturen i **Dynamic Risk Prediction** kursus-projektet og fungere som vejledning for nye udviklere, der skal overtage vedligeholdelsen og videreudviklingen.

---

## Mappe Struktur

```
Dyn_Risk_Pred_Course/
├── lectures/                  # Undervisningsmateriale (forelæsninger)
│   ├── index.qmd              # Introduktion til kurset
│   ├── data_management.qmd    # Data management
│   ├── data_preprocessing.qmd # Data preprocessing
│   ├── modelling.qmd          # Modellering
│   └── implementation.qmd     # Implementering
│
├── Code/                      # Kode og script filer
│   ├── request_fhir.R         # FHIR request script (R)
│   ├── requests_fhir.py       # FHIR request script (Python)
│   │
│   ├── exercise_solutions/    # Øvelsesdata og løsninger
│   │   ├── solutions/         # Færdige løsninger til workshops
│   │   │   ├── Workshop_1_data_preprocessing.R
│   │   │   ├── Workshop_2_modelling.R
│   │   │   ├── Workshop_3_Implementation.R
│   │   │   ├── Workshop_1_data_preprocessing.ipynb
│   │   │   ├── Workshop_2_Modelling.ipynb
│   │   │   ├── Workshop_3_Implementation.ipynb
│   │   │   ├── request_fhir.R         # FHIR request (kopi for øvelser)
│   │   │   ├── request_fhir.py        # FHIR request (kopi for øvelser)
│   │   │   └── requirements.txt       # Python afhængigheder
│   │
│   └── additional_code/       # Yderligere hjælpekode
│       └── Metric_calculation.py     # Metrik beregninger
│
├── exercise_data/             # Øvelsesdata
│   ├── PAD-introduction.html  # Introduktion til PAD
│   ├── raw_data/              # Rå data
│   │   ├── baseline_data.csv
│   │   ├── blood_data.csv
│   │   ├── diag_data.csv
│   │   ├── dict_data.csv
│   │   ├── events.csv
│   │   ├── quest_data.csv
│   │   ├── snomed.csv
│   │   ├── treat_data.csv
│   │   └── visit_date.csv
│   └── formatted_data/         # Formateret data
│       ├── Data_ready_for_workshop2.csv
│       └── Data_ready_for_workshop2.rds
│
├── css/                       # CSS stilarter
│   ├── materialark.scss
│   ├── materialight.scss
│   └── styles.css
│
├── cards/                     # Billeder af Sandbox crew
│   ├── AlbaMartinez.qmd
│   ├── JacobHansen.qmd
│   ├── JakobSkelmose.qmd
│   ├── JenniferBartell.qmd
│   └── SamueleSoraggi.qmd
│
├── img/                       # Billeder til obligatorisk setup
│   ├── logo.png
│   ├── AlbaMartinez.jpg
│   ├── AlexJose.jpg
│   └── ...
│
├── images/                    # Billeder til forelæsninger
│   ├── calibration_plot.png
│   ├── class_problem.png
│   ├── Decision_tree_l4.png
│   └── ...
│
├── README.md                  # Hoved README
├── _quarto.yml                # Quarto konfigurationsfil
├── .quarto/                   # Quarto cache
├── Dyn_Risk_Pred_Course.Rproj # RStudio projektfil
├── renv.lock                  # R pakke versioner
├── .Rbuildignore              # R build ignore regler
├── DESCRIPTION                # Projekt beskrivelse
├── LICENSE.md                 # Licens
└── .gitignore                 # Git ignore regler
```

---

## Undervisningsmateriale (lectures/)

Forelæsningsmapperne indeholder al det teoretiske undervisningsmateriale i **Quarto Markdown (.qmd)** format. 

| Fil | Beskrivelse |
|-----|------------|
| `index.qmd` | Startside/oversigt over kurset |
| `data_management.qmd` | Data håndtering - hvordan man strukturere og organiserer data |
| `data_preprocessing.qmd` | Data forbehandling - rengøring, transformation og forberedelse |
| `modelling.qmd` | Modellering - opbygning af forudsigelsesmodeller |
| `implementation.qmd` | Implementering - hvordan man implementerer modeller i praksis |

**Bemærk:** Quarto-filer (.qmd) kan renderes til HTML, PDF eller andre formater ved hjælp af Quarto CLI.

**Kør kursus lokalt:** Kursus kan blive testet på lokal enhed ved at bruge følgende commando i terminalen i root mappen: `quarto preview lecture/index.md`

---

## Kode og Øvelser (Code/)

### Root niveau scripts

| Fil | Formål |
|-----|--------|
| `request_fhir.R` | R script til FHIR API anmodninger |
| `requests_fhir.py` | Python script til FHIR API anmodninger |

### exercise_solutions/

Denne mappe indeholder **færdige løsninger** til alle workshop-øvelserne i `solutions/` undermappen:

| Workshop | Filer                                                                    | Beskrivelse |
|----------|--------------------------------------------------------------------------|------------|
| **Workshop 1** | `Workshop_1_data_preprocessing.R`, `Workshop_1_data_preprocessing.ipynb` | Data forbehandling |
| **Workshop 2** | `Workshop_2_modelling.R`, `Workshop_2_Modelling.ipynb`                   | Modellering og evaluering |
| **Workshop 3** | `Workshop_3_Implementation.R`, `Workshop_3_Implementation.ipynb`         | Implementering af modeller |

**Yderligere filer i solutions/:**
- `request_fhir.R` - Kopi af FHIR script til øvelser
- `request_fhir.py` - Kopi af FHIR script til øvelser
- `requirements.txt` - Python afhængigheder (Når man skal lave kurset i python, starter mane med at skrive følgende i python terminalen: `pip install -r requirements.tx`)

### additional_code/

| Fil | Formål |
|-----|--------|
| `Metric_calculation.py` | Beregning af evalueringsmetrikker |

---

## Data (exercise_data/)

| Fil | Beskrivelse |
|-----|------------|
| `PAD-introduction.html` | Introduktion til Peripheral Artery Disease (PAD) |

**Rodniveau datafiler:**
- `Data_ready_for_workshop2.csv` - Forberedt data til workshop 2
- `Data_ready_for_workshop2_test.csv` - Test dataset
- `Data_ready_for_workshop2_test.rds` - Test dataset i R format

### raw_data/

Rå data til øvelserne:

| Fil | Beskrivelse |
|-----|------------|
| `baseline_data.csv` | Baseline data for patienter |
| `blood_data.csv` | Blodprøve data |
| `diag_data.csv` | Diagnose data |
| `dict_data.csv` | Ordbogsdata / reference data |
| `events.csv` | Begivenhedsdata / events |
| `quest_data.csv` | Spørgeskema data |
| `snomed.csv` | SNOMED CT kode referencer |
| `treat_data.csv` | Behandlingsdata |
| `visit_date.csv` | Besøgsdatoer for patienter |

### formatted_data/

Forbehandlet og formateret data:

| Fil | Beskrivelse |
|-----|------------|
| `Data_ready_for_workshop2.csv` | Forberedt data til workshop 2 (CSV format) |
| `Data_ready_for_workshop2.rds` | Forberedt data til workshop 2 (R format) |

---

## Asset Mapper

| Mappe | Beskrivelse | Indhold |
|-------|------------|---------|
| `css/` | CSS stilarter til projektet | materialark.scss, materialight.scss, styles.css |
| `cards/` | Flashcards til kursusdeltagere | .qmd filer med kontaktinformation |
| `img/` | Billeder af kursusdeltagere | Profilbilleder og logoer |
| `images/` | Billeder til forelæsninger | Diagrammer, plots, illustrationer |

---


### Projekt Konfiguration

- **`_quarto.yml`** - Quarto indstillinger for bygning af dokumentation
- **`renv.lock`** - Låste R pakke versioner
- **`.gitignore`** - Git ignore regler
- **`Dyn_Risk_Pred_Course.Rproj`** - RStudio projektfil
- **`.Rbuildignore`** - R build ignore regler
- **`DESCRIPTION`** - Projekt beskrivelse
- **`LICENSE.md`** - Licensinformation

---

## Quarto Installation

For at kunne arbejde med kursusmaterialet lokalt, skal Quarto være installeret.

### Installér Quarto CLI

1. **Download** Quarto fra [quarto.org](https://quarto.org/docs/get-started/)
2. **Windows/Mac:** Kør installationsprogrammet og følg instruktionerne
3. **Linux (Ubuntu/Debian):** `sudo apt-get install quarto`
4. **Verificer installation:** `quarto --version`



## Github manual: 

1) Åben Rstudio/Python med 'audited privileges'

2) Åben terminalen i R Studio (Top bar -> Tools -> Terminal -> New Terminal)

3) skriv i terminalen: "git pull"

4) skriv i terminalen: "quarto preview lectures/index.qmd" for at se kurset i hjemmeside format.

5) Lav ændringer i kursus filerne eller kode til øvelser

6) (HVIS DER BLIVER ÆNDRET NOGET) Skriv i terminalen:
    6.1 'git add .' (Tilføj alle ændringer)
    6.2 'git commit -m "skriv en kommentar"' (Commit ændringer med en kommentar)
    6.3 'git push' (Skub ændringerne til Github)

---

*Dokument oprettet: 12-05-2026*
*Senest opdateret: 22-05-2026*
