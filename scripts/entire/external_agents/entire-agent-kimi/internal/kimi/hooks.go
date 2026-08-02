package kimi

import (
	"bytes"
	"encoding/json"
	"errors"
	"fmt"
	"os"
	"path/filepath"
	"strings"
	"time"

	"github.com/learn-ukrainian/learn-ukrainian.github.io/scripts/entire/external_agents/entire-agent-kimi/internal/protocol"
)

const (
	blockBegin = "# BEGIN learn-ukrainian Entire Kimi hooks v1 separator="
	blockEnd   = "# END learn-ukrainian Entire Kimi hooks v1"
)

var hookSpecs = []struct{ event, hook string }{
	{"SessionStart", "session-start"},
	{"UserPromptSubmit", "turn-start"},
	{"Stop", "turn-end"},
	{"PreCompact", "compaction"},
	{"SessionEnd", "session-end"},
}

type rawHook struct {
	HookEventName string          `json:"hook_event_name"`
	HookType      string          `json:"hook_type"`
	SessionID     string          `json:"session_id"`
	SessionRef    string          `json:"session_ref"`
	Timestamp     string          `json:"timestamp"`
	CWD           string          `json:"cwd"`
	Source        string          `json:"source"`
	Reason        string          `json:"reason"`
	Trigger       string          `json:"trigger"`
	UserPrompt    string          `json:"user_prompt"`
	Prompt        json.RawMessage `json:"prompt"`
}

func (a *Agent) ParseHook(hook string, input []byte) (*protocol.Event, error) {
	var raw rawHook
	if len(bytes.TrimSpace(input)) > 0 {
		if err := json.Unmarshal(input, &raw); err != nil {
			return nil, fmt.Errorf("parse Kimi hook: %w", err)
		}
	}
	if !validSessionID(raw.SessionID) {
		raw.SessionID = stubSessionID
	}
	ref := raw.SessionRef
	if strings.TrimSpace(ref) == "" {
		dir, _ := a.GetSessionDir(protocol.RepoRoot())
		var err error
		ref, err = a.ResolveSessionFile(dir, raw.SessionID)
		if err != nil {
			return nil, err
		}
	}
	timestamp := raw.Timestamp
	if _, err := time.Parse(time.RFC3339, timestamp); err != nil {
		timestamp = time.Now().UTC().Format(time.RFC3339)
	}
	event := &protocol.Event{
		SessionID:  raw.SessionID,
		SessionRef: ref,
		Timestamp:  timestamp,
		Model:      latestModel(ref),
		Metadata:   map[string]string{"agent": agentName},
	}
	if raw.CWD != "" {
		event.Metadata["cwd"] = raw.CWD
	}
	if raw.Source != "" {
		event.Metadata["source"] = raw.Source
	}
	if raw.Reason != "" {
		event.Metadata["reason"] = raw.Reason
	}
	if raw.Trigger != "" {
		event.Metadata["trigger"] = raw.Trigger
	}
	if raw.HookEventName != "" {
		event.Metadata["hook_event_name"] = raw.HookEventName
	}
	switch hook {
	case "session-start":
		event.Type = 1
	case "turn-start":
		event.Type = 2
		event.Prompt = hookPrompt(raw)
	case "turn-end":
		event.Type = 3
	case "compaction":
		event.Type = 4
	case "session-end":
		event.Type = 5
	default:
		return nil, nil
	}
	return event, nil
}

func hookPrompt(raw rawHook) string {
	if strings.TrimSpace(raw.UserPrompt) != "" {
		return raw.UserPrompt
	}
	var direct string
	if json.Unmarshal(raw.Prompt, &direct) == nil && strings.TrimSpace(direct) != "" {
		return direct
	}
	var parts []contentPart
	if json.Unmarshal(raw.Prompt, &parts) != nil {
		return ""
	}
	var text []string
	for _, part := range parts {
		if part.Type == "text" && strings.TrimSpace(part.Text) != "" {
			text = append(text, part.Text)
		}
	}
	return strings.Join(text, "\n")
}

