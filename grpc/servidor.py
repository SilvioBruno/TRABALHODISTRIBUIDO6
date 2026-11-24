"""CRUD gRPC do streaming. Porta 8004.

Antes de subir, gere os stubs:

    powershell -ExecutionPolicy Bypass -File scripts\\gerar_grpc.ps1
"""

from __future__ import annotations

import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ))
sys.path.insert(0, str(RAIZ / "grpc_gen"))

try:
    import grpc
except ImportError:
    sys.stderr.write("Instale as dependências com: pip install -r requirements.txt\n")
    raise SystemExit(1)

try:
    import streaming_pb2 as pb
    import streaming_pb2_grpc as pb_grpc
except ImportError:
    sys.stderr.write(
        "Stubs do gRPC ausentes. Rode scripts\\gerar_grpc.ps1 depois de instalar as dependências.\n"
    )
    raise SystemExit(1)

from streaming.servico import ErroServico, StreamingServico

servico = StreamingServico()

_STATUS = {
    "NAO_ENCONTRADO": grpc.StatusCode.NOT_FOUND,
    "CONFLITO": grpc.StatusCode.ALREADY_EXISTS,
    "VALIDACAO": grpc.StatusCode.INVALID_ARGUMENT,
}


def _rpc(contexto, funcao):
    try:
        return funcao()
    except ErroServico as erro:
        contexto.abort(_STATUS.get(erro.codigo, grpc.StatusCode.INTERNAL), erro.mensagem)


def _usuario(dados):
    return pb.Usuario(id=dados["id"], nome=dados["nome"], idade=dados["idade"])


def _musica(dados):
    return pb.Musica(id=dados["id"], nome=dados["nome"], artista=dados["artista"])


def _playlist(dados):
    return pb.Playlist(
        id=dados["id"],
        nome=dados["nome"],
        usuario_id=dados["usuarioId"],
        musicas=[_musica(item) for item in dados["musicas"]],
    )


class StreamingGrpc(pb_grpc.StreamingMusicasServicer):
    def CriarUsuario(self, requisicao, contexto):
        return _rpc(
            contexto,
            lambda: _usuario(servico.criar_usuario(requisicao.nome, requisicao.idade)),
        )

    def ObterUsuario(self, requisicao, contexto):
        return _rpc(contexto, lambda: _usuario(servico.obter_usuario(requisicao.id)))

    def ListarUsuarios(self, requisicao, contexto):
        return _rpc(
            contexto,
            lambda: pb.ListaUsuarios(usuarios=[_usuario(item) for item in servico.listar_usuarios()]),
        )

    def AtualizarUsuario(self, requisicao, contexto):
        nome = requisicao.nome if requisicao.HasField("nome") else None
        idade = requisicao.idade if requisicao.HasField("idade") else None
        return _rpc(contexto, lambda: _usuario(servico.atualizar_usuario(requisicao.id, nome, idade)))

    def RemoverUsuario(self, requisicao, contexto):
        def acao():
            servico.remover_usuario(requisicao.id)
            return pb.Vazio()

        return _rpc(contexto, acao)

    def CriarMusica(self, requisicao, contexto):
        return _rpc(
            contexto,
            lambda: _musica(servico.criar_musica(requisicao.nome, requisicao.artista)),
        )

    def ObterMusica(self, requisicao, contexto):
        return _rpc(contexto, lambda: _musica(servico.obter_musica(requisicao.id)))

    def ListarMusicas(self, requisicao, contexto):
        return _rpc(
            contexto,
            lambda: pb.ListaMusicas(musicas=[_musica(item) for item in servico.listar_musicas()]),
        )

    def AtualizarMusica(self, requisicao, contexto):
        nome = requisicao.nome if requisicao.HasField("nome") else None
        artista = requisicao.artista if requisicao.HasField("artista") else None
        return _rpc(
            contexto,
            lambda: _musica(servico.atualizar_musica(requisicao.id, nome, artista)),
        )

    def RemoverMusica(self, requisicao, contexto):
        def acao():
            servico.remover_musica(requisicao.id)
            return pb.Vazio()

        return _rpc(contexto, acao)

    def CriarPlaylist(self, requisicao, contexto):
        return _rpc(
            contexto,
            lambda: _playlist(
                servico.criar_playlist(
                    requisicao.nome,
                    requisicao.usuario_id,
                    list(requisicao.musica_ids),
                )
            ),
        )

    def ObterPlaylist(self, requisicao, contexto):
        return _rpc(contexto, lambda: _playlist(servico.obter_playlist(requisicao.id)))

    def ListarPlaylists(self, requisicao, contexto):
        return _rpc(
            contexto,
            lambda: pb.ListaPlaylists(
                playlists=[_playlist(item) for item in servico.listar_playlists()]
            ),
        )

    def AtualizarPlaylist(self, requisicao, contexto):
        nome = requisicao.nome if requisicao.HasField("nome") else None
        return _rpc(
            contexto,
            lambda: _playlist(
                servico.atualizar_playlist(
                    requisicao.id,
                    nome=nome,
                    musica_ids=list(requisicao.musica_ids),
                    substituir_musicas=requisicao.substituir_musicas,
                )
            ),
        )

    def RemoverPlaylist(self, requisicao, contexto):
        def acao():
            servico.remover_playlist(requisicao.id)
            return pb.Vazio()

        return _rpc(contexto, acao)

    def ListarPlaylistsDoUsuario(self, requisicao, contexto):
        return _rpc(
            contexto,
            lambda: pb.ListaPlaylists(
                playlists=[
                    _playlist(item) for item in servico.listar_playlists_do_usuario(requisicao.id)
                ]
            ),
        )

    def ListarMusicasDaPlaylist(self, requisicao, contexto):
        return _rpc(
            contexto,
            lambda: pb.ListaMusicas(
                musicas=[_musica(item) for item in servico.listar_musicas_da_playlist(requisicao.id)]
            ),
        )

    def ListarPlaylistsComMusica(self, requisicao, contexto):
        return _rpc(
            contexto,
            lambda: pb.ListaPlaylists(
                playlists=[
                    _playlist(item) for item in servico.listar_playlists_com_musica(requisicao.id)
                ]
            ),
        )

    def AdicionarMusicaNaPlaylist(self, requisicao, contexto):
        return _rpc(
            contexto,
            lambda: _playlist(
                servico.adicionar_musica_na_playlist(requisicao.playlist_id, requisicao.musica_id)
            ),
        )

    def RemoverMusicaDaPlaylist(self, requisicao, contexto):
        return _rpc(
            contexto,
            lambda: _playlist(
                servico.remover_musica_da_playlist(requisicao.playlist_id, requisicao.musica_id)
            ),
        )


def main():
    from concurrent import futures

    servidor = grpc.server(futures.ThreadPoolExecutor(max_workers=8))
    pb_grpc.add_StreamingMusicasServicer_to_server(StreamingGrpc(), servidor)
    servidor.add_insecure_port("127.0.0.1:8004")
    servidor.start()
    print("gRPC em 127.0.0.1:8004")
    servidor.wait_for_termination()


if __name__ == "__main__":
    main()
