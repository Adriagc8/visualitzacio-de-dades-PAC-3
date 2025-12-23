"""
Dashboard narratiu PAC 3 - Visualització de Dades (VERSIÓ 2 i 3)
Història: "Les reserves locals (PRT) cancel·len més que les internacionals"

VERSIÓ 2: Visualitzacions avançades
- Sankey diagram (flux Origen → Hotel → Cancel·lació)
- Treemap (impacte de risc per país)
- Dumbbell Plot (diferència de risc)
- Violin Plot, Histograma i Barres apilades

VERSIÓ 3: Navegació millorada (generada a partir de V2)
- Menú de navegació fixe amb enllaços als actes
- Indicador de progrés de scroll
- Botó "Tornar a dalt"
- Transicions suaus i hover effects
"""

import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from plotly.offline import plot
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT
import os

# ============================================================================
# CONFIGURACIÓ I CONSTANTS
# ============================================================================

# Paleta de colors semàntica (amb saturació reduïda per look més professional)
COLORS = {
    'local': '#C0392B',      # Vermell (PRT) - saturació reduïda ~15%
    'international': '#2980B9',  # Blau - saturació reduïda ~15%
    'city_hotel': '#7D3C98',     # Porpra - saturació reduïda ~15%
    'resort_hotel': '#229954',   # Verd - saturació reduïda ~15%
    'canceled': '#C0392B',       # Càlid
    'not_canceled': '#2980B9'    # Fred
}

# ============================================================================
# FASE 1: NETEGA DE DADES
# ============================================================================

# NOTA: La funció clean_data() s'ha eliminat perquè la neteja de dades
# es fa al notebook R (hotel_bookings.Rmd) - Component 1 de la PAC.
# Les dades netes es generen allà i es guarden a hotel_bookings_clean.csv.
# Això assegura consistència entre l'EDA i la visualització final.

# ============================================================================
# FASE 2: TAULES INTERMÈDIES
# ============================================================================

def create_tbl_volume_hotel_year(df):
    """TAULA 1: Volum de reserves per hotel i any"""
    tbl = df.groupby(['hotel', 'arrival_date_year']).size().reset_index(name='n_bookings')
    return tbl

def create_tbl_cancel_rate_hotel_year(df):
    """TAULA 2: Taxa de cancel·lació per hotel i any"""
    tbl = df.groupby(['hotel', 'arrival_date_year']).agg({
        'is_canceled': ['count', 'sum']
    }).reset_index()
    tbl.columns = ['hotel', 'arrival_date_year', 'n_bookings', 'n_canceled']
    tbl['cancel_rate'] = tbl['n_canceled'] / tbl['n_bookings']
    tbl['cancel_rate_pct'] = tbl['cancel_rate'] * 100
    return tbl

def create_tbl_cancel_rate_country(df, min_bookings=1000):
    """TAULA 3: Taxa de cancel·lació per país (amb volum)"""
    # Filtrar països amb mínim de reserves
    country_counts = df.groupby('country').size()
    valid_countries = country_counts[country_counts >= min_bookings].index
    
    df_filtered = df[df['country'].isin(valid_countries)].copy()
    
    tbl = df_filtered.groupby('country').agg({
        'is_canceled': ['count', 'sum']
    }).reset_index()
    tbl.columns = ['country', 'n_bookings', 'n_canceled']
    tbl['cancel_rate'] = tbl['n_canceled'] / tbl['n_bookings']
    tbl['cancel_rate_pct'] = tbl['cancel_rate'] * 100
    tbl = tbl.sort_values('cancel_rate_pct', ascending=False)
    return tbl

def create_tbl_country_hotel_cancel(df, min_bookings=1000):
    """TAULA 4: País × hotel (estructura bubble/heatmap)"""
    # Filtrar països amb mínim de reserves
    country_counts = df.groupby('country').size()
    valid_countries = country_counts[country_counts >= min_bookings].index
    
    df_filtered = df[df['country'].isin(valid_countries)].copy()
    
    tbl = df_filtered.groupby(['country', 'hotel']).agg({
        'is_canceled': ['count', 'sum']
    }).reset_index()
    tbl.columns = ['country', 'hotel', 'n_bookings', 'n_canceled']
    tbl['cancel_rate'] = tbl['n_canceled'] / tbl['n_bookings']
    tbl['cancel_rate_pct'] = tbl['cancel_rate'] * 100
    return tbl

def create_tbl_origin_hotel_cancel(df):
    """TAULA 5: Local vs Internacional per hotel"""
    tbl = df.groupby(['origin_group', 'hotel']).agg({
        'is_canceled': ['count', 'sum']
    }).reset_index()
    tbl.columns = ['origin_group', 'hotel', 'n_bookings', 'n_canceled']
    tbl['cancel_rate'] = tbl['n_canceled'] / tbl['n_bookings']
    tbl['cancel_rate_pct'] = tbl['cancel_rate'] * 100
    return tbl

def create_tbl_sankey_flow(df):
    """TAULA 6: Dades per Sankey diagram (Origen → Hotel → Cancel·lació)"""
    # Agrupar per origen, hotel i estat de cancel·lació
    flow_data = df.groupby(['origin_group', 'hotel', 'is_canceled']).size().reset_index(name='count')
    
    # Crear etiquetes per estat
    flow_data['status'] = flow_data['is_canceled'].apply(lambda x: 'Cancel·lada' if x == 1 else 'No cancel·lada')
    
    return flow_data

# ============================================================================
# FASE 3: GRÀFICS PLOTLY (VERSIÓ AVANÇADA)
# ============================================================================

def create_graph1_volume_hotel_year(tbl):
    """
    ACTE 1: Distribució del volum de reserves per tipus d'hotel (2015–2017)
    Stacked Area Chart: mostra evolució temporal i pes relatiu
    """
    # Preparar dades per Stacked Area Chart
    hotels = sorted(tbl['hotel'].unique())
    years = sorted(tbl['arrival_date_year'].unique())
    
    # Colors coherents amb la resta del dashboard
    hotel_colors = {
        'City Hotel': COLORS['city_hotel'],   # Porpra
        'Resort Hotel': COLORS['resort_hotel']  # Verd
    }
    
    # Preparar dades per cada hotel i any
    fig = go.Figure()
    
    # Calcular totals per any per percentatges
    year_totals = {}
    for year in years:
        year_totals[year] = tbl[tbl['arrival_date_year'] == year]['n_bookings'].sum()
    
    # Preparar dades per a cada hotel
    hotel_data_dict = {}
    hover_texts_dict = {}
    pct_dict = {}
    
    for hotel in hotels:
        hotel_data = []
        hover_texts = []
        pct_year_list = []
        
        for year in years:
            data = tbl[(tbl['hotel'] == hotel) & (tbl['arrival_date_year'] == year)]
            if len(data) > 0:
                n_bookings = data['n_bookings'].values[0]
                hotel_data.append(n_bookings)
                year_total = year_totals[year]
                pct_year = (n_bookings / year_total * 100) if year_total > 0 else 0
                
                hover_texts.append(
                    f'<b>{hotel} - {year}</b><br>' +
                    f'Reserves: {n_bookings:,}<br>' +
                    f'% dins de {year}: {pct_year:.1f}%<br>' +
                    f'Total {year}: {year_total:,} reserves'
                )
                pct_year_list.append(pct_year)
            else:
                hotel_data.append(0)
                hover_texts.append('')
                pct_year_list.append(0)
        
        hotel_data_dict[hotel] = hotel_data
        hover_texts_dict[hotel] = hover_texts
        pct_dict[hotel] = pct_year_list
    
    # Crear traces per cada hotel (apilades)
    for hotel in hotels:
        fig.add_trace(go.Scatter(
            x=years,
            y=hotel_data_dict[hotel],
            mode='lines',
            name=hotel,
            stackgroup='one',  # Apilar les àrees
            fill='tonexty' if hotel != hotels[0] else 'tozeroy',
            line=dict(width=2, color=hotel_colors[hotel]),
            fillcolor=hotel_colors[hotel],
            hovertemplate='%{hovertext}<extra></extra>',
            hovertext=hover_texts_dict[hotel]
        ))
    
    # Afegir percentatges com a anotacions dins de cada any (després de crear totes les traces)
    for i, year in enumerate(years):
        for hotel in hotels:
            if hotel_data_dict[hotel][i] > 0 and pct_dict[hotel][i] > 0:
                # Calcular la base acumulada per a aquest any
                base_y = 0
                for prev_hotel in hotels:
                    if prev_hotel == hotel:
                        break
                    base_y += hotel_data_dict[prev_hotel][i]
                
                # Posició Y: base + percentatge de l'alçada de l'àrea
                # Per City Hotel (primer): 75% de l'alçada
                # Per Resort Hotel (segon): 25% de l'alçada
                if hotel == hotels[0]:  # City Hotel (a dalt)
                    y_pos = base_y + hotel_data_dict[hotel][i] * 0.75
                else:  # Resort Hotel (a baix)
                    y_pos = base_y + hotel_data_dict[hotel][i] * 0.25
                
                fig.add_annotation(
                    text=f'{pct_dict[hotel][i]:.0f}%',
                    x=year,
                    y=y_pos,
                    xref='x',
                    yref='y',
                    showarrow=False,
                    font=dict(size=11, color='white'),
                    bgcolor='rgba(0, 0, 0, 0.6)',
                    bordercolor='white',
                    borderwidth=1,
                    borderpad=4
                )
    
    # Calcular estadístiques per anotació editorial
    total_all = tbl['n_bookings'].sum()
    city_total = tbl[tbl['hotel'] == 'City Hotel']['n_bookings'].sum()
    city_pct = (city_total / total_all * 100) if total_all > 0 else 0
    
    # Afegir anotació editorial sobre City Hotel
    fig.add_annotation(
        text=f"<b>El City Hotel concentra prop de dos terços del volum cada any</b>",
        xref="paper", yref="paper",
        x=0.5, y=0.95,
        xanchor="center", yanchor="top",
        bgcolor='rgba(125, 60, 152, 0.9)',  # Porpra coherent amb City Hotel
        bordercolor='white',
        borderwidth=2,
        font=dict(size=13, color='white'),
        align='center',
        showarrow=False
    )
    
    fig.update_layout(
        title={
            'text': 'Distribució del volum de reserves per tipus d\'hotel (2015–2017)<br><sub>El City Hotel concentra de manera consistent la major part del volum</sub>',
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 20}
        },
        xaxis=dict(
            title='Any',
            tickmode='linear',
            tick0=2015,
            dtick=1,
            tickfont=dict(size=12)
        ),
        yaxis=dict(
            title='Nombre de reserves',
            tickfont=dict(size=12),
            gridcolor='rgba(0, 0, 0, 0.1)',
            gridwidth=1
        ),
        template='plotly_white',
        height=600,
        margin=dict(l=60, r=20, t=120, b=60),
        legend=dict(
            orientation='h',
            yanchor='bottom',
            y=1.02,
            xanchor='right',
            x=1,
            font=dict(size=12)
        ),
        hovermode='x unified'
    )
    
    return fig

