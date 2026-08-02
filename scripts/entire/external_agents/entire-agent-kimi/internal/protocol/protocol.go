package protocol

import (
	"encoding/json"
	"flag"
	"fmt"
	"io"
	"os"
)

type Agent interface {
	Info() Info
	Detect() DetectResponse
	GetSessionID(*HookInput) string
	GetSessionDir(string) (string, error)
	ResolveSessionFile(string, string) (string, error)
	ReadSession(*HookInput) (Session, error)
	WriteSession(Session) error
	ReadTranscript(string) ([]byte, error)
	ParseHook(string, []byte) (*Event, error)
	InstallHooks(bool, bool) (int, error)
	UninstallHooks() error
	AreHooksInstalled() bool
	GetTranscriptPosition(string) (int, error)
	ExtractModifiedFiles(string, int) ([]string, int, error)
	ExtractPrompts(string, int) ([]string, error)
	CalculateTokens([]byte, int) (TokenUsage, error)
	FormatResumeCommand(string) string
}

func WriteJSON(w io.Writer, value any) error {
	enc := json.NewEncoder(w)
	enc.SetEscapeHTML(false)
	return enc.Encode(value)
}

func readJSON[T any](r io.Reader) (*T, error) {
	var value T
	if err := json.NewDecoder(r).Decode(&value); err != nil {
		return nil, err
	}
	return &value, nil
}

func RepoRoot() string {
	if root := os.Getenv("ENTIRE_REPO_ROOT"); root != "" {
		return root
	}
	root, _ := os.Getwd()
	return root
}

