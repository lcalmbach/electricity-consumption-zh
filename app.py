import streamlit as st
from streamlit_option_menu import option_menu
import pandas as pd
import plots
from datetime import datetime, timedelta

__version__ = '0.0.2'
__author__ = 'Lukas Calmbach'
__author_email__ = 'lcalmbach@gmail.com'
VERSION_DATE = '2022-10-10'
my_name = 'Bruttoverbrauch Elektrizität der Stadt Zürich'
my_kuerzel = "El-zh"
SOURCE_URL = 'https://data.stadt-zuerich.ch/dataset/ewz_bruttolastgang_stadt_zuerich'
GIT_REPO = 'https://github.com/lcalmbach/electricity-consumption-zh'
APP_INFO = f"""<div style="background-color:'#34282C'; padding: 10px;border-radius: 15px; font-color:'black';">
    <small>App created by <a href="mailto:{__author_email__}">{__author__}</a><br>
    version: {__version__} ({VERSION_DATE})<br>
    source: <a href="{SOURCE_URL}">Stadt Zürich Open Data/EWZ</a>
    <br><a href="{GIT_REPO}">git-repo</a>
    """

def_options_days = (1, 365)
def_options_hours = (0, 23)
def_options_weeks = (1, 53)

def init():
    st.set_page_config(  # Alternate names: setup_page, page, layout
        initial_sidebar_state = "auto", 
        page_title = 'E-Verbrauch-zh', 
        page_icon = '⚡',
    )
    
@st.cache
def get_data():
    def add_aggregation_codes(df):
        df['zeitpunkt']= pd.to_datetime(df['zeitpunkt'])
        df['year'] = df['zeitpunkt'].dt.year
        df['day'] = 15
        df['month'] = 7
        df['year_date'] = pd.to_datetime(df[['year','month','day']])
        df['hour'] = df['zeitpunkt'].dt.hour
        df['minute'] = df['zeitpunkt'].dt.minute
        df['date'] = pd.to_datetime(df['zeitpunkt']).dt.date
        df['date'] = pd.to_datetime(df['date'])
        df['week'] = df['zeitpunkt'].dt.isocalendar().week
        df['month'] = df['zeitpunkt'].dt.month
        df['year'] = df['zeitpunkt'].dt.year
        df['week_date'] = df['date'] - pd.offsets.Week(weekday=6)
        df['month_date'] = pd.to_datetime(df[['year','month','day']])
        df['day_in_month'] = pd.to_datetime(df['zeitpunkt']).dt.day
        df['day'] = df['zeitpunkt'].dt.day
        df['hour_date'] = pd.to_datetime(df[['year', 'month', 'day', 'hour']])
        df['day'] = df['zeitpunkt'].dt.dayofyear
        df['zeit'] = df['zeitpunkt'].dt.strftime('%H:%M')
        df['day_of_week'] = df['zeitpunkt'].dt.dayofweek
        df['week_time'] = df['day_of_week'] + df['hour']/24 + df['zeitpunkt'].dt.minute / (24*60)
        return df

    df = pd.DataFrame()
    for jahr in [2019,2020,2021,2022]:
        _df = pd.read_csv(f'./data/{jahr}_ewz_bruttolastgang.csv', sep=',')
        df = pd.concat([df, _df], axis=0)
    df = df[(df['status']=='E') | (df['zeitpunkt']<'2020-06-15')]
    df = df[['zeitpunkt','bruttolastgang']]
    df['bruttolastgang'] = df['bruttolastgang'] / 1e6
    df = add_aggregation_codes(df)
    return df


def get_interval_dates(sel_days):
    base_date = datetime(2022, 1, 1)
    fmt = "%d.%m/%y"
    dat1 = base_date + timedelta(days=sel_days[0]-1)
    dat2 = base_date + timedelta(days=sel_days[1]-1)
    return f"{dat1.strftime(fmt)[:5]} - {dat2.strftime(fmt)[:5]}"


def consumption_year(df):
    def show_plot(df):
        settings = {'x': 'day', 'y':'cum_bruttolastgang', 'color':'year:O', 'tooltip':['year','day', 'cum_bruttolastgang'], 
                'width':800,'height':400, 'y_title': 'Kumulierter Verbrauch [GWh]', 'x_title': 'Tag im Jahr', 
                'title': "Kumulierter Verbrauch"}
        plots.line_chart(df, settings)
        # st.markdown(figure_text['year'][0])

        settings['y'] = 'bruttolastgang'
        settings['y_title'] = 'Verbrauch [MWh]'
        settings['title'] = "Tages-Verbrauch"
        plots.line_chart(df, settings)
        # st.markdown(figure_text['year'][1])

    def get_filtered_data(df):
        with st.sidebar.expander('🔎 Filter', expanded=True):
            sel_days = st.slider('Auswahl Tag im Jahr', min_value=1, max_value=max(def_options_days), value=def_options_days)
            st.markdown(get_interval_dates(sel_days))
            sel_years = st.multiselect('Auswahl Jahre', options=range(2019,2023), help="keine Auswahl = alle Jahre")
        if sel_days != def_options_days:
            df = df[(df['day'] >= sel_days[0]) & (df['day'] <= sel_days[1])]
        if sel_years:
            df = df[df['year'].isin(sel_years)]
        return df

    df_day = get_filtered_data(df.copy())
    fields = ['year', 'day', 'bruttolastgang']
    agg_fields = ['year','day']
    df_day = df_day[fields].groupby(agg_fields).sum().reset_index()
    df_day['cum_bruttolastgang']=df_day.groupby(['year'])['bruttolastgang'].cumsum()
    df_day = df_day[df_day['bruttolastgang'] > 2]
    show_plot(df_day)