def create_graph2_cancel_rate_hotel_year(tbl):
    """
    ACTE 2: La bretxa de risc entre hotels
    Dumbbell Plot: mostra la diferència de taxa de cancel·lació entre City i Resort
    NOVA VISUALITZACIÓ AVANÇADA
    """
    fig = go.Figure()
    
    years = sorted(tbl['arrival_date_year'].unique())
    
    # Preparar dades per Dumbbell Plot
    resort_rates = []
    city_rates = []
    resort_bookings = []
    city_bookings = []
    resort_canceled = []
    city_canceled = []
    differences = []
    
    for year in years:
        data_year = tbl[tbl['arrival_date_year'] == year]
        
        # Resort Hotel (punt esquerre)
        resort_data = data_year[data_year['hotel'] == 'Resort Hotel']
        if len(resort_data) > 0:
            resort_rates.append(resort_data['cancel_rate_pct'].values[0])
            resort_bookings.append(int(resort_data['n_bookings'].values[0]))
            resort_canceled.append(int(resort_data['n_canceled'].values[0]))
        else:
            resort_rates.append(0)
            resort_bookings.append(0)
            resort_canceled.append(0)
        
        # City Hotel (punt dret)
        city_data = data_year[data_year['hotel'] == 'City Hotel']
        if len(city_data) > 0:
            city_rates.append(city_data['cancel_rate_pct'].values[0])
            city_bookings.append(int(city_data['n_bookings'].values[0]))
            city_canceled.append(int(city_data['n_canceled'].values[0]))
        else:
            city_rates.append(0)
            city_bookings.append(0)
            city_canceled.append(0)
        
        # Calcular diferència
        diff = city_rates[-1] - resort_rates[-1]
        differences.append(diff)
    
    # Crear traces per al Dumbbell Plot
    # 1. Línies que uneixen els punts (dumbbell)
    for i, year in enumerate(years):
        fig.add_trace(go.Scatter(
            x=[resort_rates[i], city_rates[i]],
            y=[year, year],
            mode='lines',
            line=dict(color='#95A5A6', width=3, dash='solid'),
            showlegend=False,
            hoverinfo='skip'
        ))
    
    # 2. Punts per Resort Hotel (esquerra, verd)
    fig.add_trace(go.Scatter(
        x=resort_rates,
        y=years,
        mode='markers+text',
        name='Resort Hotel',  # Nom sense cap font personalitzada
        legendgroup='hotels',
        marker=dict(
            size=12,
            color=COLORS['resort_hotel'],  # Verd (coherent amb dashboard)
            line=dict(width=2, color='white')
        ),
        text=[f'{r:.1f}%' for r in resort_rates],
        textposition='middle left',
        textfont=dict(size=10, color=COLORS['resort_hotel']),
        hovertemplate='<b>Resort Hotel - %{y}</b><br>' +
                      'Taxa: %{x:.1f}%<br>' +
                      'Reserves: %{customdata[0]:,}<br>' +
                      'Cancel·lades: %{customdata[1]:,}<br>' +
                      '<extra></extra>',
        customdata=list(zip(resort_bookings, resort_canceled))
    ))
    
    # 3. Punts per City Hotel (dreta, porpra) - més visible
    fig.add_trace(go.Scatter(
        x=city_rates,
        y=years,
        mode='markers+text',
        name='City Hotel',  # Nom sense cap font personalitzada
        legendgroup='hotels',
        marker=dict(
            size=15,  # Punt més gran (era 12)
            color=COLORS['city_hotel'],  # Porpra (coherent amb dashboard)
            line=dict(width=3, color='white')  # Contorn més marcat (era 2)
        ),
        text=[f'{c:.1f}%' for c in city_rates],
        textposition='middle right',
        textfont=dict(size=10, color=COLORS['city_hotel']),
        hovertemplate='<b>City Hotel - %{y}</b><br>' +
                      'Taxa: %{x:.1f}%<br>' +
                      'Reserves: %{customdata[0]:,}<br>' +
                      'Cancel·lades: %{customdata[1]:,}<br>' +
                      '<extra></extra>',
        customdata=list(zip(city_bookings, city_canceled))
    ))
    
    # 4. Anotacions amb diferències (només per anys amb diferència significativa)
    annotations = []
    for i, year in enumerate(years):
        if abs(differences[i]) > 5:  # Només si la diferència és >5 punts
            # Posició al mig de la línia
            mid_x = (resort_rates[i] + city_rates[i]) / 2
            diff_text = f"+{differences[i]:.1f} pp" if differences[i] > 0 else f"{differences[i]:.1f} pp"
            
            annotations.append(dict(
                x=mid_x,
                y=year,
                text=diff_text,
                showarrow=False,
                font=dict(size=11, color='#2c3e50', family='Arial'),  # Canviat de Arial Black a Arial
                bgcolor='rgba(255,255,255,0.9)',
                bordercolor='#34495e',
                borderwidth=1,
                align='center'
            ))
    
    # Calcular diferència mitjana
    avg_diff = np.mean(differences)
    
    # Afegir anotació general sobre el patró
    fig.add_annotation(
        text=f"<b>Diferència mitjana:</b><br>{avg_diff:.1f} punts percentuals<br>en tots els anys",
        xref="paper", yref="paper",
        x=0.98, y=0.98,
        xanchor="right", yanchor="top",
        bgcolor='rgba(192, 57, 43, 0.9)',
        bordercolor='white',
        borderwidth=2,
        font=dict(size=11, color='white'),
        align='right',
        showarrow=False
    )
    
    fig.update_layout(
        title={
            'text': 'La taxa de cancel·lació és sistemàticament més alta al City Hotel<br><sub>Comparació directa City vs Resort per any (2015–2017) | La longitud de la línia indica la diferència de risc</sub>',
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 20}
        },
        xaxis_title='Taxa de cancel·lació (%)',
        yaxis_title='Any',
        xaxis=dict(
            range=[25, 50],  # Escala fins a 50% (suficient per les dades)
            title_standoff=5,
            showgrid=True,
            gridcolor='#ecf0f1',
            gridwidth=0.5,  # Grid més sutil
            dtick=5,  # Línies cada 10% (0, 10, 20, 30, 40, 50)
            showline=True,
            linecolor='#bdc3c7',
            linewidth=1
        ),
        yaxis=dict(
            tickmode='array',
            tickvals=years,
            ticktext=[str(y) for y in years],
            showgrid=False  # Sense grid vertical per no competir amb les línies
        ),
        template='plotly_white',
        height=400,
        hovermode='closest',
        showlegend=True,
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1,
            # No especificar font per evitar el prefix "Aa" - usarà la font per defecte
            itemclick=False,
            itemdoubleclick=False,
            traceorder='normal',
            bgcolor='rgba(255,255,255,0.8)',
            bordercolor='rgba(0,0,0,0.2)',
            borderwidth=1
        ),
        annotations=annotations
    )
    
    return fig

def create_graph3_country_cancel_rate(tbl_country, tbl_country_hotel):
    """
    ACTE 3: Vista analítica secundària - Comparació entre mercats
    Bubble chart com a vista de suport (no clímax)
    """
    # Determinar hotel dominant per país
    hotel_dominant = {}
    for country, group in tbl_country_hotel.groupby('country'):
        hotel_dominant[country] = group.loc[group['n_bookings'].idxmax(), 'hotel']
    
    # Afegir hotel dominant a la taula principal
    tbl_country['hotel_dominant'] = tbl_country['country'].map(hotel_dominant)
    tbl_country['is_prt'] = tbl_country['country'] == 'PRT'
    
    # Ordenar per taxa de cancel·lació (descendent) - PRT a dalt
    tbl_country = tbl_country.sort_values('cancel_rate_pct', ascending=False)
    
    # Calcular mitjana global
    total_canceled = tbl_country['n_canceled'].sum()
    total_bookings = tbl_country['n_bookings'].sum()
    global_avg = (total_canceled / total_bookings * 100) if total_bookings > 0 else 0
    
    # Colors: PRT destacat, resta en gris clar amb opacitat baixa
    colors = []
    line_colors = []
    opacities = []
    for _, row in tbl_country.iterrows():
        if row['is_prt']:
            colors.append(COLORS['local'])  # Vermell per PRT
            line_colors.append('white')
            opacities.append(0.9)  # Opacitat alta per PRT
        else:
            colors.append('#BDC3C7')  # Gris clar per la resta
            line_colors.append('#95A5A6')
            opacities.append(0.4)  # Opacitat baixa per la resta
    
    # Calcular mida dels bubbles (perceptual, no extrema)
    max_size = max(tbl_country['n_bookings'])
    min_diameter = 15
    max_diameter = 50  # Reduït per evitar mides extremes
    sizes_list = (min_diameter + (np.sqrt(tbl_country['n_bookings'] / max_size) * (max_diameter - min_diameter))).tolist()
    
    # Formatar dades per al tooltip
    cancel_rates_formatted = [f"{rate:.1f}%" for rate in tbl_country['cancel_rate_pct']]
    bookings_formatted = [f"{n:,}" for n in tbl_country['n_bookings']]
    canceled_formatted = [f"{n:,}" for n in tbl_country['n_canceled']]
    
    # Calcular impacte (cancel·lacions absolutes) per destacar PRT
    prt_row = tbl_country[tbl_country['country'] == 'PRT']
    prt_canceled = prt_row['n_canceled'].values[0] if len(prt_row) > 0 else 0
    prt_rate = prt_row['cancel_rate_pct'].values[0] if len(prt_row) > 0 else 0
    prt_bookings = prt_row['n_bookings'].values[0] if len(prt_row) > 0 else 0
    
    # Preparar text per als bubbles: només PRT i països grans
    bubble_texts = []
    bubble_text_sizes = []
    for idx, row in tbl_country.iterrows():
        country = row['country']
        bookings = row['n_bookings']
        # Mostrar text només per PRT i països amb >10k reserves
        if row['is_prt']:
            bubble_texts.append(f"{bookings:,}")
            bubble_text_sizes.append(11)
        elif bookings > 10000:  # GBR, FRA, etc.
            bubble_texts.append(f"{bookings:,}")
            bubble_text_sizes.append(9)
        else:
            bubble_texts.append('')  # Sense text per la resta
            bubble_text_sizes.append(9)
    
    # Line widths: més gruixut per PRT
    line_widths = [3 if row['is_prt'] else 1 for _, row in tbl_country.iterrows()]
    
    # Convertir Series a llistes per evitar problemes de serialització
    x_values = tbl_country['cancel_rate_pct'].tolist()
    y_values = tbl_country['country'].tolist()
    
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=x_values,
        y=y_values,
        mode='markers+text',
        marker=dict(
            size=sizes_list,
            sizemode='diameter',  # Diàmetre mode - més directe i visible
            color=colors,
            line=dict(width=line_widths, color=line_colors),
            opacity=opacities
        ),
        text=bubble_texts,
        textposition='middle center',
        textfont=dict(size=bubble_text_sizes, color='white'),
        hovertemplate='<b>%{y}</b><br>' +
                      'Taxa cancel·lació: %{customdata[0]}<br>' +
                      'Reserves: %{customdata[1]}<br>' +
                      'Cancel·lades: %{customdata[2]}<br>' +
                      '<extra></extra>',
        customdata=list(zip(
            cancel_rates_formatted,
            bookings_formatted,
            canceled_formatted
        )),
        showlegend=False
    ))
    
    # Afegir línia vertical per mitjana global (molt fina)
    fig.add_vline(
        x=global_avg,
        line_dash="dash",
        line_color="#7f8c8d",
        line_width=1,
        annotation_text=f"Mitjana global: {global_avg:.1f}%",
        annotation_position="top",
        annotation_font_size=10,
        annotation_font_color="#7f8c8d"
    )
    
    fig.update_layout(
        title={
            'text': 'Comparació analítica entre mercats<br><sub>Relació entre taxa de cancel·lació (%) i volum de reserves (mida del punt) | Vista analítica de suport</sub>',
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 18}
        },
        xaxis_title='Taxa de cancel·lació (%)',
        yaxis_title='País',
        xaxis=dict(
            range=[15, 65],  # Escala compacta
            showgrid=True,
            gridcolor='#ecf0f1',
            gridwidth=0.5,
            dtick=10,  # Ticks cada 10% (20, 30, 40, 50, 60)
            showline=True,
            linecolor='#bdc3c7',
            linewidth=1
        ),
        yaxis=dict(
            categoryorder='array',
            categoryarray=y_values,  # Ordenat per taxa descendent
            showgrid=False
        ),
        template='plotly_white',
        height=600,
        hovermode='closest',
        showlegend=False,
        margin=dict(l=100, r=100, t=100, b=50)
    )
    
    return fig

