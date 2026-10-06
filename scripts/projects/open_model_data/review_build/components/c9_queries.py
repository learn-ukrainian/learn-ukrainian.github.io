"""Independent LF-only SQLite heading, edge-excision and body census.

No Python parser or extractor flags participate in this source reconstruction.
"""

import unicodedata
from itertools import groupby

# SQLite GLOB has no Unicode properties. Generate its character class from the
# standard Unicode categories matching regex [^\W\d_] (letters, Nl, No),
# without calling the extractor or inspecting source text.
_WORD_TERMINALS = [
    point
    for point in range(0x110000)
    if unicodedata.category(chr(point)).startswith("L") or unicodedata.category(chr(point)) in {"Nl", "No"}
]
_WORD_RANGES = [
    [point for _, point in group]
    for _, group in groupby(enumerate(_WORD_TERMINALS), lambda pair: pair[1] - pair[0])
]
WORD_TERMINAL_GLOB = "[" + "".join(
    chr(points[0]) + "-" + chr(points[-1]) if len(points) > 2 else "".join(map(chr, points))
    for points in _WORD_RANGES
) + "]"


WORD_GLOB = WORD_TERMINAL_GLOB[:-1] + "_" + "".join(
    chr(point) for point in range(0x110000) if unicodedata.category(chr(point)) == "Nd"
) + "]"


def label_prefix_sql(column, labels):
    """Independent SQL word-boundary test for printed marker/label prefixes."""
    return "(" + " OR ".join(
        f"(substr({column},1,{len(label)})='{label}' AND "
        f"(length({column})={len(label)} OR substr({column},{len(label) + 1},1) NOT GLOB '{WORD_GLOB}'))"
        for label in labels
    ) + ")"


HEADING_LABEL_SQL = label_prefix_sql(
    "n.text", ("Тема", "ТЕМА", "Розділ", "РОЗДІЛ", "Урок", "УРОК", "Параграф", "ПАРАГРАФ")
)
EXERCISE_LABEL_SQL = label_prefix_sql(
    "text", ("Вправа", "Вправи", "Завдання", "Запитання", "Питання",
             "ВПРАВА", "ВПРАВИ", "ЗАВДАННЯ", "ЗАПИТАННЯ", "ПИТАННЯ",
             "вправа", "вправи", "завдання", "запитання", "питання")
)


ELIGIBLE_SQL = """(
 source_file GLOB '[1-9]-klas-?*' OR source_file GLOB '10-klas-?*'
 OR source_file GLOB '11-klas-?*' OR source_file GLOB '10-11-klas-?*'
 OR source_file GLOB 'uni-?*'
)"""

