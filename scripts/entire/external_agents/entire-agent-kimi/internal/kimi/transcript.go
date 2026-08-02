package kimi

import (
	"bufio"
	"bytes"
	"encoding/json"
	"errors"
	"io"
	"os"
	"path/filepath"
	"sort"
	"strings"

	"github.com/learn-ukrainian/learn-ukrainian.github.io/scripts/entire/external_agents/entire-agent-kimi/internal/protocol"
)

type wireRecord struct {
	Type       string          `json:"type"`
	ModelAlias string          `json:"modelAlias"`
	Model      string          `json:"model"`
	Input      []contentPart   `json:"input"`
	Event      json.RawMessage `json:"event"`
	Usage      usageRecord     `json:"usage"`
}

type contentPart struct {
	Type string `json:"type"`
	Text string `json:"text"`
}
type usageRecord struct {
	InputOther         int `json:"inputOther"`
	InputCacheRead     int `json:"inputCacheRead"`
	InputCacheCreation int `json:"inputCacheCreation"`
	Output             int `json:"output"`
}
type loopEvent struct {
	Type string                     `json:"type"`
	Name string                     `json:"name"`
	Args map[string]json.RawMessage `json:"args"`
}

func (a *Agent) GetTranscriptPosition(path string) (int, error) {
	if err := validateSessionRef(path); err != nil {
		return 0, err
	}
	info, err := os.Stat(path)
	if errors.Is(err, os.ErrNotExist) {
		return 0, nil
	}
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
	for _, record := range parseWireRecords(data) {
		if record.Type != "context.append_loop_event" {
			continue
		}
		var event loopEvent
		if json.Unmarshal(record.Event, &event) != nil || event.Type != "tool.call" {
			continue
		}
		if event.Name != "Write" && event.Name != "Edit" {
			continue
		}
		raw, ok := event.Args["path"]
		if !ok {
			continue
		}
		var value string
		if json.Unmarshal(raw, &value) != nil {
			continue
		}
		if normalized, ok := normalizeRepoPath(value); ok {
			seen[normalized] = struct{}{}
		}
	}
	files := make([]string, 0, len(seen))
	for value := range seen {
		files = append(files, value)
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
	for _, record := range parseWireRecords(data) {
		if record.Type != "turn.prompt" {
			continue
		}
		var parts []string
		for _, part := range record.Input {
			if part.Type == "text" && strings.TrimSpace(part.Text) != "" {
				parts = append(parts, part.Text)
			}
		}
		if len(parts) > 0 {
			prompts = append(prompts, strings.Join(parts, "\n"))
		}
	}
	return prompts, nil
}

func (a *Agent) CalculateTokens(data []byte, offset int) (protocol.TokenUsage, error) {
	if offset < 0 {
		offset = 0
	}
	if offset >= len(data) {
		return protocol.TokenUsage{}, nil
	}
	partialLine := offset > 0 && data[offset-1] != '\n'
	data = data[offset:]
	if partialLine {
		if next := bytes.IndexByte(data, '\n'); next >= 0 {
			data = data[next+1:]
		} else {
			return protocol.TokenUsage{}, nil
		}
	}
	var total protocol.TokenUsage
	for _, record := range parseWireRecords(data) {
		if record.Type != "usage.record" {
			continue
		}
		total.InputTokens += max(record.Usage.InputOther, 0)
		total.CacheReadTokens += max(record.Usage.InputCacheRead, 0)
		total.CacheCreationTokens += max(record.Usage.InputCacheCreation, 0)
		total.OutputTokens += max(record.Usage.Output, 0)
		total.APICallCount++
	}
	return total, nil
}

func transcriptRange(path string, offset int) ([]byte, int, error) {
	if err := validateSessionRef(path); err != nil {
		return nil, 0, err
	}
	f, err := os.Open(path)
	if errors.Is(err, os.ErrNotExist) {
		return nil, 0, nil
	}
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
		return nil, position, nil
	}
	partialLine := false
	if offset > 0 {
		if _, err := f.Seek(int64(offset-1), io.SeekStart); err != nil {
			return nil, 0, err
		}
		var previous [1]byte
		if _, err := io.ReadFull(f, previous[:]); err != nil {
			return nil, 0, err
		}
		partialLine = previous[0] != '\n'
	}
	if _, err := f.Seek(int64(offset), io.SeekStart); err != nil {
		return nil, 0, err
	}
	data, err := io.ReadAll(io.LimitReader(f, 64*1024*1024))
	if err != nil {
		return nil, 0, err
	}
	if partialLine {
		if next := bytes.IndexByte(data, '\n'); next >= 0 {
			data = data[next+1:]
		} else {
			data = nil
		}
	}
	return data, position, nil
}

func parseWireRecords(data []byte) []wireRecord {
	records := []wireRecord{}
	scanner := bufio.NewScanner(bytes.NewReader(data))
	scanner.Buffer(make([]byte, 64*1024), 8*1024*1024)
	for scanner.Scan() {
		var record wireRecord
		if json.Unmarshal(scanner.Bytes(), &record) == nil {
			records = append(records, record)
		}
	}
	return records
}

func latestModel(path string) string {
	if err := validateSessionRef(path); err != nil {
		return ""
	}
	data, err := os.ReadFile(path)
	if err != nil {
		return ""
	}
	model := ""
	for _, record := range parseWireRecords(data) {
		if record.ModelAlias != "" {
			model = record.ModelAlias
		}
		if record.Type == "usage.record" && record.Model != "" {
			model = record.Model
		}
	}
	return model
}

func normalizeRepoPath(value string) (string, bool) {
	value = strings.TrimSpace(value)
	if value == "" {
		return "", false
	}
	root, err := filepath.Abs(protocol.RepoRoot())
	if err != nil {
		return "", false
	}
	path := filepath.Clean(value)
	if !filepath.IsAbs(path) {
		path = filepath.Join(root, path)
	}
	abs, err := filepath.Abs(path)
	if err != nil || !pathWithin(abs, root) {
		return "", false
	}
	rel, err := filepath.Rel(root, abs)
	if err != nil || rel == "." {
		return "", false
	}
	return filepath.ToSlash(rel), true
}
