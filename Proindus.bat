@echo off
cd C:\Users\Usuario\Desktop\Proyecto_Proindus
start /min uvicorn main:app
streamlit run app.py
pause