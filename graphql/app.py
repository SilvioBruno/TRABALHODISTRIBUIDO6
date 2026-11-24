"""CRUD GraphQL do streaming. Porta 8002, endpoint /graphql."""

import sys
from pathlib import Path
from typing import List, Optional

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import strawberry
from fastapi import FastAPI
from graphql import GraphQLError
from strawberry.fastapi import GraphQLRouter

from streaming.servico import ErroServico, StreamingServico

servico = StreamingServico()


def _falha(erro: ErroServico):
    raise GraphQLError(erro.mensagem, extensions={"codigo": erro.codigo})


@strawberry.type
class MusicaTipo:
    id: int
    nome: str
    artista: str

    @strawberry.field(name="playlists")
    def playlists(self, info: strawberry.Info) -> List["PlaylistTipo"]:
        try:
            dados = info.context["servico"].listar_playlists_com_musica(self.id)
        except ErroServico as erro:
            _falha(erro)
        return [_playlist(item) for item in dados]


@strawberry.type
class UsuarioTipo:
    id: int
    nome: str
    idade: int

    @strawberry.field(name="playlists")
    def playlists(self, info: strawberry.Info) -> List["PlaylistTipo"]:
        try:
            dados = info.context["servico"].listar_playlists_do_usuario(self.id)
        except ErroServico as erro:
            _falha(erro)
        return [_playlist(item) for item in dados]


@strawberry.type
class PlaylistTipo:
    id: int
    nome: str
    usuario_id: int = strawberry.field(name="usuarioId")
    musicas: List[MusicaTipo]

    @strawberry.field(name="usuario")
    def usuario(self, info: strawberry.Info) -> UsuarioTipo:
        try:
            dados = info.context["servico"].obter_usuario(self.usuario_id)
        except ErroServico as erro:
            _falha(erro)
        return _usuario(dados)


def _usuario(dados: dict) -> UsuarioTipo:
    return UsuarioTipo(id=dados["id"], nome=dados["nome"], idade=dados["idade"])


def _musica(dados: dict) -> MusicaTipo:
    return MusicaTipo(id=dados["id"], nome=dados["nome"], artista=dados["artista"])


def _playlist(dados: dict) -> PlaylistTipo:
    return PlaylistTipo(
        id=dados["id"],
        nome=dados["nome"],
        usuario_id=dados["usuarioId"],
        musicas=[_musica(item) for item in dados["musicas"]],
    )


@strawberry.type
class Query:
    @strawberry.field
    def usuarios(self, info: strawberry.Info) -> List[UsuarioTipo]:
        return [_usuario(item) for item in info.context["servico"].listar_usuarios()]

    @strawberry.field
    def usuario(self, info: strawberry.Info, id: int) -> UsuarioTipo:
        try:
            return _usuario(info.context["servico"].obter_usuario(id))
        except ErroServico as erro:
            _falha(erro)

    @strawberry.field
    def musicas(self, info: strawberry.Info) -> List[MusicaTipo]:
        return [_musica(item) for item in info.context["servico"].listar_musicas()]

    @strawberry.field
    def musica(self, info: strawberry.Info, id: int) -> MusicaTipo:
        try:
            return _musica(info.context["servico"].obter_musica(id))
        except ErroServico as erro:
            _falha(erro)

    @strawberry.field
    def playlists(self, info: strawberry.Info) -> List[PlaylistTipo]:
        return [_playlist(item) for item in info.context["servico"].listar_playlists()]

    @strawberry.field
    def playlist(self, info: strawberry.Info, id: int) -> PlaylistTipo:
        try:
            return _playlist(info.context["servico"].obter_playlist(id))
        except ErroServico as erro:
            _falha(erro)

    @strawberry.field(name="playlistsDoUsuario")
    def playlists_do_usuario(self, info: strawberry.Info, usuarioId: int) -> List[PlaylistTipo]:
        try:
            dados = info.context["servico"].listar_playlists_do_usuario(usuarioId)
        except ErroServico as erro:
            _falha(erro)
        return [_playlist(item) for item in dados]

    @strawberry.field(name="musicasDaPlaylist")
    def musicas_da_playlist(self, info: strawberry.Info, playlistId: int) -> List[MusicaTipo]:
        try:
            dados = info.context["servico"].listar_musicas_da_playlist(playlistId)
        except ErroServico as erro:
            _falha(erro)
        return [_musica(item) for item in dados]

    @strawberry.field(name="playlistsComMusica")
    def playlists_com_musica(self, info: strawberry.Info, musicaId: int) -> List[PlaylistTipo]:
        try:
            dados = info.context["servico"].listar_playlists_com_musica(musicaId)
        except ErroServico as erro:
            _falha(erro)
        return [_playlist(item) for item in dados]


