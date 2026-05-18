from fastapi import FastAPI, Depends, File, UploadFile
from sqlalchemy.orm import Session
from database import SessionLocal, engine
import models
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
import cloudinary
import cloudinary.uploader
import os

cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET")
)

models.Base.metadata.create_all(bind=engine)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class Produto(BaseModel):
    nome: str
    categoria: str
    preco: Optional[float] = None
    imagem: Optional[str] = None

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/")
def home():
    return {"mensagem": "API rodando com sucesso!"}

@app.get("/produtos")
def listar_produtos(db: Session = Depends(get_db)):
    return db.query(models.Produto).all()

@app.get("/produtos/{produto_id}")
def pegar_produto(produto_id: int, db: Session = Depends(get_db)):
    produto = db.query(models.Produto).filter(models.Produto.id == produto_id).first()
    if produto:
        return produto
    return {"erro": "Produto não encontrado"}

@app.post("/produtos")
def criar_produto(produto: Produto, db: Session = Depends(get_db)):
    novo_produto = models.Produto(
        nome=produto.nome,
        preco=produto.preco,
        categoria=produto.categoria,
        imagem=produto.imagem
    )
    db.add(novo_produto)
    db.commit()
    db.refresh(novo_produto)
    return {"mensagem": "Produto criado com sucesso!", "produto": novo_produto}

@app.put("/produtos/{produto_id}")
def atualizar_produto(produto_id: int, produto: Produto, db: Session = Depends(get_db)):
    p = db.query(models.Produto).filter(models.Produto.id == produto_id).first()
    if p:
        p.nome = produto.nome
        p.preco = produto.preco
        p.categoria = produto.categoria
        p.imagem = produto.imagem
        db.commit()
        db.refresh(p)
        return {"mensagem": "Produto atualizado com sucesso!", "produto": p}
    return {"erro": "Produto não encontrado"}

@app.post("/upload")
async def upload_imagem(file: UploadFile = File(...)):
    resultado = cloudinary.uploader.upload(file.file)
    return {"url": resultado["secure_url"]}

@app.delete("/produtos/{produto_id}")
def deletar_produto(produto_id: int, db: Session = Depends(get_db)):
    p = db.query(models.Produto).filter(models.Produto.id == produto_id).first()
    if p:
        db.delete(p)
        db.commit()
        return {"mensagem": "Produto deletado com sucesso!"}
    return {"erro": "Produto não encontrado"}