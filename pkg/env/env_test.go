package env

import (
	"context"
	"fmt"
	"testing"

	sphere "github.com/pbarker/sphere/api/gen/go/v1alpha"
	"github.com/stretchr/testify/require"
	"google.golang.org/grpc"
)

func TestLocal(t *testing.T) {
	address := fmt.Sprintf("localhost:%s", "32794")
	conn, err := grpc.Dial(address, grpc.WithInsecure(), grpc.WithBlock())
	require.Nil(t, err)
	defer conn.Close()
	fmt.Println("connected!")

	sphereClient := sphere.NewEnvironmentAPIClient(conn)
	_, err = sphereClient.Info(context.Background(), &sphere.Empty{})
	require.Nil(t, err)
	server := Server{Client: sphereClient}

	// server, err := NewLocalServer(GymServerConfig)
	// require.Nil(t, err)

	fmt.Println("creating env")
	env, err := server.Make("CartPole-v0")
	require.Nil(t, err)
	fmt.Printf("env: %+v\n", env)

	for i := 0; i <= 20; i++ {
		// fmt.Printf("episode %d \n", i)
		_, err := env.Reset()
		// fmt.Printf("observation: %+v \n", obv)
		require.Nil(t, err)

		for ts := 0; ts <= int(env.MaxEpisodeSteps); ts++ {
			// fmt.Println("getting sample action")
			action, err := env.SampleAction()
			require.Nil(t, err)
			// fmt.Printf("sample action: %d \n", action)

			resp, err := env.Step(action)
			require.Nil(t, err)
			// fmt.Printf("step response: %+v \n", resp)

			if resp.Done {
				fmt.Printf("Episode finished after %d timesteps \n", ts+1)
				break
			}
		}
	}
	env.End()
}