def create_graph3b_treemap_country(tbl_country):
    """
    ACTE 3B: Treemap jeràrquic per país
    Vista alternativa d'impacte de risc per mercat
    Àrea = volum de reserves, Color = taxa de cancel·lació
    """
    # Preparar dades per al treemap
    # Crear jerarquia: País → volum i color per taxa
    # Passar taxa com a customdata per poder-la mostrar al texttemplate
    cancel_rates = tbl_country['cancel_rate_pct'].tolist()
    countries = tbl_country['country'].tolist()
    bookings = tbl_country['n_bookings'].tolist()
    
    # Calcular total per determinar quins rectangles són petits
    total_bookings = sum(bookings)
    
    # Preparar text template: només país per rectangles grans, només codi per petits
    text_templates = []
    for i, country in enumerate(countries):
        pct_total = (bookings[i] / total_bookings * 100) if total_bookings > 0 else 0
        # Si representa >3% del total, mostrar nom complet, sinó només codi
        if pct_total > 3:
            text_templates.append(f'<b>{country}</b><br>{bookings[i]:,}<br>Taxa: {cancel_rates[i]:.1f}%')
        else:
            # Només mostrar codi del país
            text_templates.append(f'<b>{country}</b>')
    
    # Escala de color més perceptual i progressiva (verd → groc → vermell)
    # Més punts intermedis per transició més suau
    colorscale_perceptual = [
        [0.0, '#2ECC71'],    # Verd clar (baix risc)
        [0.2, '#27AE60'],    # Verd (baix-mitjà risc)
        [0.4, '#F1C40F'],    # Groc (risc mitjà)
        [0.6, '#E67E22'],    # Taronja (risc mitjà-alt)
        [0.8, '#E74C3C'],    # Vermell clar (alt risc)
        [1.0, '#C0392B']     # Vermell fosc (molt alt risc)
    ]
    
    fig = go.Figure(go.Treemap(
        labels=countries,
        parents=[''] * len(tbl_country),  # Tots són fills del root
        values=bookings,  # Àrea proporcional al volum
        marker=dict(
            colors=cancel_rates,  # Color per taxa
            colorscale=colorscale_perceptual,  # Escala més perceptual
            showscale=True,
            colorbar=dict(
                title=dict(text="Taxa cancel·lació (%)", side="right"),
                tickformat='.1f'
            ),
            line=dict(width=2, color='white')
        ),
        text=text_templates,
        textinfo='text',
        hovertemplate='<b>%{label}</b><br>' +
                      'Reserves: %{value:,}<br>' +
                      'Taxa cancel·lació: %{color:.1f}%<br>' +
                      '<extra></extra>',
        branchvalues='total'
    ))
    
    # Destacar PRT amb anotació
    prt_row = tbl_country[tbl_country['country'] == 'PRT']
    if len(prt_row) > 0:
        prt_rate = prt_row['cancel_rate_pct'].values[0]
        prt_bookings = prt_row['n_bookings'].values[0]
        fig.add_annotation(
            text=f"<b>PRT: Gran volum ({prt_bookings:,})<br>i alta taxa ({prt_rate:.1f}%)</b>",
            xref="paper", yref="paper",
            x=0.02, y=0.98,
            xanchor="left", yanchor="top",
            bgcolor='rgba(192, 57, 43, 0.9)',
            bordercolor='white',
            borderwidth=2,
            font=dict(size=12, color='white'),
            align='left',
            showarrow=False
        )
    
    fig.update_layout(
        title={
            'text': 'Impacte de risc per mercat (Treemap)<br><sub>Àrea = volum de reserves | Color = taxa de cancel·lació | PRT destaca per volum i risc</sub>',
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 18}
        },
        template='plotly_white',
        height=500,
        margin=dict(l=20, r=20, t=100, b=20)
    )
    
    return fig

def create_graph4_sankey_flow(df):
    """
    ACTE 4: Sankey diagram - Flux de reserves
    Origen → Tipus d'hotel → Estat final (cancel·lada / no)
    NOVA VISUALITZACIÓ AVANÇADA
    """
    # Preparar dades per Sankey
    flow_data = create_tbl_sankey_flow(df)
    
    # Crear nodes únics amb índexs
    # Nivell 1: Origen
    origins = sorted(flow_data['origin_group'].unique())
    # Nivell 2: Hotel
    hotels = sorted(flow_data['hotel'].unique())
    # Nivell 3: Estat
    statuses = sorted(flow_data['status'].unique())
    
    # Crear llista de nodes (origen + hotel + estat)
    all_nodes = origins + hotels + statuses
    node_indices = {node: i for i, node in enumerate(all_nodes)}
    
    # Crear enllaços
    # Enllaços Origen → Hotel
    source = []
    target = []
    value = []
    link_labels = []
    
    # Colors per origen
    origin_colors = {
        'Local (PRT)': COLORS['local'],
        'International': COLORS['international']
    }
    
    # Colors per hotel
    hotel_colors = {
        'City Hotel': COLORS['city_hotel'],
        'Resort Hotel': COLORS['resort_hotel']
    }
    
    # Colors per estat - contrast augmentat
    status_colors = {
        'Cancel·lada': '#C0392B',  # Vermell més intens per millor contrast
        'No cancel·lada': '#2980B9'  # Blau més intens per millor contrast
    }
    
    # Enllaços Origen → Hotel
    for origin in origins:
        for hotel in hotels:
            data = flow_data[(flow_data['origin_group'] == origin) & (flow_data['hotel'] == hotel)]
            if len(data) > 0:
                total = data['count'].sum()
                source.append(node_indices[origin])
                target.append(node_indices[hotel])
                value.append(total)
                # link_colors no s'utilitza (simplificat)
                link_labels.append(f"{origin} → {hotel}: {total:,}")
    
    # Enllaços Hotel → Estat
    for hotel in hotels:
        for status in statuses:
            data = flow_data[(flow_data['hotel'] == hotel) & (flow_data['status'] == status)]
            if len(data) > 0:
                total = data['count'].sum()
                source.append(node_indices[hotel])
                target.append(node_indices[status])
                value.append(total)
                # link_colors no s'utilitza (simplificat)
                link_labels.append(f"{hotel} → {status}: {total:,}")
    
    # Crear colors de nodes
    node_colors = []
    for node in all_nodes:
        if node in origins:
            node_colors.append(origin_colors[node])
        elif node in hotels:
            node_colors.append(hotel_colors[node])
        else:
            node_colors.append(status_colors[node])
    
    # Crear Sankey (versió simplificada per evitar problemes de permisos)
    # Usar dict() directament en lloc de go.Sankey() per evitar problemes d'importació
    sankey_data = dict(
        type='sankey',
        node=dict(
            pad=15,
            thickness=20,
            line=dict(color="black", width=0.5),
            label=all_nodes,
            color=node_colors
        ),
        link=dict(
            source=source,
            target=target,
            value=value
        )
    )
    
    fig = go.Figure(data=[sankey_data])
    
    # Calcular estadístiques per anotacions
    local_canceled = flow_data[(flow_data['origin_group'] == 'Local (PRT)') & 
                               (flow_data['status'] == 'Cancel·lada')]['count'].sum()
    local_total = flow_data[flow_data['origin_group'] == 'Local (PRT)']['count'].sum()
    local_rate = (local_canceled / local_total * 100) if local_total > 0 else 0
    
    intl_canceled = flow_data[(flow_data['origin_group'] == 'International') & 
                              (flow_data['status'] == 'Cancel·lada')]['count'].sum()
    intl_total = flow_data[flow_data['origin_group'] == 'International']['count'].sum()
    intl_rate = (intl_canceled / intl_total * 100) if intl_total > 0 else 0
    
    # Identificar flux dominant: Local → City Hotel → Cancel·lada
    local_city_canceled = flow_data[(flow_data['origin_group'] == 'Local (PRT)') & 
                                    (flow_data['hotel'] == 'City Hotel') & 
                                    (flow_data['status'] == 'Cancel·lada')]['count'].sum()
    local_city_total = flow_data[(flow_data['origin_group'] == 'Local (PRT)') & 
                                 (flow_data['hotel'] == 'City Hotel')]['count'].sum()
    
    # Afegir anotació amb xifra agregada visible
    fig.add_annotation(
        text=f"<b>{local_rate:.0f}% de les reserves locals<br>es cancel·len</b>",
        xref="paper", yref="paper",
        x=0.02, y=0.98,
        xanchor="left", yanchor="top",
        bgcolor='rgba(192, 57, 43, 0.95)',  # Vermell per destacar
        bordercolor='white',
        borderwidth=3,
        font=dict(size=13, color='white'),
        align='left',
        showarrow=False
    )
    
    # Afegir anotació destacant el flux dominant
    if local_city_canceled > 0:
        fig.add_annotation(
            text=f"<b>Flux principal:</b><br>Cancel·lacions locals<br>via City Hotel<br>({local_city_canceled:,} reserves)",
            xref="paper", yref="paper",
            x=0.98, y=0.02,
            xanchor="right", yanchor="bottom",
            bgcolor='rgba(125, 60, 152, 0.9)',  # Porpra (coherent amb City Hotel)
            bordercolor='white',
            borderwidth=2,
            font=dict(size=11, color='white'),
            align='right',
            showarrow=False
        )
    
    fig.update_layout(
        title={
            'text': 'Flux de reserves: Origen → Hotel → Estat<br><sub>Visualització de trajectòries completes | L\'amplada representa el volum de reserves</sub>',
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 20}
        },
        template='plotly_white',
        height=600,
        margin=dict(l=50, r=50, t=100, b=50)
    )
    
    return fig

def create_graph4_fallback(flow_data):
    """
    Fallback si el Sankey no funciona: barres apilades per mostrar el flux
    """
    fig = go.Figure()
    
    # Agrupar per origen i estat
    for origin in sorted(flow_data['origin_group'].unique()):
        data_origin = flow_data[flow_data['origin_group'] == origin]
        canceled = data_origin[data_origin['status'] == 'Cancel·lada']['count'].sum()
        not_canceled = data_origin[data_origin['status'] == 'No cancel·lada']['count'].sum()
        
        fig.add_trace(go.Bar(
            name=origin,
            x=['Cancel·lada', 'No cancel·lada'],
            y=[canceled, not_canceled],
            marker_color=COLORS['local'] if origin == 'Local (PRT)' else COLORS['international']
        ))
    
    fig.update_layout(
        title='Flux de reserves per origen i estat (visualització alternativa)',
        barmode='group',
        template='plotly_white',
        height=400
    )
    
    return fig

