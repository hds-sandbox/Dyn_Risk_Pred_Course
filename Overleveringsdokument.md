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
│   ├── implementation.qmd     # Implementering
│   └── images/                # Billeder til forelæsninger
│
├── Code/                      # Kode og øvelsesløsninger
│   ├── exercise_solutions/    # Løsninger til workshop-øvelser
│   │   ├── solutions/         # Færdige løsninger
│   │   │   ├── Workshop_0_data_sources_asquisition.*  # Data kilder
│   │   │   ├── Workshop_1_data_management.*          # Data håndtering
│   │   │   ├── Workshop_2_Modelling.*                 # Modellering
│   │   │   ├── Workshop_3_Implementation.*            # Implementering
│   │   │   └── modelling_simlpified.py               # Forenklet modellering
│   │   ├── fhir_mock_server.py                       # FHIR mock server
│   │   ├── request_fhir.py                            # FHIR request script (Python)
│   │   └── request_fhir.R                            # FHIR request script (R)
│   │
│   └── additional_code/       # Yderligere hjælpekode
│       └── Metric_calculation.py                     # Metrik beregninger
│
│
├── exercise_data/             # Øvelsesdata
│   ├── formatted_data/        # Formaterede datafiler
│   ├── raw_data/              # Rå data
│   └── PAD-introduction.html  # Introduktion til PAD
│
├── images/                    # Billeder og illustrationer ( Bruges i forelæsninger)
├── img/                       # Yderligere billeder
├── cards/                     # (Kort/ flashcards til kursus)
├── css/                       # CSS stilarter
├── martin_guide/              # Yderligere vejledning (Martin)
│
├── Data_ready_for_workshop2.csv      # Forberedt data til workshop 2
├── Data_ready_for_workshop2_test.csv  # Test data til workshop 2
├── Data_ready_for_workshop2_test.rds  # Test data (R format)
│
├── README.md                  # Hoved README
├── _quarto.yml                # Quarto konfigurationsfil
├── .quarto/                   # Quarto cache
├── Dyn_Risk_Pred_Course.Rproj # RStudio projektfil
├── renv.lock                  # R pakke versioner
└── .gitignore                 # Git ignore regler
```

---

## 📚 Undervisningsmateriale (lectures/)

Forelæsningsmapperne indeholder al det teoretiske undervisningsmateriale i **Quarto Markdown (.qmd)** format. 

| Fil | Beskrivelse |
|-----|------------|
| `index.qmd` | Startside/oversigt over kurset |
| `data_management.qmd` | Data håndtering - hvordan man strukturere og organiserer data |
| `data_preprocessing.qmd` | Data forbehandling - rengøring, transformation og forberedelse |
| `modelling.qmd` | Modellering - opbygning af forudsigelsesmodeller |
| `implementation.qmd` | Implementering - hvordan man implementerer modeller i praksis |

**Bemærk:** Quarto-filer (.qmd) kan renderes til HTML, PDF eller andre formater ved hjælp af Quarto CLI.

---

## 💻 Kode og Øvelser (Code/)

### exercise_solutions/

Denne mappe indeholder **færdige løsninger** til alle workshop-øvelserne. Løsningerne findes i `solutions/` undermappen og er organiseret efter workshop-nummer:

| Workshop | Filer | Beskrivelse |
|----------|-------|------------|
| **Workshop 0** | `Workshop_0_data_sources_asquisition.ipynb/.Rmd` | Data kilder og indhentning |
| **Workshop 1** | `Workshop_1_data_management.ipynb`, `.py`, `.R` | Data håndtering og forberedelse |
| **Workshop 2** | `Workshop_2_Modelling.ipynb`, `.py`, `.R`, `.md` | Modellering og evaluering |
| **Workshop 3** | `Workshop_3_Implementation.ipynb`, `.py`, `.R` | Implementering af modeller |

**Yderligere filer:**
- `modelling_simlpified.py` - Forenklet version af modellering
- `requirements.txt` - Python afhængigheder
- `Data_ready_for_workshop2_pytest.csv` - Test data

### Hjælpe scripts

| Fil | Formål |
|-----|--------|
| `request_fhir.py` | Python script til FHIR API anmodninger |
| `request_fhir.R` | R script til FHIR API anmodninger |
| `fhir_mock_server.py` | Mock server til test af FHIR integration |

### additional_code/

| Fil | Formål |
|-----|--------|
| `Metric_calculation.py` | Beregning af evalueringsmetrikker |

---

## 📊 Data (exercise_data/)

| Mappe/Fil | Beskrivelse |
|-----------|------------|
| `formatted_data/` | Forbehandlede datafiler klar til brug |
| `raw_data/` | Rå datafiler (uforbehandlede) |
| `PAD-introduction.html` | Introduktion til Peripheral Artery Disease (PAD) |

**Rodniveau datafiler:**
- `Data_ready_for_workshop2.csv` - Forberedt data til workshop 2
- `Data_ready_for_workshop2_test.csv` - Test dataset
- `Data_ready_for_workshop2_test.rds` - Test dataset i R format

---

## 🎨 Asset Mapper

| Mappe | Beskrivelse |
|-------|------------|
| `images/` | Billeder brugt i forelæsninger og dokumentation |
| `img/` | Yderligere billeder |
| `css/` | CSS stilarter til projektet |
| `cards/` | Flashcards eller kort til kursusmateriale |

---

## 🛠 Værktøjer og Teknologier

### Brugte Teknologier

| Teknologi | Formål |
|-----------|--------|
| **R** | Statistisk analyse og modellering |
| **Python** | Scripting, data forbehandling, maskinlæring |
| **Quarto** | Dokumentations generering (HTML/PDF) |
| **Jupyter Notebooks** | Interaktive øvelser og løsninger |
| **FHIR** | Sundhedsdata standard (HL7) |
| **RStudio** | Udviklingsmiljø (R) |
| **renv** | R pakke management |

### Projekt Konfiguration

- **`_quarto.yml`** - Quarto indstillinger for bygning af dokumentation
- **`renv.lock`** - Låste R pakke versioner
- **`.gitignore`** - Git ignore regler
- **`Dyn_Risk_Pred_Course.Rproj`** - RStudio projektfil

---

## 🚀 Hurtig Start Guide

### 1. Opsætning af Udviklingsmiljø

#### For R udvikling:
```bash
# Installer renv (hvis ikke allerede installeret)
install.packages("renv")

