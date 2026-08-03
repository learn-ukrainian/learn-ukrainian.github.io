package fleet

import (
	"bufio"
	"bytes"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"os"
	"path/filepath"
	"regexp"
	"sort"
	"strings"
	"time"

	"github.com/learn-ukrainian/learn-ukrainian.github.io/scripts/entire/external_agents/entire-agent-kimi/internal/protocol"
)

const (
	agentName = "fleet"
	agentType = "Project Runner"
	marker    = "{\"schema\":\"entire-agent-fleet-hooks.v1\"}\n"
)

var sessionIDPattern = regexp.MustCompile(`^fleet-[0-9a-f]{32}$`)

type Agent struct{}

type transcriptRecord struct {
	Type      string            `json:"type"`
	SessionID string            `json:"session_id"`
	Timestamp string            `json:"timestamp"`
	RepoPath  string            `json:"repo_path"`
	Text      string            `json:"text"`
	Path      string            `json:"path"`
	Model     string            `json:"model"`
	Metadata  map[string]string `json:"metadata"`
}

func New() *Agent { return &Agent{} }

func (a *Agent) Info() protocol.Info {
	return protocol.Info{
		ProtocolVersion: protocol.Version,
		Name:            agentName,
		Type:            agentType,
		Description:     "External-agent capture for unsupported learn-ukrainian project-runner hosts",
		IsPreview:       true,
		ProtectedDirs:   []string{"batch_state/entire/fleet-sessions/v1"},
		HookNames:       []string{"session-start", "turn-start", "turn-end", "session-end"},
		Capabilities: protocol.Capabilities{
			Hooks:              true,
			TranscriptAnalyzer: true,
			UsesTerminal:       true,
		},
	}
}

func (a *Agent) Detect() protocol.DetectResponse {
	return protocol.DetectResponse{Present: true}
}

func (a *Agent) GetSessionID(input *protocol.HookInput) string {
	if input != nil && validSessionID(input.SessionID) {
		return input.SessionID
	}
	return ""
}

func (a *Agent) GetSessionDir(_ string) (string, error) {
	return captureRoot()
}

func (a *Agent) ResolveSessionFile(sessionDir, sessionID string) (string, error) {
	if !validSessionID(sessionID) {
		return "", fmt.Errorf("invalid fleet session id")
	}
	root, err := captureRoot()
	if err != nil {
		return "", err
	}
	if strings.TrimSpace(sessionDir) == "" {
		sessionDir = root
	}
	dir, err := filepath.Abs(sessionDir)
	if err != nil || !pathWithin(dir, root) {
		return "", fmt.Errorf("session directory escapes fleet capture root")
	}
	ref := filepath.Join(dir, sessionID, "transcript.jsonl")
	if err := validateSessionRef(ref); err != nil {
		return "", err
	}
	return ref, nil
}

func (a *Agent) ReadSession(input *protocol.HookInput) (protocol.Session, error) {
	if input == nil || !validSessionID(input.SessionID) {
		return protocol.Session{}, fmt.Errorf("valid hook input is required")
	}
	ref := input.SessionRef
	if strings.TrimSpace(ref) == "" {
		dir, err := a.GetSessionDir(protocol.RepoRoot())
		if err != nil {
			return protocol.Session{}, err
		}
		ref, err = a.ResolveSessionFile(dir, input.SessionID)
		if err != nil {
			return protocol.Session{}, err
		}
	}
	if err := validateSessionRef(ref); err != nil {
		return protocol.Session{}, err
	}
	data, err := os.ReadFile(ref)
	if err != nil {
		return protocol.Session{}, err
	}
	records := parseRecords(data)
	repoPath := protocol.RepoRoot()
	startTime := time.Now().UTC().Format(time.RFC3339)
	for _, record := range records {
		if record.Type != "session" || record.SessionID != input.SessionID {
			continue
		}
		if strings.TrimSpace(record.RepoPath) != "" {
			repoPath = record.RepoPath
		}
		if validTimestamp(record.Timestamp) {
			startTime = record.Timestamp
		}
		break
	}
	files, _, err := a.ExtractModifiedFiles(ref, 0)
	if err != nil {
		return protocol.Session{}, err
	}
	return protocol.Session{
		SessionID:     input.SessionID,
		AgentName:     agentName,
		RepoPath:      repoPath,
		SessionRef:    ref,
		StartTime:     startTime,
		NativeData:    data,
		ModifiedFiles: files,
		NewFiles:      []string{},
		DeletedFiles:  []string{},
	}, nil
}

