package br.com.raiadrogasil.bluesky.financeiro.dao;

import java.util.ArrayList;
import java.util.Date;
import java.util.List;

import javax.persistence.EntityManager;
import javax.persistence.Query;

import br.com.raiadrogasil.bluesky.comum.util.ValueConverter;
import br.com.raiadrogasil.bluesky.financeiro.vo.FiltroFaturaVO;
import br.com.raiadrogasil.bluesky.vo.ArquivoFaturamentoVO;

public class ArquivosFaturamentoDAO {

	private EntityManager em;

	public ArquivosFaturamentoDAO(EntityManager em) {
		this.em = em;
	}

	public List<ArquivoFaturamentoVO> buscarArquivosFaturamento(FiltroFaturaVO filtroFaturaVO) throws Exception {
		try {
			List<ArquivoFaturamentoVO> list = new ArrayList<ArquivoFaturamentoVO>();
			Query query = em.createNativeQuery(getQueryArquivosFaturamento(filtroFaturaVO).toString());
			int i = 1;
			query.setParameter(i++, filtroFaturaVO.getContrato().getCdContrato());
			query.setParameter(i++, filtroFaturaVO.getDataInicio());
			query.setParameter(i++, filtroFaturaVO.getDataFim());
			
			list = montarListaArquivosFaturamento(query.getResultList());
			
			return list;
			
		} catch (Exception e) {
			String mensagem = "Erro ao obter os Arquivo de Faturamento";
			throw new Exception(mensagem, e);			
		}		
	}
	
	public List<ArquivoFaturamentoVO> buscarArquivosFaturamento(FiltroFaturaVO filtroFaturaVO, Long nrUnidade) throws Exception {
		try {
			List<ArquivoFaturamentoVO> list = new ArrayList<ArquivoFaturamentoVO>();
			Query query = em.createNativeQuery(getQueryArquivosFaturamentoPorUnidade(filtroFaturaVO, nrUnidade).toString());
			int i = 1;
			query.setParameter(i++, filtroFaturaVO.getContrato().getCdContrato());
			query.setParameter(i++, nrUnidade);
			query.setParameter(i++, filtroFaturaVO.getDataInicio());
			query.setParameter(i++, filtroFaturaVO.getDataFim());
			
			list = montarListaArquivosFaturamento(query.getResultList());
			
			return list;
			
		} catch (Exception e) {
			String mensagem = "Erro ao obter os Arquivo de Faturamento";
			throw new Exception(mensagem, e);			
		}		
	}
	
	private List<ArquivoFaturamentoVO> montarListaArquivosFaturamento(List resultList) {
		List<ArquivoFaturamentoVO> list = new ArrayList<ArquivoFaturamentoVO>();
		
		@SuppressWarnings("unchecked")
		List<Object[]> result = (List<Object[]>) resultList;
		for (Object[] objects : result) {
			ArquivoFaturamentoVO vo = new ArquivoFaturamentoVO();
			vo.setIdFatura(ValueConverter.castToLong(objects[BuscarDetalhes.Coluna.ID_FATURA.getIndex()]));
			vo.setDtVencimento(ValueConverter.castToDate(objects[BuscarDetalhes.Coluna.DT_VENCIMENTO.getIndex()]));
			vo.setVlFatura(ValueConverter.castToBigDecimal(objects[BuscarDetalhes.Coluna.VL_FATURA.getIndex()]));
			vo.setDtPagamento(ValueConverter.castToDate(objects[BuscarDetalhes.Coluna.DT_PAGAMENTO.getIndex()]));
			vo.setVlPagamento(ValueConverter.castToBigDecimal(objects[BuscarDetalhes.Coluna.VL_PAGAMENTO.getIndex()]));
			vo.setNmEmpresa(ValueConverter.castToString(objects[BuscarDetalhes.Coluna.NM_UNIDADE.getIndex()]));
			vo.setBoleto(ValueConverter.castToString(objects[BuscarDetalhes.Coluna.BOLETO.getIndex()]));
			vo.setNotaDebitoCartaPagamento(ValueConverter.castToString(objects[BuscarDetalhes.Coluna.NOTA_DEBITO_CARTA_PAGAMENTO.getIndex()]));
			vo.setPrestacaoContasResumo(ValueConverter.castToString(objects[BuscarDetalhes.Coluna.PRESTACAO_CONTAS_RESUMO.getIndex()]));
			vo.setPrestacaoContasDetalhado(ValueConverter.castToString(objects[BuscarDetalhes.Coluna.PRESTACAO_CONTAS_DETALHADO.getIndex()]));
			vo.setDtFaturamento(ValueConverter.castToDate(objects[BuscarDetalhes.Coluna.DT_FATURAMENTO.getIndex()]));
			vo.setDtPeriodoInicio(ValueConverter.castToDate(objects[BuscarDetalhes.Coluna.DT_PERIODO_INICIO.getIndex()]));
			vo.setDtPeriodoFim(ValueConverter.castToDate(objects[BuscarDetalhes.Coluna.DT_PERIODO_FIM.getIndex()]));
			vo.setNrFatura(ValueConverter.castToBigDecimal(objects[BuscarDetalhes.Coluna.NR_UNIDADE.getIndex()]));
			list.add(vo);
		}
		
		return list;
	}

