package fleet

import (
	"bytes"
	"encoding/json"
	"os"
	"path/filepath"
	"strings"
	"sync"
	"testing"

	"github.com/learn-ukrainian/learn-ukrainian.github.io/scripts/entire/external_agents/entire-agent-kimi/internal/protocol"
)

const fixtureSessionID = "fleet-0123456789abcdef0123456789abcdef"

func TestSessionAnalysisAndHookMapping(t *testing.T) {
	agent, ref, repo := fixtureAgent(t)
	session, err := agent.ReadSession(&protocol.HookInput{SessionID: fixtureSessionID, SessionRef: ref})
	if err != nil {
		t.Fatal(err)
	}
	if session.AgentName != agentName || session.RepoPath != repo || session.StartTime != "2026-08-03T00:00:00Z" {
		t.Fatalf("session=%+v", session)
	}
	if got := strings.Join(session.ModifiedFiles, ","); got != "scripts/a.py,scripts/z.py" {
		t.Fatalf("modified files=%q", got)
	}
	prompts, err := agent.ExtractPrompts(ref, 0)
	if err != nil || len(prompts) != 1 || prompts[0] != "source-blind canary" {
		t.Fatalf("prompts=%v err=%v", prompts, err)
	}
	payload, _ := json.Marshal(protocol.HookInput{
		SessionID:  fixtureSessionID,
		SessionRef: ref,
		Timestamp:  "2026-08-03T00:00:01Z",
		UserPrompt: "source-blind canary",
		RawData: map[string]any{
			"harness":         "hermes",
			"requested_model": "deepseek-v4-flash",
			"actual_model":    "deepseek-v4.1",
		},
	})
	for hook, want := range map[string]int{"session-start": 1, "turn-start": 2, "turn-end": 3, "session-end": 5} {
		event, err := agent.ParseHook(hook, payload)
		if err != nil || event.Type != want || event.Model != "deepseek-v4.1" {
			t.Fatalf("hook=%s event=%+v err=%v", hook, event, err)
		}
		if hook == "turn-start" && event.Prompt != "source-blind canary" {
			t.Fatalf("turn prompt=%q", event.Prompt)
		}
		if hook != "turn-start" && event.Prompt != "" {
			t.Fatalf("unexpected prompt for %s: %q", hook, event.Prompt)
		}
	}
}

func TestUnknownActualModelDoesNotFabricateRequestedSelector(t *testing.T) {
	agent, ref, _ := fixtureAgent(t)
	payload, _ := json.Marshal(protocol.HookInput{
		SessionID:  fixtureSessionID,
		SessionRef: ref,
		RawData: map[string]any{
			"harness":            "cursor-headless",
			"requested_model":    "auto",
			"actual_model_known": "false",
		},
	})
	event, err := agent.ParseHook("turn-end", payload)
	if err != nil {
		t.Fatal(err)
	}
	if event.Model != "" {
		t.Fatalf("model=%q, want unknown", event.Model)
	}
}

func TestTraversalAndSymlinkEscapeFailClosed(t *testing.T) {
	agent, _, _ := fixtureAgent(t)
	root, _ := captureRoot()
	if _, err := agent.ResolveSessionFile(root, "../escape"); err == nil {
		t.Fatal("invalid session id accepted")
	}
	if _, err := agent.ReadTranscript(filepath.Join(root, "outside.jsonl")); err == nil {
		t.Fatal("non-canonical transcript accepted")
	}
	escape := t.TempDir()
	linked := filepath.Join(root, "fleet-aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa")
	if err := os.Symlink(escape, linked); err != nil {
		t.Fatal(err)
	}
	if _, err := agent.ReadTranscript(filepath.Join(linked, "transcript.jsonl")); err == nil {
		t.Fatal("symlink escape accepted")
	}
}

func TestMarkerInstallIsConcurrentIdempotentAndPrivate(t *testing.T) {
	agent, _, _ := fixtureAgent(t)
	const workers = 12
	var wg sync.WaitGroup
	counts := make(chan int, workers)
	errorsSeen := make(chan error, workers)
	for range workers {
		wg.Add(1)
		go func() {
			defer wg.Done()
			count, err := agent.InstallHooks(false, false)
			counts <- count
			errorsSeen <- err
		}()
	}
	wg.Wait()
	close(counts)
	close(errorsSeen)
	for err := range errorsSeen {
		if err != nil {
			t.Fatal(err)
		}
	}
	total := 0
	for count := range counts {
		total += count
	}
	if total != 4 || !agent.AreHooksInstalled() {
		t.Fatalf("total=%d installed=%v", total, agent.AreHooksInstalled())
	}
	path, _ := markerPath()
	info, err := os.Stat(path)
	if err != nil || info.Mode().Perm() != 0o600 {
		t.Fatalf("marker mode=%v err=%v", info.Mode().Perm(), err)
	}
	if err := agent.UninstallHooks(); err != nil || agent.AreHooksInstalled() {
		t.Fatalf("uninstall err=%v installed=%v", err, agent.AreHooksInstalled())
	}
}

func TestWriteSessionUsesExactPrivateStorage(t *testing.T) {
	agent, ref, repo := fixtureAgent(t)
	want := []byte("{\"roundtrip\":true}\n")
	if err := agent.WriteSession(protocol.Session{
		SessionID:  fixtureSessionID,
		RepoPath:   repo,
		SessionRef: ref,
		NativeData: want,
	}); err != nil {
		t.Fatal(err)
	}
	got, err := os.ReadFile(ref)
	if err != nil || !bytes.Equal(got, want) {
		t.Fatalf("got=%q err=%v", got, err)
	}
	info, _ := os.Stat(ref)
	if info.Mode().Perm() != 0o600 {
		t.Fatalf("mode=%v", info.Mode().Perm())
	}
}

func fixtureAgent(t *testing.T) (*Agent, string, string) {
	t.Helper()
	repo := t.TempDir()
	root := filepath.Join(t.TempDir(), "fleet-sessions", "v1")
	markerHome := filepath.Join(t.TempDir(), "fleet-home")
	t.Setenv("ENTIRE_REPO_ROOT", repo)
	t.Setenv("ENTIRE_FLEET_CAPTURE_ROOT", root)
	t.Setenv("ENTIRE_AGENT_FLEET_HOME", markerHome)
	sessionDir := filepath.Join(root, fixtureSessionID)
	if err := os.MkdirAll(sessionDir, 0o700); err != nil {
		t.Fatal(err)
	}
	ref := filepath.Join(sessionDir, "transcript.jsonl")
	lines := []string{
		`{"type":"session","session_id":"` + fixtureSessionID + `","timestamp":"2026-08-03T00:00:00Z","repo_path":"` + repo + `","metadata":{"harness":"hermes"}}`,
		`{"type":"user","timestamp":"2026-08-03T00:00:01Z","text":"source-blind canary"}`,
		`{"type":"assistant","timestamp":"2026-08-03T00:00:02Z","text":"canary ok","model":"deepseek-v4.1"}`,
		`{"type":"file","timestamp":"2026-08-03T00:00:02Z","path":"scripts/z.py"}`,
		`{"type":"file","timestamp":"2026-08-03T00:00:02Z","path":"../escape"}`,
		`{"type":"file","timestamp":"2026-08-03T00:00:02Z","path":"scripts/a.py"}`,
		`{"type":"terminal","timestamp":"2026-08-03T00:00:02Z","metadata":{"outcome":"ok"}}`,
	}
	if err := os.WriteFile(ref, []byte(strings.Join(lines, "\n")+"\n"), 0o600); err != nil {
		t.Fatal(err)
	}
	return New(), ref, repo
}
