# Imagens e áudio para as 28 palavras

As 28 ilustrações SVG são originais PageCraft, criadas com assistência Codex e disponibilizadas sob CC0-1.0. Têm um `viewBox` de 240 × 240, fundo transparente e um título acessível. Não contêm texto visível, emoji, scripts ou recursos externos.

Os MP3 usam a voz sintética portuguesa de Portugal `pt-PT-RaquelNeural`, fornecida por Microsoft Edge Read Aloud através de `edge-tts`, com velocidade `-12%`. A voz está sujeita aos termos do serviço Microsoft e não à licença CC0 das ilustrações. O manifesto identifica os textos gravados, os ficheiros e os seus hashes SHA-256.

São 28 palavras inteiras e 11 instruções. Não há gravações de fonemas nem de sílabas isoladas. A atividade deve começar muda e permitir ouvir por escolha da criança. As imagens e as demonstrações têm de permitir jogar também sem som.

Para gerar as imagens em falta:

```sh
python3 scripts/prepare_m28p_tic_assets.py --verify
```

Para gerar também os áudios em falta:

```sh
uv run --with edge-tts python scripts/prepare_m28p_tic_assets.py --audio --verify
```

O script preserva os ficheiros existentes. `--overwrite` permite regenerá-los. Os MP3 são descarregados para um ficheiro temporário e só substituem o destino depois de o pedido terminar. O manifesto é atualizado quando os ficheiros mudam.

A ilustração de `telhado` usa uma seta para assinalar a parte superior de uma casa. `gema` mostra o centro amarelo de um ovo partido. `quadro` representa um quadro de sala de aula. `cigarra` tem seis patas, olhos laterais e asas compridas com nervuras.