def create_graph5a_lead_time(df):
    """
    ACTE 5A: Lead time (violin plot)
    Limitant outliers per millor visualització
    """
    fig = go.Figure()
    
    origins = ['Local (PRT)', 'International']
    for origin in origins:
        data = df[df['origin_group'] == origin]['lead_time'].dropna()
        if len(data) > 0:
            # Limitar a percentil 95 per evitar cues extremes
            p95 = data.quantile(0.95)
            data_filtered = data[data <= p95]
            
            # Calcular estadístiques per al tooltip (amb dades completes)
            median_val = data.median()
            q1_val = data.quantile(0.25)
            q3_val = data.quantile(0.75)
            mean_val = data.mean()
            max_val = data.max()
            
            # Per violin plots, cal passar x repetit per cada punt
            x_values = [origin] * len(data_filtered)
            fig.add_trace(
                go.Violin(
                    y=data_filtered.tolist(),
                    x=x_values,
                    name=origin,
                    box_visible=True,
                    box_fillcolor='white',  # Box blanc per destacar mediana
                    box_line=dict(color='black', width=2),  # Línia més fosca per mediana
                    meanline_visible=True,
                    meanline=dict(color='#34495e', width=2),  # Línia de mitjana més visible
                    fillcolor=COLORS['local'] if origin == 'Local (PRT)' else COLORS['international'],
                    line_color='black',
                    opacity=0.7,
                    scalegroup='lead_time',
                    side='both',
                    hovertemplate='<b>%{x}</b><br>' +
                                  f'Mitjana: {mean_val:.1f} dies<br>' +
                                  f'<b>Mediana: {median_val:.1f} dies</b><br>' +
                                  f'Q1: {q1_val:.1f} dies<br>' +
                                  f'Q3: {q3_val:.1f} dies<br>' +
                                  f'Màxim: {max_val:.0f} dies<br>' +
                                  f'N: {len(data):,}<br>' +
                                  '<extra></extra>',
                    width=0.8
                )
            )
    
    # Limitar eix Y al percentil 95 per evitar que els outliers distreguin
    all_data = df['lead_time'].dropna()
    y_max = all_data.quantile(0.95) * 1.1  # 10% de marge per sobre del P95
    
    fig.update_layout(
        title={
            'text': 'Lead Time (dies d\'antelació)<br><sub>Mostrant fins al percentil 95 (hi ha outliers per sobre) | Les reserves locals tendeixen a reservar amb menys antelació</sub>',
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 18}
        },
        xaxis_title='Origen',
        yaxis_title='Dies',
        yaxis=dict(range=[0, y_max]),
        template='plotly_white',
        height=400,
        showlegend=True
    )
    
    return fig

def create_graph5b_booking_changes(df):
    """
    ACTE 5B: Booking changes (histograma agrupat)
    Mostra la distribució de freqüències de canvis per origen
    """
    fig = go.Figure()
    
    origins = ['Local (PRT)', 'International']
    
    # Agrupar canvis: 0, 1, 2, 3, 4, 5+
    def categorize_changes(x):
        if x == 0:
            return '0'
        elif x == 1:
            return '1'
        elif x == 2:
            return '2'
        elif x == 3:
            return '3'
        elif x == 4:
            return '4'
        else:
            return '5+'
    
    # Preparar dades
    changes_data = df.copy()
    changes_data['changes_cat'] = changes_data['booking_changes'].apply(categorize_changes)
    
    categories = ['0', '1', '2', '3', '4', '5+']
    
    for origin in origins:
        data_origin = changes_data[changes_data['origin_group'] == origin]
        total = len(data_origin)
        
        # Calcular percentatges per categoria
        pct_values = []
        counts = []
        for cat in categories:
            count = len(data_origin[data_origin['changes_cat'] == cat])
            counts.append(count)
            pct = (count / total * 100) if total > 0 else 0
            pct_values.append(pct)
        
        fig.add_trace(go.Bar(
            name=origin,
            x=categories,
            y=pct_values,
            marker_color=COLORS['local'] if origin == 'Local (PRT)' else COLORS['international'],
            hovertemplate='<b>%{fullData.name}</b><br>' +
                          'Canvis: %{x}<br>' +
                          'Percentatge: %{y:.1f}%<br>' +
                          'Recompte: %{customdata:,}<br>' +
                          '<extra></extra>',
            customdata=counts
        ))
    
    # Calcular diferència en canvis (percentatge de reserves amb 1+ canvis)
    local_changes = changes_data[changes_data['origin_group'] == 'Local (PRT)']
    intl_changes = changes_data[changes_data['origin_group'] == 'International']
    
    local_pct_1plus = (len(local_changes[local_changes['booking_changes'] > 0]) / len(local_changes) * 100) if len(local_changes) > 0 else 0
    intl_pct_1plus = (len(intl_changes[intl_changes['booking_changes'] > 0]) / len(intl_changes) * 100) if len(intl_changes) > 0 else 0
    diff_pct = local_pct_1plus - intl_pct_1plus
    
    # Calcular percentatge de reserves sense canvis (0)
    local_pct_0 = (len(local_changes[local_changes['booking_changes'] == 0]) / len(local_changes) * 100) if len(local_changes) > 0 else 0
    intl_pct_0 = (len(intl_changes[intl_changes['booking_changes'] == 0]) / len(intl_changes) * 100) if len(intl_changes) > 0 else 0
    diff_pct_0 = intl_pct_0 - local_pct_0
    
    # Afegir anotació destacant la diferència
    if diff_pct > 0:
        fig.add_annotation(
            text=f"<b>Les reserves locals presenten<br>{diff_pct:.1f}% més canvis<br>que les internacionals</b>",
            xref="paper", yref="paper",
            x=0.98, y=0.95,
            xanchor="right", yanchor="top",
            bgcolor='rgba(231, 76, 60, 0.9)',
            bordercolor='white',
            borderwidth=2,
            font=dict(size=11, color='white'),
            align='right',
            showarrow=False
        )
    
    # Afegir anotació sobre reserves sense canvis
    if diff_pct_0 > 0:
        fig.add_annotation(
            text=f"<b>Les reserves sense canvis (0)<br>són {diff_pct_0:.1f}% menys freqüents<br>entre locals</b>",
            xref="paper", yref="paper",
            x=0.02, y=0.95,
            xanchor="left", yanchor="top",
            bgcolor='rgba(52, 152, 219, 0.9)',
            bordercolor='white',
            borderwidth=2,
            font=dict(size=11, color='white'),
            align='left',
            showarrow=False
        )
    
    fig.update_layout(
        title={
            'text': 'Distribució de canvis a la reserva<br><sub>Les reserves locals presenten una major proporció de canvis, indicant major flexibilitat i volatilitat</sub>',
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 18}
        },
        xaxis_title='Nombre de canvis',
        yaxis_title='Percentatge de reserves (%)',
        barmode='group',
        template='plotly_white',
        height=400,
        showlegend=True
    )
    
    return fig

def create_graph5c_deposit_type(df):
    """
    ACTE 5C: Deposit type (barres apilades al 100%)
    """
    fig = go.Figure()
    
    deposit_counts = df.groupby(['origin_group', 'deposit_type']).size().reset_index(name='count')
    
    # Calcular percentatges per grup
    deposit_pct_list = []
    for origin in ['Local (PRT)', 'International']:
        data_origin = deposit_counts[deposit_counts['origin_group'] == origin]
        total = data_origin['count'].sum()
        for _, row in data_origin.iterrows():
            deposit_pct_list.append({
                'origin_group': origin,
                'deposit_type': row['deposit_type'],
                'pct': (row['count'] / total * 100) if total > 0 else 0
            })
    
    deposit_pct = pd.DataFrame(deposit_pct_list)
    
    # Ordenar tipus de dipòsit per compromís (de més a menys): Non Refund > Refundable > No Deposit
    deposit_order = ['Non Refund', 'Refundable', 'No Deposit']
    deposit_types = [dt for dt in deposit_order if dt in deposit_pct['deposit_type'].unique()]
    # Afegir qualsevol altre tipus que no estigui a la llista
    for dt in sorted(deposit_pct['deposit_type'].unique()):
        if dt not in deposit_types:
            deposit_types.append(dt)
    
    # Colors per tipus de dipòsit
    deposit_colors = {
        'No Deposit': '#E74C3C',
        'Non Refund': '#E67E22',
        'Refundable': '#3498DB'
    }
    
    # Crear traces per cada tipus de dipòsit (en ordre de compromís)
    for dt in deposit_types:
        values = []
        for origin in ['Local (PRT)', 'International']:
            data = deposit_pct[(deposit_pct['origin_group'] == origin) & 
                              (deposit_pct['deposit_type'] == dt)]
            if len(data) > 0:
                values.append(data['pct'].values[0])
            else:
                values.append(0)
        
        fig.add_trace(
            go.Bar(
                name=dt,
                x=['Local (PRT)', 'International'],
                y=values,
                marker_color=deposit_colors.get(dt, '#95A5A6'),
                hovertemplate='<b>%{x}</b><br>' +
                              f'Tipus: {dt}<br>' +
                              'Percentatge: %{y:.1f}%<br>' +
                              '<extra></extra>'
            )
        )
    
    # Calcular diferència en "Non Refund" (més compromís)
    local_non_refund = deposit_pct[(deposit_pct['origin_group'] == 'Local (PRT)') & 
                                   (deposit_pct['deposit_type'] == 'Non Refund')]
    intl_non_refund = deposit_pct[(deposit_pct['origin_group'] == 'International') & 
                                  (deposit_pct['deposit_type'] == 'Non Refund')]
    
    local_pct_nr = local_non_refund['pct'].values[0] if len(local_non_refund) > 0 else 0
    intl_pct_nr = intl_non_refund['pct'].values[0] if len(intl_non_refund) > 0 else 0
    diff_nr = intl_pct_nr - local_pct_nr
    
    # Afegir anotació connectant dipòsit amb cancel·lació
    if diff_nr > 0:
        fig.add_annotation(
            text=f"<b>Les reserves internacionals tenen<br>{diff_nr:.1f}% més dipòsits<br>Non Refund (més compromís)</b><br><br>Els dipòsits Non Refund impliquen<br>més compromís i menys cancel·lació",
            xref="paper", yref="paper",
            x=0.02, y=0.98,
            xanchor="left", yanchor="top",
            bgcolor='rgba(52, 152, 219, 0.9)',
            bordercolor='white',
            borderwidth=2,
            font=dict(size=11, color='white'),
            align='left',
            showarrow=False
        )
    
    fig.update_layout(
        title={
            'text': 'Tipus de dipòsit per origen<br><sub>Non Refund implica més compromís amb la reserva i està associat a menys cancel·lacions</sub>',
            'x': 0.5,
            'xanchor': 'center',
            'font': {'size': 18}
        },
        xaxis_title='Origen',
        yaxis_title='Percentatge (%)',
        barmode='stack',
        template='plotly_white',
        height=400,
        showlegend=True,
        legend=dict(
            traceorder='normal',  # Mantenir ordre de traces (ja ordenat per compromís)
            orientation="v",
            yanchor="middle",
            y=0.5,
            xanchor="right",
            x=1.02
        )
    )
    
    return fig

# ============================================================================
# FASE 4: GENERACIÓ HTML
# ============================================================================