func (a *Agent) WriteSession(session protocol.Session) error {
	if !validSessionID(session.SessionID) {
		return fmt.Errorf("invalid fleet session id")
	}
	ref := session.SessionRef
	if strings.TrimSpace(ref) == "" {
		dir, err := a.GetSessionDir(session.RepoPath)
		if err != nil {
			return err
		}
		ref, err = a.ResolveSessionFile(dir, session.SessionID)
		if err != nil {
			return err
		}
	}
	if err := validateSessionRef(ref); err != nil {
		return err
	}
	if err := os.MkdirAll(filepath.Dir(ref), 0o700); err != nil {
		return err
	}
	if err := os.Chmod(filepath.Dir(ref), 0o700); err != nil {
		return err
	}
	return atomicWrite(ref, session.NativeData, 0o600)
}

func (a *Agent) ReadTranscript(sessionRef string) ([]byte, error) {
	if err := validateSessionRef(sessionRef); err != nil {
		return nil, err
	}
	return os.ReadFile(sessionRef)
}

func (a *Agent) ParseHook(hook string, input []byte) (*protocol.Event, error) {
	var raw protocol.HookInput
	if err := json.Unmarshal(input, &raw); err != nil {
		return nil, fmt.Errorf("parse fleet hook: %w", err)
	}
	if !validSessionID(raw.SessionID) {
		return nil, fmt.Errorf("invalid fleet session id")
	}
	if strings.TrimSpace(raw.SessionRef) == "" {
		dir, err := a.GetSessionDir(protocol.RepoRoot())
		if err != nil {
			return nil, err
		}
		raw.SessionRef, err = a.ResolveSessionFile(dir, raw.SessionID)
		if err != nil {
			return nil, err
		}
	}
	if err := validateSessionRef(raw.SessionRef); err != nil {
		return nil, err
	}
	eventType := 0
	switch hook {
	case "session-start":
		eventType = 1
	case "turn-start":
		eventType = 2
	case "turn-end":
		eventType = 3
	case "session-end":
		eventType = 5
	default:
		return nil, nil
	}
	timestamp := raw.Timestamp
	if !validTimestamp(timestamp) {
		timestamp = time.Now().UTC().Format(time.RFC3339)
	}
	metadata := map[string]string{"agent": agentName}
	for key, value := range raw.RawData {
		text, ok := value.(string)
		if !ok || strings.TrimSpace(text) == "" {
			continue
		}
		metadata[key] = text
	}
	model := metadata["actual_model"]
	if model == "" && metadata["actual_model_known"] != "false" {
		model = metadata["requested_model"]
	}
	event := &protocol.Event{
		Type:       eventType,
		SessionID:  raw.SessionID,
		SessionRef: raw.SessionRef,
		Model:      model,
		Timestamp:  timestamp,
		Metadata:   metadata,
	}
	if hook == "turn-start" {
		event.Prompt = raw.UserPrompt
	}
	return event, nil
}

