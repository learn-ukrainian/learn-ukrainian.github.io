-- Applied only by the existing migration owner; never by the API or Sources.
DO $roles$ BEGIN
  IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'hramatka_v4_control_writer') THEN
    CREATE ROLE hramatka_v4_control_writer NOLOGIN;
  END IF;
  IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'hramatka_v4_sources_writer') THEN
    CREATE ROLE hramatka_v4_sources_writer NOLOGIN;
  END IF;
END $roles$;

ALTER TABLE public.v4_execution_attempts ADD COLUMN deadline_at timestamptz;
-- Pre-contract attempts cannot inherit an unbounded capability.
UPDATE public.v4_execution_attempts SET deadline_at = started_at::timestamptz + interval '1800 seconds';
ALTER TABLE public.v4_execution_attempts ALTER COLUMN deadline_at SET NOT NULL;
ALTER TABLE public.v4_execution_dispatch_bindings ADD COLUMN semantic_input_json text;

CREATE TABLE public.v4_operation_authorizations (
 authorization_digest text PRIMARY KEY CHECK (authorization_digest ~ '^[a-f0-9]{64}$'),
 request_id text NOT NULL UNIQUE REFERENCES public.requests(request_id),
 operation text NOT NULL CHECK (operation IN ('author', 'reviewer')),
 target text NOT NULL,
 role text NOT NULL,
 seat text NOT NULL,
 harness text NOT NULL,
 timeout_seconds integer NOT NULL CHECK (timeout_seconds = 1800),
 principal_json text NOT NULL,
 authz_policy_sha256 text NOT NULL,
 trust_policy_sha256 text NOT NULL,
 binding_sha256 text NOT NULL,
 authorization_body_sha256 text NOT NULL,
 execution_body_sha256 text NOT NULL,
 authorization_jti_digest text NOT NULL UNIQUE,
 execution_jti_digest text UNIQUE,
 state text NOT NULL CHECK (state IN ('armed', 'claimed', 'terminal', 'revoked')),
 expires_at timestamptz NOT NULL,
 claimed_at timestamptz,
 deadline_at timestamptz,
 terminal_at timestamptz,
 revoked_at timestamptz
);
CREATE TABLE public.v4_operation_jtis (
 jti_digest text PRIMARY KEY CHECK (jti_digest ~ '^[a-f0-9]{64}$'),
 consumed_at timestamptz NOT NULL DEFAULT clock_timestamp()
);

CREATE FUNCTION public.hramatka_v4_record_sources_invocation_v1(
 p_capability_digest text, p_tool text, p_version text, p_outcome text
) RETURNS text LANGUAGE plpgsql SECURITY DEFINER SET search_path = pg_catalog, public AS $function$
DECLARE
 a public.v4_execution_attempts%ROWTYPE;
 outcome jsonb;
 record jsonb;
 ordinal integer;
 identifier text;
 invocation text;
 structured_digest text;
 ok boolean;
 stamp text;