func Run(agent Agent, args []string, stdin io.Reader, stdout io.Writer) error {
	if len(args) == 0 {
		return fmt.Errorf("usage: entire-agent-kimi <subcommand> [args]")
	}
	switch args[0] {
	case "info":
		return WriteJSON(stdout, agent.Info())
	case "detect":
		return WriteJSON(stdout, agent.Detect())
	case "get-session-id":
		in, err := readJSON[HookInput](stdin)
		if err != nil {
			return err
		}
		return WriteJSON(stdout, SessionIDResponse{SessionID: agent.GetSessionID(in)})
	case "get-session-dir":
		fs := newFlags("get-session-dir")
		repo := fs.String("repo-path", "", "repo path")
		if err := fs.Parse(args[1:]); err != nil {
			return err
		}
		dir, err := agent.GetSessionDir(*repo)
		if err != nil {
			return err
		}
		return WriteJSON(stdout, SessionDirResponse{SessionDir: dir})
	case "resolve-session-file":
		fs := newFlags("resolve-session-file")
		dir := fs.String("session-dir", "", "session dir")
		id := fs.String("session-id", "", "session id")
		if err := fs.Parse(args[1:]); err != nil {
			return err
		}
		path, err := agent.ResolveSessionFile(*dir, *id)
		if err != nil {
			return err
		}
		return WriteJSON(stdout, SessionFileResponse{SessionFile: path})
	case "read-session":
		in, err := readJSON[HookInput](stdin)
		if err != nil {
			return err
		}
		session, err := agent.ReadSession(in)
		if err != nil {
			return err
		}
		return WriteJSON(stdout, session)
	case "write-session":
		session, err := readJSON[Session](stdin)
		if err != nil {
			return err
		}
		return agent.WriteSession(*session)
	case "read-transcript":
		fs := newFlags("read-transcript")
		ref := fs.String("session-ref", "", "session ref")
		if err := fs.Parse(args[1:]); err != nil {
			return err
		}
		data, err := agent.ReadTranscript(*ref)
		if err != nil {
			return err
		}
		_, err = stdout.Write(data)
		return err
	case "chunk-transcript":
		fs := newFlags("chunk-transcript")
		max := fs.Int("max-size", 0, "max size")
		if err := fs.Parse(args[1:]); err != nil {
			return err
		}
		if *max <= 0 {
			return fmt.Errorf("max-size must be positive")
		}
		data, err := io.ReadAll(stdin)
		if err != nil {
			return err
		}
		chunks := make([][]byte, 0, (len(data) / *max)+1)
		if len(data) == 0 {
			chunks = append(chunks, []byte{})
		}
		for start := 0; start < len(data); start += *max {
			end := min(start+*max, len(data))
			chunks = append(chunks, append([]byte(nil), data[start:end]...))
		}
		return WriteJSON(stdout, ChunkResponse{Chunks: chunks})
	case "reassemble-transcript":
		in, err := readJSON[ChunkResponse](stdin)
		if err != nil {
			return err
		}
		for _, chunk := range in.Chunks {
			if _, err := stdout.Write(chunk); err != nil {
				return err
			}
		}
		return nil
	case "format-resume-command":
		fs := newFlags("format-resume-command")
		id := fs.String("session-id", "", "session id")
		if err := fs.Parse(args[1:]); err != nil {
			return err
		}
		return WriteJSON(stdout, ResumeResponse{Command: agent.FormatResumeCommand(*id)})
	case "parse-hook":
		fs := newFlags("parse-hook")
		hook := fs.String("hook", "", "hook")
		if err := fs.Parse(args[1:]); err != nil {
			return err
		}
		data, err := io.ReadAll(stdin)
		if err != nil {
			return err
		}
		event, err := agent.ParseHook(*hook, data)
		if err != nil {
			return err
		}
		if event == nil {
			_, err = io.WriteString(stdout, "null\n")
			return err
		}
		return WriteJSON(stdout, event)
	case "install-hooks":
		fs := newFlags("install-hooks")
		localDev := fs.Bool("local-dev", false, "local dev")
		force := fs.Bool("force", false, "force")
		if err := fs.Parse(args[1:]); err != nil {
			return err
		}
		count, err := agent.InstallHooks(*localDev, *force)
		if err != nil {
			return err
		}
		return WriteJSON(stdout, HooksInstalledResponse{HooksInstalled: count})
	case "uninstall-hooks":
		return agent.UninstallHooks()
	case "are-hooks-installed":
		return WriteJSON(stdout, HookStatusResponse{Installed: agent.AreHooksInstalled()})
	case "get-transcript-position":
		fs := newFlags("get-transcript-position")
		path := fs.String("path", "", "path")
		if err := fs.Parse(args[1:]); err != nil {
			return err
		}
		position, err := agent.GetTranscriptPosition(*path)
		if err != nil {
			return err
		}
		return WriteJSON(stdout, PositionResponse{Position: position})
	case "extract-modified-files":
		fs := newFlags("extract-modified-files")
		path := fs.String("path", "", "path")
		offset := fs.Int("offset", 0, "offset")
		if err := fs.Parse(args[1:]); err != nil {
			return err
		}
		files, position, err := agent.ExtractModifiedFiles(*path, *offset)
		if err != nil {
			return err
		}
		return WriteJSON(stdout, ExtractFilesResponse{Files: files, CurrentPosition: position})
	case "extract-prompts":
		fs := newFlags("extract-prompts")
		ref := fs.String("session-ref", "", "session ref")
		offset := fs.Int("offset", 0, "offset")
		if err := fs.Parse(args[1:]); err != nil {
			return err
		}
		prompts, err := agent.ExtractPrompts(*ref, *offset)
		if err != nil {
			return err
		}
		return WriteJSON(stdout, ExtractPromptsResponse{Prompts: prompts})
	case "extract-summary":
		return WriteJSON(stdout, ExtractSummaryResponse{Summary: "", HasSummary: false})
	case "calculate-tokens":
		fs := newFlags("calculate-tokens")
		offset := fs.Int("offset", 0, "offset")
		if err := fs.Parse(args[1:]); err != nil {
			return err
		}
		data, err := io.ReadAll(stdin)
		if err != nil {
			return err
		}
		usage, err := agent.CalculateTokens(data, *offset)
		if err != nil {
			return err
		}
		return WriteJSON(stdout, usage)
	default:
		return fmt.Errorf("unknown subcommand: %s", args[0])
	}
}

func newFlags(name string) *flag.FlagSet {
	fs := flag.NewFlagSet(name, flag.ContinueOnError)
	fs.SetOutput(io.Discard)
	return fs
}
