"""Mostra as cinco consultas do enunciado no servidor REST.

Uso: python clientes/demo_rest.py
"""

import json
import sys
import urllib.request

BASE = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8001"

CONSULTAS = [
    ("Todos os usuários", "/usuarios"),
    ("Todas as músicas", "/musicas"),
    ("Playlists do usuário 1", "/usuarios/1/playlists"),
    ("Músicas da playlist 1", "/playlists/1/musicas"),
    ("Playlists com a música 2", "/musicas/2/playlists"),
]


def main():
    for titulo, caminho in CONSULTAS:
        with urllib.request.urlopen(BASE + caminho) as resposta:
            dados = json.load(resposta)
        print("\n== " + titulo)
        print(json.dumps(dados, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
