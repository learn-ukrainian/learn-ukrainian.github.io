package kimi

import (
	"bufio"
	"encoding/json"
	"errors"
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"regexp"
	"strings"
	"time"

	"github.com/learn-ukrainian/learn-ukrainian.github.io/scripts/entire/external_agents/entire-agent-kimi/internal/protocol"
)

const (
	agentName     = "kimi"
	agentType     = "Kimi Code"
	stubSessionID = "kimi-session"
)

var sessionIDPattern = regexp.MustCompile(`^[A-Za-z0-9][A-Za-z0-9._-]{0,191}$`)

type Agent struct{ LookPath func(string) (string, error) }

func New() *Agent { return &Agent{LookPath: exec.LookPath} }

func (a *Agent) Info() protocol.Info {
	return protocol.Info{
		ProtocolVersion: protocol.Version,
		Name:            agentName,
		Type:            agentType,
		Description:     "Kimi Code CLI external-agent integration for Entire",
		IsPreview:       true,
		ProtectedDirs:   []string{".kimi-code"},
		ProtectedFiles:  []string{"config.toml", "session_index.jsonl"},
		HookNames:       []string{"session-start", "turn-start", "turn-end", "compaction", "session-end"},
		Capabilities: protocol.Capabilities{
			Hooks:              true,
			TranscriptAnalyzer: true,
			TokenCalculator:    true,
			UsesTerminal:       true,
		},
	}
}

func (a *Agent) Detect() protocol.DetectResponse {
	lookPath := a.LookPath
	if lookPath == nil {
		lookPath = exec.LookPath
	}
	_, err := lookPath("kimi")
	return protocol.DetectResponse{Present: err == nil}
}

func (a *Agent) GetSessionID(input *protocol.HookInput) string {
	if input != nil && validSessionID(input.SessionID) {
		return input.SessionID
	}
	return stubSessionID
}

func (a *Agent) GetSessionDir(_ string) (string, error) {
	return filepath.Join(kimiHome(), "sessions"), nil
}

func (a *Agent) ResolveSessionFile(sessionDir, sessionID string) (string, error) {
	if !validSessionID(sessionID) {
		return "", fmt.Errorf("invalid Kimi session id")
	}
	if found, ok := lookupSession(sessionID); ok {
		return found, nil
	}
	if strings.TrimSpace(sessionDir) == "" {
		sessionDir = filepath.Join(kimiHome(), "sessions")
	}
	dir, err := filepath.Abs(sessionDir)
	if err != nil {
		return "", err
	}
	return filepath.Join(dir, ".entire-sidecars", sessionID+".jsonl"), nil
}

func (a *Agent) ReadSession(input *protocol.HookInput) (protocol.Session, error) {
	if input == nil {
		return protocol.Session{}, fmt.Errorf("hook input is required")
	}
	id := a.GetSessionID(input)
	ref := input.SessionRef
	var err error
	if strings.TrimSpace(ref) == "" {
		dir, dirErr := a.GetSessionDir(protocol.RepoRoot())
		if dirErr != nil {
			return protocol.Session{}, dirErr
		}
		ref, err = a.ResolveSessionFile(dir, id)
		if err != nil {
			return protocol.Session{}, err
		}
	}
	if err := validateSessionRef(ref); err != nil {
		return protocol.Session{}, err
	}
	data, err := os.ReadFile(ref)
	if errors.Is(err, os.ErrNotExist) {
		data = nil
	} else if err != nil {
		return protocol.Session{}, err
	}
	files, _, err := a.ExtractModifiedFiles(ref, 0)
	if errors.Is(err, os.ErrNotExist) {
		files = []string{}
	} else if err != nil {
		return protocol.Session{}, err
	}
	return protocol.Session{
		SessionID:     id,
		AgentName:     agentName,
		RepoPath:      protocol.RepoRoot(),
		SessionRef:    ref,
		StartTime:     sessionStartTime(ref),
		NativeData:    data,
		ModifiedFiles: nonNil(files),
		NewFiles:      []string{},
		DeletedFiles:  []string{},
	}, nil
}

func (a *Agent) WriteSession(session protocol.Session) error {
	if !validSessionID(session.SessionID) {
		return fmt.Errorf("invalid Kimi session id")
	}
	if err := validateSessionRef(session.SessionRef); err != nil {
		return err
	}
	if err := os.MkdirAll(filepath.Dir(session.SessionRef), 0o700); err != nil {
		return err
	}
	return atomicWrite(session.SessionRef, session.NativeData, 0o600)
}

