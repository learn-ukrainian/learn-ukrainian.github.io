package main

import (
	"fmt"
	"os"

	"github.com/learn-ukrainian/learn-ukrainian.github.io/scripts/entire/external_agents/entire-agent-kimi/internal/kimi"
	"github.com/learn-ukrainian/learn-ukrainian.github.io/scripts/entire/external_agents/entire-agent-kimi/internal/protocol"
)

func main() {
	if err := protocol.Run(kimi.New(), os.Args[1:], os.Stdin, os.Stdout); err != nil {
		_, _ = fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
}
