package kimi

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

const fixtureSessionID = "session_12345678-1234-1234-1234-123456789abc"

func TestNativeWireResolutionAndAnalysis(t *testing.T) {
	agent, wire, repo := fixtureAgent(t)
	dir, err := agent.GetSessionDir(repo)
	if err != nil {
		t.Fatal(err)
	}
	resolved, err := agent.ResolveSessionFile(dir, fixtureSessionID)
	if err != nil {
		t.Fatal(err)
	}
	if resolved != wire {
		t.Fatalf("resolved %q, want %q", resolved, wire)
	}

	position, err := agent.GetTranscriptPosition(wire)
	if err != nil || position <= 0 {
		t.Fatalf("position=%d err=%v", position, err)
	}
	files, current, err := agent.ExtractModifiedFiles(wire, 0)
	if err != nil {
		t.Fatal(err)
	}
	if current != position {
		t.Fatalf("current=%d, want %d", current, position)
	}
	if got := strings.Join(files, ","); got != "src/main.go,src/new.go" {
		t.Fatalf("files=%q", got)
	}
	prompts, err := agent.ExtractPrompts(wire, 0)
	if err != nil {
		t.Fatal(err)
	}
	if len(prompts) != 1 || prompts[0] != "Implement the adapter" {
		t.Fatalf("prompts=%v", prompts)
	}
	data, err := os.ReadFile(wire)
	if err != nil {
		t.Fatal(err)
	}
	usage, err := agent.CalculateTokens(data, 0)
	if err != nil {
		t.Fatal(err)
	}
	if usage.InputTokens != 120 || usage.CacheReadTokens != 40 || usage.CacheCreationTokens != 3 || usage.OutputTokens != 21 || usage.APICallCount != 1 {
		t.Fatalf("usage=%+v", usage)
	}
}

func TestHookMappingUsesNativeModel(t *testing.T) {
	agent, wire, _ := fixtureAgent(t)
	payload := map[string]any{
		"hook_event_name": "UserPromptSubmit",
		"session_id":      fixtureSessionID,
		"cwd":             protocol.RepoRoot(),
		"prompt":          []map[string]string{{"type": "text", "text": "Use Kimi natively"}},
	}
	data, _ := json.Marshal(payload)
	event, err := agent.ParseHook("turn-start", data)
	if err != nil {
		t.Fatal(err)
	}
	if event.Type != 2 || event.SessionID != fixtureSessionID || event.SessionRef != wire {
		t.Fatalf("event=%+v", event)
	}
	if event.Prompt != "Use Kimi natively" {
		t.Fatalf("prompt=%q", event.Prompt)
	}
	if event.Model != "kimi-code/k3" {
		t.Fatalf("model=%q", event.Model)
	}

	for hook, want := range map[string]int{"session-start": 1, "turn-end": 3, "compaction": 4, "session-end": 5} {
		mapped, err := agent.ParseHook(hook, data)
		if err != nil || mapped.Type != want {
			t.Fatalf("hook=%s type=%v err=%v", hook, mapped, err)
		}
	}
}

func TestOffsetAtJSONLBoundary(t *testing.T) {
	agent, wire, _ := fixtureAgent(t)
	before, err := os.Stat(wire)
	if err != nil {
		t.Fatal(err)
	}
	appendLine(t, wire, `{"type":"turn.prompt","input":[{"type":"text","text":"Second prompt"}]}`)
	appendLine(t, wire, `{"type":"usage.record","model":"kimi-code/k3","usage":{"inputOther":7,"inputCacheRead":2,"inputCacheCreation":1,"output":4}}`)
	prompts, err := agent.ExtractPrompts(wire, int(before.Size()))
	if err != nil || len(prompts) != 1 || prompts[0] != "Second prompt" {
		t.Fatalf("prompts=%v err=%v", prompts, err)
	}
	data, _ := os.ReadFile(wire)
	usage, err := agent.CalculateTokens(data, int(before.Size()))
	if err != nil || usage.InputTokens != 7 || usage.OutputTokens != 4 || usage.APICallCount != 1 {
		t.Fatalf("usage=%+v err=%v", usage, err)
	}
}

func TestHookInstallPreservesConfigAndIsConcurrentIdempotent(t *testing.T) {
	agent, _, _ := fixtureAgent(t)
	config := configPath()
	original := []byte("default_model = \"kimi-code/k3\"\n[providers.kimi]\napi_key = \"credential-canary\"")
	if err := os.WriteFile(config, original, 0o600); err != nil {
		t.Fatal(err)
	}

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
	installed := 0
	for count := range counts {
		installed += count
	}
	if installed != len(hookSpecs) {
		t.Fatalf("installed total=%d", installed)
	}
	if !agent.AreHooksInstalled() {
		t.Fatal("hooks not reported installed")
	}
	withHooks, _ := os.ReadFile(config)
	if !bytes.Contains(withHooks, original) || bytes.Count(withHooks, []byte(blockBegin)) != 1 {
		t.Fatal("config bytes were not preserved")
	}
	if err := agent.UninstallHooks(); err != nil {
		t.Fatal(err)
	}
	restored, _ := os.ReadFile(config)
	if !bytes.Equal(restored, original) {
		t.Fatalf("uninstall changed original bytes\ngot: %q\nwant: %q", restored, original)
	}
}

