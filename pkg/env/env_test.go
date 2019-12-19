package env

import "testing"

func TestLocal(t *testing.T) {
	env := NewLocalEnv("CartPole-v0", true)
}