def consumption_day(df):
    def show_plot(df):
        settings = {'x': 'zeit', 'x_dt': 'O', 'y':'bruttolastgang', 'color':'year:O', 'tooltip':['year','zeit', 'bruttolastgang'], 
                'width':800,'height':400, 'title': 'Tagesganglinie, mittlerer Viertelstunden-Verbrauch'}
        
        settings['x_labels'] = [f"{str(x).rjust(2, '0')}:00" for x in range(0,23+1)]
        plots.line_chart(df, settings)

    def get_filtered_data(df):
        with st.sidebar.expander('🔎 Filter', expanded=True):
            sel_days = st.slider('Auswahl Tag im Jahr', min_value=1, max_value=365, value=def_options_days)
            st.markdown(get_interval_dates(sel_days))
            
            sel_years = st.multiselect('Auswahl Jahre', options=range(2019,2023), help="keine Auswahl = alle Jahre")
            if sel_days != def_options_days:
                df = df[(df['day'] >= sel_days[0]) & (df['day'] <= sel_days[1])]
        if sel_years:
            df = df[df['year'].isin(sel_years)]
        return df

    df_time = get_filtered_data(df.copy())
    df_time['bruttolastgang'] = df_time['bruttolastgang'] * 1000
    fields = ['year', 'zeit', 'bruttolastgang']
    agg_fields = ['year','zeit']
    df_time = df_time[fields].groupby(agg_fields).mean().reset_index()
    show_plot(df_time)

def consumption_week(df):
    def show_plot(df):
        settings = {'x': 'week_time', 'x_dt': 'O', 'y':'bruttolastgang', 'color':'year:O', 'tooltip':['year','week_time', 'bruttolastgang'], 
                'width':800,'height':400, 'title': 'Wochenganglinie, mittlerer Viertelstunden-Verbrauch', 'x_title': 'Wochentag',
                'y_title': 'Verbrauch [MWh]'}
        
        # settings['x_labels'] = {0: 'So',1:'Mon',2:'Di',3:'Mi',4:'Do',5:'Fr',6:'Sa'}
        # settings['x_labels'] = ['Mon','Di','Mi','Do','Fr','Sa','So']
        settings['x_labels'] = [0,1,2,3,4,5,6]
        plots.line_chart(df, settings)

    def get_filtered_data(df):
        with st.sidebar.expander('🔎 Filter', expanded=True):
            sel_weeks = st.slider('Auswahl Kalenderwochen', min_value=1, max_value=max(def_options_weeks), value=def_options_weeks)
            st.markdown(get_interval_dates(sel_weeks))
            
            sel_years = st.multiselect('Auswahl Jahre', options=range(2019,2023), help="keine Auswahl = alle Jahre")
            if sel_weeks != def_options_weeks:
                df = df[(df['week'] >= sel_weeks[0]) & (df['week'] <= sel_weeks[1])]
        if sel_years:
            df = df[df['year'].isin(sel_years)]
        return df

    df_time = get_filtered_data(df.copy())
    df_time['bruttolastgang'] = df_time['bruttolastgang'] * 1000
    fields = ['year', 'week_time', 'bruttolastgang']
    agg_fields = ['year','week_time']
    df_time = df_time[fields].groupby(agg_fields).mean().reset_index()
    show_plot(df_time)

def main():
    init()
    df = get_data()
    st.markdown("### Bruttoverbrauch elektrische Energie der Stadt Zürich, seit 2019")
    st.markdown(f"Quelle: [Stadt Zürich Open Data]({SOURCE_URL})")
    st.sidebar.markdown("### ⚡ Verbrauch-zh")

    menu_options = ['Jahresverlauf', 'Tagesverlauf', 'Wochenverbrauch']
    with st.sidebar:
        menu_action = option_menu(None, menu_options, 
        icons=['calendar', 'clock', 'calendar'], 
        menu_icon="cast", default_index=0)

    if menu_action == menu_options[0]:
        consumption_year(df)
    elif menu_action == menu_options[1]:
        consumption_day(df)
    elif menu_action == menu_options[2]:
        consumption_week(df)

    st.sidebar.markdown(APP_INFO, unsafe_allow_html=True)

if __name__ == '__main__':
    main()



