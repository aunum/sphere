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
			obv, reward, done, err := env.Step(action)
			require.Nil(t, err)
			fmt.Printf("observation: \n%+v\n", obv)
			fmt.Printf("reward: %+v \n", reward)
			if done {
				fmt.Printf("Episode finished after %d timesteps \n", ts+1)
				break
			}
		}
	}
	env.End()
}

func customLocalServer(t *testing.T, port string) *Server {
	address := fmt.Sprintf("localhost:%s", port)
	conn, err := grpc.Dial(address, grpc.WithInsecure(), grpc.WithBlock())
	require.Nil(t, err)
	defer conn.Close()
	fmt.Println("connected!")

	sphereClient := sphere.NewEnvironmentAPIClient(conn)
	_, err = sphereClient.Info(context.Background(), &sphere.Empty{})
	require.Nil(t, err)
	server := &Server{Client: sphereClient}
	return server
}
