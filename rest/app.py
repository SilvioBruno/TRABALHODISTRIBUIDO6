"""CRUD REST do streaming. Porta 8001."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import List, Optional

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fastapi import FastAPI
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel, Field

from streaming.servico import ErroServico, StreamingServico

app = FastAPI(title="Streaming de músicas — REST", version="0.1")
servico = StreamingServico()

_STATUS = {"NAO_ENCONTRADO": 404, "CONFLITO": 409, "VALIDACAO": 400}


class UsuarioIn(BaseModel):
    nome: str
    idade: int


class UsuarioPatch(BaseModel):
    nome: Optional[str] = None
    idade: Optional[int] = None


class MusicaIn(BaseModel):
    nome: str
    artista: str


class MusicaPatch(BaseModel):
    nome: Optional[str] = None
    artista: Optional[str] = None


class PlaylistIn(BaseModel):
    nome: str
    usuarioId: int
    musicaIds: List[int] = Field(min_length=1)


class PlaylistPatch(BaseModel):
    nome: Optional[str] = None
    musicaIds: Optional[List[int]] = None


class MusicaNaPlaylist(BaseModel):
    musicaId: int


@app.exception_handler(ErroServico)
def tratar_erro(_requisicao, erro: ErroServico):
    return JSONResponse(
        status_code=_STATUS.get(erro.codigo, 400),
        content={"codigo": erro.codigo, "mensagem": erro.mensagem},
    )


@app.get("/")
def raiz():
    return {"tecnologia": "REST", "recursos": ["/usuarios", "/musicas", "/playlists"]}


@app.post("/usuarios", status_code=201)
def criar_usuario(corpo: UsuarioIn):
    return servico.criar_usuario(corpo.nome, corpo.idade)


@app.get("/usuarios")
def listar_usuarios():
    return servico.listar_usuarios()


@app.get("/usuarios/{usuario_id}")
def obter_usuario(usuario_id: int):
    return servico.obter_usuario(usuario_id)


@app.put("/usuarios/{usuario_id}")
def atualizar_usuario(usuario_id: int, corpo: UsuarioPatch):
    return servico.atualizar_usuario(usuario_id, corpo.nome, corpo.idade)


@app.delete("/usuarios/{usuario_id}", status_code=204)
def remover_usuario(usuario_id: int):
    servico.remover_usuario(usuario_id)
    return Response(status_code=204)


@app.get("/usuarios/{usuario_id}/playlists")
def playlists_do_usuario(usuario_id: int):
    return servico.listar_playlists_do_usuario(usuario_id)


@app.post("/musicas", status_code=201)
def criar_musica(corpo: MusicaIn):
    return servico.criar_musica(corpo.nome, corpo.artista)


@app.get("/musicas")
def listar_musicas():
    return servico.listar_musicas()


@app.get("/musicas/{musica_id}")
def obter_musica(musica_id: int):
    return servico.obter_musica(musica_id)


@app.put("/musicas/{musica_id}")
def atualizar_musica(musica_id: int, corpo: MusicaPatch):
    return servico.atualizar_musica(musica_id, corpo.nome, corpo.artista)


@app.delete("/musicas/{musica_id}", status_code=204)
def remover_musica(musica_id: int):
    servico.remover_musica(musica_id)
    return Response(status_code=204)


@app.get("/musicas/{musica_id}/playlists")
def playlists_com_musica(musica_id: int):
    return servico.listar_playlists_com_musica(musica_id)


@app.post("/playlists", status_code=201)
def criar_playlist(corpo: PlaylistIn):
    return servico.criar_playlist(corpo.nome, corpo.usuarioId, corpo.musicaIds)


@app.get("/playlists")
def listar_playlists():
    return servico.listar_playlists()


@app.get("/playlists/{playlist_id}")
def obter_playlist(playlist_id: int):
    return servico.obter_playlist(playlist_id)


@app.put("/playlists/{playlist_id}")
def atualizar_playlist(playlist_id: int, corpo: PlaylistPatch):
    return servico.atualizar_playlist(
        playlist_id,
        nome=corpo.nome,
        musica_ids=corpo.musicaIds,
        substituir_musicas=corpo.musicaIds is not None,
    )


@app.delete("/playlists/{playlist_id}", status_code=204)
def remover_playlist(playlist_id: int):
    servico.remover_playlist(playlist_id)
    return Response(status_code=204)


@app.get("/playlists/{playlist_id}/musicas")
def musicas_da_playlist(playlist_id: int):
    return servico.listar_musicas_da_playlist(playlist_id)


@app.post("/playlists/{playlist_id}/musicas")
def adicionar_musica(playlist_id: int, corpo: MusicaNaPlaylist):
    return servico.adicionar_musica_na_playlist(playlist_id, corpo.musicaId)


@app.delete("/playlists/{playlist_id}/musicas/{musica_id}")
def remover_musica_da_playlist(playlist_id: int, musica_id: int):
    return servico.remover_musica_da_playlist(playlist_id, musica_id)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8001)
