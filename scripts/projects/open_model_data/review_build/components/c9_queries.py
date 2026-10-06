"""Independent SQLite census and headed-body queries; no persisted source text.

The grammar admits explicit section markers, not ambiguous numbered exercises.
Offsets are Unicode character offsets, as required by the Value contract.
Only numeric whole lines are excised. No spelling or hyphenation is changed.
"""

ELIGIBLE_SQL = """(
 source_file GLOB '[1-9]-klas-?*' OR source_file GLOB '10-klas-?*'
 OR source_file GLOB '11-klas-?*' OR source_file GLOB '10-11-klas-?*'
 OR source_file GLOB 'uni-?*'
)"""

# This SQL is deliberately independent of the Python heading parser. SQLite
# performs the census and reconstructs the complete expected response parts.
CTE = f"""WITH RECURSIVE
eligible AS (
 SELECT * FROM textbook_sections WHERE {ELIGIBLE_SQL}
),
lines(section_id, source_file, page_start, start, raw, rest) AS (
 SELECT section_id, source_file, page_start, 0,
 substr(full_text,1,CASE instr(full_text,char(10)) WHEN 0 THEN length(full_text)
 ELSE instr(full_text,char(10)) END),
 substr(full_text,1+CASE instr(full_text,char(10)) WHEN 0 THEN length(full_text)
 ELSE instr(full_text,char(10)) END) FROM eligible
 UNION ALL
 SELECT section_id,source_file,page_start,start+length(raw),
 substr(rest,1,CASE instr(rest,char(10)) WHEN 0 THEN length(rest)
 ELSE instr(rest,char(10)) END),
 substr(rest,1+CASE instr(rest,char(10)) WHEN 0 THEN length(rest)
 ELSE instr(rest,char(10)) END) FROM lines WHERE rest<>''
),
trimmed AS (
 SELECT *,trim(raw,' '||char(9)||char(10)||char(13)) AS heading,
 CASE WHEN trim(raw,' '||char(9)||char(10)||char(13))<>''
 AND trim(raw,' '||char(9)||char(10)||char(13)) NOT GLOB '*[^0-9]*'
 THEN '' ELSE raw END AS kept FROM lines
),
positioned AS (
 SELECT *,coalesce(sum(length(kept)) OVER (
 PARTITION BY section_id ORDER BY start ROWS BETWEEN UNBOUNDED PRECEDING AND 1 PRECEDING),0) AS clean_start,
 start+length(raw)-length(ltrim(raw,' '||char(9)||char(10)||char(13))) AS title_start
 FROM trimmed
),
tails AS (
 SELECT *,CASE
 WHEN substr(heading,1,1)='§' THEN ltrim(substr(heading,2),' '||char(9))
 WHEN substr(heading,1,5) IN ('Тема ','ТЕМА ') THEN substr(heading,6)
 WHEN substr(heading,1,7) IN ('Розділ ','РОЗДІЛ ') THEN substr(heading,8)
 END AS tail FROM positioned
),
numbers AS (
 SELECT *,length(tail)-length(ltrim(tail,'0123456789')) AS digits FROM tails
),
titles AS (
 SELECT *,substr(tail,digits+1) AS after_number FROM numbers
),
found AS (
 SELECT *,title_start+length(heading) AS title_end,
 clean_start+length(raw)-length(ltrim(raw,' '||char(9)||char(10)||char(13)))+length(heading) AS clean_end
 FROM titles WHERE digits BETWEEN 1 AND 3 AND CAST(substr(tail,1,digits) AS INTEGER)>0
 AND substr(after_number,1,1) IN ('.',' ',char(9))
 AND trim(CASE WHEN substr(after_number,1,1)='.' THEN substr(after_number,2)
 ELSE after_number END,' '||char(9))<>''
 AND length(heading)<=180
),
pages AS (
 SELECT section_id,source_file,page_start,group_concat(kept,'') AS clean
 FROM (SELECT * FROM positioned ORDER BY section_id,start) GROUP BY section_id
),
headings AS (
 SELECT *,lead(page_start,1,(SELECT max(e.page_start)+1 FROM eligible e
 WHERE e.source_file=found.source_file)) OVER book AS next_page,
 lead(clean_start+title_start-start,1,0) OVER book AS next_start
 FROM found WINDOW book AS (PARTITION BY source_file ORDER BY page_start,start)
),
parts AS (
 SELECT h.section_id AS heading_id,h.heading,p.section_id,p.source_file,p.page_start,
 substr(p.clean,
 CASE WHEN p.section_id=h.section_id THEN h.clean_end ELSE 0 END+1,
 (CASE WHEN p.page_start=h.next_page THEN h.next_start ELSE length(p.clean) END)
 -(CASE WHEN p.section_id=h.section_id THEN h.clean_end ELSE 0 END)) AS body
 FROM headings h JOIN pages p ON p.source_file=h.source_file
 AND p.page_start>=h.page_start
 AND (p.page_start<h.next_page OR (p.page_start=h.next_page AND h.next_start>0))
)
"""


def query(sql: str, parameters=()) -> dict:
    return {"kind": "sql", "store": "sources.db", "sql": sql, "parameters": list(parameters)}


UNIT_QUERY = query(
    CTE + "SELECT json_array(json_array('sources.db','textbook_sections',"
    "'section_id='||section_id,json_array(title_start,title_end))) FROM headings"
)
# Binding reads only the independently identified book, never another book's
# pages. Both parameters come from the candidate's authenticated heading value.
SCOPED_CTE = CTE.replace(
    "WITH RECURSIVE\n",
    "WITH RECURSIVE scope(id,title) AS (SELECT ?,?),\n",
).replace(
    f"WHERE {ELIGIBLE_SQL}",
    f"WHERE {ELIGIBLE_SQL} AND source_file=(SELECT source_file FROM textbook_sections "
    "WHERE section_id=(SELECT id FROM scope))",
)
HEADING_QUERY = query(
    SCOPED_CTE + "SELECT heading FROM headings WHERE section_id=(SELECT id FROM scope) "
    "AND heading=(SELECT title FROM scope)"
)
BODY_QUERY = query(
    SCOPED_CTE + "SELECT body FROM parts WHERE heading_id=(SELECT id FROM scope) "
    "AND heading=(SELECT title FROM scope) ORDER BY page_start"
)
END_QUERY = query(
    SCOPED_CTE + "SELECT max(page_start)+1 FROM parts WHERE heading_id=(SELECT id FROM scope) "
    "AND heading=(SELECT title FROM scope)"
)
