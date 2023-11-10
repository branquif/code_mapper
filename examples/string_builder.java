
package br.com.raiadrogasil.emissornfe.business;


/**
 * Implementa as regras particulares para a cria��o de uma nota fiscal de devolu��o ao consumidor.

 */
public class NFeCompraIncorporacaoBusiness extends NFeBusiness {

	private Logger log = Logger.getLogger(this.getClass().getName());
	private String AMBIENTE;

	public NFeCompraIncorporacaoBusiness(final EntityManager em) throws Exception {
		super.em = em;
		ParametrosSistemaFacade.getInstance().carregarParametrosSistema();
		this.AMBIENTE = ParametrosSistemaFacade.getInstance().findByParametroSistema("AMBIENTE");
	}



	@SuppressWarnings("unused")
	private TbProduto getTbProduto(long cdProduto) {
		final String select =
				"select * from tb_produto "
				+ "where cd_produto = ? ";
		final Query qry = em.createNativeQuery(select, TbProduto.class);
		qry.setParameter(1, cdProduto);
		return (TbProduto) qry.getSingleResult();
	}


	@SuppressWarnings("unused")
	private Long getTbNfOriginal(long cdFilial, int cdProduto, int tpProcesso) throws SQLException {
		Long idNf = 0L;
		try {
			StringBuilder sql = new StringBuilder();
			sql.append(" SELECT /*+FULL(N)*/ N.ID_NF ");
			sql.append("     FROM TB_NF N ");
			sql.append("    INNER JOIN TB_NF_ITEM NFI ON (N.ID_NF = NFI.ID_NF) ");
			sql.append("    INNER JOIN TB_PRO\acDUTO PROD ON (PROD.CD_PRODUTO = NFI.CD_PRODUTO) ");
			sql.append("    WHERE N.CD_OPERACAO_FISCAL = 1 ");
			sql.append("          AND N.ID_CLIENTE IN (2400642,52307619) ");
			sql.append("          AND N.CD_FILIAL IN (?)");
			sql.append("          AND (NFI.CD_PRODUTO = ? OR PROD.CD_CLAS_FISCAL = (SELECT CD_CLAS_FISCAL FROM TB_PRODUTO WHERE CD_PRODUTO = NFI.CD_PRODUTO))");
			sql.append("          AND N.DT_EMISSAO BETWEEN SYSDATE-200 AND SYSDATE-45 ");
			sql.append("          AND ROWNUM <= 1");
			log.log(Level.INFO, "[PARAMETERS] getTbNfOriginal CDFILIAL: " + cdFilial + " || CDPRODUTO: " + cdProduto);
			log.log(Level.INFO, "[QUERY] getTbNfOriginal: " + sql.toString());
			final Query qry = em.createNativeQuery(sql.toString());
			qry.setParameter(1, cdFilial);
			qry.setParameter(2, cdProduto);
			idNf = ((BigDecimal) qry.getSingleResult()).longValue();
		} catch (NoResultException e) {

			StringBuilder sql = new StringBuilder();
			sql.append(" SELECT FIL.CD_FILIAL,TG.SG_ESTADO");
			sql.append("  FROM TB_FILIAL FIL");
			sql.append("  INNER JOIN TB_ENDERECO_GERAL TG ON (TG.CD_FILIAL = FIL.CD_FILIAL)");
			sql.append(" WHERE TG.SG_ESTADO = (SELECT SG_ESTADO FROM TB_ENDERECO_GERAL WHERE CD_FILIAL = ?)");
			sql.append("        AND TG.SG_ESTADO IS NOT NULL");
			sql.append("        AND FIL.CD_FILIAL NOT IN (?)");
			final Query qry = em.createNativeQuery(sql.toString());
			qry.setParameter(1, cdFilial);
			qry.setParameter(2, cdFilial);
			for(Object record: qry.getResultList()){
				Object[] linha = (Object[]) record;
				sql = new StringBuilder();
				sql.append(" SELECT /*+FULL(N)*/ N.ID_NF ");
				sql.append("     FROM TB_NF N ");
				sql.append("    INNER JOIN TB_NF_ITEM NFI ON (N.ID_NF = NFI.ID_NF) ");
				sql.append("    INNER JOIN TB_PRODUTO PROD ON (PROD.CD_PRODUTO = NFI.CD_PRODUTO) ");
				sql.append("    WHERE N.CD_OPERACAO_FISCAL = 1 ");
				sql.append("          AND N.ID_CLIENTE IN (2400642,52307619) ");
				sql.append("          AND N.CD_FILIAL IN (SELECT FIL.CD_FILIAL");
				sql.append("                                FROM TB_FILIAL FIL");
				sql.append("                                INNER JOIN TB_ENDERECO_GERAL TG ON (TG.CD_FILIAL = FIL.CD_FILIAL AND TG.SG_ESTADO IS NOT NULL)");
				sql.append("                               WHERE TG.SG_ESTADO = (SELECT SG_ESTADO FROM TB_ENDERECO_GERAL WHERE CD_FILIAL = ?))");
				sql.append("          AND (NFI.CD_PRODUTO = ? OR PROD.CD_CLAS_FISCAL = (SELECT CD_CLAS_FISCAL FROM TB_PRODUTO WHERE CD_PRODUTO = NFI.CD_PRODUTO))");
				sql.append("          AND N.DT_EMISSAO BETWEEN SYSDATE-200 AND SYSDATE-45 ");
				sql.append("          AND ROWNUM <= 1");
				final Query query = em.createNativeQuery(sql.toString());
				query.setParameter(1, (BigDecimal)linha[0]);
				query.setParameter(2, cdProduto);
				try {
					idNf = ((BigDecimal) query.getSingleResult()).longValue();
					log.log(Level.INFO, "[PARAMETERS] getTbNfOriginal CDFILIAL: " + (BigDecimal)linha[0] + " || CDPRODUTO: " + cdProduto);
					log.log(Level.INFO, "[QUERY] getTbNfOriginal: " + sql.toString());
					break;
				} catch (NoResultException e2) {
					log.log(Level.WARNING,"[WANR] N�o encontrou idNf valido para filial " + (BigDecimal)linha[0]);
				}
			}
		}
		if (isNullOrBlankNumber(idNf)){
			StringBuilder sql = new StringBuilder();
			sql.append(" SELECT /*+FULL(N)*/ N.ID_NF ");
			sql.append("     FROM TB_NF N ");
			sql.append("    INNER JOIN TB_NF_ITEM NFI ON (N.ID_NF = NFI.ID_NF) ");
			sql.append("    INNER JOIN TB_PRODUTO PROD ON (PROD.CD_PRODUTO = NFI.CD_PRODUTO) ");
			sql.append("    WHERE N.CD_OPERACAO_FISCAL = 1 ");
			sql.append("          AND N.ID_CLIENTE IN (2400642,52307619) ");
//			sql.append("          AND N.CD_FILIAL IN (?)");
			sql.append("          AND (NFI.CD_PRODUTO = ? OR PROD.CD_CLAS_FISCAL = (SELECT CD_CLAS_FISCAL FROM TB_PRODUTO WHERE CD_PRODUTO = NFI.CD_PRODUTO))");
			sql.append("          AND N.DT_EMISSAO BETWEEN SYSDATE-200 AND SYSDATE-45 ");
			sql.append("          AND ROWNUM <= 1");
			log.log(Level.INFO, "[PARAMETERS] getTbNfOriginal CDFILIAL: " + cdFilial + " || CDPRODUTO: " + cdProduto);
			log.log(Level.INFO, "[QUERY] getTbNfOriginal: " + sql.toString());
			final Query qry = em.createNativeQuery(sql.toString());
			qry.setParameter(1, cdFilial);
			qry.setParameter(2, cdProduto);
			idNf = ((BigDecimal) qry.getSingleResult()).longValue();
		}
		return idNf;
	}
