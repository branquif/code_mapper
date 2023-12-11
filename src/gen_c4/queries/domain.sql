WITH RECURSIVE domains (code, name, description, level, path) AS (
  SELECT code, name, description, 0 AS level, cast(code as text) AS path
  FROM TB_DOMAIN
  WHERE parent_code IS NULL  -- Root elements

  UNION ALL

  SELECT d.code, d.name, d.description, ancestor.level + 1 AS level, ancestor.path || '->' || cast(d.code as text)
  FROM TB_DOMAIN AS d
  INNER JOIN domains AS ancestor ON d.parent_code = ancestor.code
)
SELECT * FROM domains
ORDER BY path;