@strawberry.type
class Mutation:
    @strawberry.mutation(name="criarUsuario")
    def criar_usuario(self, info: strawberry.Info, nome: str, idade: int) -> UsuarioTipo:
        try:
            return _usuario(info.context["servico"].criar_usuario(nome, idade))
        except ErroServico as erro:
            _falha(erro)

    @strawberry.mutation(name="atualizarUsuario")
    def atualizar_usuario(
        self,
        info: strawberry.Info,
        id: int,
        nome: Optional[str] = None,
        idade: Optional[int] = None,
    ) -> UsuarioTipo:
        try:
            return _usuario(info.context["servico"].atualizar_usuario(id, nome, idade))
        except ErroServico as erro:
            _falha(erro)

    @strawberry.mutation(name="removerUsuario")
    def remover_usuario(self, info: strawberry.Info, id: int) -> bool:
        try:
            info.context["servico"].remover_usuario(id)
        except ErroServico as erro:
            _falha(erro)
        return True

    @strawberry.mutation(name="criarMusica")
    def criar_musica(self, info: strawberry.Info, nome: str, artista: str) -> MusicaTipo:
        try:
            return _musica(info.context["servico"].criar_musica(nome, artista))
        except ErroServico as erro:
            _falha(erro)

    @strawberry.mutation(name="atualizarMusica")
    def atualizar_musica(
        self,
        info: strawberry.Info,
        id: int,
        nome: Optional[str] = None,
        artista: Optional[str] = None,
    ) -> MusicaTipo:
        try:
            return _musica(info.context["servico"].atualizar_musica(id, nome, artista))
        except ErroServico as erro:
            _falha(erro)

    @strawberry.mutation(name="removerMusica")
    def remover_musica(self, info: strawberry.Info, id: int) -> bool:
        try:
            info.context["servico"].remover_musica(id)
        except ErroServico as erro:
            _falha(erro)
        return True

    @strawberry.mutation(name="criarPlaylist")
    def criar_playlist(
        self,
        info: strawberry.Info,
        nome: str,
        usuarioId: int,
        musicaIds: List[int],
    ) -> PlaylistTipo:
        try:
            return _playlist(info.context["servico"].criar_playlist(nome, usuarioId, musicaIds))
        except ErroServico as erro:
            _falha(erro)

    @strawberry.mutation(name="atualizarPlaylist")
    def atualizar_playlist(
        self,
        info: strawberry.Info,
        id: int,
        nome: Optional[str] = None,
        musicaIds: Optional[List[int]] = None,
    ) -> PlaylistTipo:
        try:
            return _playlist(
                info.context["servico"].atualizar_playlist(
                    id,
                    nome=nome,
                    musica_ids=musicaIds,
                    substituir_musicas=musicaIds is not None,
                )
            )
        except ErroServico as erro:
            _falha(erro)

    @strawberry.mutation(name="removerPlaylist")
    def remover_playlist(self, info: strawberry.Info, id: int) -> bool:
        try:
            info.context["servico"].remover_playlist(id)
        except ErroServico as erro:
            _falha(erro)
        return True

    @strawberry.mutation(name="adicionarMusicaNaPlaylist")
    def adicionar_musica(
        self, info: strawberry.Info, playlistId: int, musicaId: int
    ) -> PlaylistTipo:
        try:
            return _playlist(
                info.context["servico"].adicionar_musica_na_playlist(playlistId, musicaId)
            )
        except ErroServico as erro:
            _falha(erro)

    @strawberry.mutation(name="removerMusicaDaPlaylist")
    def remover_musica_da_playlist(
        self, info: strawberry.Info, playlistId: int, musicaId: int
    ) -> PlaylistTipo:
        try:
            return _playlist(
                info.context["servico"].remover_musica_da_playlist(playlistId, musicaId)
            )
        except ErroServico as erro:
            _falha(erro)


async def contexto():
    return {"servico": servico}


schema = strawberry.Schema(query=Query, mutation=Mutation)
graphql_app = GraphQLRouter(schema, context_getter=contexto, graphql_ide="graphiql")

app = FastAPI(title="Streaming de músicas — GraphQL", version="0.1")
app.include_router(graphql_app, prefix="/graphql")


@app.get("/")
def raiz():
    return {"tecnologia": "GraphQL", "endpoint": "/graphql"}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8002)
