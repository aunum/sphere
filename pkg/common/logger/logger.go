package logger

import (
	"fmt"
	"io"
	"os"
	"strings"
	"time"

	"github.com/fatih/color"
)

// Logger creates a new instance of a logger.
type Logger func(format string, a ...interface{})

const (
	// ErrorLevel logging.
	ErrorLevel = 1
	// WarningLevel logging.
	WarningLevel = 2
	// InfoLevel logging.
	InfoLevel = 3
	// DebugLevel logging.
	DebugLevel = 4
	// DumpLevel logging.
	DumpLevel = 5
)

const (
	// ErrorLabel is a label for a Error message.
	ErrorLabel = "✖"
	// DebugLabel is a label for a debug message.
	DebugLabel = "▶"
	// DumpLabel is a label for a dump message.
	DumpLabel = "▼"
	// InfoLabel is a label for an informative message.
	InfoLabel = "ℹ"
	// SuccessLabel is a label for a success message.
	SuccessLabel = "✔"
	// WarningLabel is a label for a warning message.
	WarningLabel = "!"
)

var (
	// Level to log at. Defaults to info level.
	Level = InfoLevel
	// Color should be enabled for logs.
	Color = true
	// TestMode is enabled.
	TestMode = false
	// Timestamps should be printed.
	Timestamps = false
)

// Fatalf message logs formatted Error then exits.
func Fatalf(format string, a ...interface{}) {
	if Level >= ErrorLevel {
		a, w := extractLoggerArgs(format, a...)
		s := fmt.Sprintf(label(format, ErrorLabel), a...)

		if !TestMode {
			if Color {
				w = color.Output
				s = color.RedString(s)
			}
		}
		fmt.Fprintf(w, s)
		os.Exit(1)
	}
}

// Fatal logs Error message then exits with code 1.
func Fatal(a ...interface{}) {
	Fatalf(buildFormat(a), a...)
}

// Errorf is a formatted Error message.
func Errorf(format string, a ...interface{}) {
	if Level >= ErrorLevel {
		a, w := extractLoggerArgs(format, a...)
		s := fmt.Sprintf(label(format, ErrorLabel), a...)

		if !TestMode {
			if Color {
				w = color.Output
				s = color.RedString(s)
			}
		}
		fmt.Fprintf(w, s)
	}
}

// Error message.
func Error(a ...interface{}) {
	Errorf(buildFormat(a), a...)
}

// Infof is a formatted Info message.
func Infof(format string, a ...interface{}) {
	if Level >= InfoLevel {
		a, w := extractLoggerArgs(format, a...)
		s := fmt.Sprintf(label(format, InfoLabel), a...)

		if !TestMode {
			if Color {
				w = color.Output
				s = color.CyanString(s)
			}
		}
		fmt.Fprintf(w, s)
	}
}

// Info message.
func Info(a ...interface{}) {
	Infof(buildFormat(a), a...)
}

// Successf is a formatted Success message.
func Successf(format string, a ...interface{}) {
	if Level >= InfoLevel {
		a, w := extractLoggerArgs(format, a...)
		s := fmt.Sprintf(label(format, SuccessLabel), a...)

		if !TestMode {
			if Color {
				w = color.Output
				s = color.GreenString(s)
			}
		}
		fmt.Fprintf(w, s)
	}
}

// Success message.
func Success(a ...interface{}) {
	Successf(buildFormat(a), a...)
}

// Debugf is a formatted Debug message.
func Debugf(format string, a ...interface{}) {
	if Level >= DebugLevel {
		a, w := extractLoggerArgs(format, a...)
		s := fmt.Sprintf(label(format, DebugLabel), a...)

		if !TestMode {
			if Color {
				w = color.Output
				s = color.MagentaString(s)
			}
		}
		fmt.Fprintf(w, s)
	}
}

// Debug message.
func Debug(a ...interface{}) {
	Debugf(buildFormat(a), a...)
}

// Dumpf is a formatted Dump message.
func Dumpf(format string, a ...interface{}) {
	if Level >= DumpLevel {
		a, w := extractLoggerArgs(format, a...)
		s := fmt.Sprintf(label(format, DumpLabel), a...)

		if !TestMode {
			if Color {
				w = color.Output
				s = color.MagentaString(s)
			}
		}
		fmt.Fprintf(w, s)
	}
}

// Dump message.
func Dump(a ...interface{}) {
	Dumpf(buildFormat(a), a...)
}

// Warningf is a formatted Warning message.
func Warningf(format string, a ...interface{}) {
	if Level >= WarningLevel {
		a, w := extractLoggerArgs(format, a...)
		s := fmt.Sprintf(label(format, WarningLabel), a...)

		if !TestMode {
			if Color {
				w = color.Output
				s = color.YellowString(s)
			}
		}
		fmt.Fprintf(w, s)
	}
}

// Warning message.
func Warning(a ...interface{}) {
	Warningf(buildFormat(a), a...)
}

func extractLoggerArgs(format string, a ...interface{}) ([]interface{}, io.Writer) {
	var w io.Writer = os.Stdout

	if n := len(a); n > 0 {
		// extract an io.Writer at the end of a
		if value, ok := a[n-1].(io.Writer); ok {
			w = value
			a = a[0 : n-1]
		}
	}

	return a, w
}

func label(format, label string) string {
	if Timestamps {
		return labelWithTime(format, label)
	}
	return labelWithoutTime(format, label)
}

func labelWithTime(format, label string) string {
	t := time.Now()
	rfct := t.Format(time.RFC3339)
	if !strings.Contains(format, "\n") {
		format = fmt.Sprintf("%s%s", format, "\n")
	}
	return fmt.Sprintf("%s [%s]  %s", rfct, label, format)
}

func labelWithoutTime(format, label string) string {
	if !strings.Contains(format, "\n") {
		format = fmt.Sprintf("%s%s", format, "\n")
	}
	return fmt.Sprintf("[%s]  %s", label, format)
}

func buildFormat(f ...interface{}) string {
	var fin string
	for _, i := range f {
		if _, ok := i.(error); ok {
			fin += "%s "
		} else if _, ok := i.(string); ok {
			fin += "%s "
		} else {
			fin += "%#v "
		}
	}
	return fin
}