	private static class BuscarDetalhes {
		public enum Coluna {
			ID_FATURA(0),
			DT_VENCIMENTO(1),
			VL_FATURA(2),			
			DT_PAGAMENTO(3),
			VL_PAGAMENTO(4),
			NM_UNIDADE(5),
			BOLETO(6),
			NOTA_DEBITO_CARTA_PAGAMENTO(7),
			PRESTACAO_CONTAS_RESUMO(8),
			PRESTACAO_CONTAS_DETALHADO(9),
			DT_FATURAMENTO(10),
			DT_PERIODO_INICIO(11),
			DT_PERIODO_FIM(12),
			NR_UNIDADE(13);
			
			private final int index;
			Coluna(int index) { this.index = index; }
			public int getIndex() { return this.index; }
		}		
	}

	private StringBuilder getQueryArquivosFaturamento(FiltroFaturaVO filtroFaturaVO) {
		StringBuilder sqlBuscarArquivosFaturamento = new StringBuilder();
		sqlBuscarArquivosFaturamento
				.append(" SELECT f.id_fatura, ")
				.append("        f.dt_vencimento, ")
				.append("        f.vl_fatura, ")
				.append("        f.dt_pagamento, ")
				.append("        f.vl_pagamento, ")
				.append("        u.nm_unidade, ")
				.append("        (select fa.ds_caminho_arquivo ")
				.append("           from tb_bf_fatura_arquivo fa ")
				.append("          where fa.id_fatura = f.id_fatura ")
				.append("            and fa.nr_arquivo = ")
				.append("                (select max(fasq.nr_arquivo) ")
				.append("                   from tb_bf_fatura_arquivo fasq ")
				.append("                  where fasq.id_fatura = fa.id_fatura ")
				.append("                    and fasq.cd_tp_fatura_arquivo = 1)) as boleto, ")
				.append("        (select fa.ds_caminho_arquivo ")
				.append("           from tb_bf_fatura_arquivo fa ")
				.append("          where fa.id_fatura = f.id_fatura ")
				.append("            and fa.nr_arquivo = ")
				.append("                (select max(fasq.nr_arquivo) ")
				.append("                   from tb_bf_fatura_arquivo fasq ")
				.append("                  where fasq.id_fatura = fa.id_fatura ")
				.append("                    and (fasq.cd_tp_fatura_arquivo = 3 or ")
				.append("                        fasq.cd_tp_fatura_arquivo = 2))) as nota_debito_carta_pagamento, ")
				.append("        (select fa.ds_caminho_arquivo ")
				.append("           from tb_bf_fatura_arquivo fa ")
				.append("          where fa.id_fatura = f.id_fatura ")
				.append("            and fa.nr_arquivo = ")
				.append("                (select max(fasq.nr_arquivo) ")
				.append("                   from tb_bf_fatura_arquivo fasq ")
				.append("                  where fasq.id_fatura = fa.id_fatura ")
				.append("                    and fasq.cd_tp_fatura_arquivo = 4)) as prestacao_contas_resumo, ")
				.append("        (select fa.ds_caminho_arquivo ")
				.append("           from tb_bf_fatura_arquivo fa ")
				.append("          where fa.id_fatura = f.id_fatura ")
				.append("            and fa.nr_arquivo = ")
				.append("                (select max(fasq.nr_arquivo) ")
				.append("                   from tb_bf_fatura_arquivo fasq ")
				.append("                  where fasq.id_fatura = fa.id_fatura ")
				.append("                    and fasq.cd_tp_fatura_arquivo = 5)) as prestacao_contas_detalhado, ")
				.append("        f.dt_faturamento, ")
				.append("        f.dt_periodo_inicio, ")
				.append("        f.dt_periodo_fim, ")
				.append("        f.nr_fatura ")
				.append("   from tb_bf_fatura f, tb_bf_fatura_unidade u ")
				.append("  where f.cd_contrato = u.cd_contrato ")
				.append("    and f.nr_unidade = u.nr_unidade ")
				.append("    and f.cd_contrato = ? ");

		if(filtroFaturaVO.getDataInicio() != null && !filtroFaturaVO.getDataInicio().equals(""))
			sqlBuscarArquivosFaturamento.append("and f.dt_periodo_inicio >= ? ");
		if(filtroFaturaVO.getDataFim() != null && !filtroFaturaVO.getDataFim().equals(""))
			sqlBuscarArquivosFaturamento.append("and f.dt_periodo_fim <= ? ");

		sqlBuscarArquivosFaturamento.append("    order by f.id_fatura ");

		return sqlBuscarArquivosFaturamento;
	}
	
