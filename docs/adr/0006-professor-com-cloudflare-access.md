# Professor remoto com código por e-mail

O professor pediu a substituição do emparelhamento local por Cloudflare Access, limitado a `atila.sos@gmail.com` e ao fornecedor One-time PIN. Protegemos todo o hostname já existente `estudio.infantinho.xyz`; o hostname `pagecraft.infantinho.xyz` continua público para os alunos. Esta separação permite proteger também as APIs e pré-visualizações sem impor login aos alunos, mas exige que todas as ligações partilhadas com a turma usem o hostname público.

O servidor só concede o papel Professor remoto quando recebe, pelo canal do túnel e hostname privado, um JWT assinado para a audiência desta aplicação, com emissor, validade e e-mail corretos. Cookies locais e códigos antigos não autenticam remotamente. A confiança direta no computador mantém o bootstrap de automação. Esta decisão substitui apenas o mecanismo de professor remoto do ADR-0005; cada atividade continua a precisar de revisão do professor antes de ser publicada.
