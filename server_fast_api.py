# from fastapi import FastAPI, Request, Form
# from fastapi.responses import RedirectResponse
# import sqlite3

# app = FastAPI()

# # Initialisation de la base

# @app.post("/register")
# async def register_user(userEmail: str = Form(...), password: str = Form(...)):
#     conn = sqlite3.connect("users.db")
#     cursor = conn.cursor()
#     try:
#         cursor.execute("INSERT INTO users (userEmail, password) VALUES (?, ?)", (userEmail, password))
#         conn.commit()
#         return RedirectResponse(url="http://localhost:8000", status_code=303)  # Redirige vers Chainlit
#     except sqlite3.IntegrityError:
#         return {"erreur": "Ce nom d'utilisateur exist déjà ."}
#     finally:
#         conn.close()

# @app.get("/back_to_register")
# async def back_to_register():
#     return RedirectResponse(url="http://localhost:8501", status_code=303)

# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run(app, host="localhost", port=5000,reload=True)


from fastapi import FastAPI, Form
from fastapi.responses import RedirectResponse, JSONResponse
import sqlite3

app = FastAPI()


@app.post("/register")
async def register_user(userEmail: str = Form(...), password: str = Form(...)):
    conn = sqlite3.connect("users.db")
    cursor = conn.cursor()
    
    
    try:
        cursor.execute("INSERT INTO users (userEmail, password) VALUES (?, ?)", (userEmail, password))
        conn.commit()
        return JSONResponse(content={"message": "Inscription réussie"}, status_code=201)
    except sqlite3.IntegrityError:
        return JSONResponse(content={"erreur": "Ce nom d'utilisateur existe déjà."}, status_code=400)
    finally:
        conn.close()

@app.get("/back_to_register")
async def back_to_register():
    return RedirectResponse(url="http://localhost:8501", status_code=303)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="localhost", port=5000, reload=True)