func (a *Agent) InstallHooks(_ bool, force bool) (int, error) {
	path, err := markerPath()
	if err != nil {
		return 0, err
	}
	if err := os.MkdirAll(filepath.Dir(path), 0o700); err != nil {
		return 0, err
	}
	release, err := acquireLock(path + ".lock")
	if err != nil {
		return 0, err
	}
	defer release()
	data, readErr := os.ReadFile(path)
	if readErr == nil && string(data) == marker && !force {
		return 0, nil
	}
	if readErr == nil && string(data) != marker && !force {
		return 0, fmt.Errorf("fleet hook marker drifted; rerun with --force")
	}
	if readErr != nil && !errors.Is(readErr, os.ErrNotExist) {
		return 0, readErr
	}
	if err := atomicWrite(path, []byte(marker), 0o600); err != nil {
		return 0, err
	}
	return 4, nil
}

func (a *Agent) UninstallHooks() error {
	path, err := markerPath()
	if err != nil {
		return err
	}
	if err := os.Remove(path); err != nil && !errors.Is(err, os.ErrNotExist) {
		return err
	}
	return nil
}

func (a *Agent) AreHooksInstalled() bool {
	path, err := markerPath()
	if err != nil {
		return false
	}
	data, err := os.ReadFile(path)
	return err == nil && string(data) == marker
}

func (a *Agent) GetTranscriptPosition(path string) (int, error) {
	if err := validateSessionRef(path); err != nil {
		return 0, err
	}
	info, err := os.Stat(path)
	if err != nil {
		return 0, err
	}
	return int(info.Size()), nil
}

func (a *Agent) ExtractModifiedFiles(path string, offset int) ([]string, int, error) {
	data, position, err := transcriptRange(path, offset)
	if err != nil {
		return nil, 0, err
	}
	seen := map[string]struct{}{}
	for _, record := range parseRecords(data) {
		if record.Type != "file" {
			continue
		}
		if normalized, ok := normalizeRepoPath(record.Path); ok {
			seen[normalized] = struct{}{}
		}
	}
	files := make([]string, 0, len(seen))
	for path := range seen {
		files = append(files, path)
	}
	sort.Strings(files)
	return files, position, nil
}

func (a *Agent) ExtractPrompts(path string, offset int) ([]string, error) {
	data, _, err := transcriptRange(path, offset)
	if err != nil {
		return nil, err
	}
	prompts := []string{}
	for _, record := range parseRecords(data) {
		if record.Type == "user" && strings.TrimSpace(record.Text) != "" {
			prompts = append(prompts, record.Text)
		}
	}
	return prompts, nil
}

func (a *Agent) CalculateTokens(_ []byte, _ int) (protocol.TokenUsage, error) {
	return protocol.TokenUsage{}, nil
}

func (a *Agent) FormatResumeCommand(_ string) string { return "" }

func validSessionID(value string) bool { return sessionIDPattern.MatchString(value) }

func captureRoot() (string, error) {
	root := strings.TrimSpace(os.Getenv("ENTIRE_FLEET_CAPTURE_ROOT"))
	if root == "" {
		root = filepath.Join(protocol.RepoRoot(), "batch_state", "entire", "fleet-sessions", "v1")
	}
	return filepath.Abs(root)
}

func markerPath() (string, error) {
	home := strings.TrimSpace(os.Getenv("ENTIRE_AGENT_FLEET_HOME"))
	if home == "" {
		userHome, err := os.UserHomeDir()
		if err != nil {
			return "", err
		}
		home = filepath.Join(userHome, ".config", "entire-agent-fleet")
	}
	abs, err := filepath.Abs(home)
	if err != nil {
		return "", err
	}
	return filepath.Join(abs, "hooks-v1.json"), nil
}