def generate_html_v3(figures, output_file='index.html'):
    """
    Genera l'HTML final amb narrativa i gràfics (VERSIÓ 3)
    Millores: Menú de navegació fixe, indicador de progrés, botó "Tornar a dalt"
    """
    html_content = f"""
<!DOCTYPE html>
<html lang="ca">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="description" content="Anàlisi del risc de cancel·lació en reserves hoteleres a Portugal (2015-2017). Visualització narrativa que explora com el volum, el tipus d'hotel i el comportament del client influeixen en el risc de cancel·lació.">
    <meta name="keywords" content="visualització de dades, hotel bookings, cancel·lació, Portugal, storytelling, dashboard narratiu">
    <meta name="author" content="PAC 3 - Visualització de Dades">
    <title>Per què les reserves locals cancel·len més?</title>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
            scroll-behavior: smooth;
        }}
        
        /* Indicador de progrés de scroll */
        .scroll-progress {{
            position: fixed;
            top: 0;
            left: 0;
            width: 0%;
            height: 4px;
            background: linear-gradient(90deg, #3498DB, #2980B9);
            z-index: 1000;
            transition: width 0.1s ease;
        }}
        
        /* Menú de navegació fixe */
        .nav-menu {{
            position: fixed;
            top: 4px;
            left: 50%;
            transform: translateX(-50%);
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(10px);
            padding: 10px 20px;
            border-radius: 0 0 10px 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            z-index: 999;
            display: flex;
            gap: 15px;
            flex-wrap: wrap;
            justify-content: center;
            max-width: 1400px;
            width: calc(100% - 40px);
        }}
        
        .nav-menu a {{
            color: #34495e;
            text-decoration: none;
            padding: 8px 15px;
            border-radius: 5px;
            font-size: 0.9em;
            font-weight: 500;
            transition: all 0.3s ease;
            white-space: nowrap;
        }}
        
        .nav-menu a:hover {{
            background-color: #3498DB;
            color: white;
            transform: translateY(-2px);
        }}
        
        .nav-menu a.active {{
            background-color: #2980B9;
            color: white;
        }}
        
        /* Espai per al menú fixe */
        .content-wrapper {{
            padding-top: 60px;
        }}
        
        .header {{
            text-align: center;
            margin-bottom: 40px;
            padding: 30px;
            background: white;
            border-radius: 10px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        
        h1 {{
            color: #2c3e50;
            font-size: 2.5em;
            margin-bottom: 10px;
        }}
        
        .subtitle {{
            color: #7f8c8d;
            font-size: 1.2em;
            font-style: italic;
        }}
        
        .version-badge {{
            display: inline-block;
            background: #27AE60;
            color: white;
            padding: 5px 15px;
            border-radius: 20px;
            font-size: 0.9em;
            margin-top: 10px;
        }}
        
        .acte {{
            background: white;
            margin: 30px 0;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            scroll-margin-top: 80px;
            transition: transform 0.3s ease, box-shadow 0.3s ease;
        }}
        
        .acte:hover {{
            transform: translateY(-2px);
            box-shadow: 0 4px 8px rgba(0,0,0,0.15);
        }}
        
        .acte h2 {{
            color: #34495e;
            border-bottom: 3px solid #3498DB;
            padding-bottom: 10px;
            margin-bottom: 20px;
        }}
        
        .acte-text {{
            margin-bottom: 30px;
            font-size: 1.1em;
            color: #555;
        }}
        
        .graph-container {{
            margin: 20px 0;
        }}
        
        .takeaway {{
            margin-top: 20px;
            padding: 15px;
            background-color: #f8f9fa;
            border-left: 4px solid #3498DB;
            color: #2c3e50;
            font-size: 1.05em;
        }}
        
        .takeaway strong {{
            color: #2980B9;
            font-weight: 600;
        }}
        
        .takeaway .key-message {{
            font-style: italic;
            color: #34495e;
            margin-top: 8px;
            display: block;
        }}
        
        .viz-note {{
            background-color: #fff3cd;
            border-left: 4px solid #ffc107;
            padding: 10px;
            margin: 10px 0;
            font-size: 0.95em;
            color: #856404;
        }}
        
        /* Botó "Tornar a dalt" */
        .back-to-top {{
            position: fixed;
            bottom: 30px;
            right: 30px;
            background: #3498DB;
            color: white;
            width: 50px;
            height: 50px;
            border-radius: 50%;
            display: none;
            align-items: center;
            justify-content: center;
            cursor: pointer;
            box-shadow: 0 4px 10px rgba(0,0,0,0.2);
            transition: all 0.3s ease;
            z-index: 998;
            font-size: 24px;
        }}
        
        .back-to-top:hover {{
            background: #2980B9;
            transform: translateY(-3px);
            box-shadow: 0 6px 15px rgba(0,0,0,0.3);
        }}
        
        .back-to-top.show {{
            display: flex;
        }}
        
        @media (max-width: 768px) {{
            .nav-menu {{
                padding: 8px 10px;
                gap: 8px;
            }}
            
            .nav-menu a {{
                font-size: 0.8em;
                padding: 6px 10px;
            }}
            
            .content-wrapper {{
                padding-top: 80px;
            }}
        }}
    </style>
</head>
<body>
    <!-- Indicador de progrés de scroll -->
    <div class="scroll-progress" id="scrollProgress"></div>
    
    <!-- Menú de navegació fixe -->
    <nav class="nav-menu" id="navMenu" role="navigation" aria-label="Navegació principal">
        <a href="#header" aria-label="Anar a l'inici">Inici</a>
        <a href="#acte1" aria-label="Anar a l'Acte 1: Context">Acte 1</a>
        <a href="#acte2" aria-label="Anar a l'Acte 2: Tensió">Acte 2</a>
        <a href="#acte3" aria-label="Anar a l'Acte 3: Clímax">Acte 3</a>
        <a href="#acte4" aria-label="Anar a l'Acte 4: Detall">Acte 4</a>
        <a href="#acte5" aria-label="Anar a l'Acte 5: Explicació">Acte 5</a>
        <a href="#metodologia" aria-label="Anar a la secció de metodologia">Metodologia</a>
    </nav>
    
    <div class="content-wrapper">
        <div class="header" id="header">
            <h1>Per què les reserves locals cancel·len més?</h1>
            <p class="subtitle">Una història de dades sobre risc de cancel·lació en reserves hoteleres a Portugal (2015–2017)</p>
        </div>

        <div class="acte" id="acte1">
            <h2>Acte 1 — Context: El Sistema de Reserves</h2>
            <div class="acte-text">
                <p>Tot i que el dataset inclou dos tipus d'hotel, el volum de reserves no és equilibrat. 
                El City Hotel concentra aproximadament dos terços de les reserves en tots els anys analitzats, 
                fet que amplifica qualsevol risc associat a aquest segment.</p>
                <p style="font-style: italic; color: #555; margin-top: 15px;"><em>Aquesta distribució desigual implica que qualsevol diferència de comportament associada al City Hotel tindrà un impacte desproporcionat sobre el risc global del sistema.</em></p>
            </div>
            <div class="viz-note">
                <strong>Visualització temporal:</strong> He utilitzat un Stacked Area Chart perquè permet visualitzar simultàniament el pes relatiu de cada hotel i la seva evolució temporal, mostrant que la dominància del City Hotel és consistent al llarg dels anys.
            </div>
            <div class="graph-container" id="graph1" role="img" aria-label="Gràfic de volum de reserves per tipus d'hotel i any. Mostra que el City Hotel concentra aproximadament dos terços de les reserves cada any."></div>
            <div class="takeaway">
                <strong>Takeaway:</strong> El City Hotel concentra la major part del volum operatiu de manera sostinguda, preparant el context per a l'anàlisi de risc.
                <span class="key-message">"El City Hotel concentra aproximadament dos terços de totes les reserves cada any."</span>
            </div>
        </div>

        <div class="acte" id="acte2">
            <h2>Acte 2 — Tensió: La Diferència de Risc</h2>
            <div class="acte-text">
                <p>En tots els anys analitzats, la taxa de cancel·lació del City Hotel supera la del Resort Hotel. 
                La diferència es manté estable al llarg del temps, cosa que indica que no es tracta d'un fenomen puntual, 
                sinó d'un patró estructural.</p>
            </div>
            <div class="viz-note">
                <strong>Visualització de diferència:</strong> He utilitzat un Dumbbell Plot perquè permet visualitzar directament la diferència de risc entre els dos tipus d'hotel, fent que la bretxa sigui més evident que amb barres tradicionals.
            </div>
            <div class="graph-container" id="graph2" role="img" aria-label="Gràfic de comparació de taxes de cancel·lació entre City Hotel i Resort Hotel. Mostra que el City Hotel té una taxa sistemàticament superior."></div>
            <div class="acte-text" style="margin-top: 15px; font-style: italic; color: #555;">
                <p>La diferència no només és constant, sinó també rellevant en magnitud.</p>
            </div>
            <div class="acte-text" style="margin-top: 15px; color: #555;">
                <p><em>La persistència d'aquesta diferència al llarg dels anys analitzats suggereix que el risc de cancel·lació no respon a fluctuacions puntuals, sinó a un patró estructural associat al tipus d'hotel.</em></p>
            </div>
            <div class="takeaway">
                <strong>Takeaway:</strong> El patró de major risc al City Hotel es manté consistent al llarg dels anys, indicant un patró estructural.
                <span class="key-message">"La diferència de risc entre City i Resort es manté estable en tots els anys analitzats."</span>
            </div>
        </div>

        <div class="acte" id="acte3">
            <h2>Acte 3 — Clímax: L'Impacte de Portugal</h2>
            <div class="acte-text">
                <p>Aquí apareix un patró especialment rellevant des del punt de vista operatiu: el país amb més reserves (Portugal) també presenta una taxa de 
                cancel·lació més alta que la majoria de mercats internacionals. El Treemap mostra simultàniament 
                el volum de reserves (àrea) i la taxa de cancel·lació (color), revelant l'impacte agregat del risc.</p>
            </div>
            <div class="viz-note">
                <strong>Visualització d'impacte:</strong> He utilitzat un Treemap perquè permet visualitzar simultàniament el volum (àrea) i la taxa de cancel·lació (color), fent evident que Portugal no només té una taxa alta, sinó també un impacte operatiu significatiu per la seva gran quantitat de reserves.
            </div>
            <div class="graph-container" id="graph3" role="img" aria-label="Treemap que mostra l'impacte de risc per país. Portugal destaca per combinar alta taxa de cancel·lació i alt volum de reserves."></div>
            <div class="takeaway">
                <strong>Takeaway:</strong> Portugal combina alta taxa de cancel·lació i alt volum de reserves, el que implica un risc operatiu significatiu.
                <span class="key-message">"Portugal combina alta taxa i alt volum de cancel·lacions."</span>
            </div>
        </div>

        <div class="acte" id="acte4">
            <h2>Acte 4 — Detall: El Flux de Cancel·lacions</h2>
            <div class="acte-text">
                <p>El diagrama de Sankey mostra el flux complet de reserves des de l'origen fins a l'estat final. 
                Això permet veure trajectòries completes i on es concentra el flux de cancel·lacions, 
                no només comparacions estàtiques.</p>
            </div>
            <div class="viz-note">
                <strong>Visualització de flux:</strong> He utilitzat un Sankey perquè vull mostrar fluxos i composició, no només comparacions estàtiques. L'amplada de cada flux representa el volum de reserves.
            </div>
            <div class="graph-container" id="graph4" role="img" aria-label="Diagrama de Sankey que mostra el flux de reserves des de l'origen fins a l'estat final. Visualitza on es concentra el flux de cancel·lacions."></div>
            <div class="acte-text" style="margin-top: 15px; color: #555;">
                <p><em>El diagrama de flux mostra que una part significativa de les cancel·lacions de reserves locals es canalitza a través del City Hotel, reforçant la interacció entre l'origen de la reserva i el tipus d'hotel.</em></p>
            </div>
            <div class="takeaway">
                <strong>Takeaway:</strong> El patró de major cancel·lació local es manté tant al City Hotel com al Resort Hotel, i es visualitza clarament en el flux de reserves.
            </div>
        </div>

        <div class="acte" id="acte5">
            <h2>Acte 5 — Explicació: Possibles Causes</h2>
            <div class="acte-text">
                <p>Una possible peça del trencaclosques és el comportament de reserva. Les reserves locals mostren patrons 
                diferents: reserven amb menys antelació, fan més canvis a les reserves i utilitzen menys dipòsits Non Refund 
                (que impliquen més compromís). Aquests factors poden estar associats a una major volatilitat i, per tant, 
                més cancel·lacions.</p>
            </div>
            <div class="graph-container" id="graph5a" role="img" aria-label="Violin plot que compara la distribució de lead time (dies d'antelació) entre reserves locals i internacionals."></div>
            <div class="graph-container" id="graph5b" role="img" aria-label="Histograma que mostra la distribució de canvis a la reserva per origen. Les reserves locals presenten més canvis."></div>
            <div class="graph-container" id="graph5c" role="img" aria-label="Gràfic de barres apilades que mostra el tipus de dipòsit per origen. Les reserves locals utilitzen menys dipòsits Non Refund."></div>
            <div class="acte-text" style="margin-top: 15px; color: #555; font-style: italic;">
                <p><em>Cal remarcar que aquestes relacions no impliquen una causalitat directa, sinó associacions observades en el comportament de reserva.</em></p>
            </div>
            <div class="takeaway">
                <strong>Takeaway:</strong> Les reserves locals presenten una major proporció de canvis, menys antelació i menys dipòsits amb compromís, factors que poden contribuir a una major volatilitat i cancel·lació.
            </div>
        </div>
        
        <!-- Secció de metodologia i eines -->
        <div class="acte" id="metodologia" style="background-color: #f8f9fa; border-top: 3px solid #3498DB;">
            <h2 style="border-bottom: 3px solid #3498DB;">Sobre aquesta visualització</h2>
            <div class="acte-text">
                <h3 style="color: #34495e; margin-top: 20px; margin-bottom: 10px;">Metodologia</h3>
                <p>El conjunt de dades recull més de 117.000 reserves realitzades entre 2015 i 2017 en dos hotels de Portugal: un hotel urbà a Lisboa i un resort a l'Algarve.</p>
                <p>Abans de construir la visualització final, s'ha realitzat una fase d'analítica visual exploratòria utilitzant el notebook proporcionat (Component 1 de la PAC), introduint diverses correccions per garantir la qualitat de les dades. Les dades netes generades en aquesta fase s'utilitzen directament per a la visualització narrativa, assegurant consistència entre l'anàlisi exploratòria i la visualització final.</p>
                <p>Les correccions aplicades durant l'EDA inclouen:</p>
                <ul style="margin-left: 20px; color: #555;">
                    <li>Eliminació d'outliers en adults, infants i bebès</li>
                    <li>Eliminació de valors negatius o extremadament elevats a l'ADR</li>
                    <li>Tractament coherent de valors nuls</li>
                    <li>Construcció robusta de la variable temporal</li>
                </ul>
                <p>Aquest procés assegura que les visualitzacions reflecteixin patrons reals de comportament i no errors de registre.</p>
                
                <h3 style="color: #34495e; margin-top: 30px; margin-bottom: 10px;">Eines i Tecnologies</h3>
                <p>La visualització s'ha creat utilitzant <strong>Plotly</strong>, una llibreria Python per a visualitzacions interactives. Aquesta elecció permet crear visualitzacions avançades com diagrames de Sankey, treemaps i violin plots, mantenint alhora la interactivitat necessària per a una experiència narrativa efectiva.</p>
                <p>Les funcionalitats interactives emprades inclouen:</p>
                <ul style="margin-left: 20px; color: #555;">
                    <li><strong>Tooltips informatius:</strong> Al passar el ratolí sobre els elements es mostra informació detallada</li>
                    <li><strong>Zoom i pan:</strong> Permet explorar els gràfics en detall</li>
                    <li><strong>Disseny responsive:</strong> S'adapta a diferents mides de pantalla</li>
                    <li><strong>Navegació interactiva:</strong> Menú fixe i indicador de progrés per facilitar la navegació</li>
                </ul>
                
                <h3 style="color: #34495e; margin-top: 30px; margin-bottom: 10px;">Decisions de Disseny</h3>
                <p>Cada tècnica de visualització s'ha escollit en funció de la pregunta analítica que es vol respondre:</p>
                <ul style="margin-left: 20px; color: #555;">
                    <li><strong>Stacked Area Chart:</strong> Permet visualitzar simultàniament el pes relatiu i l'evolució temporal</li>
                    <li><strong>Dumbbell Plot:</strong> Visualitza directament la diferència de risc entre grups</li>
                    <li><strong>Treemap:</strong> Mostra simultàniament volum (àrea) i taxa de cancel·lació (color)</li>
                    <li><strong>Sankey Diagram:</strong> Visualitza fluxos i trajectòries completes</li>
                    <li><strong>Violin Plot, Histograma i Barres apilades:</strong> Permeten comparar distribucions, freqüències i composicions</li>
                </ul>
                <p>La paleta de colors és consistent al llarg del dashboard per diferenciar hotels i origen del client, utilitzant una tipografia clara (Segoe UI) i s'han eliminat elements visuals que no aporten informació rellevant.</p>
                
                <h3 style="color: #34495e; margin-top: 30px; margin-bottom: 10px;">Objectiu i Usuari</h3>
                <p>L'objectiu de la visualització és explicar el risc de cancel·lació des d'un punt de vista operatiu, pensada per a perfils de gestió hotelera o anàlisi de negoci.</p>
                <p>La història s'ha estructurat com una narrativa en cinc actes, seguint una progressió de context, tensió, clímax i possible explicació, facilitant una comprensió progressiva d'un fenomen complex.</p>
            </div>
        </div>
    </div>
    
    <!-- Botó "Tornar a dalt" -->
    <div class="back-to-top" id="backToTop" onclick="window.scrollTo({{top: 0, behavior: 'smooth'}})" aria-label="Tornar a dalt">↑</div>

    <script>
        // Gràfics Plotly
        var graph1 = {figures[0]};
        Plotly.newPlot('graph1', graph1.data, graph1.layout, {{responsive: true}});

        var graph2 = {figures[1]};
        Plotly.newPlot('graph2', graph2.data, graph2.layout, {{responsive: true}});

        var graph3 = {figures[2]};
        Plotly.newPlot('graph3', graph3.data, graph3.layout, {{responsive: true}});
        
        var graph4 = {figures[3]};
        Plotly.newPlot('graph4', graph4.data, graph4.layout, {{responsive: true}});
        
        var graph5a = {figures[4]};
        Plotly.newPlot('graph5a', graph5a.data, graph5a.layout, {{responsive: true}});
        
        var graph5b = {figures[5]};
        Plotly.newPlot('graph5b', graph5b.data, graph5b.layout, {{responsive: true}});
        
        var graph5c = {figures[6]};
        Plotly.newPlot('graph5c', graph5c.data, graph5c.layout, {{responsive: true}});
        
        // Indicador de progrés de scroll
        window.addEventListener('scroll', function() {{
            var scrollProgress = document.getElementById('scrollProgress');
            var scrollTop = window.pageYOffset || document.documentElement.scrollTop;
            var scrollHeight = document.documentElement.scrollHeight - window.innerHeight;
            var progress = (scrollTop / scrollHeight) * 100;
            scrollProgress.style.width = progress + '%';
        }});
        
        // Actualitzar menú actiu segons scroll
        window.addEventListener('scroll', function() {{
            var sections = ['header', 'acte1', 'acte2', 'acte3', 'acte4', 'acte5', 'metodologia'];
            var scrollPos = window.pageYOffset + 100;
            
            sections.forEach(function(sectionId, index) {{
                var section = document.getElementById(sectionId);
                if (section) {{
                    var sectionTop = section.offsetTop;
                    var sectionBottom = sectionTop + section.offsetHeight;
                    
                    if (scrollPos >= sectionTop && scrollPos < sectionBottom) {{
                        // Eliminar classe active de tots els enllaços
                        document.querySelectorAll('.nav-menu a').forEach(function(link) {{
                            link.classList.remove('active');
                        }});
                        
                        // Afegir classe active a l'enllaç corresponent
                        var navLinks = document.querySelectorAll('.nav-menu a');
                        if (navLinks[index + 1]) {{
                            navLinks[index + 1].classList.add('active');
                        }}
                    }}
                }}
            }});
        }});
        
        // Mostrar/ocultar botó "Tornar a dalt"
        window.addEventListener('scroll', function() {{
            var backToTop = document.getElementById('backToTop');
            if (window.pageYOffset > 300) {{
                backToTop.classList.add('show');
            }} else {{
                backToTop.classList.remove('show');
            }}
        }});
        
        // Scroll suau per als enllaços del menú
        document.querySelectorAll('.nav-menu a').forEach(function(link) {{
            link.addEventListener('click', function(e) {{
                e.preventDefault();
                var targetId = this.getAttribute('href').substring(1);
                var targetElement = document.getElementById(targetId);
                if (targetElement) {{
                    targetElement.scrollIntoView({{ behavior: 'smooth', block: 'start' }});
                }}
            }});
        }});
    </script>
</body>
</html>
"""
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"Dashboard V3 generat: {output_file}")