func TestDriftRequiresForceAndTraversalFailsClosed(t *testing.T) {
	agent, _, _ := fixtureAgent(t)
	config := configPath()
	block := managedBlock(false)
	block = bytes.Replace(block, []byte("timeout = 30"), []byte("timeout = 29"), 1)
	if err := os.WriteFile(config, block, 0o600); err != nil {
		t.Fatal(err)
	}
	if _, err := agent.InstallHooks(false, false); err == nil {
		t.Fatal("drifted block did not fail")
	}
	if _, err := agent.InstallHooks(false, true); err != nil {
		t.Fatal(err)
	}
	if !agent.AreHooksInstalled() {
		t.Fatal("force did not repair block")
	}
	if _, err := agent.ResolveSessionFile(filepath.Join(kimiHome(), "sessions"), "../escape"); err == nil {
		t.Fatal("invalid session id accepted")
	}
	if _, err := agent.ReadTranscript(filepath.Join(kimiHome(), "outside.jsonl")); err == nil {
		t.Fatal("outside transcript accepted")
	}
}

func TestSessionRoundTripUsesValidatedStorage(t *testing.T) {
	agent, _, repo := fixtureAgent(t)
	dir, _ := agent.GetSessionDir(repo)
	ref, err := agent.ResolveSessionFile(dir, "session_roundtrip")
	if err != nil {
		t.Fatal(err)
	}
	want := protocol.Session{SessionID: "session_roundtrip", AgentName: agentName, RepoPath: repo, SessionRef: ref, StartTime: "2026-08-02T00:00:00Z", NativeData: []byte("{\"fixture\":true}"), ModifiedFiles: []string{}, NewFiles: []string{}, DeletedFiles: []string{}}
	if err := agent.WriteSession(want); err != nil {
		t.Fatal(err)
	}
	got, err := agent.ReadSession(&protocol.HookInput{SessionID: want.SessionID, SessionRef: ref})
	if err != nil {
		t.Fatal(err)
	}
	if !bytes.Equal(got.NativeData, want.NativeData) || got.SessionRef != ref {
		t.Fatalf("roundtrip=%+v", got)
	}
}

func fixtureAgent(t *testing.T) (*Agent, string, string) {
	t.Helper()
	home := t.TempDir()
	repo := t.TempDir()
	t.Setenv("KIMI_CODE_HOME", home)
	t.Setenv("ENTIRE_REPO_ROOT", repo)
	sessionDir := filepath.Join(home, "sessions", "wd_fixture", fixtureSessionID)
	wire := filepath.Join(sessionDir, "agents", "main", "wire.jsonl")
	if err := os.MkdirAll(filepath.Dir(wire), 0o700); err != nil {
		t.Fatal(err)
	}
	fixture := strings.Join([]string{
		`{"type":"metadata","protocol_version":1}`,
		`{"type":"config.update","modelAlias":"kimi-code/k3"}`,
		`{"type":"turn.prompt","input":[{"type":"text","text":"Implement the adapter"}]}`,
		`{"type":"context.append_loop_event","event":{"type":"tool.call","name":"Write","args":{"path":"src/new.go"}}}`,
		`{"type":"context.append_loop_event","event":{"type":"tool.call","name":"Edit","args":{"path":"src/main.go"}}}`,
		`{"type":"usage.record","model":"kimi-code/k3","usage":{"inputOther":120,"inputCacheRead":40,"inputCacheCreation":3,"output":21}}`,
	}, "\n") + "\n"
	if err := os.WriteFile(wire, []byte(fixture), 0o600); err != nil {
		t.Fatal(err)
	}
	index := map[string]string{"sessionId": fixtureSessionID, "sessionDir": sessionDir, "workDir": repo}
	data, _ := json.Marshal(index)
	if err := os.WriteFile(filepath.Join(home, "session_index.jsonl"), append(data, '\n'), 0o600); err != nil {
		t.Fatal(err)
	}
	return New(), wire, repo
}

func appendLine(t *testing.T, path, line string) {
	t.Helper()
	f, err := os.OpenFile(path, os.O_APPEND|os.O_WRONLY, 0o600)
	if err != nil {
		t.Fatal(err)
	}
	defer func() { _ = f.Close() }()
	if _, err := f.WriteString(line + "\n"); err != nil {
		t.Fatal(err)
	}
}
