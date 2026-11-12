import streamlit as st
import ezdxf
import fitz
import numpy as np
from shapely.geometry import Polygon
from shapely.affinity import translate, rotate
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from PIL import Image
import io
import os

NARANJA = "#E9531E"
VERDE = "#138A36"
FONDO = "#F4F6F5"
OSCURO = "#1E293B"

COLORES = {
    "Espalda": {"fill": "#E9531E", "edge": "#9A3412"},
    "Delantero": {"fill": "#138A36", "edge": "#064E3B"},
    "Manga": {"fill": "#F59E0B", "edge": "#92400E"},
    "Cuello / Pretina": {"fill": "#0284C7", "edge": "#075985"},
    "Bolsillo / Puño": {"fill": "#64748B", "edge": "#1E293B"},
    "Molde PDF": {"fill": "#138A36", "edge": "#E9531E"}
}

st.set_page_config(
    page_title="Módulo de Corte | Waldy Uniformes",
    page_icon="✂️",
    layout="wide"
)

st.markdown(
    "<style>"
    f".main {{ background-color: {FONDO}; }}"
    f".stButton>button {{ background-color: {NARANJA}; color: white; "
    "font-weight: bold; border-radius: 8px; border: none; }}"
    f".stButton>button:hover {{ background-color: {VERDE}; color: white; }}"
    "</style>",
    unsafe_allow_html=True
)

if "orden_corte" not in st.session_state:
    st.session_state.orden_corte = []
if "rc" not in st.session_state:
    st.session_state.rc = 0

def reiniciar():
    st.session_state.orden_corte = []
    st.session_state.rc += 1

def svg_logo():
    s = [
        '<svg viewBox="0 0 420 265" xmlns="http://www.w3.org/2000/svg" ',
        'style="width:100%;max-width:210px;display:block;margin:auto;">',
        '<rect width="420" height="265" fill="#F8F9FA" rx="6"/>',
        f'<path d="M22,22 C22,12 38,12 38,22 L38,85 C38,95 52,95 52,85 ',
        'L52,55 C52,45 68,45 68,55 L68,85 C68,95 82,95 82,85 L82,22 ',
        'C82,12 98,12 98,22 L98,88 C98,112 72,118 60,104 ',
        f'C48,118 22,112 22,88 Z" fill="{NARANJA}"/>',
        f'<path d="M158,42 C130,42 110,60 110,80 C110,100 130,115 158,115 ',
        'L164,115 L164,42 Z M148,96 C134,96 126,88 126,79 ',
        f'C126,70 134,61 148,61 L148,96 Z" fill="{NARANJA}"/>',
        f'<rect x="176" y="42" width="17" height="73" rx="8" fill="{NARANJA}"/>',
        f'<path d="M254,14 L254