# Åben projektet i RStudio
# Kør for at genoprette pakker
renv::restore()
```

#### For Python udvikling:
```bash
# Opret virtuel miljø (anbefalet)
python -m venv venv

# Aktiver miljø (Windows)
venv\Scripts\activate

# Installer afhængigheder
pip install -r Code/exercise_solutions/solutions/requirements.txt
```

### 2. Bygning af Dokumentation

```bash
# Installer Quarto (hvis ikke installeret)
# Se https://quarto.org/docs/get-started/

# Byg alle forelæsninger
quarto render lectures/

# Byg specifik fil
quarto render lectures/index.qmd
```

### 3. Kørsel af Øvelser

- Åben Jupyter Notebooks i `Code/exercise_solutions/solutions/`
- Eller kør R scripts direkte i RStudio
- Python scripts kan køres med: `python Code/exercise_solutions/solutions/Workshop_2_Modelling.py`

---

## 📝 Arbejdsflow

### Typisk Udviklingsflow

1. **Rediger forelæsninger** → Rediger `.qmd` filer i `lectures/`
2. **Test kode** → Kør scripts i `Code/` mapperne
3. **Opdater data** → Placér nye datafiler i `exercise_data/`
4. **Byg dokumentation** → `quarto render`
5. **Test løsninger** → Verificér workshop løsninger
6. **Commit ændringer** → Git commit og push

---

## 🔍 Fejlfinding

### Almindelige Problemer

| Problem | Løsning |
|---------|---------|
| Quarto render fehler | Kontroller at alle afhængigheder er installeret (`quarto check`) |
| R pakker mangler | Kør `renv::restore()` |
| Python pakker mangler | Kør `pip install -r requirements.txt` |
| FHIR API fehler | Kontroller API endpoint og autentifikation |
| Data filer mangler | Kontroller stier i scripts |

---

## Github manual: 

1) Åben Rstudio/python med 'audited privileges'

2) Åben terminalen i R studio (Top bar -> Tools -> Terminal -> New Terminal)

3) skriv i terminalen: "git pull"

4) skriv i terminalen: "quarto preview lectures/index.qmd" for at se kurset i hjemmeside format.

5) Lav ændringer i kursus filenere eller kode til øvelser

6) (HVIS DER BLIVER ÆNDRET NOGET) Skriv i terminalen:
    6.1 'git add .' (Tilføj alle ændringer)
    6.2 'git commit -m "skriv en kommentar"' (Commit ændringer med en kommentar)
    6.3 'git push' (Skub ændringerne til Github)

---

*Dokument oprettet: 12-05-2026*
*Senest opdateret: 12-05-2026*