def generate_html(figures, output_file='dashboard_v2.html'):
    """
    Genera l'HTML final amb narrativa i gràfics (VERSIÓ 2)
    """
    html_content = f"""
<!DOCTYPE html>
<html lang="ca">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Per què les reserves locals cancel·len més? (Versió Avançada)</title>
    <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .header {{
            text-align: center;
            margin-bottom: 40px;
            padding: 30px;
            background: white;
            border-radius: 10px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #2c3e50;
            font-size: 2.5em;
            margin-bottom: 10px;
        }}
        .subtitle {{
            color: #7f8c8d;
            font-size: 1.2em;
            font-style: italic;
        }}
        .version-badge {{
            display: inline-block;
            background: #E67E22;
            color: white;
            padding: 5px 15px;
            border-radius: 20px;
            font-size: 0.9em;
            margin-top: 10px;
        }}
        .acte {{
            background: white;
            margin: 30px 0;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .acte h2 {{
            color: #34495e;
            border-bottom: 3px solid #3498DB;
            padding-bottom: 10px;
            margin-bottom: 20px;
        }}
        .acte-text {{
            margin-bottom: 30px;
            font-size: 1.1em;
            color: #555;
        }}
        .graph-container {{
            margin: 20px 0;
        }}
        .takeaway {{
            margin-top: 20px;
            padding: 15px;
            background-color: #f8f9fa;
            border-left: 4px solid #3498DB;
            color: #2c3e50;
            font-size: 1.05em;
        }}
        .takeaway strong {{
            color: #2980B9;
            font-weight: 600;
        }}
        .takeaway .key-message {{
            font-style: italic;
            color: #34495e;
            margin-top: 8px;
            display: block;
        }}
        .viz-note {{
            background-color: #fff3cd;
            border-left: 4px solid #ffc107;
            padding: 10px;
            margin: 10px 0;
            font-size: 0.95em;
            color: #856404;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Per què les reserves locals cancel·len més?</h1>
        <p class="subtitle">Una història de dades sobre risc de cancel·lació en reserves hoteleres a Portugal (2015–2017)</p>
    </div>

    <div class="acte">
        <h2>Acte 1 — Context</h2>
        <div class="acte-text">
            <p>Tot i que el dataset inclou dos tipus d'hotel, el volum de reserves no és equilibrat. 
            El City Hotel concentra aproximadament dos terços de les reserves en tots els anys analitzats, 
            fet que amplifica qualsevol risc associat a aquest segment.</p>
            <p style="font-style: italic; color: #555; margin-top: 15px;"><em>Aquesta distribució desigual implica que qualsevol diferència de comportament associada al City Hotel tindrà un impacte desproporcionat sobre el risc global del sistema.</em></p>
        </div>
        <div class="viz-note">
            <strong>Visualització temporal:</strong> He utilitzat un Stacked Area Chart perquè permet visualitzar simultàniament el pes relatiu de cada hotel i la seva evolució temporal, mostrant que la dominància del City Hotel és consistent al llarg dels anys.
        </div>
        <div class="graph-container" id="graph1"></div>
        <div class="takeaway">
            <strong>Takeaway:</strong> El City Hotel concentra la major part del volum operatiu de manera sostinguda, preparant el context per a l'anàlisi de risc.
            <span class="key-message">"El City Hotel concentra aproximadament dos terços de totes les reserves cada any."</span>
        </div>
    </div>

    <div class="acte">
        <h2>Acte 2 — Tensió</h2>
        <div class="acte-text">
            <p>En tots els anys analitzats, la taxa de cancel·lació del City Hotel supera la del Resort Hotel. 
            La diferència es manté estable al llarg del temps, cosa que indica que no es tracta d'un fenomen puntual, 
            sinó d'un patró estructural.</p>
        </div>
        <div class="viz-note">
            <strong>Visualització de diferència:</strong> He utilitzat un Dumbbell Plot perquè permet visualitzar directament la diferència de risc entre els dos tipus d'hotel, fent que la bretxa sigui més evident que amb barres tradicionals.
        </div>
        <div class="graph-container" id="graph2"></div>
        <div class="acte-text" style="margin-top: 15px; font-style: italic; color: #555;">
            <p>La diferència no només és constant, sinó també rellevant en magnitud.</p>
        </div>
        <div class="acte-text" style="margin-top: 15px; color: #555;">
            <p><em>La persistència d'aquesta diferència al llarg dels anys analitzats suggereix que el risc de cancel·lació no respon a fluctuacions puntuals, sinó a un patró estructural associat al tipus d'hotel.</em></p>
        </div>
        <div class="takeaway">
            <strong>Takeaway:</strong> El patró de major risc al City Hotel es manté consistent al llarg dels anys, indicant un patró estructural.
            <span class="key-message">"La diferència de risc entre City i Resort es manté estable en tots els anys analitzats."</span>
        </div>
    </div>

    <div class="acte">
        <h2>Acte 3 — Clímax</h2>
        <div class="acte-text">
            <p>Aquí apareix un patró especialment rellevant des del punt de vista operatiu: el país amb més reserves (Portugal) també presenta una taxa de 
            cancel·lació més alta que la majoria de mercats internacionals. El Treemap mostra simultàniament 
            el volum de reserves (àrea) i la taxa de cancel·lació (color), revelant l'impacte agregat del risc.</p>
        </div>
        <div class="viz-note">
            <strong>Visualització d'impacte:</strong> He utilitzat un Treemap perquè permet visualitzar simultàniament el volum (àrea) i la taxa de cancel·lació (color), fent evident que Portugal no només té una taxa alta, sinó també un impacte operatiu significatiu per la seva gran quantitat de reserves.
        </div>
        <div class="graph-container" id="graph3"></div>
        <div class="takeaway">
            <strong>Takeaway:</strong> Portugal combina alta taxa de cancel·lació i alt volum de reserves, el que implica un risc operatiu significatiu.
            <span class="key-message">"Portugal combina alta taxa i alt volum de cancel·lacions."</span>
        </div>
    </div>

    <div class="acte">
        <h2>Acte 4 — On passa exactament</h2>
        <div class="acte-text">
            <p>El diagrama de Sankey mostra el flux complet de reserves des de l'origen fins a l'estat final. 
            Això permet veure trajectòries completes i on es concentra el flux de cancel·lacions, 
            no només comparacions estàtiques.</p>
        </div>
        <div class="viz-note">
            <strong>Visualització de flux:</strong> He utilitzat un Sankey perquè vull mostrar fluxos i composició, no només comparacions estàtiques. L'amplada de cada flux representa el volum de reserves.
        </div>
        <div class="graph-container" id="graph4"></div>
        <div class="acte-text" style="margin-top: 15px; color: #555;">
            <p><em>El diagrama de flux mostra que una part significativa de les cancel·lacions de reserves locals es canalitza a través del City Hotel, reforçant la interacció entre l'origen de la reserva i el tipus d'hotel.</em></p>
        </div>
        <div class="takeaway">
            <strong>Takeaway:</strong> El patró de major cancel·lació local es manté tant al City Hotel com al Resort Hotel, i es visualitza clarament en el flux de reserves.
        </div>
    </div>

    <div class="acte">
        <h2>Acte 5 — Possible explicació</h2>
        <div class="acte-text">
            <p>Una possible peça del trencaclosques és el comportament de reserva. Les reserves locals mostren patrons 
            diferents: reserven amb menys antelació, fan més canvis a les reserves i utilitzen menys dipòsits Non Refund 
            (que impliquen més compromís). Aquests factors poden estar associats a una major volatilitat i, per tant, 
            més cancel·lacions.</p>
        </div>
        <div class="graph-container" id="graph5a"></div>
        <div class="graph-container" id="graph5b"></div>
        <div class="graph-container" id="graph5c"></div>
        <div class="acte-text" style="margin-top: 15px; color: #555; font-style: italic;">
            <p><em>Cal remarcar que aquestes relacions no impliquen una causalitat directa, sinó associacions observades en el comportament de reserva.</em></p>
        </div>
        <div class="takeaway">
            <strong>Takeaway:</strong> Les reserves locals presenten una major proporció de canvis, menys antelació i menys dipòsits amb compromís, factors que poden contribuir a una major volatilitat i cancel·lació.
        </div>
    </div>

    <script>
        // Gràfic 1
        var graph1 = {figures[0]};
        Plotly.newPlot('graph1', graph1.data, graph1.layout, {{responsive: true}});

        // Gràfic 2
        var graph2 = {figures[1]};
        Plotly.newPlot('graph2', graph2.data, graph2.layout, {{responsive: true}});

        // Gràfic 3 (Treemap)
        var graph3 = {figures[2]};
        Plotly.newPlot('graph3', graph3.data, graph3.layout, {{responsive: true}});
        
        // Gràfic 4 (Sankey)
        var graph4 = {figures[3]};
        Plotly.newPlot('graph4', graph4.data, graph4.layout, {{responsive: true}});
        
        // Gràfics 5 (3 independents)
        var graph5a = {figures[4]};
        Plotly.newPlot('graph5a', graph5a.data, graph5a.layout, {{responsive: true}});
        
        var graph5b = {figures[5]};
        Plotly.newPlot('graph5b', graph5b.data, graph5b.layout, {{responsive: true}});
        
        var graph5c = {figures[6]};
        Plotly.newPlot('graph5c', graph5c.data, graph5c.layout, {{responsive: true}});
    </script>
</body>
</html>
"""
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    print(f"Dashboard generat: {output_file}")

