package env

import (
	"fmt"
	"testing"

	"github.com/stretchr/testify/require"
)

func TestLocal(t *testing.T) {
	// address := fmt.Sprintf("localhost:%s", "32769")
	// conn, err := grpc.Dial(address, grpc.WithInsecure(), grpc.WithBlock())
	// require.Nil(t, err)
	// defer conn.Close()
	// fmt.Println("connected!")

	// sphereClient := sphere.NewEnvironmentAPIClient(conn)
	// _, err = sphereClient.Info(context.Background(), &sphere.Empty{})
	// require.Nil(t, err)
	// server := Server{Client: sphereClient}

	server, err := NewLocalServer(GymServerConfig)
	require.Nil(t, err)

	fmt.Println("creating env")
	env, err := server.Make("CartPole-v0")
	require.Nil(t, err)
	fmt.Printf("env: %+v\n", env)

	for i := 0; i <= 20; i++ {
		_, err := env.Reset()
		require.Nil(t, err)

		for ts := 0; ts <= int(env.MaxEpisodeSteps); ts++ {
			action, err := env.SampleAction()
			require.Nil(t, err)
			resp, err := env.Step(action)
			require.Nil(t, err)
			if resp.Done {
				fmt.Printf("Episode finished after %d timesteps \n", ts+1)
				break
			}
		}
	}
	env.End()
}
