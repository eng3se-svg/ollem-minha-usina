# -*- coding: utf-8 -*-
"""Contrato da FONTE DE DADOS do app. Hoje: FieldOps (produção) e Demo (testes).
Para trocar de fonte, basta criar outra classe com estes métodos e apontar APP_FONTE para ela.

Formato de uma USINA (o app usa exatamente estes campos):
{
  "id": "str",                  identificador estável da usina na fonte
  "nome": "str",                opcional; o app mostra "Usina em <bairro>"
  "bairro": "str",              bairro ou cidade (nunca o endereço completo)
  "kwp": 14.85,                 potência instalada
  "estado": "online|offline|alarme",
  "potencia_kw": 4.46 | null,   potência agora
  "hoje_kwh": 7.2, "mes_kwh": 880.1 | null, "total_kwh": 29298.0 | null,
  "atualizado": 1794831203.7,   epoch (s) da última leitura da fonte
  "ultimo_online": 1794831203.7,epoch (s) da última comunicação da usina
  "esperado_meses": [12 x kWh/mês] | null,   do projeto (melhor fonte do esperado)
  "pvgis": [12 x kWh/kWp/mês] | null,        alternativa ao projeto
  "distribuidora": "Enel Rio" | null, "tarifa": 1.06 | null,
  "investido": 45000 | null,    valor do contrato em R$ (para o "Retorno do investimento"; sem ele o cartão não aparece)
  "g": {"AAAA-MM-DD": kWh, ...}               geração diária (pode ser só um período)
}
NUNCA devolver nome do portal do fabricante, login, senha, CPF ou telefone dentro da usina.
"""


class ClienteFonte(dict):
    """{'id', 'nome', 'usinas': [ids]}"""


class Fonte:
    nome = 'base'

    def buscar_cliente(self, doc: str, telefone: str):
        """Devolve ClienteFonte se o CPF/CNPJ (só dígitos) e o celular (DDD+número) forem do MESMO cadastro; senão None."""
        raise NotImplementedError

    def cliente(self, cliente_id: str):
        """Dados atuais do cliente (para revalidar a sessão e listar usinas)."""
        raise NotImplementedError

    def usinas(self, cliente_id: str, dias: int):
        """Lista de usinas do cliente, cada uma com 'g' dos últimos `dias` dias."""
        raise NotImplementedError

    def geracao(self, cliente_id: str, usina_id: str, de: str, ate: str):
        """{'AAAA-MM-DD': kWh} da usina no período (inclusive). Só se a usina for do cliente."""
        raise NotImplementedError

    def registrar_solicitacao(self, cliente_id: str, usina_id: str, tipo: str, detalhes: dict) -> str:
        """Cria a solicitação na fonte (ordem de serviço / oportunidade / pedido de relatório). Devolve o id externo."""
        raise NotImplementedError

    def situacao_solicitacoes(self, cliente_id: str, ids_externos: list) -> dict:
        """{id_externo: 'recebido'|'agendado'|'feito'|'gerando'|'pronto'|'respondido'|'cancelado', ...}. Pode devolver {}."""
        return {}

    def anexo_relatorio(self, cliente_id: str, id_externo: str):
        """(bytes_pdf, nome) do relatório pronto, ou None."""
        return None

    def excluir_conta(self, cliente_id: str):
        """Avisa a fonte que o cliente excluiu a conta do app (opcional)."""
        return None