def export_to_pdf(figures_list, output_file='pac3.pdf'):
    """
    Exporta el dashboard versió 3 a PDF
    """
    print(f"\nExportant a PDF: {output_file}...")
    
    # Crear directori temporal per a les imatges
    img_dir = 'temp_images'
    os.makedirs(img_dir, exist_ok=True)
    
    try:
        # Exportar cada gràfic a imatge
        img_paths = []
        for i, fig in enumerate(figures_list, 1):
            img_path = os.path.join(img_dir, f'graph_{i}.png')
            fig.write_image(img_path, width=1200, height=600, scale=2)
            img_paths.append(img_path)
            print(f"   Gràfic {i} exportat")
        
        # Crear PDF
        doc = SimpleDocTemplate(output_file, pagesize=A4)
        story = []
        
        # Estils
        styles = getSampleStyleSheet()
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor='#2c3e50',
            spaceAfter=12,
            alignment=TA_CENTER
        )
        subtitle_style = ParagraphStyle(
            'CustomSubtitle',
            parent=styles['Normal'],
            fontSize=14,
            textColor='#7f8c8d',
            fontStyle='italic',
            spaceAfter=30,
            alignment=TA_CENTER
        )
        acte_title_style = ParagraphStyle(
            'ActeTitle',
            parent=styles['Heading2'],
            fontSize=18,
            textColor='#34495e',
            spaceAfter=12,
            spaceBefore=20
        )
        text_style = ParagraphStyle(
            'ActeText',
            parent=styles['Normal'],
            fontSize=11,
            textColor='#555',
            spaceAfter=15,
            alignment=TA_LEFT
        )
        note_style = ParagraphStyle(
            'NoteStyle',
            parent=styles['Normal'],
            fontSize=10,
            textColor='#856404',
            backColor='#fff3cd',
            borderPadding=10,
            spaceAfter=10,
            alignment=TA_LEFT
        )
        section_title_style = ParagraphStyle(
            'SectionTitle',
            parent=styles['Heading3'],
            fontSize=14,
            textColor='#34495e',
            spaceAfter=10,
            spaceBefore=15
        )
        
        # Títol i subtítol
        story.append(Paragraph("Per què les reserves locals cancel·len més?", title_style))
        story.append(Paragraph("Una història de dades sobre risc de cancel·lació en reserves hoteleres a Portugal (2015–2017)", subtitle_style))
        story.append(Spacer(1, 0.3*inch))
        
        # Acte 1
        story.append(Paragraph("Acte 1 — Context", acte_title_style))
        story.append(Paragraph("Tot i que el dataset inclou dos tipus d'hotel, el volum de reserves no és equilibrat. El City Hotel concentra aproximadament dos terços de les reserves en tots els anys analitzats, fet que amplifica qualsevol risc associat a aquest segment.", text_style))
        story.append(Paragraph("<i>Aquesta distribució desigual implica que qualsevol diferència de comportament associada al City Hotel tindrà un impacte desproporcionat sobre el risc global del sistema.</i>", text_style))
        story.append(Paragraph("<b>Visualització temporal:</b> Stacked Area Chart que permet visualitzar simultàniament el pes relatiu de cada hotel i la seva evolució temporal, mostrant que la dominància del City Hotel és consistent al llarg dels anys.", note_style))
        story.append(Image(img_paths[0], width=7*inch, height=4*inch))
        story.append(Spacer(1, 0.2*inch))
        
        # Acte 2
        story.append(PageBreak())
        story.append(Paragraph("Acte 2 — Tensió", acte_title_style))
        story.append(Paragraph("En tots els anys analitzats, la taxa de cancel·lació del City Hotel supera la del Resort Hotel. La diferència es manté estable al llarg del temps, cosa que indica que no es tracta d'un fenomen puntual, sinó d'un patró estructural.", text_style))
        story.append(Paragraph("<b>Visualització de diferència:</b> Dumbbell Plot que permet visualitzar directament la diferència de risc entre els dos tipus d'hotel.", note_style))
        story.append(Image(img_paths[1], width=7*inch, height=3.5*inch))
        story.append(Paragraph("<i>La diferència no només és constant, sinó també rellevant en magnitud.</i>", text_style))
        story.append(Paragraph("<i>La persistència d'aquesta diferència al llarg dels anys analitzats suggereix que el risc de cancel·lació no respon a fluctuacions puntuals, sinó a un patró estructural associat al tipus d'hotel.</i>", text_style))
        story.append(Spacer(1, 0.2*inch))
        
        # Acte 3
        story.append(PageBreak())
        story.append(Paragraph("Acte 3 — Clímax", acte_title_style))
        story.append(Paragraph("Aquí apareix un patró especialment rellevant des del punt de vista operatiu: el país amb més reserves (Portugal) també presenta una taxa de cancel·lació més alta que la majoria de mercats internacionals. El Treemap mostra simultàniament el volum de reserves (àrea) i la taxa de cancel·lació (color), revelant l'impacte agregat del risc.", text_style))
        story.append(Paragraph("<b>Visualització d'impacte:</b> Treemap que permet visualitzar simultàniament el volum (àrea) i la taxa de cancel·lació (color), fent evident que Portugal no només té una taxa alta, sinó també un impacte operatiu significatiu per la seva gran quantitat de reserves.", note_style))
        story.append(Image(img_paths[2], width=7*inch, height=4*inch))
        story.append(Spacer(1, 0.2*inch))
        
        # Acte 4
        story.append(PageBreak())
        story.append(Paragraph("Acte 4 — On passa exactament", acte_title_style))
        story.append(Paragraph("El diagrama de Sankey mostra el flux complet de reserves des de l'origen fins a l'estat final. Això permet veure trajectòries completes i on es concentra el flux de cancel·lacions, no només comparacions estàtiques.", text_style))
        story.append(Paragraph("<b>Visualització de flux:</b> He utilitzat un Sankey perquè vull mostrar fluxos i composició, no només comparacions estàtiques. L'amplada de cada flux representa el volum de reserves.", note_style))
        story.append(Image(img_paths[3], width=7*inch, height=4*inch))
        story.append(Paragraph("<i>El diagrama de flux mostra que una part significativa de les cancel·lacions de reserves locals es canalitza a través del City Hotel, reforçant la interacció entre l'origen de la reserva i el tipus d'hotel.</i>", text_style))
        story.append(Spacer(1, 0.2*inch))
        
        # Acte 5
        story.append(PageBreak())
        story.append(Paragraph("Acte 5 — Possible explicació", acte_title_style))
        story.append(Paragraph("Una possible peça del trencaclosques és el comportament de reserva. Les reserves locals mostren patrons diferents: reserven amb menys antelació, fan més canvis a les reserves i utilitzen menys dipòsits Non Refund (que impliquen més compromís). Aquests factors poden estar associats a una major volatilitat i, per tant, més cancel·lacions.", text_style))
        story.append(Image(img_paths[4], width=7*inch, height=3.5*inch))
        story.append(Spacer(1, 0.1*inch))
        story.append(Image(img_paths[5], width=7*inch, height=3.5*inch))
        story.append(Spacer(1, 0.1*inch))
        story.append(Image(img_paths[6], width=7*inch, height=3.5*inch))
        story.append(Paragraph("<i>Cal remarcar que aquestes relacions no impliquen una causalitat directa, sinó associacions observades en el comportament de reserva.</i>", text_style))
        
        # Secció "Sobre aquesta visualització"
        story.append(PageBreak())
        story.append(Paragraph("Sobre aquesta visualització", acte_title_style))
        
        # Metodologia
        story.append(Paragraph("<b>Metodologia</b>", section_title_style))
        story.append(Paragraph("El conjunt de dades recull més de 117.000 reserves realitzades entre 2015 i 2017 en dos hotels de Portugal: un hotel urbà a Lisboa i un resort a l'Algarve.", text_style))
        story.append(Paragraph("Abans de construir la visualització final, s'ha realitzat una fase d'analítica visual exploratòria utilitzant el notebook proporcionat (Component 1 de la PAC), introduint diverses correccions per garantir la qualitat de les dades. Les dades netes generades en aquesta fase s'utilitzen directament per a la visualització narrativa, assegurant consistència entre l'anàlisi exploratòria i la visualització final.", text_style))
        story.append(Paragraph("Les correccions aplicades durant l'EDA inclouen:", text_style))
        story.append(Paragraph("• Eliminació d'outliers en adults, infants i bebès", text_style))
        story.append(Paragraph("• Eliminació de valors negatius o extremadament elevats a l'ADR", text_style))
        story.append(Paragraph("• Tractament coherent de valors nuls", text_style))
        story.append(Paragraph("• Construcció robusta de la variable temporal", text_style))
        story.append(Paragraph("Aquest procés assegura que les visualitzacions reflecteixin patrons reals de comportament i no errors de registre.", text_style))
        story.append(Spacer(1, 0.2*inch))
        
        # Eines i Tecnologies
        story.append(Paragraph("<b>Eines i Tecnologies</b>", section_title_style))
        story.append(Paragraph("La visualització s'ha creat utilitzant <b>Plotly</b>, una llibreria Python per a visualitzacions interactives. Aquesta elecció permet crear visualitzacions avançades com diagrames de Sankey, treemaps i violin plots, mantenint alhora la interactivitat necessària per a una experiència narrativa efectiva.", text_style))
        story.append(Paragraph("Les funcionalitats interactives emprades inclouen:", text_style))
        story.append(Paragraph("• <b>Tooltips informatius:</b> Al passar el ratolí sobre els elements es mostra informació detallada", text_style))
        story.append(Paragraph("• <b>Zoom i pan:</b> Permet explorar els gràfics en detall", text_style))
        story.append(Paragraph("• <b>Disseny responsive:</b> S'adapta a diferents mides de pantalla", text_style))
        story.append(Paragraph("• <b>Navegació interactiva:</b> Menú fixe i indicador de progrés per facilitar la navegació", text_style))
        story.append(Spacer(1, 0.2*inch))
        
        # Decisions de Disseny
        story.append(Paragraph("<b>Decisions de Disseny</b>", section_title_style))
        story.append(Paragraph("Cada tècnica de visualització s'ha escollit en funció de la pregunta analítica que es vol respondre:", text_style))
        story.append(Paragraph("• <b>Stacked Area Chart:</b> Permet visualitzar simultàniament el pes relatiu i l'evolució temporal", text_style))
        story.append(Paragraph("• <b>Dumbbell Plot:</b> Visualitza directament la diferència de risc entre grups", text_style))
        story.append(Paragraph("• <b>Treemap:</b> Mostra simultàniament volum (àrea) i taxa de cancel·lació (color)", text_style))
        story.append(Paragraph("• <b>Sankey Diagram:</b> Visualitza fluxos i trajectòries completes", text_style))
        story.append(Paragraph("• <b>Violin Plot, Histograma i Barres apilades:</b> Permeten comparar distribucions, freqüències i composicions", text_style))
        story.append(Paragraph("La paleta de colors és consistent al llarg del dashboard per diferenciar hotels i origen del client, utilitzant una tipografia clara (Segoe UI) i s'han eliminat elements visuals que no aporten informació rellevant.", text_style))
        story.append(Spacer(1, 0.2*inch))
        
        # Objectiu i Usuari
        story.append(Paragraph("<b>Objectiu i Usuari</b>", section_title_style))
        story.append(Paragraph("L'objectiu de la visualització és explicar el risc de cancel·lació des d'un punt de vista operatiu, pensada per a perfils de gestió hotelera o anàlisi de negoci.", text_style))
        story.append(Paragraph("La història s'ha estructurat com una narrativa en cinc actes, seguint una progressió de context, tensió, clímax i possible explicació, facilitant una comprensió progressiva d'un fenomen complex.", text_style))
        
        # Generar PDF
        doc.build(story)
        print(f"PDF generat: {output_file}")
        
    except Exception as e:
        print(f"   ⚠️  Error exportant a PDF: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        # Netejar imatges temporals
        import shutil
        if os.path.exists(img_dir):
            shutil.rmtree(img_dir)
            print("   Imatges temporals eliminades")

# ============================================================================
# MAIN
# ============================================================================

def main():
    print("=" * 60)
    print("DASHBOARD NARRATIU - PAC 3 (VERSIÓ 2: AVANÇADA)")
    print("=" * 60)
    
    # Carregar dades netes (generades pel notebook R - Component 1)
    print("\n1. Carregant dades netes...")
    try:
        df_clean = pd.read_csv('hotel_bookings_clean.csv')
        print(f"   ✓ Dades netes carregades des de hotel_bookings_clean.csv")
        print(f"   Dades netes: {len(df_clean)} registres")
    except FileNotFoundError:
        print("   ❌ ERROR: hotel_bookings_clean.csv no trobat!")
        print("   ⚠️  Has d'executar primer el notebook R (hotel_bookings.Rmd) per generar les dades netes.")
        print("   El notebook neteja les dades segons els criteris de l'EDA i les guarda a hotel_bookings_clean.csv")
        raise FileNotFoundError("hotel_bookings_clean.csv no trobat. Executa primer el notebook R.")
    
    # Crear variable origin_group (no està al CSV net, s'afegeix aquí)
    if 'origin_group' not in df_clean.columns:
        df_clean['origin_group'] = df_clean['country'].apply(
            lambda x: 'Local (PRT)' if x == 'PRT' else 'International'
        )
    
    # Crear taules intermèdies
    print("\n2. Creant taules intermèdies...")
    tbl_volume = create_tbl_volume_hotel_year(df_clean)
    tbl_cancel_hotel = create_tbl_cancel_rate_hotel_year(df_clean)
    tbl_cancel_country = create_tbl_cancel_rate_country(df_clean, min_bookings=1000)
    tbl_country_hotel = create_tbl_country_hotel_cancel(df_clean, min_bookings=1000)
    
    print(f"   - Volum per hotel/any: {len(tbl_volume)} registres")
    print(f"   - Cancel·lació per hotel/any: {len(tbl_cancel_hotel)} registres")
    print(f"   - Cancel·lació per país: {len(tbl_cancel_country)} països")
    print(f"   - Cancel·lació país×hotel: {len(tbl_country_hotel)} registres")
    
    # Crear gràfics
    print("\n3. Generant gràfics...")
    print("   - Acte 1: Barres apilades (mantingut)")
    fig1 = create_graph1_volume_hotel_year(tbl_volume)
    
    print("   - Acte 2: Dumbbell Plot (mantingut)")
    fig2 = create_graph2_cancel_rate_hotel_year(tbl_cancel_hotel)
    
    print("   - Acte 3: Treemap (clímax)")
    fig3 = create_graph3b_treemap_country(tbl_cancel_country)
    
    print("   - Acte 4: Sankey diagram (NOVETAT)")
    fig4 = create_graph4_sankey_flow(df_clean)
    
    print("   - Acte 5: Lead Time, Booking Changes, Deposit Type (3 gràfics independents)")
    fig5a = create_graph5a_lead_time(df_clean)
    fig5b = create_graph5b_booking_changes(df_clean)
    fig5c = create_graph5c_deposit_type(df_clean)
    
    # Convertir gràfics a JSON per HTML
    figures_json = [
        fig1.to_json(),
        fig2.to_json(),
        fig3.to_json(),
        fig4.to_json(),
        fig5a.to_json(),
        fig5b.to_json(),
        fig5c.to_json()
    ]
    
    # Generar HTML
    print("\n4. Generant HTML...")
    generate_html_v3(figures_json, 'index.html')
    
    # Exportar a PDF (opcional)
    print("\n5. Exportant a PDF (opcional)...")
    try:
        export_to_pdf([fig1, fig2, fig3, fig4, fig5a, fig5b, fig5c], 'pac3.pdf')
    except Exception as e:
        print(f"   ⚠️  No s'ha pogut exportar a PDF: {e}")
        print("   Assegura't d'instal·lar: pip install kaleido reportlab")
    
    print("\nFitxers generats:")
    print("  - index.html")
    print("  - pac3.pdf")
    print("\nObre 'index.html' al navegador per visualitzar el dashboard.")

if __name__ == '__main__':
    main()