CTE = f"""WITH RECURSIVE
eligible AS (SELECT * FROM textbook_sections WHERE {ELIGIBLE_SQL}),
split(section_id,source_file,page_start,start,raw,rest) AS NOT MATERIALIZED (
 SELECT section_id,source_file,page_start,0,
 substr(full_text,1,CASE instr(full_text,char(10)) WHEN 0 THEN length(full_text)
 ELSE instr(full_text,char(10)) END),
 substr(full_text,1+CASE instr(full_text,char(10)) WHEN 0 THEN length(full_text)
 ELSE instr(full_text,char(10)) END) FROM eligible
 UNION ALL
 SELECT section_id,source_file,page_start,start+length(raw),
 substr(rest,1,CASE instr(rest,char(10)) WHEN 0 THEN length(rest)
 ELSE instr(rest,char(10)) END),
 substr(rest,1+CASE instr(rest,char(10)) WHEN 0 THEN length(rest)
 ELSE instr(rest,char(10)) END) FROM split WHERE rest<>''
),
lines AS MATERIALIZED (
 SELECT section_id,source_file,page_start,start,raw,trim(raw,' '||char(9)||char(10)||char(13)) AS text,
 row_number() OVER (PARTITION BY section_id ORDER BY start) AS line_number
 FROM split
),
page_edges AS (
 SELECT section_id,min(CASE WHEN text<>'' AND text GLOB '*[^0-9]*' THEN start END) AS first_line,
 max(CASE WHEN text<>'' AND text GLOB '*[^0-9]*' THEN start END) AS last_line
 FROM lines GROUP BY section_id
),
edges AS MATERIALIZED (
 SELECT l.*,CASE WHEN substr(text,1,1) GLOB '[0-9]' AND substr(ltrim(text,'0123456789'),1,1) GLOB '[A-Za-zА-Яа-яІіЇїЄєҐґ]' THEN ltrim(text,'0123456789')
 WHEN substr(text,-1) GLOB '[0-9]' AND substr(rtrim(text,'0123456789'),-1) GLOB '[A-Za-zА-Яа-яІіЇїЄєҐґ]' THEN rtrim(text,'0123456789') ELSE text END AS edge_key
 FROM lines l JOIN page_edges p USING(section_id) WHERE start IN (first_line,last_line)
),
recurring AS MATERIALIZED (
 SELECT source_file,edge_key FROM edges WHERE edge_key<>'' AND length(edge_key)<=180
 GROUP BY source_file,edge_key HAVING count(DISTINCT page_start)>=2
),
page_flags AS (
 SELECT section_id,max(CASE WHEN text IN ('ЗМІСТ','Зміст') OR
 (substr(text,-1) GLOB '[0-9]' AND
 (substr(replace(replace(rtrim(text,'0123456789'),' ',''),char(9),''),-3)='...'
 OR (length(text)-length(rtrim(text,'0123456789')) BETWEEN 1 AND 4
 AND substr(rtrim(text,'0123456789'),-1) IN (' ',char(9))
 AND substr(rtrim(rtrim(text,'0123456789'),' '||char(9)),-1) GLOB '{WORD_TERMINAL_GLOB}')))
 AND NOT {EXERCISE_LABEL_SQL}
 AND NOT EXISTS (SELECT 1 FROM markers m WHERE m.section_id=lines.section_id AND m.start=lines.start AND m.title='')
 THEN 1 ELSE 0 END) AS contents FROM lines GROUP BY section_id
),
tails AS MATERIALIZED (
 SELECT *,CASE WHEN substr(text,1,1)='§' THEN ltrim(substr(text,2),' '||char(9))
 WHEN substr(text,1,5) IN ('Тема ','ТЕМА ') THEN ltrim(substr(text,6),' '||char(9))
 WHEN substr(text,1,7) IN ('Розділ ','РОЗДІЛ ') THEN ltrim(substr(text,8),' '||char(9))
 END AS tail FROM lines
),
tokens AS (
 SELECT *,substr(tail,1,length(tail)-length(ltrim(tail,'0123456789IVXLCDMІХ–—-'))) AS token,
 ltrim(tail,'0123456789IVXLCDMІХ–—-') AS after_number FROM tails WHERE tail IS NOT NULL
),
normalized AS (
 SELECT *,replace(replace(token,'–','-'),'—','-') AS num,
 trim(CASE WHEN substr(after_number,1,1)='.' THEN substr(after_number,2)
 ELSE after_number END,' '||char(9)) AS title FROM tokens
),
markers AS MATERIALIZED (
 SELECT * FROM normalized WHERE length(token) BETWEEN 1 AND 8
 AND (after_number='' OR substr(after_number,1,1) IN ('.',' ',char(9)))
 AND ((token NOT GLOB '*[^IVXLCDMІХ]*') OR
 (num NOT GLOB '*[^0-9-]*' AND CAST(num AS INTEGER)>0 AND
 ((instr(num,'-')=0 AND length(num)<=3) OR
 (instr(num,'-') BETWEEN 2 AND 4 AND
 length(num)-length(replace(num,'-',''))=1 AND
 length(substr(num,instr(num,'-')+1)) BETWEEN 1 AND 3
 AND CAST(substr(num,instr(num,'-')+1) AS INTEGER)>0))))
 AND instr(title,'§')=0 AND instr(title,'РОЗДІЛ')=0 AND instr(title,'Розділ')=0
 AND instr(title,'ТЕМА')=0 AND instr(title,'Тема')=0
),
joined AS MATERIALIZED (
 SELECT m.*,n.text AS next_text,n.start AS next_line,n.raw AS next_raw,
 CASE WHEN m.title='' AND n.text<>'' AND length(n.text)<=100 AND n.text GLOB '[A-ZА-ЯІЇЄҐ]*'
 AND n.text NOT GLOB '*[.;:!?§]*' AND NOT {HEADING_LABEL_SQL} THEN 1
 WHEN n.text<>'' AND length(n.text)<=100 AND n.text GLOB '*[A-ZА-ЯІЇЄҐ]*'
 AND n.text NOT GLOB '*[a-zа-яіїєґ0-9.;:!?§]*'
 AND m.title GLOB '*[A-ZА-ЯІЇЄҐ]*'
 AND m.title NOT GLOB '*[a-zа-яіїєґ0-9.;:!?§]*' THEN 1 ELSE 0 END AS join_next
 FROM markers m LEFT JOIN lines n ON n.section_id=m.section_id AND n.start=m.start+length(m.raw)
),
all_found AS MATERIALIZED (
 SELECT *,start+length(raw)-length(ltrim(raw,' '||char(9)||char(10)||char(13))) AS title_start,
 CASE WHEN join_next=1 THEN next_line+length(rtrim(next_raw,' '||char(9)||char(10)||char(13)))
 ELSE start+length(rtrim(raw,' '||char(9)||char(10)||char(13))) END AS title_end
 FROM joined WHERE (title<>'' OR join_next=1) AND
 length(text)+CASE WHEN join_next=1 THEN length(next_text)+1 ELSE 0 END<=180
),
ranked AS MATERIALIZED (
 SELECT f.*,p.contents,
 min(CASE WHEN p.contents=0 THEN f.page_start END) OVER (PARTITION BY f.source_file,substr(e.full_text,f.title_start+1,f.title_end-f.title_start)) AS first_page
 FROM all_found f JOIN page_flags p USING(section_id) JOIN eligible e USING(section_id)
),
classified AS MATERIALIZED (
 SELECT f.*,CASE WHEN contents=0 AND page_start>first_page AND EXISTS (
 SELECT 1 FROM edges e WHERE e.section_id=f.section_id AND e.start=f.start)
 THEN 1 ELSE 0 END AS running FROM ranked f
),
excised AS MATERIALIZED (
 SELECT l.*,CASE WHEN (text<>'' AND text NOT GLOB '*[^0-9]*') OR EXISTS (
 SELECT 1 FROM edges e JOIN recurring r USING(source_file,edge_key)
 WHERE e.section_id=l.section_id AND e.start=l.start AND NOT EXISTS (
 SELECT 1 FROM classified f WHERE f.section_id=l.section_id AND
 l.start>=f.start AND l.start<f.title_end AND f.running=0)) OR EXISTS (
 SELECT 1 FROM classified f WHERE f.section_id=l.section_id AND f.running=1
 AND l.start>=f.start AND l.start<f.title_end)
 THEN '' ELSE raw END AS kept FROM lines l
),
positioned AS MATERIALIZED (
 SELECT *,coalesce(sum(length(kept)) OVER (PARTITION BY section_id ORDER BY start
 ROWS BETWEEN UNBOUNDED PRECEDING AND 1 PRECEDING),0) AS clean_start FROM excised
),
found AS MATERIALIZED (
 SELECT f.section_id,f.source_file,f.page_start,f.start,f.title_start,f.title_end,
 substr(e.full_text,f.title_start+1,f.title_end-f.title_start) AS heading,
 p.clean_start+f.title_start-f.start AS clean_start,
 q.clean_start+length(q.kept)-(q.start+length(q.raw)-f.title_end) AS clean_end
 FROM classified f JOIN positioned p USING(section_id,start) JOIN eligible e USING(section_id)
 JOIN positioned q ON q.section_id=f.section_id AND q.start=CASE WHEN f.join_next=1 THEN f.next_line ELSE f.start END
 WHERE f.running=0
),
pages AS MATERIALIZED (
 SELECT section_id,source_file,page_start,group_concat(kept,'') AS clean
 FROM (SELECT * FROM positioned ORDER BY section_id,start) GROUP BY section_id
),
headings AS MATERIALIZED (
 SELECT *,lead(page_start,1,(SELECT max(e.page_start)+1 FROM eligible e WHERE e.source_file=found.source_file))
 OVER book AS next_page,lead(clean_start,1,0) OVER book AS next_start FROM found
 WINDOW book AS (PARTITION BY source_file ORDER BY page_start,start)
),
parts AS (
 SELECT h.section_id AS heading_id,h.heading,p.section_id,p.source_file,p.page_start,
 substr(p.clean,CASE WHEN p.section_id=h.section_id THEN h.clean_end ELSE 0 END+1,
 (CASE WHEN p.page_start=h.next_page THEN h.next_start ELSE length(p.clean) END)
 -(CASE WHEN p.section_id=h.section_id THEN h.clean_end ELSE 0 END)) AS body
 FROM headings h JOIN pages p ON p.source_file=h.source_file AND p.page_start>=h.page_start
 AND (p.page_start<h.next_page OR (p.page_start=h.next_page AND h.next_start>0))
)
"""


def query(sql: str, parameters=()) -> dict:
    return {"kind": "sql", "store": "sources.db", "sql": sql, "parameters": list(parameters)}


UNIT_QUERY = query(
    CTE + "SELECT json_array(json_array('sources.db','textbook_sections',"
    "'section_id='||section_id,json_array(title_start,title_end))) FROM classified WHERE running=0"
)
EXCISION_QUERY = query(
    CTE + "SELECT json_array('section_id='||p.section_id,p.line_number,e.full_text) "
    "FROM positioned p JOIN eligible e USING(section_id) WHERE p.kept='' AND p.text<>'' "
    "ORDER BY p.source_file,p.page_start,p.start"
)
SCOPED_CTE = CTE.replace("WITH RECURSIVE\n", "WITH RECURSIVE scope(id,title) AS (SELECT ?,?),\n").replace(
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
