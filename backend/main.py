# main.py
from fastapi import FastAPI
# Si cette ligne ne fait pas d'erreur, c'est que main.py est bien à la racine !
from tools.scraper import get_fuel_prices 

app = FastAPI()

@app.get("/")
def home():
    return {"message": "Le serveur est prêt !"}