func validateSessionRef(path string) error {
	if strings.TrimSpace(path) == "" {
		return fmt.Errorf("session_ref is required")
	}
	root, err := captureRoot()
	if err != nil {
		return err
	}
	abs, err := filepath.Abs(path)
	if err != nil || !pathWithin(abs, root) {
		return fmt.Errorf("session_ref escapes fleet capture root")
	}
	rel, err := filepath.Rel(root, abs)
	if err != nil {
		return err
	}
	parts := strings.Split(filepath.Clean(rel), string(filepath.Separator))
	if len(parts) != 2 || !validSessionID(parts[0]) || parts[1] != "transcript.jsonl" {
		return fmt.Errorf("session_ref is not an exact fleet transcript")
	}
	parent := filepath.Dir(abs)
	resolvedRoot, rootErr := filepath.EvalSymlinks(root)
	resolvedParent, parentErr := filepath.EvalSymlinks(parent)
	if rootErr == nil && parentErr == nil {
		if !pathWithin(resolvedParent, resolvedRoot) {
			return fmt.Errorf("session_ref resolves outside fleet capture root")
		}
	}
	return nil
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

func normalizeRepoPath(value string) (string, bool) {
	value = strings.TrimSpace(value)
	if value == "" || filepath.IsAbs(value) {
		return "", false
	}
	clean := filepath.Clean(value)
	if clean == "." || clean == ".." || strings.HasPrefix(clean, ".."+string(filepath.Separator)) {
		return "", false
	}
	return filepath.ToSlash(clean), true
}

func validTimestamp(value string) bool {
	_, err := time.Parse(time.RFC3339Nano, value)
	return err == nil
}

func transcriptRange(path string, offset int) ([]byte, int, error) {
	if err := validateSessionRef(path); err != nil {
		return nil, 0, err
	}
	f, err := os.Open(path)
	if err != nil {
		return nil, 0, err
	}
	defer func() { _ = f.Close() }()
	info, err := f.Stat()
	if err != nil {
		return nil, 0, err
	}
	position := int(info.Size())
	if offset < 0 {
		offset = 0
	}
	if offset >= position {
		return []byte{}, position, nil
	}
	partial := false
	if offset > 0 {
		if _, err := f.Seek(int64(offset-1), io.SeekStart); err != nil {
			return nil, 0, err
		}
		var previous [1]byte
		if _, err := io.ReadFull(f, previous[:]); err != nil {
			return nil, 0, err
		}
		partial = previous[0] != '\n'
	}
	if _, err := f.Seek(int64(offset), io.SeekStart); err != nil {
		return nil, 0, err
	}
	data, err := io.ReadAll(io.LimitReader(f, 64*1024*1024))
	if err != nil {
		return nil, 0, err
	}
	if partial {
		if next := bytes.IndexByte(data, '\n'); next >= 0 {
			data = data[next+1:]
		} else {
			data = nil
		}
	}
	return data, position, nil
}

func parseRecords(data []byte) []transcriptRecord {
	records := []transcriptRecord{}
	scanner := bufio.NewScanner(bytes.NewReader(data))
	scanner.Buffer(make([]byte, 64*1024), 8*1024*1024)
	for scanner.Scan() {
		var record transcriptRecord
		if json.Unmarshal(scanner.Bytes(), &record) == nil {
			records = append(records, record)
		}
	}
	return records
}

func atomicWrite(path string, data []byte, mode os.FileMode) error {
	dir := filepath.Dir(path)
	if err := os.MkdirAll(dir, 0o700); err != nil {
		return err
	}
	tmp, err := os.CreateTemp(dir, ".entire-fleet-*")
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

func acquireLock(path string) (func(), error) {
	for attempt := 0; attempt < 100; attempt++ {
		file, err := os.OpenFile(path, os.O_CREATE|os.O_EXCL|os.O_WRONLY, 0o600)
		if err == nil {
			_ = file.Close()
			return func() { _ = os.Remove(path) }, nil
		}
		if !errors.Is(err, os.ErrExist) {
			return nil, err
		}
		if info, statErr := os.Stat(path); statErr == nil && time.Since(info.ModTime()) > time.Minute {
			_ = os.Remove(path)
			continue
		}
		time.Sleep(20 * time.Millisecond)
	}
	return nil, fmt.Errorf("timed out waiting for fleet hook marker lock")
}
