package br.com.raiadrogasil.bluesky.financeiro.dao;

import java.math.BigDecimal;
import java.text.SimpleDateFormat;
import java.util.Date;
import java.util.List;

import javax.persistence.EntityManager;
import javax.persistence.Query;

import br.com.raiadrogasil.bluesky.entity.fatura.Fatura;

public class FaturaDAO {

    private EntityManager em;
    SimpleDateFormat sdf = new SimpleDateFormat("dd/MM/yyyy");

    public FaturaDAO(EntityManager em){
        this.em = em;
    }

    @SuppressWarnings("unchecked")
    public List<Fatura> buscarFaturas(Long cdEmpresa, Long cdContrato, Date dtPeriodoFim,
                                      Date dtVencimento, Date dtVencimentoFim, BigDecimal vlFaturaIni, BigDecimal vlFaturaFim,
                                      List<Integer> situacaoContrato, Date dtFaturamentoIni, Date dtFatutamentoFim,
                                      Long tpPagamento, Long cdFaturaStatus, Date dtLiberacaoIni, Date dtLiberacaoFim,
                                      Long idFaturaIni, Long idFaturaFim, String atribuicaoSap, Integer tipoPme, Integer tipoFatura) throws Exception{

        StringBuilder sqlBuscarFaturas = new StringBuilder();

        try{

            addInicioQuery(sqlBuscarFaturas);

            montarQuery(cdEmpresa, cdContrato, dtPeriodoFim, dtVencimento,dtVencimentoFim, vlFaturaIni, vlFaturaFim, situacaoContrato, dtFaturamentoIni,
                dtFatutamentoFim, tpPagamento, cdFaturaStatus, dtLiberacaoIni, dtLiberacaoFim,
                idFaturaIni, idFaturaFim, atribuicaoSap,tipoPme, tipoFatura, sqlBuscarFaturas);

            Query query = em.createNativeQuery(sqlBuscarFaturas.toString(),Fatura.class);

            montarSetParameter(cdEmpresa, cdContrato, dtPeriodoFim, dtVencimento,dtVencimentoFim,
                vlFaturaIni, vlFaturaFim, situacaoContrato, dtFaturamentoIni,
                dtFatutamentoFim, tpPagamento, cdFaturaStatus, sdf,
                query, dtLiberacaoIni, dtLiberacaoFim, idFaturaIni, idFaturaFim, atribuicaoSap, tipoPme);

            return query.getResultList();

        }catch (Exception e) {
            String mensagem = "Erro ao obter os Arquivo de Faturamento";
            throw new Exception(mensagem, e);
        }
    }

    private void montarQuery(Long cdEmpresa, Long cdContrato, Date dtPeriodoFim, Date dtVencimento, Date dtVencimentoFim, BigDecimal vlFaturaIni,
                             BigDecimal vlFaturaFim, List<Integer> situacaoContrato, Date dtFaturamentoIni, Date dtFatutamentoFim,
                             Long tpPagamento, Long cdFaturaStatus, Date dtLiberacaoIni, Date dtLiberacaoFim,
                             Long idFaturaIni, Long idFaturaFim, String atribuicaoSap, Integer tipoPme, Integer tipoFatura,
                             StringBuilder sqlBuscarFaturas) {

        final int FATURA_PADRAO = 0;
        final int FATURA_PREMIUM = 1;

        if(cdContrato != null){
            sqlBuscarFaturas.append(" and f.cd_contrato = ?1 ");
        }

        if(dtPeriodoFim != null){
            sqlBuscarFaturas.append(" and f.dt_periodo_fim = ?2 ");
        }

        if(dtVencimento != null){
            sqlBuscarFaturas.append(" and f.dt_vencimento >= ?3 ");
        }

        if(dtVencimentoFim != null){
            sqlBuscarFaturas.append(" and f.dt_vencimento <= ?4 ");
        }

        if(vlFaturaIni != null && vlFaturaFim != null){
            sqlBuscarFaturas.append(" and f.vl_fatura between ?5 and ?6 ");
        }

        /*if(situacaoPgto != null && situacaoPgto == 1){
            sqlBuscarFaturas.append(" and f.dt_pagamento is null ");
        }

        if(situacaoPgto != null && situacaoPgto == 2){
            sqlBuscarFaturas.append(" and f.dt_pagamento is not null ");
        }*/

        if(dtFaturamentoIni != null && dtFatutamentoFim != null ){
            sqlBuscarFaturas.append(" and f.DT_PERIODO_INICIO >= ?7 and f.DT_PERIODO_FIM <= ?8 ");
        }

        if(tpPagamento != null){
            sqlBuscarFaturas.append(" and f.cd_tp_doc_recebimento = ?9 ");
        }

        if(cdFaturaStatus != null){
            sqlBuscarFaturas.append(" and f.cd_fatura_status = ?10 ");
        }

        if(dtLiberacaoIni != null && dtLiberacaoFim != null ){
            sqlBuscarFaturas.append(" and TRUNC(f.DT_LIBERACAO_FATURA) >= ?11 and  TRUNC(f.DT_LIBERACAO_FATURA) <= ?12 ");
        }

        if(idFaturaIni != null){
            sqlBuscarFaturas.append(" and F.ID_FATURA >= ?13 ");
        }

        if(idFaturaFim != null){
            sqlBuscarFaturas.append(" and F.ID_FATURA <= ?14 ");
        }

        if(!"".equals(atribuicaoSap)){
            sqlBuscarFaturas.append(" and (F.ID_SAP_LANC_FI = ?15 OR F.ID_RECEBIMENTO_SAP = ?15) ");
        }

        if(tipoPme == 0){
            sqlBuscarFaturas.append(" and C.FL_PME <> 1 ");
        }
        if (tipoPme == 1){
            sqlBuscarFaturas.append(" and C.FL_PME = 1 ");
        }

        if (tipoFatura == FATURA_PADRAO){
            sqlBuscarFaturas.append(" and (f.fl_fatura_premium is null or f.fl_fatura_premium = 0) ");
        }

        if (tipoFatura == FATURA_PREMIUM) {
            sqlBuscarFaturas.append(" and f.fl_fatura_premium = 1 ");
        }
    }

