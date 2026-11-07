# Sistema de Gest?o Acad?mica UFPA

> **Comunidade 9** ? Fonte prim?ria: `server.py`, `README.md`

## Vis?o Geral
Mapeamento das especificidades institucionais da Universidade Federal do Par? (UFPA) no ambiente SIGAA.

---

## ?? Peculiaridades do SIGAA UFPA
1. **Autentica??o em Dois N?veis:** Para algumas opera??es cadastrais (como atualiza??o de perfil), o SIGAA requer autentica??o em dois passos exigindo confirma??o de dados pessoais (CPF, Data de Nascimento e Senha).
2. **Sazonalidade de Matr?cula:** Durante o processamento das turmas no in?cio de cada per?odo letivo, a emiss?o de hist?ricos e atestados ? temporariamente bloqueada pela PROEG/UFPA.
3. **Consultas P?blicas de Turmas:**
   * Lista p?blica de turmas: `https://sigaa.ufpa.br/sigaa/public/turmas/listar.jsf?aba=p-ensino`
   * Busca de componentes curriculares: `https://sigaa.ufpa.br/sigaa/public/componentes/busca_componentes.jsf?aba=p-ensino`