func (a *Agent) InstallHooks(_ bool, force bool) (int, error) {
	path := configPath()
	if err := os.MkdirAll(filepath.Dir(path), 0o700); err != nil {
		return 0, err
	}
	release, err := acquireConfigLock(path + ".entire-kimi.lock")
	if err != nil {
		return 0, err
	}
	defer release()
	original, err := os.ReadFile(path)
	if errors.Is(err, os.ErrNotExist) {
		original = nil
	} else if err != nil {
		return 0, err
	}
	without, found, exact, err := removeManagedBlock(original)
	if err != nil {
		return 0, err
	}
	if found && exact && !force {
		return 0, nil
	}
	if found && !exact && !force {
		return 0, fmt.Errorf("managed Entire Kimi hook block drifted; rerun with --force")
	}
	if found {
		original = without
	}
	separatorInserted := len(original) > 0 && original[len(original)-1] != '\n'
	updated := append([]byte(nil), original...)
	if separatorInserted {
		updated = append(updated, '\n')
	}
	updated = append(updated, managedBlock(separatorInserted)...)
	mode := os.FileMode(0o600)
	if info, statErr := os.Stat(path); statErr == nil {
		mode = info.Mode().Perm()
	}
	if err := atomicWrite(path, updated, mode); err != nil {
		return 0, err
	}
	return len(hookSpecs), nil
}

func (a *Agent) UninstallHooks() error {
	path := configPath()
	if err := os.MkdirAll(filepath.Dir(path), 0o700); err != nil {
		return err
	}
	release, err := acquireConfigLock(path + ".entire-kimi.lock")
	if err != nil {
		return err
	}
	defer release()
	original, err := os.ReadFile(path)
	if errors.Is(err, os.ErrNotExist) {
		return nil
	}
	if err != nil {
		return err
	}
	updated, found, _, err := removeManagedBlock(original)
	if err != nil || !found {
		return err
	}
	mode := os.FileMode(0o600)
	if info, statErr := os.Stat(path); statErr == nil {
		mode = info.Mode().Perm()
	}
	return atomicWrite(path, updated, mode)
}

func (a *Agent) AreHooksInstalled() bool {
	data, err := os.ReadFile(configPath())
	if err != nil {
		return false
	}
	_, found, exact, err := removeManagedBlock(data)
	return err == nil && found && exact
}

func configPath() string { return filepath.Join(kimiHome(), "config.toml") }

func managedBlock(separatorInserted bool) []byte {
	separator := "existing"
	if separatorInserted {
		separator = "inserted"
	}
	var b strings.Builder
	b.WriteString(blockBegin + separator + "\n")
	for _, spec := range hookSpecs {
		b.WriteString("[[hooks]]\n")
		b.WriteString("event = \"")
		b.WriteString(spec.event)
		b.WriteString("\"\n")
		b.WriteString("command = \"sh -c 'command -v entire >/dev/null 2>&1 || exit 0; entire hooks kimi ")
		b.WriteString(spec.hook)
		b.WriteString(" || true'\"\n")
		b.WriteString("timeout = 30\n\n")
	}
	b.WriteString(blockEnd + "\n")
	return []byte(b.String())
}

func removeManagedBlock(data []byte) ([]byte, bool, bool, error) {
	start := bytes.Index(data, []byte(blockBegin))
	if start < 0 {
		return append([]byte(nil), data...), false, false, nil
	}
	if bytes.Index(data[start+len(blockBegin):], []byte(blockBegin)) >= 0 {
		return nil, false, false, fmt.Errorf("multiple Entire Kimi hook blocks")
	}
	lineEndRel := bytes.IndexByte(data[start:], '\n')
	if lineEndRel < 0 {
		return nil, true, false, nil
	}
	lineEnd := start + lineEndRel
	header := string(data[start:lineEnd])
	separatorInserted := strings.HasSuffix(header, "inserted")
	separatorExisting := strings.HasSuffix(header, "existing")
	endRel := bytes.Index(data[lineEnd+1:], []byte(blockEnd))
	if endRel < 0 {
		return nil, true, false, nil
	}
	end := lineEnd + 1 + endRel + len(blockEnd)
	if end < len(data) && data[end] == '\n' {
		end++
	}
	exact := false
	if separatorInserted || separatorExisting {
		expected := managedBlock(separatorInserted)
		exact = bytes.Equal(data[start:end], expected)
	}
	removeStart := start
	if separatorInserted && start > 0 && data[start-1] == '\n' {
		removeStart--
	}
	updated := append([]byte(nil), data[:removeStart]...)
	updated = append(updated, data[end:]...)
	return updated, true, exact, nil
}

func acquireConfigLock(path string) (func(), error) {
	for attempt := 0; attempt < 100; attempt++ {
		file, err := os.OpenFile(path, os.O_CREATE|os.O_EXCL|os.O_WRONLY, 0o600)
		if err == nil {
			_, _ = fmt.Fprintf(file, "%d\n", os.Getpid())
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
	return nil, fmt.Errorf("timed out waiting for Kimi config lock")
}
