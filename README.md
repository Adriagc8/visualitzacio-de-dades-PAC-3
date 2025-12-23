# PAC 3 - Narrativa de Dades amb Visualització

## Descripció del Projecte

Aquest projecte implementa una visualització narrativa de dades sobre el risc de cancel·lació de reserves hoteleres a Portugal (2015-2017). La història explora com el volum, el tipus d'hotel i el comportament del client influeixen en el risc de cancel·lació, amb especial atenció a les diferències entre reserves locals i internacionals.

## Estructura del Projecte

El projecte està dividit en dos components principals:

1. **Component 1: Analítica Visual (EDA)** - Notebook R que neteja les dades i realitza l'anàlisi exploratòria
2. **Component 2: Visualització Narrativa** - Script Python que genera el dashboard interactiu i el PDF

## Requisits Previs

### Per al Component 1 (R):
- **R** (versió 4.0 o superior)
- **RStudio Desktop**
- **Packages R necessaris** (s'instal·len automàticament al executar el notebook):
  - `ggplot2`
  - `fitdistrplus`
  - `MASS`
  - `survival`
  - `ggstatsplot`
  - `tidyverse`
  - `lubridate`
  - `ggmosaic`

### Per al Component 2 (Python):
- **Python** (versió 3.7 o superior)
- **pip** (gestor de paquets de Python)

## Instruccions d'Instal·lació i Execució

### Pas 1: Preparar l'entorn R

1. **Instal·lar R i RStudio:**
   - Descarregar R des de: https://cran.r-project.org/
   - Descarregar RStudio Desktop des de: https://posit.co/downloads/
   - Seguir les instruccions d'instal·lació per al teu sistema operatiu

2. **Verificar la instal·lació:**
   - Obrir RStudio
   - Verificar que R està correctament configurat

### Pas 2: Executar el Notebook R (Component 1)

1. **Descarregar els fitxers necessaris:**
   - `hotel_bookings.csv` - Dataset original
   - `hotel_bookings.Rmd` - Notebook d'anàlisi visual

2. **Posar tots els fitxers a la mateixa carpeta**

3. **Obrir el notebook:**
   - Fer doble clic sobre `hotel_bookings.Rmd` (s'obrirà a RStudio)
   - O obrir RStudio manualment i obrir el fitxer des del menú

4. **Instal·lar packages (si cal):**
   - Al executar el notebook per primera vegada, RStudio demanarà instal·lar els packages necessaris
   - Seguir les instruccions per instal·lar-los

5. **Executar el notebook:**
   - Anar al menú "Code" → "Run Region" → "Run All"
   - O utilitzar la icona "Run All" de la barra d'eines
   - Això executarà totes les cel·les del notebook, incloent la neteja de dades

6. **Verificar la generació del fitxer net:**
   - Al final de l'execució, s'hauria de generar el fitxer `hotel_bookings_clean.csv`
   - Aquest fitxer conté les dades netes que s'utilitzaran per a la visualització

### Pas 3: Preparar l'entorn Python

1. **Verificar Python:**
   ```bash
   python --version
   # O
   python3 --version
   ```

2. **Instal·lar les llibreries Python necessàries:**
   
   **utilitzant requirements.txt:**
   ```bash
   pip install -r requirements.txt
   # O
   pip3 install -r requirements.txt
   ```
   
   Això instal·larà automàticament totes les dependències necessàries:
   - `pandas` (>=2.0.0) - Manipulació i anàlisi de dades
   - `plotly` (>=5.18.0) - Visualitzacions interactives
   - `numpy` (>=1.24.0) - Càlculs numèrics
   - `kaleido` (>=0.2.1) - Exportació de gràfics Plotly a imatges (necessari per al PDF)
   - `reportlab` (>=4.0.0) - Generació de PDFs
   
   **Opció alternativa (instal·lació manual):**
   ```bash
   pip install pandas numpy plotly reportlab kaleido
   # O
   pip3 install pandas numpy plotly reportlab kaleido
   ```

### Pas 4: Executar el Script Python (Component 2)

1. **Verificar que existeix `hotel_bookings_clean.csv`:**
   - Aquest fitxer hauria d'haver-se generat al Pas 2
   - Si no existeix, tornar al Pas 2 i executar el notebook R

2. **Executar el script:**
   ```bash
   python visualització_tipus_storytelling.py
   # O
   python3 visualització_tipus_storytelling.py
   ```

3. **El script generarà:**
   - `index.html` - Dashboard interactiu amb visualitzacions avançades
   - `pac3.pdf` - Versió PDF del dashboard

### Pas 5: Visualitzar els Resultats

1. **Obrir el dashboard interactiu:**
   - Fer doble clic sobre `index.html`
   - O obrir-lo amb qualsevol navegador web modern

2. **Navegar pel dashboard:**
   - El dashboard està organitzat en 5 actes narratius
   - Utilitzar el menú fixe a la part superior per saltar entre seccions
   - Explorar les visualitzacions interactives (tooltips, zoom, pan)

3. **Revisar el PDF:**
   - Obrir `pac3.pdf` amb qualsevol lector de PDFs
   - Conté la mateixa informació que l'HTML però en format estàtic

## 📁 Estructura de Fitxers

```
PAC 3/
├── hotel_bookings.csv              # Dataset original
├── hotel_bookings.Rmd              # Notebook R (Component 1 - EDA)
├── hotel_bookings_clean.csv       # Dataset net (generat pel notebook R)
├── visualització_tipus_storytelling.py  # Script Python (Component 2)
├── requirements.txt                # Dependències Python
├── index.html                      # Dashboard interactiu (generat)
├── pac3.pdf                        # Dashboard PDF (generat)
└── README.md                       # Aquest fitxer
```

## Visualitzacions Incloses

El dashboard inclou les següents visualitzacions avançades:

1. **Stacked Area Chart** - Evolució temporal del volum de reserves per hotel
2. **Dumbbell Plot** - Comparació directa de taxes de cancel·lació entre hotels
3. **Treemap** - Impacte de risc per país (àrea = volum, color = taxa)
4. **Sankey Diagram** - Flux complet de reserves (Origen → Hotel → Estat)
5. **Violin Plot** - Distribució de lead time per origen
6. **Histograma** - Distribució de canvis a la reserva
7. **Barres Apilades** - Tipus de dipòsit per origen


## Notes Importants

- **Ordre d'execució:** És **imprescindible** executar primer el notebook R abans del script Python
- **Consistència de dades:** Les dades netes generades a l'EDA s'utilitzen directament a la visualització, assegurant consistència entre components
- **Dependències:** El script Python requereix que `hotel_bookings_clean.csv` existeixi; si no, mostrarà un error clar

## Autor

Adria Gonzalez Copado
