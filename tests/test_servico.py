import unittest

from streaming.servico import ErroServico, StreamingServico


class TestStreaming(unittest.TestCase):
    def setUp(self):
        self.servico = StreamingServico()

    def test_consultas_do_enunciado(self):
        self.assertEqual([u["nome"] for u in self.servico.listar_usuarios()], ["Ana", "Bruno"])
        self.assertEqual(len(self.servico.listar_musicas()), 4)
        playlists = self.servico.listar_playlists_do_usuario(1)
        self.assertEqual([p["nome"] for p in playlists], ["Clássicos", "Viagem"])
        musicas = self.servico.listar_musicas_da_playlist(1)
        self.assertEqual(
            [m["nome"] for m in musicas],
            ["Bohemian Rhapsody", "Garota de Ipanema"],
        )
        com_a_musica = self.servico.listar_playlists_com_musica(2)
        self.assertEqual([p["nome"] for p in com_a_musica], ["Clássicos", "Viagem"])

    def test_crud_usuario_musica_e_playlist(self):
        usuario = self.servico.criar_usuario("  Caio ", 19)
        self.assertEqual(usuario["nome"], "Caio")
        self.assertEqual(self.servico.atualizar_usuario(usuario["id"], idade=20)["idade"], 20)

        musica = self.servico.criar_musica("Construção", "Chico Buarque")
        playlist = self.servico.criar_playlist("Novas", usuario["id"], [musica["id"]])
        self.assertEqual(playlist["musicas"][0]["nome"], "Construção")

        playlist = self.servico.adicionar_musica_na_playlist(playlist["id"], 1)
        self.assertEqual(len(playlist["musicas"]), 2)

        self.servico.remover_playlist(playlist["id"])
        self.servico.remover_musica(musica["id"])
        self.servico.remover_usuario(usuario["id"])
        with self.assertRaises(ErroServico) as erro:
            self.servico.obter_usuario(usuario["id"])
        self.assertEqual(erro.exception.codigo, "NAO_ENCONTRADO")

    def test_playlist_nao_fica_vazia(self):
        with self.assertRaises(ErroServico) as erro:
            self.servico.criar_playlist("Vazia", 1, [])
        self.assertEqual(erro.exception.codigo, "VALIDACAO")

        with self.assertRaises(ErroServico) as erro:
            self.servico.remover_musica_da_playlist(3, 3)
        self.assertEqual(erro.exception.codigo, "VALIDACAO")

        with self.assertRaises(ErroServico) as erro:
            self.servico.remover_musica(3)
        self.assertEqual(erro.exception.codigo, "VALIDACAO")

    def test_remover_musica_atualiza_as_playlists(self):
        self.servico.remover_musica(1)
        nomes = [m["nome"] for m in self.servico.listar_musicas_da_playlist(1)]
        self.assertEqual(nomes, ["Garota de Ipanema"])
        self.assertEqual(self.servico.listar_playlists_com_musica(2)[0]["nome"], "Clássicos")

    def test_remover_usuario_remove_as_playlists_dele(self):
        self.servico.remover_usuario(1)
        with self.assertRaises(ErroServico):
            self.servico.obter_playlist(1)
        self.assertEqual([p["nome"] for p in self.servico.listar_playlists()], ["Rock"])
        self.assertEqual(len(self.servico.listar_musicas()), 4)

    def test_conflito_e_referencia_inexistente(self):
        with self.assertRaises(ErroServico) as erro:
            self.servico.adicionar_musica_na_playlist(1, 1)
        self.assertEqual(erro.exception.codigo, "CONFLITO")

        with self.assertRaises(ErroServico) as erro:
            self.servico.criar_playlist("Órfã", 99, [1])
        self.assertEqual(erro.exception.codigo, "NAO_ENCONTRADO")

        with self.assertRaises(ErroServico) as erro:
            self.servico.atualizar_usuario(1)
        self.assertEqual(erro.exception.codigo, "VALIDACAO")


if __name__ == "__main__":
    unittest.main()
