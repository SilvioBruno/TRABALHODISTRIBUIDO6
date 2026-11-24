"""Núcleo do serviço de streaming, compartilhado pelas quatro tecnologias."""

from streaming.servico import ErroServico, StreamingServico

__all__ = ["ErroServico", "StreamingServico"]