BEGIN
 SELECT * INTO a FROM public.v4_execution_attempts
 WHERE capability_digest = p_capability_digest FOR UPDATE;
 IF NOT FOUND OR a.state <> 'running' OR a.deadline_at <= clock_timestamp() THEN
   RAISE EXCEPTION 'inactive V4 Sources capability';
 END IF;
 IF NOT EXISTS (SELECT FROM public.v4_operation_authorizations o
   JOIN public.requests r ON r.request_id=o.request_id
   WHERE r.state = 'running' AND r.expires_at::timestamptz=a.deadline_at
     AND o.request_id = a.request_id AND o.state = 'claimed'
     AND o.deadline_at = a.deadline_at AND o.deadline_at > clock_timestamp()) THEN
   RAISE EXCEPTION 'unowned V4 Sources capability';
 END IF;
 IF p_tool IS NULL AND p_version IS NULL AND p_outcome IS NULL THEN
   RETURN jsonb_build_object('attempt_id',a.attempt_id,'state',a.state)::text;
 END IF;
 IF p_tool IS NULL OR p_version IS NULL OR p_outcome IS NULL
    OR p_tool NOT IN ('verify_word', 'verify_words', 'verify_lemma', 'verify_stress', 'check_modern_form')
    OR p_version !~ '^[a-f0-9]{64}$' OR octet_length(p_outcome) > 1048576 THEN
   RAISE EXCEPTION 'invalid V4 Sources result';
 END IF;
 outcome := p_outcome::jsonb;
 IF outcome->>'tool' IS DISTINCT FROM p_tool
    OR outcome->>'disposition' NOT IN ('supported','partial','negative','invalid_input','not_found','ambiguous')
    OR outcome->>'disposition' IS NULL
    OR jsonb_typeof(outcome->'success') IS DISTINCT FROM 'boolean' THEN
   RAISE EXCEPTION 'invalid V4 Sources disposition';
 END IF;
 ok := outcome->'success' = 'true'::jsonb AND outcome->>'disposition' = 'supported';
 IF ok AND (jsonb_typeof(outcome->'evidence_identifiers') IS DISTINCT FROM 'array'
   OR jsonb_array_length(outcome->'evidence_identifiers') NOT BETWEEN 1 AND 64
   OR EXISTS (SELECT FROM jsonb_array_elements_text(outcome->'evidence_identifiers') AS x(value)
       WHERE value !~ '^(vesum|sources):[a-f0-9]{64}$')
   OR (SELECT count(DISTINCT value) FROM jsonb_array_elements_text(outcome->'evidence_identifiers'))
       <> jsonb_array_length(outcome->'evidence_identifiers')) THEN
   RAISE EXCEPTION 'invalid V4 evidence identifiers';
 END IF;
 SELECT count(*) + 1 INTO ordinal FROM public.v4_sources_invocations WHERE attempt_id = a.attempt_id;
 structured_digest := encode(sha256(convert_to(p_outcome, 'UTF8')), 'hex');
 identifier := CASE WHEN ok THEN outcome->'evidence_identifiers'->>0
                    ELSE 'sources:unsuccessful-' || structured_digest END;
 invocation := 'v4sources-' || encode(sha256(convert_to(a.attempt_id || ':' || ordinal::text || ':' || structured_digest, 'UTF8')), 'hex');
 stamp := to_char(clock_timestamp() AT TIME ZONE 'UTC', 'YYYY-MM-DD"T"HH24:MI:SS"Z"');
 record := jsonb_build_object('invocation_id', invocation, 'attempt_id', a.attempt_id,
   'ordinal', ordinal, 'identifier', identifier, 'tool_id', 'mcp__sources__' || p_tool,
   'tool_version', p_version, 'structured_result_sha256', structured_digest,
   'lookup_ids', CASE WHEN ok THEN outcome->'evidence_identifiers' ELSE jsonb_build_array(identifier) END,
   'success', ok, 'disposition', outcome->>'disposition', 'recorded_at', stamp);
 INSERT INTO public.v4_sources_invocations(invocation_id, record_sha256, record_json, recorded_at, request_id, attempt_id)
 VALUES(invocation, encode(sha256(convert_to(record::text, 'UTF8')), 'hex'), record::text, stamp, a.request_id, a.attempt_id);
 RETURN record::text;
END $function$;
REVOKE ALL ON FUNCTION public.hramatka_v4_record_sources_invocation_v1(text,text,text,text) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION public.hramatka_v4_record_sources_invocation_v1(text,text,text,text) TO hramatka_v4_sources_writer;

-- Remove existing direct grants on V4 tables, including generic Fleet/ops/Actions.
DO $acl$ DECLARE item record; v4_table text; BEGIN
 FOREACH v4_table IN ARRAY ARRAY['v4_operation_authorizations','v4_operation_jtis',
  'v4_execution_dispatch_bindings','v4_execution_attempts','v4_execution_observations',
  'v4_authorship_receipts','v4_sources_invocations'] LOOP
  EXECUTE format('REVOKE ALL ON TABLE public.%I FROM PUBLIC', v4_table);
  FOR item IN SELECT grantee FROM information_schema.role_table_grants
    WHERE table_schema = 'public' AND information_schema.role_table_grants.table_name = v4_table
      AND grantee <> current_user LOOP
    EXECUTE format('REVOKE ALL ON TABLE public.%I FROM %I', v4_table, item.grantee);
  END LOOP;
 END LOOP;
END $acl$;
GRANT SELECT, INSERT, UPDATE, DELETE ON public.v4_operation_authorizations, public.v4_operation_jtis,
 public.v4_execution_dispatch_bindings, public.v4_execution_attempts, public.v4_execution_observations,
 public.v4_authorship_receipts TO hramatka_v4_control_writer;
GRANT SELECT ON public.v4_sources_invocations TO hramatka_v4_control_writer;
GRANT SELECT, INSERT, UPDATE ON public.requests, public.conversations, public.comms_messages,
 public.fleet_comms_artifact_blobs TO hramatka_v4_control_writer;