func (a *Agent) ReadTranscript(sessionRef string) ([]byte, error) {
	if err := validateSessionRef(sessionRef); err != nil {
		return nil, err
	}
	return os.ReadFile(sessionRef)
}

func (a *Agent) FormatResumeCommand(sessionID string) string {
	if !validSessionID(sessionID) {
		return "kimi --continue"
	}
	return "kimi --session " + sessionID
}

func validSessionID(value string) bool { return sessionIDPattern.MatchString(value) }

func kimiHome() string {
	if value := strings.TrimSpace(os.Getenv("KIMI_CODE_HOME")); value != "" {
		if abs, err := filepath.Abs(value); err == nil {
			return abs
		}
	}
	home, err := os.UserHomeDir()
	if err != nil {
		return filepath.Join(os.TempDir(), ".kimi-code")
	}
	return filepath.Join(home, ".kimi-code")
}

type sessionIndexRecord struct {
	SessionID  string `json:"sessionId"`
	SessionDir string `json:"sessionDir"`
	WorkDir    string `json:"workDir"`
}

func lookupSession(sessionID string) (string, bool) {
	f, err := os.Open(filepath.Join(kimiHome(), "session_index.jsonl"))
	if err != nil {
		return "", false
	}
	defer func() { _ = f.Close() }()
	root := filepath.Join(kimiHome(), "sessions")
	var matched string
	scanner := bufio.NewScanner(f)
	scanner.Buffer(make([]byte, 64*1024), 2*1024*1024)
	for scanner.Scan() {
		var record sessionIndexRecord
		if json.Unmarshal(scanner.Bytes(), &record) != nil || record.SessionID != sessionID {
			continue
		}
		dir := record.SessionDir
		if !filepath.IsAbs(dir) {
			dir = filepath.Join(kimiHome(), dir)
		}
		wire := filepath.Join(filepath.Clean(dir), "agents", "main", "wire.jsonl")
		if pathWithin(wire, root) {
			matched = wire
		}
	}
	return matched, matched != ""
}

func validateSessionRef(path string) error {
	if strings.TrimSpace(path) == "" {
		return fmt.Errorf("session_ref is required")
	}
	abs, err := filepath.Abs(path)
	if err != nil {
		return err
	}
	sessionsRoot := filepath.Join(kimiHome(), "sessions")
	if pathWithin(abs, sessionsRoot) {
		return nil
	}
	if pathWithin(abs, protocol.RepoRoot()) {
		return nil
	}
	return fmt.Errorf("session_ref escapes Kimi session storage")
}

func pathWithin(path, root string) bool {
	absPath, err := filepath.Abs(path)
	if err != nil {
		return false
	}
	absRoot, err := filepath.Abs(root)
	if err != nil {
		return false
	}
	rel, err := filepath.Rel(absRoot, absPath)
	return err == nil && rel != ".." && !strings.HasPrefix(rel, ".."+string(filepath.Separator))
}

func sessionStartTime(ref string) string {
	statePath := filepath.Join(filepath.Dir(filepath.Dir(filepath.Dir(ref))), "state.json")
	data, err := os.ReadFile(statePath)
	if err == nil {
		var state struct {
			CreatedAt float64 `json:"createdAt"`
		}
		if json.Unmarshal(data, &state) == nil && state.CreatedAt > 0 {
			return time.UnixMilli(int64(state.CreatedAt)).UTC().Format(time.RFC3339)
		}
	}
	if info, err := os.Stat(ref); err == nil {
		return info.ModTime().UTC().Format(time.RFC3339)
	}
	return time.Now().UTC().Format(time.RFC3339)
}

func atomicWrite(path string, data []byte, mode os.FileMode) error {
	dir := filepath.Dir(path)
	tmp, err := os.CreateTemp(dir, ".entire-kimi-*")
	if err != nil {
		return err
	}
	tmpPath := tmp.Name()
	defer func() { _ = os.Remove(tmpPath) }()
	if err := tmp.Chmod(mode); err != nil {
		_ = tmp.Close()
		return err
	}
	if _, err := tmp.Write(data); err != nil {
		_ = tmp.Close()
		return err
	}
	if err := tmp.Sync(); err != nil {
		_ = tmp.Close()
		return err
	}
	if err := tmp.Close(); err != nil {
		return err
	}
	return os.Rename(tmpPath, path)
}

func nonNil(values []string) []string {
	if values == nil {
		return []string{}
	}
	return values
}