    public void addInicioQuery(StringBuilder sqlBuscarFaturas) {
        sqlBuscarFaturas
            .append(" select * from tb_bf_fatura f, ")
            .append(" tb_bf_fatura_unidade u,  TB_BF_CONTRATO c, TB_BF_CONTRATO_SITUACAO si  ")
            .append(" where f.cd_contrato = u.cd_contrato and ")
            .append(" f.nr_unidade = u.nr_unidade ")
            .append(" and  f.cd_contrato = c.cd_contrato ")
            .append(" and  u.cd_contrato = c.cd_contrato ")
            .append(" and si.CD_SIT_CONTRATO = c.CD_SIT_CONTRATO ");
    }

    public void montarSetParameter(Long cdEmpresa, Long cdContrato, Date dtPeriodoFim,
                                   Date dtVencimento, Date dtVencimentoFim, BigDecimal vlFaturaIni, BigDecimal vlFaturaFim,
                                   List<Integer> situacaoContrato, Date dtFaturamentoIni, Date dtFatutamentoFim,
                                   Long tpPagamento, Long cdFaturaStatus, SimpleDateFormat sdf,
                                   Query query, Date dtLiberacaoIni, Date dtLiberacaoFim,
                                   Long idFaturaIni, Long idFaturaFim, String atribuicaoSap, Integer tipoPme) {

        if(cdContrato != null){
            query.setParameter(1, cdContrato);
        }
        if(dtPeriodoFim != null){
            query.setParameter(2, dtPeriodoFim);
        }
        if(dtVencimento != null){
            query.setParameter(3, dtVencimento);
        }
        if(dtVencimentoFim != null){
            query.setParameter(4, dtVencimentoFim);
        }
        if(vlFaturaIni != null){
            query.setParameter(5, vlFaturaIni);
        }
        if(vlFaturaFim != null){
            query.setParameter(6, vlFaturaFim);
        }
        if(dtFaturamentoIni != null){
            query.setParameter(7, dtFaturamentoIni);
        }
        if(dtFatutamentoFim != null){
            query.setParameter(8, dtFatutamentoFim);
        }
        if(tpPagamento != null){
            query.setParameter(9, tpPagamento);
        }
        if(cdFaturaStatus != null){
            query.setParameter(10, cdFaturaStatus);
        }
        if(dtLiberacaoIni != null){
            query.setParameter(11, sdf.format(dtLiberacaoIni));
        }
        if(dtLiberacaoFim != null){
            query.setParameter(12, sdf.format(dtLiberacaoFim));
        }
        if(idFaturaIni != null){
            query.setParameter(13, idFaturaIni);
        }
        if(idFaturaFim != null){
            query.setParameter(14, idFaturaFim);
        }
        if(atribuicaoSap != null){
            query.setParameter(15, atribuicaoSap);
        }

    }
}
