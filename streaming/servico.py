"""Regras do streaming de músicas, independentes do protocolo.

O diagrama do enunciado liga três recursos:

- Usuário (ID, nome, idade) possui uma coleção de playlists (0..*);
- Playlist (ID, nome) pertence a um usuário e contém 1..* músicas;
- Música (ID, nome, artista) pertence ao catálogo do serviço e entra em 0..* playlists.
"""

from __future__ import annotations

from dataclasses import dataclass
from threading import Lock


class ErroServico(Exception):
    """Erro de negócio. `codigo` é NAO_ENCONTRADO, VALIDACAO ou CONFLITO."""

    def __init__(self, codigo: str, mensagem: str) -> None:
        super().__init__(mensagem)
        self.codigo = codigo
        self.mensagem = mensagem


@dataclass
class _Usuario:
    id: int
    nome: str
    idade: int


@dataclass
class _Musica:
    id: int
    nome: str
    artista: str


@dataclass
class _Playlist:
    id: int
    nome: str
    usuario_id: int
    musica_ids: list


class StreamingServico:
    def __init__(self, com_exemplo: bool = True) -> None:
        self._lock = Lock()
        self._usuarios = {}
        self._musicas = {}
        self._playlists = {}
        self._seq = {"usuario": 0, "musica": 0, "playlist": 0}
        if com_exemplo:
            self._carregar_exemplo()

    def criar_usuario(self, nome, idade):
        with self._lock:
            usuario = _Usuario(self._novo_id("usuario"), self._texto(nome, "Nome"), self._idade(idade))
            self._usuarios[usuario.id] = usuario
            return self._dados_usuario(usuario)

    def obter_usuario(self, usuario_id):
        with self._lock:
            return self._dados_usuario(self._exigir_usuario(usuario_id))

    def listar_usuarios(self):
        with self._lock:
            return [self._dados_usuario(u) for u in self._usuarios.values()]

    def atualizar_usuario(self, usuario_id, nome=None, idade=None):
        with self._lock:
            if nome is None and idade is None:
                raise ErroServico("VALIDACAO", "Informe nome ou idade para alterar.")
            usuario = self._exigir_usuario(usuario_id)
            if nome is not None:
                usuario.nome = self._texto(nome, "Nome")
            if idade is not None:
                usuario.idade = self._idade(idade)
            return self._dados_usuario(usuario)

    def remover_usuario(self, usuario_id):
        with self._lock:
            self._exigir_usuario(usuario_id)
            ids = [p.id for p in self._playlists.values() if p.usuario_id == usuario_id]
            for playlist_id in ids:
                del self._playlists[playlist_id]
            del self._usuarios[usuario_id]

    def criar_musica(self, nome, artista):
        with self._lock:
            musica = _Musica(
                self._novo_id("musica"),
                self._texto(nome, "Nome"),
                self._texto(artista, "Artista"),
            )
            self._musicas[musica.id] = musica
            return self._dados_musica(musica)

    def obter_musica(self, musica_id):
        with self._lock:
            return self._dados_musica(self._exigir_musica(musica_id))

    def listar_musicas(self):
        with self._lock:
            return [self._dados_musica(m) for m in self._musicas.values()]

    def atualizar_musica(self, musica_id, nome=None, artista=None):
        with self._lock:
            if nome is None and artista is None:
                raise ErroServico("VALIDACAO", "Informe nome ou artista para alterar.")
            musica = self._exigir_musica(musica_id)
            if nome is not None:
                musica.nome = self._texto(nome, "Nome")
            if artista is not None:
                musica.artista = self._texto(artista, "Artista")
            return self._dados_musica(musica)

    def remover_musica(self, musica_id):
        with self._lock:
            self._exigir_musica(musica_id)
            for playlist in self._playlists.values():
                if musica_id in playlist.musica_ids and len(playlist.musica_ids) == 1:
                    raise ErroServico(
                        "VALIDACAO",
                        "A música é a única da playlist %s (%s)." % (playlist.id, playlist.nome),
                    )
            for playlist in self._playlists.values():
                playlist.musica_ids = [i for i in playlist.musica_ids if i != musica_id]
            del self._musicas[musica_id]

    def criar_playlist(self, nome, usuario_id, musica_ids):
        with self._lock:
            self._exigir_usuario(usuario_id)
            playlist = _Playlist(
                self._novo_id("playlist"),
                self._texto(nome, "Nome"),
                usuario_id,
                self._validar_musicas(musica_ids),
            )
            self._playlists[playlist.id] = playlist
            return self._dados_playlist(playlist)

    def obter_playlist(self, playlist_id):
        with self._lock:
            return self._dados_playlist(self._exigir_playlist(playlist_id))

    def listar_playlists(self):
        with self._lock:
            return [self._dados_playlist(p) for p in self._playlists.values()]

    def atualizar_playlist(self, playlist_id, nome=None, musica_ids=None, substituir_musicas=False):
        with self._lock:
            if nome is None and not substituir_musicas:
                raise ErroServico("VALIDACAO", "Informe o nome ou a nova lista de músicas.")
            playlist = self._exigir_playlist(playlist_id)
            if nome is not None:
                playlist.nome = self._texto(nome, "Nome")
            if substituir_musicas:
                playlist.musica_ids = self._validar_musicas(musica_ids)
            return self._dados_playlist(playlist)

    def remover_playlist(self, playlist_id):
        with self._lock:
            self._exigir_playlist(playlist_id)
            del self._playlists[playlist_id]

    def listar_playlists_do_usuario(self, usuario_id):
        with self._lock:
            self._exigir_usuario(usuario_id)
            return [
                self._dados_playlist(p)
                for p in self._playlists.values()
                if p.usuario_id == usuario_id
            ]

    def listar_musicas_da_playlist(self, playlist_id):
        with self._lock:
            playlist = self._exigir_playlist(playlist_id)
            return [self._dados_musica(self._musicas[i]) for i in playlist.musica_ids]

    def listar_playlists_com_musica(self, musica_id):
        with self._lock:
            self._exigir_musica(musica_id)
            return [
                self._dados_playlist(p)
                for p in self._playlists.values()
                if musica_id in p.musica_ids
            ]

    def adicionar_musica_na_playlist(self, playlist_id, musica_id):
        with self._lock:
            playlist = self._exigir_playlist(playlist_id)
            self._exigir_musica(musica_id)
            if musica_id in playlist.musica_ids:
                raise ErroServico("CONFLITO", "A música já está na playlist.")
            playlist.musica_ids.append(musica_id)
            return self._dados_playlist(playlist)

    def remover_musica_da_playlist(self, playlist_id, musica_id):
        with self._lock:
            playlist = self._exigir_playlist(playlist_id)
            if musica_id not in playlist.musica_ids:
                raise ErroServico("NAO_ENCONTRADO", "A playlist não contém essa música.")
            if len(playlist.musica_ids) == 1:
                raise ErroServico("VALIDACAO", "A playlist precisa ter ao menos uma música.")
            playlist.musica_ids = [i for i in playlist.musica_ids if i != musica_id]
            return self._dados_playlist(playlist)

    def _carregar_exemplo(self):
        self._criar_direto_usuario("Ana", 22)
        self._criar_direto_usuario("Bruno", 30)
        self._criar_direto_musica("Bohemian Rhapsody", "Queen")
        self._criar_direto_musica("Garota de Ipanema", "Tom Jobim")
        self._criar_direto_musica("Smells Like Teen Spirit", "Nirvana")
        self._criar_direto_musica("Águas de Março", "Elis Regina")
        self._criar_direto_playlist("Clássicos", 1, [1, 2])
        self._criar_direto_playlist("Viagem", 1, [2, 4])
        self._criar_direto_playlist("Rock", 2, [3])

    def _criar_direto_usuario(self, nome, idade):
        usuario = _Usuario(self._novo_id("usuario"), nome, idade)
        self._usuarios[usuario.id] = usuario

    def _criar_direto_musica(self, nome, artista):
        musica = _Musica(self._novo_id("musica"), nome, artista)
        self._musicas[musica.id] = musica

    def _criar_direto_playlist(self, nome, usuario_id, musica_ids):
        playlist = _Playlist(self._novo_id("playlist"), nome, usuario_id, list(musica_ids))
        self._playlists[playlist.id] = playlist

    def _novo_id(self, chave):
        self._seq[chave] += 1
        return self._seq[chave]

    def _texto(self, valor, campo):
        if not isinstance(valor, str):
            raise ErroServico("VALIDACAO", "%s deve ser texto." % campo)
        limpo = valor.strip()
        if not limpo:
            raise ErroServico("VALIDACAO", "%s é obrigatório." % campo)
        return limpo

    def _idade(self, valor):
        if isinstance(valor, bool) or not isinstance(valor, int):
            raise ErroServico("VALIDACAO", "Idade deve ser um número inteiro.")
        if valor < 0 or valor > 130:
            raise ErroServico("VALIDACAO", "Idade deve estar entre 0 e 130.")
        return valor

    def _id(self, valor, campo):
        if isinstance(valor, bool) or not isinstance(valor, int) or valor <= 0:
            raise ErroServico("VALIDACAO", "%s inválido." % campo)
        return valor

    def _exigir_usuario(self, usuario_id):
        usuario_id = self._id(usuario_id, "Usuário")
        usuario = self._usuarios.get(usuario_id)
        if usuario is None:
            raise ErroServico("NAO_ENCONTRADO", "Usuário %s não encontrado." % usuario_id)
        return usuario

    def _exigir_musica(self, musica_id):
        musica_id = self._id(musica_id, "Música")
        musica = self._musicas.get(musica_id)
        if musica is None:
            raise ErroServico("NAO_ENCONTRADO", "Música %s não encontrada." % musica_id)
        return musica

    def _exigir_playlist(self, playlist_id):
        playlist_id = self._id(playlist_id, "Playlist")
        playlist = self._playlists.get(playlist_id)
        if playlist is None:
            raise ErroServico("NAO_ENCONTRADO", "Playlist %s não encontrada." % playlist_id)
        return playlist

    def _validar_musicas(self, musica_ids):
        if not isinstance(musica_ids, (list, tuple)) or len(musica_ids) == 0:
            raise ErroServico("VALIDACAO", "A playlist precisa ter ao menos uma música.")
        vistos = []
        for item in musica_ids:
            musica_id = self._id(item, "Música")
            if musica_id not in self._musicas:
                raise ErroServico("NAO_ENCONTRADO", "Música %s não encontrada." % musica_id)
            if musica_id in vistos:
                raise ErroServico("VALIDACAO", "A lista de músicas não pode ter duplicatas.")
            vistos.append(musica_id)
        return vistos

    def _dados_usuario(self, usuario):
        return {"id": usuario.id, "nome": usuario.nome, "idade": usuario.idade}

    def _dados_musica(self, musica):
        return {"id": musica.id, "nome": musica.nome, "artista": musica.artista}

    def _dados_playlist(self, playlist):
        return {
            "id": playlist.id,
            "nome": playlist.nome,
            "usuarioId": playlist.usuario_id,
            "musicas": [self._dados_musica(self._musicas[i]) for i in playlist.musica_ids],
        }
