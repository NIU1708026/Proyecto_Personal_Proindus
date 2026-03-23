import os
from dotenv import load_dotenv
from sqlmodel import create_engine, SQLModel, Session
from models import * # Importamos los modelos para que SQLModel los "vea"

# Cargamos las variables del archivo .env
load_dotenv()

database_url = os.getenv("DATABASE_URL")

# El engine es el puente entre Python y PostgreSQL
engine = create_engine(database_url, echo=True) # echo=True para ver el SQL en consola (muy útil para clase)

def create_db_and_tables():
    """Esta función crea las tablas en la nube si no existen"""
    SQLModel.metadata.create_all(engine)

def get_session():
    """Generador para obtener una sesión de base de datos"""
    with Session(engine) as session:
        yield session

if __name__ == "__main__":
    # Si ejecutas este archivo directamente, se crean las tablas
    print("Conectando a la nube y creando tablas...")
    create_db_and_tables()
    print("¡Listo! Las tablas ya están en Supabase/Neon.")