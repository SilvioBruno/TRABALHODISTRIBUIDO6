"""CRUD SOAP 1.1 do streaming. Porta 8003. WSDL em http://127.0.0.1:8003/?wsdl."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from spyne import Application, Array, Boolean, ComplexModel, Integer, ServiceBase, Unicode, rpc
from spyne.model.fault import Fault
from spyne.protocol.soap import Soap11
from spyne.server.wsgi import WsgiApplication
from wsgiref.simple_server import make_server

from streaming.servico import ErroServico, StreamingServico

NS = "urn:streaming.musicas"
servico = StreamingServico()


class UsuarioSoap(ComplexModel):
    __namespace__ = NS
    id = Integer
    nome = Unicode
    idade = Integer


class MusicaSoap(ComplexModel):
    __namespace__ = NS
    id = Integer
    nome = Unicode
    artista = Unicode


class PlaylistSoap(ComplexModel):
    __namespace__ = NS
    id = Integer
    nome = Unicode
    usuarioId = Integer
    musicas = Array(MusicaSoap)


def _usuario(dados):
    return UsuarioSoap(id=dados["id"], nome=dados["nome"], idade=dados["idade"])


def _musica(dados):
    return MusicaSoap(id=dados["id"], nome=dados["nome"], artista=dados["artista"])


def _playlist(dados):
    return PlaylistSoap(
        id=dados["id"],
        nome=dados["nome"],
        usuarioId=dados["usuarioId"],
        musicas=[_musica(item) for item in dados["musicas"]],
    )


def _chamar(funcao):
    try:
        return funcao()
    except ErroServico as erro:
        raise Fault(faultcode="Client.%s" % erro.codigo, faultstring=erro.mensagem)


class StreamingSoap(ServiceBase):
    @rpc(Unicode, Integer, _returns=UsuarioSoap)
    def criarUsuario(ctx, nome, idade):
        return _chamar(lambda: _usuario(servico.criar_usuario(nome, idade)))

    @rpc(Integer, _returns=UsuarioSoap)
    def obterUsuario(ctx, id):
        return _chamar(lambda: _usuario(servico.obter_usuario(id)))

    @rpc(_returns=Array(UsuarioSoap))
    def listarUsuarios(ctx):
        return _chamar(lambda: [_usuario(item) for item in servico.listar_usuarios()])

    @rpc(Integer, Unicode(min_occurs=0), Integer(min_occurs=0), _returns=UsuarioSoap)
    def atualizarUsuario(ctx, id, nome, idade):
        return _chamar(lambda: _usuario(servico.atualizar_usuario(id, nome or None, idade)))

    @rpc(Integer, _returns=Boolean)
    def removerUsuario(ctx, id):
        def acao():
            servico.remover_usuario(id)
            return True

        return _chamar(acao)

    @rpc(Unicode, Unicode, _returns=MusicaSoap)
    def criarMusica(ctx, nome, artista):
        return _chamar(lambda: _musica(servico.criar_musica(nome, artista)))

    @rpc(Integer, _returns=MusicaSoap)
    def obterMusica(ctx, id):
        return _chamar(lambda: _musica(servico.obter_musica(id)))

    @rpc(_returns=Array(MusicaSoap))
    def listarMusicas(ctx):
        return _chamar(lambda: [_musica(item) for item in servico.listar_musicas()])

    @rpc(Integer, Unicode(min_occurs=0), Unicode(min_occurs=0), _returns=MusicaSoap)
    def atualizarMusica(ctx, id, nome, artista):
        return _chamar(lambda: _musica(servico.atualizar_musica(id, nome or None, artista or None)))

    @rpc(Integer, _returns=Boolean)
    def removerMusica(ctx, id):
        def acao():
            servico.remover_musica(id)
            return True

        return _chamar(acao)

    @rpc(Unicode, Integer, Array(Integer), _returns=PlaylistSoap)
    def criarPlaylist(ctx, nome, usuarioId, musicaIds):
        return _chamar(lambda: _playlist(servico.criar_playlist(nome, usuarioId, list(musicaIds or []))))

    @rpc(Integer, _returns=PlaylistSoap)
    def obterPlaylist(ctx, id):
        return _chamar(lambda: _playlist(servico.obter_playlist(id)))

    @rpc(_returns=Array(PlaylistSoap))
    def listarPlaylists(ctx):
        return _chamar(lambda: [_playlist(item) for item in servico.listar_playlists()])

    @rpc(
        Integer,
        Unicode(min_occurs=0),
        Boolean,
        Array(Integer, min_occurs=0),
        _returns=PlaylistSoap,
    )
    def atualizarPlaylist(ctx, id, nome, substituirMusicas, musicaIds):
        return _chamar(
            lambda: _playlist(
                servico.atualizar_playlist(
                    id,
                    nome or None,
                    list(musicaIds or []),
                    bool(substituirMusicas),
                )
            )
        )

    @rpc(Integer, _returns=Boolean)
    def removerPlaylist(ctx, id):
        def acao():
            servico.remover_playlist(id)
            return True

        return _chamar(acao)

    @rpc(Integer, _returns=Array(PlaylistSoap))
    def listarPlaylistsDoUsuario(ctx, usuarioId):
        return _chamar(
            lambda: [_playlist(item) for item in servico.listar_playlists_do_usuario(usuarioId)]
        )

    @rpc(Integer, _returns=Array(MusicaSoap))
    def listarMusicasDaPlaylist(ctx, playlistId):
        return _chamar(
            lambda: [_musica(item) for item in servico.listar_musicas_da_playlist(playlistId)]
        )

    @rpc(Integer, _returns=Array(PlaylistSoap))
    def listarPlaylistsComMusica(ctx, musicaId):
        return _chamar(
            lambda: [_playlist(item) for item in servico.listar_playlists_com_musica(musicaId)]
        )

    @rpc(Integer, Integer, _returns=PlaylistSoap)
    def adicionarMusicaNaPlaylist(ctx, playlistId, musicaId):
        return _chamar(
            lambda: _playlist(servico.adicionar_musica_na_playlist(playlistId, musicaId))
        )

    @rpc(Integer, Integer, _returns=PlaylistSoap)
    def removerMusicaDaPlaylist(ctx, playlistId, musicaId):
        return _chamar(
            lambda: _playlist(servico.remover_musica_da_playlist(playlistId, musicaId))
        )


aplicacao = Application(
    [StreamingSoap],
    tns=NS,
    in_protocol=Soap11(),
    out_protocol=Soap11(),
    name="StreamingMusicas",
)
wsgi = WsgiApplication(aplicacao)


if __name__ == "__main__":
    servidor = make_server("127.0.0.1", 8003, wsgi)
    print("SOAP em http://127.0.0.1:8003/?wsdl")
    servidor.serve_forever()