	private StringBuilder getQueryArquivosFaturamentoPorUnidade(FiltroFaturaVO filtroFaturaVO, Long nrUnidade) {
		StringBuilder sqlBuscarArquivosFaturamento = new StringBuilder();
		sqlBuscarArquivosFaturamento
				.append(" SELECT f.id_fatura, ")
				.append("        f.dt_vencimento, ")
				.append("        f.vl_fatura, ")
				.append("        f.dt_pagamento, ")
				.append("        f.vl_pagamento, ")
				.append("        u.nm_unidade, ")
				.append("        (select fa.ds_caminho_arquivo ")
				.append("           from tb_bf_fatura_arquivo fa ")
				.append("          where fa.id_fatura = f.id_fatura ")
				.append("            and fa.nr_arquivo = ")
				.append("                (select max(fasq.nr_arquivo) ")
				.append("                   from tb_bf_fatura_arquivo fasq ")
				.append("                  where fasq.id_fatura = fa.id_fatura ")
				.append("                    and fasq.cd_tp_fatura_arquivo = 1)) as boleto, ")
				.append("        (select fa.ds_caminho_arquivo ")
				.append("           from tb_bf_fatura_arquivo fa ")
				.append("          where fa.id_fatura = f.id_fatura ")
				.append("            and fa.nr_arquivo = ")
				.append("                (select max(fasq.nr_arquivo) ")
				.append("                   from tb_bf_fatura_arquivo fasq ")
				.append("                  where fasq.id_fatura = fa.id_fatura ")
				.append("                    and (fasq.cd_tp_fatura_arquivo = 3 or ")
				.append("                        fasq.cd_tp_fatura_arquivo = 2))) as nota_debito_carta_pagamento, ")
				.append("        (select fa.ds_caminho_arquivo ")
				.append("           from tb_bf_fatura_arquivo fa ")
				.append("          where fa.id_fatura = f.id_fatura ")
				.append("            and fa.nr_arquivo = ")
				.append("                (select max(fasq.nr_arquivo) ")
				.append("                   from tb_bf_fatura_arquivo fasq ")
				.append("                  where fasq.id_fatura = fa.id_fatura ")
				.append("                    and fasq.cd_tp_fatura_arquivo = 4)) as prestacao_contas_resumo, ")
				.append("        (select fa.ds_caminho_arquivo ")
				.append("           from tb_bf_fatura_arquivo fa ")
				.append("          where fa.id_fatura = f.id_fatura ")
				.append("            and fa.nr_arquivo = ")
				.append("                (select max(fasq.nr_arquivo) ")
				.append("                   from tb_bf_fatura_arquivo fasq ")
				.append("                  where fasq.id_fatura = fa.id_fatura ")
				.append("                    and fasq.cd_tp_fatura_arquivo = 5)) as prestacao_contas_detalhado, ")
				.append("        f.dt_faturamento, ")
				.append("        f.dt_periodo_inicio, ")
				.append("        f.dt_periodo_fim, ")
				.append("        f.nr_fatura ")
				.append("   from tb_bf_fatura f, tb_bf_fatura_unidade u ")
				.append("  where f.cd_contrato = u.cd_contrato ")
				.append("    and f.nr_unidade = u.nr_unidade ")
				.append("    and f.cd_contrato = ? ")
				.append("    and u.nr_unidade = ? ");

		if(filtroFaturaVO.getDataInicio() != null && !filtroFaturaVO.getDataInicio().equals(""))
			sqlBuscarArquivosFaturamento.append("and f.dt_periodo_inicio >= ? ");
		if(filtroFaturaVO.getDataFim() != null && !filtroFaturaVO.getDataFim().equals(""))
			sqlBuscarArquivosFaturamento.append("and f.dt_periodo_fim <= ? ");

		sqlBuscarArquivosFaturamento.append("    order by f.id_fatura ");

		return sqlBuscarArquivosFaturamento;
	}
}
